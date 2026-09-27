"""Public Apple App Store version history, with conservative feature-note triage."""

from __future__ import annotations

import hashlib
import re
from datetime import date

from bs4 import BeautifulSoup

APPLE_APPS = {
    "robinhood": ("us", "938003185"),
    "coinbase": ("us", "886427730"),
    "trading212": ("gb", "566325832"),
}
APPLE_FIELDS = ["app", "platform", "country", "version", "version_date", "release_notes",
                "feature_relevance", "source_url", "retrieved_at_utc", "note_sha256", "source_html_sha256"]
GENERIC = re.compile(r"\b(bug fixes?|performance improvements?|usability improvements?|minor improvements?|"
                     r"stability improvements?|general improvements?|under the hood|thank you for choosing|"
                     r"rate us|any feedback|easiest and most trusted place|latest update)\b", re.I)
CHANGE = re.compile(r"\b(launch(?:ed)?|introduc(?:ed|ing)|add(?:ed)?|new|now (?:can|available)|"
                    r"redesign(?:ed)?|updat(?:ed)?|improv(?:ed|ing)|support(?:s|ed)?|"
                    r"enable(?:d)?|trade|transfer|earn|deposit|withdraw)\b", re.I)


def substantive_note(note: str) -> bool:
    """Only shortlist notes with a concrete action after removing standard boilerplate."""
    relevant = GENERIC.sub(" ", note)
    relevant = re.sub(r"\b(this update includes|here's what's|love the app|reach us at|"
                      r"coinbase is|trading 212|robinhood)\b", " ", relevant, flags=re.I)
    relevant = re.sub(r"\b(?:https?://\S+|\S+@\S+)\b", " ", relevant)
    return len(relevant.split()) >= 8 and bool(CHANGE.search(relevant))


def parse_apple(html: bytes, app: str, country: str, url: str, retrieved: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    heading = soup.find("h1", attrs={"data-testid": "content-modal-title"},
                        string=re.compile("Version History", re.I))
    header = heading.find_parent("div", class_="header-container") if heading else None
    content = header.find_next_sibling("div", class_="content-container") if header else None
    if content is None:
        raise ValueError("Apple version history is missing or changed format")
    rows = []
    for item in content.select("ul > li"):
        metadata = item.select_one(".metadata")
        stamp = metadata.find("time", attrs={"datetime": True}) if metadata else None
        version = metadata.find("span") if metadata else None
        notes = item.select_one("p span")
        if not (stamp and version and notes):
            continue
        version_date = stamp["datetime"][:10]
        date.fromisoformat(version_date)
        note = notes.get_text("\n", strip=True)
        version_text = version.get_text(" ", strip=True)
        if not note or not version_text:
            continue
        rows.append({"app": app, "platform": "apple_app_store", "country": country.upper(),
                     "version": version_text, "version_date": version_date,
                     "release_notes": note,
                     "feature_relevance": "specific_change_candidate" if substantive_note(note) else "generic_or_no_specific_feature",
                     "source_url": url, "retrieved_at_utc": retrieved,
                     "note_sha256": hashlib.sha256(note.encode()).hexdigest(),
                     "source_html_sha256": hashlib.sha256(html).hexdigest()})
    if not rows:
        raise ValueError("No dated versions parsed from the Apple page")
    return rows
