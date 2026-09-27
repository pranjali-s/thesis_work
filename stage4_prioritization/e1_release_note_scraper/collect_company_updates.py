#!/usr/bin/env python3
"""Discover company-authored product announcements and extract reviewable change claims."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup
from apple_history import APPLE_APPS, parse_apple, substantive_note, APPLE_FIELDS


HEADERS = {"User-Agent": "AcademicProductUpdatesCollector/1.0 (public pages; contact: researcher)",
           "Accept-Language": "en-US,en;q=0.9"}
PORTALS = {
    "robinhood_newsroom": "https://robinhood.com/us/en/newsroom/",
    "robinhood_press": "https://investors.robinhood.com/press-releases",
    "coinbase_blog": "https://www.coinbase.com/blog/landing",
    "trading212_community": "https://community.trading212.com/c/whats-new/13.json",
    "trading212_help": "https://helpcentre.trading212.com/hc/en-us/sections/33385536291101-Platform-Announcements",
}
SEED_URLS = {
    "robinhood": [
        "https://robinhood.com/us/en/newsroom/robinhood-social-beta/",
        "https://robinhood.com/us/en/newsroom/robinhood-presents-yes-no-event/",
        "https://robinhood.com/us/en/newsroom/introducing-strategies-banking-and-cortex/",
        "https://robinhood.com/us/en/newsroom/introducing-robinhood-legend-charts-on-mobile/",
        "https://robinhood.com/us/en/newsroom/robinhood-prediction-markets-hub/",
        "https://robinhood.com/us/en/newsroom/robinhood-cryptocom/",
    ],
    "coinbase": [
        "https://www.coinbase.com/blog/you-can-now-participate-in-ipos-on-coinbase",
        "https://www.coinbase.com/blog/were-lowering-fees-for-many-active-traders-on-coinbase-advanced",
        "https://www.coinbase.com/blog/coinbase-usdc-earning-brazil-canada",
        "https://www.coinbase.com/blog/coinbase-launches-derivative-contracts-in-canada",
        "https://www.coinbase.com/blog/coinbase-brings-direct-brl-trading-for-usdc",
        "https://www.coinbase.com/blog/designing-the-earn-center-one-home-for-everything-your-crypto-can-earn",
        "https://www.coinbase.com/blog/building-economic-freedom-one-pixel-at-a-time",
        "https://www.coinbase.com/blog/coinbase-unlocks-millions-of-assets-with-dex-trading",
        "https://www.coinbase.com/blog/earn-competitive-yields-by-lending-your-usdc",
    ],
}
CHANGE = re.compile(r"\b(launch(?:ed|ing)?|introduc(?:ed|ing)?|new|now (?:available|offers?|supports?|can)|"
                    r"roll(?:ed|ing)? out|redesign(?:ed)?|updat(?:ed|ing)?|add(?:ed|ing)?|"
                    r"expand(?:ed|ing)?|lower(?:ed|ing)?|simplif(?:ied|ying)|"
                    r"access|feature|integration|support(?:s|ed|ing)?|allow(?:s|ed|ing)?)\b", re.I)
FUTURE = re.compile(r"\b(coming (?:soon|later)|will (?:launch|be available|roll out|introduce|add)|"
                    r"plan(?:s|ned)? to|expected to|preview(?:ed)?|upcoming)\b", re.I)
BETA = re.compile(r"\b(beta|pilot|limited test|select(?:ed)? (?:users|customers))\b", re.I)
BUSINESS = re.compile(r"\b(banks?|institutional|developers?|API|enterprise|business|"
                      r"merchant|infrastructure|internal teams?)\b", re.I)
CORPORATE = re.compile(r"\b(earnings|quarterly results|board of directors|operating data|"
                       r"conference|shareholder|convertible notes|fund I[I]? invests)\b", re.I)
ARTICLE_FIELDS = ["app", "portal", "publication_date", "date_basis", "title", "url",
                  "author", "body_text", "body_sha256", "retrieved_at_utc", "relevance_hint"]
CLAIM_FIELDS = ["app", "publication_date", "date_basis", "source_title", "change_text",
                "timing_hint", "audience_hint", "source_url", "source_portal", "review_status"]


def normalize_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path.rstrip("/") or "/", "", ""))


def iso_date(value: str | None) -> str:
    if not value:
        return ""
    match = re.search(r"(?<!\d)(20\d\d-\d\d-\d\d)(?!\d)", value)
    if match:
        return match.group(1)
    for fmt in ("%b %d, %Y", "%B %d, %Y", "%a, %d %b %Y %H:%M:%S %z"):
        try:
            return datetime.strptime(value.strip(), fmt).date().isoformat()
        except ValueError:
            pass
    match = re.search(r"\b([A-Z][a-z]{2,8} \d{1,2}, 20\d\d)\b", value)
    return iso_date(match.group(1)) if match else ""


def json_dates(obj) -> list[str]:
    if isinstance(obj, dict):
        kind = obj.get("@type") or ""
        kinds = kind if isinstance(kind, list) else [kind]
        values = ([obj["datePublished"]] if any("Article" in str(k) or "Posting" in str(k) for k in kinds)
                  and isinstance(obj.get("datePublished"), str) else [])
        for value in obj.values():
            values.extend(json_dates(value))
        return values
    return sum((json_dates(item) for item in obj), []) if isinstance(obj, list) else []


class Collector:
    def __init__(self, output: Path, start: date | None, end: date, max_articles: int):
        self.out, self.start, self.end, self.max_articles = output, start, end, max_articles
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.article_urls: dict[str, tuple[str, str]] = {}
        self.articles: list[dict] = []
        self.claims: list[dict] = []
        self.undated: list[dict] = []
        self.help_doc_changes: list[dict] = []
        self.errors: list[dict] = []
        self.coverage: dict[str, dict] = {}
        self.seen: set[str] = set()
        self.trading_users: dict[str, dict] = {}
        self.apple_rows: list[dict] = []
        (output / "sources").mkdir(parents=True, exist_ok=True)
        self.collected = datetime.now(timezone.utc).isoformat(timespec="seconds")

    def get(self, url: str) -> tuple[bytes, str]:
        for attempt in range(3):
            try:
                response = self.session.get(url, timeout=35, allow_redirects=True)
                if response.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                response.raise_for_status()
                raw = response.content
                if len(raw) > 18_000_000:
                    raise ValueError("Response exceeds 18 MB cap")
                if b"<title>Site Unavailable</title>" in raw[:1000]:
                    raise RuntimeError("Network returned a Site Unavailable placeholder")
                file = self.out / "sources" / (hashlib.sha256(url.encode()).hexdigest()[:20] + ".html")
                file.write_bytes(raw)
                time.sleep(0.25)
                return raw, response.url
            except (requests.RequestException, ValueError, RuntimeError) as exc:
                if attempt == 2:
                    raise RuntimeError(f"{url}: {exc}") from exc
                time.sleep(2 ** attempt)
        raise AssertionError("unreachable")

    def fail(self, portal: str, url: str, exc: Exception) -> None:
        logging.warning("%s: %s", portal, exc)
        self.errors.append({"portal": portal, "url": url, "error": str(exc)})

    def add_url(self, app: str, portal: str, url: str, lastmod: str = "") -> None:
        # An item last modified before the start cannot have been first published
        # during the collection window. Absence of lastmod never excludes a page.
        if self.start and iso_date(lastmod) and date.fromisoformat(iso_date(lastmod)) < self.start:
            return
        url = normalize_url(url)
        host = urlsplit(url).netloc
        allowed = {"robinhood.com", "investors.robinhood.com", "www.coinbase.com",
                   "helpcentre.trading212.com"}
        if host in allowed and url.startswith("https://"):
            self.article_urls[url] = (app, portal)

    def discover_links(self, portal: str, app: str, index: str, path_prefix: str) -> None:
        pending, seen = [index], set()
        found = 0
        while pending:
            page = pending.pop(0)
            if page in seen:
                continue
            seen.add(page)
            try:
                raw, final = self.get(page)
                soup = BeautifulSoup(raw, "html.parser")
                for link in soup.select("a[href]"):
                    href = urljoin(final, link["href"])
                    parts = urlsplit(href)
                    if portal == "coinbase_blog":
                        acceptable = bool(re.fullmatch(r"/(?:[a-z]{2}(?:-[a-z]{2})?/)?blog/[^/]+/?", parts.path))
                        acceptable &= parts.path.rstrip("/").split("/")[-1] not in {"landing", "search"}
                    else:
                        acceptable = parts.path.startswith(path_prefix) and parts.path.rstrip("/") != urlsplit(index).path.rstrip("/")
                    if acceptable:
                        self.add_url(app, portal, href)
                        found += 1
                    # Only follow a visible 'next' link within the same index.
                    label = link.get_text(" ", strip=True).lower()
                    next_link = label in {"next", "next ›", "next →", "older", "older posts"} or "next" in link.get("rel", [])
                    if (next_link and parts.netloc == urlsplit(index).netloc and
                            parts.path.rstrip("/") == urlsplit(index).path.rstrip("/") and
                            href not in seen and href not in pending):
                        pending.append(href)
                if len(seen) > 1000:
                    raise RuntimeError("Index pagination exceeded 1000 pages")
            except Exception as exc:
                self.fail(portal, page, exc)
                break
        self.coverage[portal] = {"index": index, "pages_seen": len(seen), "links_seen": found}

    def sitemap(self, url: str, app: str, portal: str, prefix: str, depth: int = 0) -> None:
        if depth > 3:
            return
        try:
            raw, _ = self.get(url)
            root = ET.fromstring(raw)
            for child in root:
                loc = child.findtext("{*}loc") or ""
                if child.tag.endswith("sitemap"):
                    # Avoid unrelated giant price / market / profile indexes.
                    if ("blog" in loc or "newsroom" in loc) and depth < 3:
                        self.sitemap(loc, app, portal, prefix, depth + 1)
                elif urlsplit(loc).path.startswith(prefix):
                    self.add_url(app, portal, loc, child.findtext("{*}lastmod") or "")
        except Exception as exc:
            self.fail(portal, url, exc)

    def discover(self) -> None:
        for app, urls in SEED_URLS.items():
            for url in urls:
                self.add_url(app, "robinhood_newsroom" if app == "robinhood" else "coinbase_blog", url)
        self.discover_links("robinhood_newsroom", "robinhood", PORTALS["robinhood_newsroom"],
                            "/us/en/newsroom/")
        self.discover_links("robinhood_press", "robinhood", PORTALS["robinhood_press"],
                            "/news-releases/news-release-details/")
        self.discover_links("coinbase_blog", "coinbase", PORTALS["coinbase_blog"], "/blog/")
        self.sitemap("https://www.coinbase.com/sitemap-blog.xml", "coinbase",
                     "coinbase_blog", "/blog/")
        # Robinhood's root sitemap can be large, but only newsroom URLs are queued.
        self.sitemap("https://robinhood.com/sitemap.xml", "robinhood",
                     "robinhood_newsroom", "/us/en/newsroom/")
        self.discover_links("trading212_help", "trading212", PORTALS["trading212_help"],
                            "/hc/en-us/articles/")

    def extract_article(self, url: str, app: str, portal: str) -> None:
        raw, final = self.get(url)
        soup = BeautifulSoup(raw, "html.parser")
        title_node = soup.find("h1")
        if not title_node:
            raise ValueError("Missing article heading")
        title = title_node.get_text(" ", strip=True)
        published, basis = "", ""
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                for value in json_dates(json.loads(script.string or script.get_text())):
                    published = iso_date(value)
                    if published:
                        basis = "structured_datePublished"
                        break
            except (ValueError, TypeError):
                pass
            if published:
                break
        if not published:
            for key in ("article:published_time", "datePublished", "pubdate"):
                tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
                if tag and iso_date(tag.get("content")):
                    published, basis = iso_date(tag["content"]), "publication_meta"
                    break
        if not published:
            anchor = title_node.find_parent(["article", "main"]) or soup.body
            for element in list(anchor.find_all("time", attrs={"datetime": True}))[:5]:
                if iso_date(element["datetime"]):
                    published, basis = iso_date(element["datetime"]), "article_time"
                    break
        if not published:
            # Inspect the vicinity of the article heading; avoid sidebar/recent-story dates.
            snippet = title_node.parent.get_text(" ", strip=True)[:450]
            nearby_date = title_node.find_previous(["h5", "time"])
            for value in (snippet, nearby_date.get_text(" ", strip=True) if nearby_date else ""):
                if value and iso_date(str(value)):
                    published, basis = iso_date(str(value)), "heading_neighbour"
                    break
        if not published and portal == "trading212_help":
            match = re.search(r"/articles/(\d+)", urlsplit(final).path)
            if match:
                api_url = f"https://helpcentre.trading212.com/api/v2/help_center/en-us/articles/{match.group(1)}.json"
                try:
                    api_raw, _ = self.get(api_url)
                    entry = json.loads(api_raw).get("article", {})
                    published = iso_date(entry.get("created_at"))
                    basis = "help_article_created_at" if published else ""
                    modified = iso_date(entry.get("updated_at"))
                    if modified and (self.start is None or self.start <= date.fromisoformat(modified)) and date.fromisoformat(modified) <= self.end:
                        self.help_doc_changes.append({"title": title, "article_created_at": published,
                                                      "article_updated_at": modified, "url": final,
                                                      "note": "Documentation update, not verified app rollout"})
                except Exception as exc:
                    self.fail("trading212_help_api", api_url, exc)
        if not published:
            self.undated.append({"app": app, "portal": portal, "title": title, "url": final,
                                 "reason": "No trustworthy publication date found"})
            return
        if (self.start and date.fromisoformat(published) < self.start) or date.fromisoformat(published) > self.end:
            return
        container = title_node.find_parent("article") or soup.find("main") or soup.body
        if container is None:
            raise ValueError("Missing article body")
        content = []
        started = False
        for item in container.find_all(["h1", "h2", "h3", "p", "li"]):
            if item is title_node:
                started = True
                continue
            if not started:
                continue
            line = " ".join(item.get_text(" ", strip=True).split())
            if line.lower() in {"recent stories", "share", "related articles", "disclaimers",
                                "about robinhood", "articles in this section"}:
                break
            if line and len(line) >= 18 and line not in content:
                content.append(line)
        body = "\n".join(content)[:60000]
        if len(body) < 35:
            raise ValueError("Article body extraction was too short; inspect the saved page")
        relevance = "possible_product_change" if CHANGE.search(title + " " + body[:800]) else "other_review"
        if CORPORATE.search(title):
            relevance = "corporate_review"
        row = dict(app=app, portal=portal, publication_date=published, date_basis=basis,
                   title=title, url=final, author="", body_text=body,
                   body_sha256=hashlib.sha256(body.encode()).hexdigest(),
                   retrieved_at_utc=self.collected, relevance_hint=relevance)
        self.articles.append(row)
        for line in content:
            if CHANGE.search(line) and len(line) <= 900 and not re.match(r"^(disclaimers?|copyright)", line, re.I):
                self.add_claim(row, line)

    def add_claim(self, article: dict, line: str) -> None:
        hint = ("announced_future" if FUTURE.search(line) else
                "limited_beta" if BETA.search(line) else "timing_requires_review")
        audience = "business_or_developer_review" if BUSINESS.search(line) else "consumer_review"
        self.claims.append(dict(app=article["app"], publication_date=article["publication_date"],
                                date_basis=article["date_basis"], source_title=article["title"],
                                change_text=line, timing_hint=hint, audience_hint=audience,
                                source_url=article["url"], source_portal=article["portal"],
                                review_status="UNVERIFIED_CANDIDATE"))

    def trading212(self) -> None:
        portal, category_url = "trading212_community", PORTALS["trading212_community"]
        next_url = category_url
        seen_pages, seen_topics = set(), set()
        self.coverage[portal] = {"index": category_url, "pages_seen": 0, "topics_seen": 0}
        while next_url and next_url not in seen_pages:
            seen_pages.add(next_url)
            try:
                raw, _ = self.get(next_url)
                category = json.loads(raw)
                self.trading_users.update({u["username"]: u for u in category.get("users", [])})
                topic_list = category.get("topic_list", {})
                topics = topic_list.get("topics", [])
                self.coverage[portal]["pages_seen"] += 1
                for topic in topics:
                    if topic["id"] in seen_topics:
                        continue
                    seen_topics.add(topic["id"])
                    created = iso_date(topic.get("created_at"))
                    bumped = iso_date(topic.get("bumped_at"))
                    if ((created and (self.start is None or date.fromisoformat(created) >= self.start) and date.fromisoformat(created) <= self.end) or
                            (bumped and (self.start is None or date.fromisoformat(bumped) >= self.start) and date.fromisoformat(bumped) <= self.end)):
                        self.discourse_topic(topic)
                self.coverage[portal]["topics_seen"] = len(seen_topics)
                more = topic_list.get("more_topics_url")
                next_url = urljoin("https://community.trading212.com", more) if more else ""
                if next_url and urlsplit(next_url).netloc != "community.trading212.com":
                    raise ValueError("Unexpected community pagination host")
            except Exception as exc:
                self.fail(portal, next_url, exc)
                break

    def discourse_topic(self, topic: dict) -> None:
        url = f"https://community.trading212.com/t/{topic['id']}.json"
        try:
            raw, _ = self.get(url)
            data = json.loads(raw)
            users = {u["username"]: u for u in data.get("details", {}).get("participants", [])}
            users.update(self.trading_users)
            posts = data.get("post_stream", {}).get("posts", [])
            stream = data.get("post_stream", {}).get("stream", [])
            present = {post["id"] for post in posts}
            missing = [post_id for post_id in stream if post_id not in present]
            # Discourse often embeds only the first 20 posts, while an old topic may
            # have a relevant staff announcement in a recent reply.
            for offset in range(0, len(missing), 20):
                batch = missing[offset:offset + 20]
                endpoint = (f"https://community.trading212.com/t/{topic['id']}/posts.json?" +
                            urlencode([("post_ids[]", post_id) for post_id in batch]))
                try:
                    extra, _ = self.get(endpoint)
                    posts.extend(json.loads(extra).get("post_stream", {}).get("posts", []))
                except Exception as exc:
                    self.fail("trading212_community_posts", endpoint, exc)
            # Initial posts are authoritative only when posted by an identified team member.
            # Staff replies are separate dated claims, never re-dated to the original topic.
            for post in posts:
                date_value = iso_date(post.get("created_at"))
                if not date_value or (self.start and date.fromisoformat(date_value) < self.start) or date.fromisoformat(date_value) > self.end:
                    continue
                user = users.get(post.get("username"), {})
                staff = (user.get("primary_group_name") == "trading212_team" or
                         user.get("flair_name") == "trading212_team" or
                         post.get("primary_group_name") == "trading212_team" or
                         post.get("flair_name") == "trading212_team")
                if not staff:
                    continue
                body = BeautifulSoup(post.get("cooked") or "", "html.parser").get_text(" ", strip=True)
                body = " ".join(body.split())
                if len(body) < 25:
                    continue
                post_url = f"https://community.trading212.com/t/{topic['id']}/{post.get('post_number', 1)}"
                row = dict(app="trading212", portal="trading212_staff_post", publication_date=date_value,
                           date_basis="post_created_at", title=data.get("title", topic.get("title", "")),
                           url=post_url, author=post.get("username") or "", body_text=body[:60000],
                           body_sha256=hashlib.sha256(body.encode()).hexdigest(),
                           retrieved_at_utc=self.collected, relevance_hint="staff_post_review")
                self.articles.append(row)
                for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z])", body):
                    if CHANGE.search(sentence) and 25 <= len(sentence) <= 900:
                        self.add_claim(row, sentence)
            if len(stream) > len({post["id"] for post in posts}):
                self.coverage["trading212_community"]["possibly_unfetched_posts"] = True
        except Exception as exc:
            self.fail("trading212_community", url, exc)

    def run(self) -> None:
        self.discover()
        urls = list(self.article_urls.items())
        if self.max_articles:
            urls = urls[:self.max_articles]
        for index, (url, (app, portal)) in enumerate(urls, 1):
            try:
                self.extract_article(url, app, portal)
            except Exception as exc:
                self.fail(portal, url, exc)
            if index % 100 == 0:
                logging.info("Processed %d/%d company URLs", index, len(urls))
        if self.max_articles and len(self.article_urls) > self.max_articles:
            self.errors.append({"portal": "discovery", "url": "", "error": "max_articles cap reached"})
        self.trading212()
        self.collect_apple()

    def collect_apple(self) -> None:
        for app, (country, app_id) in APPLE_APPS.items():
            url = f"https://apps.apple.com/{country}/app/id{app_id}"
            try:
                raw, _ = self.get(url)
                rows = parse_apple(raw, app, country, url, self.collected)
                self.apple_rows.extend(row for row in rows if
                                       (self.start is None or date.fromisoformat(row["version_date"]) >= self.start)
                                       and date.fromisoformat(row["version_date"]) <= self.end)
                self.coverage[f"apple_{app}"] = {"url": url, "versions_visible": len(rows),
                    "oldest_visible_date": min(row["version_date"] for row in rows),
                    "newest_visible_date": max(row["version_date"] for row in rows)}
            except Exception as exc:
                self.fail(f"apple_{app}", url, exc)


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=date.fromisoformat, default=None,
                        help="Optional inclusive publication/version date; default: no lower date bound")
    parser.add_argument("--end", type=date.fromisoformat, default=None)
    parser.add_argument("--output", type=Path, default=Path("output/company_updates"))
    parser.add_argument("--max-articles", type=int, default=0,
                        help="Optional cap on company article pages; default 0 means all discovered")
    args = parser.parse_args()
    end = args.end or datetime.now(timezone.utc).date()
    if (args.start and args.start > end) or end > datetime.now(timezone.utc).date() or args.max_articles < 0:
        parser.error("Require start <= end <= today (UTC) and max-articles >= 0")
    args.output.mkdir(parents=True, exist_ok=True)
    collector = Collector(args.output, args.start, end, args.max_articles)
    collector.run()
    articles = list({row["url"]: row for row in collector.articles}.values())
    claims = list({(row["source_url"], row["change_text"]): row for row in collector.claims}.values())
    articles.sort(key=lambda r: (r["app"], r["publication_date"], r["url"]))
    claims.sort(key=lambda r: (r["app"], r["publication_date"], r["source_url"]))
    write_csv(args.output / "company_articles.csv", ARTICLE_FIELDS, articles)
    write_csv(args.output / "feature_candidates.csv", CLAIM_FIELDS, claims)
    apple_rows = sorted(collector.apple_rows, key=lambda r: (r["app"], r["version_date"], r["version"]))
    write_csv(args.output / "apple_version_history.csv", APPLE_FIELDS, apple_rows)
    write_csv(args.output / "apple_feature_notes.csv", APPLE_FIELDS,
              [r for r in apple_rows if r["feature_relevance"] == "specific_change_candidate"])
    write_csv(args.output / "undated_to_review.csv", ["app", "portal", "title", "url", "reason"],
              collector.undated)
    write_csv(args.output / "help_document_changes.csv",
              ["title", "article_created_at", "article_updated_at", "url", "note"],
              collector.help_doc_changes)
    manifest = {
        "window_start": args.start.isoformat() if args.start else None, "window_end": end.isoformat(),
        "collected_at_utc": collector.collected, "articles": len(articles), "candidate_claims": len(claims),
        "apple_versions_visible_in_window": len(apple_rows),
        "apple_specific_change_candidates": sum(r["feature_relevance"] == "specific_change_candidate" for r in apple_rows),
        "discovered_pages": len(collector.article_urls), "coverage": collector.coverage,
        "errors": collector.errors, "portals": PORTALS,
        "method": "Official company articles, dated Trading 212 staff posts and visible Apple App Store version history; candidates require manual review.",
        "caveats": ["Publication date is not the confirmed date a feature reached every user.",
                    "Future, beta, region-limited, and business products require separate verification.",
                    "Current help article edits do not establish historical feature-launch dates.",
                    "Search indexes, sitemaps, dynamic lists, and Discourse pagination can omit announcements.",
                    "Apple exposes only its visible version-history window; an app version date does not establish feature availability."]
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                                 encoding="utf-8")
    logging.info("%d company articles, %d candidate claims, %d source errors",
                 len(articles), len(claims), len(collector.errors))
    return 0 if not collector.errors else 1


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    raise SystemExit(main())
