"""Shared pseudonymization helper — kept in one place so both scrapers hash
review identifiers the same way, and so the method is auditable in one spot
rather than duplicated.

Changed in this revision: `hash_id` now takes any number of parts instead
of a single string, joining them with "|" before hashing. This is a
backward-compatible signature change (a single call like
`hash_id(review_id)` still works unchanged) — it exists so the Apple side
can namespace its hash as `hash_id("apple", raw_id)` without every caller
having to build that composite string by hand.
"""

import hashlib


def hash_id(*parts: object) -> str:
    """Non-reversible pseudonymous identifier for a review.

    A plain SHA-256 hex digest of the given parts joined with "|",
    truncated to 24 characters — long enough that collisions are not a
    practical concern at this corpus's scale, short enough to stay
    readable in a CSV.
    """
    value = "|".join(str(p) for p in parts)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:24]
