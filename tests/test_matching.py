"""Run with: python -m unittest discover tests"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
from matching import match_pages  # noqa: E402


def driver(id: str, name: str, first: str, last: str, full: str) -> dict[str, str]:
    return {'id': id, 'name': name, 'firstName': first, 'lastName': last, 'fullName': full}


DRIVERS = [
    driver('raikkonen', 'Kimi Räikkönen', 'Kimi', 'Räikkönen', 'Kimi-Matias Räikkönen'),
    driver('bhanudej', 'Birabongse Bhanudej', 'Birabongse', 'Bhanudej', 'Prince Birabongse Bhanudej Bhanubandh'),
    driver('foyt', 'Anthony Joseph Foyt', 'Anthony Joseph', 'Foyt', 'Anthony Joseph Foyt'),
    driver('zhou', 'Guanyu Zhou', 'Guanyu', 'Zhou', 'Guanyu Zhou'),
    driver('david-walker', 'David Walker', 'David', 'Walker', 'David Walker'),
    driver('peter-walker', 'Peter Walker', 'Peter', 'Walker', 'Peter Douglas Conyers Walker'),
    driver('crossley', 'Geoffrey Crossley', 'Geoffrey', 'Crossley', 'Geoffrey Crossley'),
    driver('dambrosio', "Jérôme d'Ambrosio", 'Jérôme', "D'Ambrosio", "Jérôme d'Ambrosio"),
    driver('d-orey', "Fritz d'Orey", 'Fritz', "d'Orey", "Fritz d'Orey"),
    driver('unser', 'Bobby Unser', 'Bobby', 'Unser', 'Robert William Unser'),
    driver('unser-jr', 'Jerry Unser Jr.', 'Jerry', 'Unser Jr.', 'Jeremy Michael Unser Jr.'),
    driver('schroeder', 'Rob Schroeder', 'Rob', 'Schroeder', 'Robert Schroeder'),
    driver('thorne', 'Leslie Thorne', 'Leslie', 'Thorne', 'Leslie Thorne'),
    driver('bels', 'Tom Belsø', 'Tom', 'Belsø', 'Tom Belsø'),
]


def match(*slugs: str) -> dict[str, str]:
    matches, _ = match_pages(list(slugs), DRIVERS)
    return {m.slug: m.driver_id for m in matches}


class MatchingTest(unittest.TestCase):
    def test_exact_names_without_accents(self):
        self.assertEqual(match('kimi-raikkonen'), {'kimi-raikkonen': 'raikkonen'})
        self.assertEqual(match('tom-belso'), {'tom-belso': 'bels'})

    def test_apostrophes_in_both_ways(self):
        self.assertEqual(match('fritz-d-orey'), {'fritz-d-orey': 'd-orey'})
        self.assertEqual(match('jerome-dambrosio'), {'jerome-dambrosio': 'dambrosio'})

    def test_shortened_and_initials_names(self):
        self.assertEqual(match('geoff-crossley'), {'geoff-crossley': 'crossley'})
        self.assertEqual(match('aj-foyt'), {'aj-foyt': 'foyt'})
        self.assertEqual(match('dave-walker'), {'dave-walker': 'david-walker'})

    def test_title_and_name_in_other_order(self):
        self.assertEqual(match('prince-bira'), {'prince-bira': 'bhanudej'})
        self.assertEqual(match('zhou-guanyu'), {'zhou-guanyu': 'zhou'})

    def test_same_surname_is_told_apart_by_first_name(self):
        self.assertEqual(match('jerry-unser'), {'jerry-unser': 'unser-jr'})
        self.assertEqual(match('bobby-unser'), {'bobby-unser': 'unser'})

    def test_a_driver_that_is_not_ours_is_not_given_to_a_similar_one(self):
        _, unmatched = match_pages(['joel-thorne', 'bob-schroeder', 'geki'], DRIVERS)
        self.assertEqual(unmatched, ['joel-thorne', 'bob-schroeder', 'geki'])

    def test_an_exact_match_has_priority_over_a_similar_page(self):
        self.assertEqual(
            match('rob-schroeder', 'bob-schroeder'), {'rob-schroeder': 'schroeder'}
        )

    def test_one_driver_is_not_given_to_two_pages(self):
        self.assertEqual(len(match('david-walker', 'dave-walker')), 1)


if __name__ == '__main__':
    unittest.main()
