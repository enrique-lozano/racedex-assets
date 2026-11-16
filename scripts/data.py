"""Reads the data of the RaceDex API that the scripts need: the drivers and the seasons they raced

The CSV files are read from the repository of the API on GitHub, or from another place with `--data` or the
RACEDEX_DATA_URL variable: the address of a folder with the CSV files (`.../data/csv`) or a folder of your computer.
"""

import csv
import io
import os
from pathlib import Path

import requests

DEFAULT_DATA_URL = 'https://raw.githubusercontent.com/enrique-lozano/F1-World-API/main/data/csv'
USER_AGENT = 'RaceDexAssets/1.0 (https://github.com/enrique-lozano/racedex-assets)'
ROOT = Path(__file__).resolve().parent.parent


def load_env_file() -> None:
    """Sets the variables of `.env` that are not already set"""
    env_file = ROOT / '.env'
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding='utf-8').splitlines():
        key, separator, value = line.partition('=')
        if separator and not line.lstrip().startswith('#'):
            os.environ.setdefault(key.strip(), value.strip().strip('"\''))


def data_source(option: str | None) -> str:
    return (option or os.environ.get('RACEDEX_DATA_URL') or DEFAULT_DATA_URL).rstrip('/')


def read_table(source: str, name: str) -> list[dict[str, str]]:
    if source.startswith(('http://', 'https://')):
        response = requests.get(f'{source}/{name}.csv', headers={'User-Agent': USER_AGENT}, timeout=60)
        response.raise_for_status()
        text = response.content.decode('utf-8')
    else:
        text = (Path(source) / f'{name}.csv').read_text(encoding='utf-8')
    return list(csv.DictReader(io.StringIO(text)))


def read_drivers(source: str) -> list[dict[str, str]]:
    return read_table(source, 'drivers')


def driver_seasons(source: str) -> dict[str, tuple[int, int]]:
    """driver id -> (first season, last season). Test drivers count as well"""
    season_of_entrant = {row['id']: int(row['season']) for row in read_table(source, 'entrantSeasons')}

    seasons: dict[str, tuple[int, int]] = {}
    for entry in read_table(source, 'entries'):
        season = season_of_entrant[entry['entrantSeasonId']]
        first, last = seasons.get(entry['driverId'], (season, season))
        seasons[entry['driverId']] = (min(first, season), max(last, season))
    return seasons
