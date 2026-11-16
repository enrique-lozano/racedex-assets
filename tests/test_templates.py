"""Run with: python -m unittest discover tests"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
from fetch_drivers import render_template, template_values  # noqa: E402

VERSTAPPEN = {'id': 'max-verstappen', 'abbreviation': 'VER', 'firstName': 'Max', 'lastName': 'Verstappen'}


def render(template: str, driver: dict[str, str] = VERSTAPPEN, **extra: str) -> str:
    return render_template(template, template_values(driver) | extra)


class TemplateTest(unittest.TestCase):
    def test_the_case_of_the_placeholder_sets_the_case_of_the_value(self):
        self.assertEqual(render('{first3}{last3} {FIRST3}{LAST3} {First3}{Last3}'), 'maxver MAXVER MaxVer')
        self.assertEqual(render('{tla} {TLA}'), 'ver VER')
        self.assertEqual(render('{initial} {INITIAL}'), 'm M')

    def test_names_with_underscores(self):
        self.assertEqual(render('{First}_{Last}'), 'Max_Verstappen')
        self.assertEqual(render('{first}_{last}'), 'max_verstappen')

    def test_names_with_several_words(self):
        driver = {'id': 'de-tomaso', 'abbreviation': 'DET', 'firstName': 'Alejandro', 'lastName': 'De Tomaso'}
        self.assertEqual(render('{Last} {last} {LAST}', driver), 'De_Tomaso de_tomaso DE_TOMASO')

    def test_accents_are_removed(self):
        driver = {'id': 'raikkonen', 'abbreviation': 'RAI', 'firstName': 'Kimi', 'lastName': 'Räikkönen'}
        self.assertEqual(render('{FIRST3}{LAST3}01/{Last}', driver), 'KIMRAI01/Raikkonen')

    def test_a_real_template(self):
        self.assertEqual(
            render('https://example.com/{INITIAL}/{FIRST3}{LAST3}01_{First}_{Last}/{first3}{last3}01.png'),
            'https://example.com/M/MAXVER01_Max_Verstappen/maxver01.png',
        )
        self.assertEqual(render('https://example.com/{year}/{TLA}.png', year='2024'), 'https://example.com/2024/VER.png')


if __name__ == '__main__':
    unittest.main()
