"""Matches the pages of a site (named by a slug like `aj-foyt`) with the drivers of RaceDex, by their names

1. Exact: the slug is the name, the full name or "first last" name of exactly one driver.
2. Smart: for the pages left, every word of the slug has to look like a word of the names of the driver (the same, the
   start of it, the initials, or a very similar spelling): `geoff-crossley` is Geoffrey Crossley, `aj-foyt` is Anthony
   Joseph Foyt and `zhou-guanyu` is Guanyu Zhou. If two drivers fit equally well, the page is left unmatched.

A page of a driver that is not in our data stays unmatched, instead of being given to a driver with a similar name
(Bob Schroeder is not Rob Schroeder).
"""

import difflib
import itertools
import os
import re
import unicodedata
from dataclasses import dataclass

MIN_SIMILARITY = 0.8
AMBIGUITY_MARGIN = 0.02


@dataclass
class Match:
    slug: str
    driver_id: str
    exact: bool


def words(text: str, join_apostrophes: bool = True) -> list[str]:
    """The words of a text, without accents. `d'Orey` is `dorey`, or `d orey` if `join_apostrophes` is False"""
    ascii_text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower()
    return re.findall(r'[a-z0-9]+', re.sub(r"['’`]", '' if join_apostrophes else ' ', ascii_text))


def slugify(text: str, join_apostrophes: bool = True) -> str:
    return '-'.join(words(text, join_apostrophes))


def similarity(word: str, other: str) -> float:
    if word == other:
        return 1.0
    if min(len(word), len(other)) >= 3 and (word.startswith(other) or other.startswith(word)):
        return 0.95
    # Nicknames: dave / david, jerry / jeremy
    common = len(os.path.commonprefix([word, other]))
    if common >= 3 and common / min(len(word), len(other)) >= 0.6:
        return 0.85
    if min(len(word), len(other)) >= 4:
        return difflib.SequenceMatcher(None, word, other).ratio()
    return 0.0


def name_words(driver: dict[str, str]) -> tuple[list[str], set[str]]:
    """The words of all the names of the driver (with the ones next to each other joined: `de tomaso` -> `detomaso`)
    and the initials of the names that go together (`aj` for Anthony Joseph)"""
    names = [driver['name'], driver['fullName'], f"{driver['firstName']} {driver['lastName']}"]
    candidates: list[str] = []
    initials: set[str] = set()
    for name, join in itertools.product(names, (True, False)):
        parts = words(name, join)
        candidates += parts + [a + b for a, b in zip(parts, parts[1:])]
        initials |= {''.join(part[0] for part in parts[i : i + size]) for size in (2, 3) for i in range(len(parts) - size + 1)}
    return candidates, initials


def score(slug_words: list[str], candidates: list[str], initials: set[str]) -> float | None:
    """How well the words of the slug fit a driver (0-1), or None if some word doesn't fit"""
    similarities = []
    for word in slug_words:
        best = max((similarity(word, candidate) for candidate in candidates), default=0.0)
        if len(word) <= 3 and word in initials:
            best = max(best, 0.9)
        if best < MIN_SIMILARITY:
            return None
        similarities.append(best)
    return sum(similarities) / len(similarities) if 1.0 in similarities else None


def match_pages(slugs: list[str], drivers: list[dict[str, str]]) -> tuple[list[Match], list[str]]:
    """The slugs that were matched with a driver, and the ones that were not"""
    matches: list[Match] = []
    claimed: set[str] = set()

    keys: dict[str, set[str]] = {}
    for driver in drivers:
        for name, join in itertools.product((driver['name'], driver['fullName'], f"{driver['firstName']} {driver['lastName']}"), (True, False)):
            keys.setdefault(slugify(name, join), set()).add(driver['id'])

    pending = []
    for slug in slugs:
        ids = keys.get(slug, set())
        if len(ids) == 1 and next(iter(ids)) not in claimed:
            claimed |= ids
            matches.append(Match(slug, next(iter(ids)), exact=True))
        else:
            pending.append(slug)

    candidates = {driver['id']: name_words(driver) for driver in drivers if driver['id'] not in claimed}
    unmatched = []
    for slug in pending:
        slug_words = words(slug)
        scores = sorted(
            ((score(slug_words, *candidates[driver_id]), driver_id) for driver_id in candidates if driver_id not in claimed and len(slug_words) > 1),
            key=lambda item: item[0] or 0,
            reverse=True,
        )
        scores = [item for item in scores if item[0] is not None]
        if scores and (len(scores) == 1 or scores[0][0] - scores[1][0] > AMBIGUITY_MARGIN):
            claimed.add(scores[0][1])
            matches.append(Match(slug, scores[0][1], exact=False))
        else:
            unmatched.append(slug)
    return matches, unmatched
