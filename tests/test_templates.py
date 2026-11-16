"""Run with: python -m unittest discover tests"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
from fetch_drivers import template_values  # noqa: E402


class TemplateValuesTest(unittest.TestCase):
    def test_values_of_a_driver(self):
        driver = {'id': 'max-verstappen', 'abbreviation': 'ver', 'firstName': 'Max', 'lastName': 'Verstappen'}
        self.assertEqual(
            template_values(driver),
            {
                'id': 'max-verstappen',
                'tla': 'VER',
                'ref': 'MAXVER01',
                'ref_lower': 'maxver01',
                'initial': 'M',
                'first': 'Max',
                'last': 'Verstappen',
            },
        )

    def test_accents_are_removed(self):
        driver = {'id': 'raikkonen', 'abbreviation': 'RAI', 'firstName': 'Kimi', 'lastName': 'Räikkönen'}
        values = template_values(driver)
        self.assertEqual((values['ref'], values['last']), ('KIMRAI01', 'Raikkonen'))

    def test_names_with_several_words_are_joined_by_underscores(self):
        driver = {'id': 'de-tomaso', 'abbreviation': 'DET', 'firstName': 'Alejandro', 'lastName': 'De Tomaso'}
        self.assertEqual(template_values(driver)['last'], 'De_Tomaso')


if __name__ == '__main__':
    unittest.main()
