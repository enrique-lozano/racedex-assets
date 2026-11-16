"""Downloads the driver cut-outs that are missing into drivers/{driverId}.webp, normalizing them (see normalize.py)

Usage: python -I scripts/fetch_drivers.py <drivers.csv of the RaceDex API> [--db racedex.db] [--attempts 3]

The images come from these sources, in this order. A driver that already has an image is skipped (also the ones added
by hand with add_photo.py), so the script can be re-run to pick up new drivers. To download one again, delete its image.

1. DRIVERS_SITEMAP_URL (environment variable): a sitemap with one page per driver, and an image in each. The pages are
   matched to our driver ids by name; the ones that don't match are in SLUG_OVERRIDES.
2. DRIVERS_FALLBACK_URLS (environment variable): URL templates separated by spaces, tried in order for the drivers
   that are still missing. The first one that returns a transparent image wins. A template can use:
     {id}    id of the driver in RaceDex
     {tla}   abbreviation of the driver, in capitals (VER)
     {ref}   first 3 letters of the first name + first 3 of the last name + 01, in capitals (MAXVER01)
     {year}  a season of the driver: from the last one back, `--attempts` seasons (needs the database)

Both variables are optional, but at least one is needed. They can be set in a `.env` file in the root of the repository
(see .env.example), which is not committed.
"""

import argparse
import csv
import io
import os
import re
import sqlite3
import sys
import time
import unicodedata
from pathlib import Path

import requests
from PIL import Image

# `python -I` doesn't add the script's directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from normalize import has_transparency, normalize  # noqa: E402

USER_AGENT = 'RaceDexAssets/1.0 (https://github.com/enrique-lozano/racedex-assets)'
DELAY_SECONDS = 0.3
MIN_IMAGE_SIZE = 200
ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / 'drivers'

# Page slug on the site -> our driver id
SLUG_OVERRIDES = {
    'prince-bira': 'bhanudej',
    'alessandro-de-tomaso': 'de-tomaso',
    'azdrubal-bayardo': 'fontes-bayardo',
    'dave-walker': 'david-walker',
    'francisco-godia': 'godia',
    'geoff-crossley': 'crossley',
    'gunther-bechem': 'bechem',
    'aj-foyt': 'foyt',
    'jerome-dambrosio': 'dambrosio',
    'jerry-unser': 'unser-jr',
    'ken-mcalpine': 'mcalpine',
    'pat-oconnor': 'oconnor',
    'tim-mayer': 'mayer',
    'kurt-ahrens': 'ahrens',
    'giuseppe-farina': 'farina',
    'oscar-galvez': 'galvez',
    'carlos-sainz': 'sainz',
    'zhou-guanyu': 'zhou',
}



def load_env_file() -> None:
    """Sets the variables of `.env` that are not already set"""
    env_file = ROOT / '.env'
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding='utf-8').splitlines():
        key, separator, value = line.partition('=')
        if separator and not line.lstrip().startswith('#'):
            os.environ.setdefault(key.strip(), value.strip().strip('"\''))


def get(url: str) -> bytes:
    response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=30)
    response.raise_for_status()
    return response.content


def try_get_image(url: str) -> bytes | None:
    """The image if the URL exists and is a big enough transparent image, otherwise None"""
    try:
        data = get(url)
        image = Image.open(io.BytesIO(data))
        image.load()
    except (requests.RequestException, OSError):
        return None
    finally:
        time.sleep(DELAY_SECONDS)

    return data if min(image.size) >= MIN_IMAGE_SIZE and has_transparency(image) else None


def slugify(text: str) -> str:
    ascii_text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', ascii_text).strip('-')


def reference(driver: dict[str, str]) -> str:
    letters = lambda name: slugify(name).replace('-', '').upper()[:3]
    return f"{letters(driver['firstName'])}{letters(driver['lastName'])}01"


def driver_seasons(database: Path) -> dict[str, tuple[int, int]]:
    """driver id -> (first season, last season)"""
    with sqlite3.connect(f'file:{database}?mode=ro', uri=True) as connection:
        rows = connection.execute(
            """
            SELECT e.driverId, MIN(es.season), MAX(es.season)
            FROM entries e JOIN entrantSeasons es ON es.id = e.entrantSeasonId
            GROUP BY e.driverId
            """
        ).fetchall()
    return {driver_id: (first, last) for driver_id, first, last in rows}


def fetch_from_sitemap(sitemap_url: str, drivers: list[dict[str, str]], missing: set[str]) -> tuple[dict[str, bytes], list[str]]:
    ids_by_name: dict[str, set[str]] = {}
    for driver in drivers:
        names = {driver['name'], driver['fullName'], f"{driver['firstName']} {driver['lastName']}"}
        for name in names:
            ids_by_name.setdefault(slugify(name), set()).add(driver['id'])

    sitemap = get(sitemap_url).decode()
    pages = {}
    for block in re.findall(r'<url>(.*?)</url>', sitemap, flags=re.S):
        slug = re.search(r'/drivers/([^/<]+)/</loc>', block)
        image = re.search(r'<image:loc>([^<]+)</image:loc>', block)
        if slug and image:
            pages[slug.group(1)] = image.group(1)

    found, unmatched = {}, []
    for slug, image_url in sorted(pages.items()):
        driver_id = SLUG_OVERRIDES.get(slug)
        if not driver_id:
            ids = ids_by_name.get(slug, set())
            driver_id = next(iter(ids)) if len(ids) == 1 else None
        if not driver_id:
            unmatched.append(slug)
        elif driver_id in missing:
            data = try_get_image(image_url)
            if data:
                found[driver_id] = data
            else:
                print(f'  {slug}: not a valid transparent image')
    return found, unmatched


def fetch_from_templates(
    templates: list[str],
    drivers: list[dict[str, str]],
    missing: set[str],
    seasons: dict[str, tuple[int, int]],
    attempts: int,
) -> dict[str, bytes]:
    found = {}
    for driver in drivers:
        if driver['id'] not in missing:
            continue

        values = {'id': driver['id'], 'tla': driver['abbreviation'].upper(), 'ref': reference(driver)}
        years = []
        if driver['id'] in seasons:
            first, last = seasons[driver['id']]
            years = list(range(last, max(first, last - attempts + 1) - 1, -1))

        for template in templates:
            urls = [template.format(**values, year=year) for year in years] if '{year}' in template else [template.format(**values)]
            data = next(filter(None, map(try_get_image, urls)), None)
            if data:
                found[driver['id']] = data
                break
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('drivers_csv', type=Path)
    parser.add_argument('--db', type=Path, help='RaceDex database (racedex.db), needed if a template uses {year}')
    parser.add_argument('--attempts', type=int, default=3, help='seasons tried for {year}, from the last one back')
    args = parser.parse_args()

    load_env_file()
    sitemap_url = os.environ.get('DRIVERS_SITEMAP_URL')
    templates = os.environ.get('DRIVERS_FALLBACK_URLS', '').split()
    if not sitemap_url and not templates:
        sys.exit('Set DRIVERS_SITEMAP_URL and/or DRIVERS_FALLBACK_URLS (see the top of this file)')

    with open(args.drivers_csv, newline='', encoding='utf-8') as file:
        drivers = list(csv.DictReader(file))

    seasons = {}
    if any('{year}' in template for template in templates):
        if not args.db or not args.db.exists():
            sys.exit('A template with {year} needs the database of the API: use --db <path to racedex.db>')
        seasons = driver_seasons(args.db)

    OUT_DIR.mkdir(exist_ok=True)
    have = {path.stem for path in OUT_DIR.glob('*.webp')}
    missing = {driver['id'] for driver in drivers} - have
    originals: dict[str, bytes] = {}
    unmatched: list[str] = []

    if sitemap_url:
        originals, unmatched = fetch_from_sitemap(sitemap_url, drivers, missing)
        print(f'sitemap: {len(originals)} images')
    if templates:
        extra = fetch_from_templates(templates, drivers, missing - originals.keys(), seasons, args.attempts)
        originals |= extra
        print(f'fallback URLs: {len(extra)} images ({", ".join(sorted(extra)) or "-"})')

    for driver_id, data in normalize(originals).items():
        (OUT_DIR / f'{driver_id}.webp').write_bytes(data)

    covered = {path.stem for path in OUT_DIR.glob('*.webp')}
    print(f'drivers with image {len(covered)}/{len(drivers)}')
    if unmatched:
        print('pages of the sitemap without a driver in our data:', ', '.join(unmatched))


if __name__ == '__main__':
    main()
