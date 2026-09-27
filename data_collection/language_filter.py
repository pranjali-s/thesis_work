"""English-language verification heuristic.

Same method already used to verify the original Google-Play-only corpus:
a review is flagged as majority-non-English if more than half of its
alphabetic characters fall outside the basic ASCII letter range. This is a
heuristic, not a language classifier — it catches non-Latin scripts and
heavily accented text reliably, and can miss e.g. English-adjacent
Romance-language text that happens to use mostly ASCII letters. That
trade-off is inherited unchanged from the original collection's approach,
for comparability.
"""


def is_majority_non_ascii(text: str) -> bool:
    if not text:
        return False
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    non_ascii = sum(1 for c in letters if ord(c) > 127)
    return (non_ascii / len(letters)) > 0.5


def language_matches(text: str, lang: str) -> bool:
    """Added in this revision as a thin wrapper around the heuristic above,
    so callers can pass a language code (mirroring the working Apple script's
    `--language` argument) instead of calling the heuristic directly.

    `lang="all"` (or falsy) disables filtering entirely. `lang="en"` is the
    only code this heuristic actually discriminates on — anything else is
    passed through unfiltered rather than silently mis-filtered, since this
    is an ASCII-letter heuristic, not a real language classifier.
    """
    if not lang or lang == "all":
        return True
    if lang == "en":
        return not is_majority_non_ascii(text)
    return True
