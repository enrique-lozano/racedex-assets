"""Downloads the driver cut-outs that are missing into drivers/{driverId}.webp, normalizing them (see normalize.py)

Usage: python -I scripts/fetch_drivers.py [--data <address of the CSV files>] [--attempts 3]

Drivers that already have an image are skipped (also the ones added by hand with add_photo.py), so the script can be
re-run to pick up new drivers. To download one again, delete its image. The images come from these sources, in order.
Both are optional, but at least one is needed. See scripts/README.md for how to set them.

1. DRIVERS_SITEMAP_URL: sitemap(s) with one page per driver and an image in each (separated by spaces, if there are
   several). The pages are matched to our drivers by name (see matching.py). DRIVERS_PAGE_PATH is the part of the URL
   that the driver pages have in common, `/drivers/` by default.
2. DRIVERS_FALLBACK_URLS: URL templates separated by spaces, tried in order for the drivers that are still missing.
   The first one that returns a transparent image wins. A template can use:
     {id}    id of the driver in RaceDex
     {tla}   abbreviation of the driver, in capitals (VER)
     {ref}   first 3 letters of the first name + first 3 of the last name + 01, in capitals (MAXVER01)
     {year}  a season of the driver: from the last one back, `--attempts` seasons

The variables can be in a `.env` file in the root of the repository (see .env.example), which is not committed.
The drivers (and their seasons) are read from the CSV files of the RaceDex API on GitHub, see data.py.
"""

import argparse
import io
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests
from PIL import Image

# `python -I` doesn't add the script's directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from data import data_source, driver_seasons, load_env_file, read_drivers  # noqa: E402
from matching import match_pages, slugify  # noqa: E402
from normalize import has_transparency, normalize  # noqa: E402

from data import USER_AGENT  # noqa: E402
DELAY_SECONDS = 0.3
MIN_IMAGE_SIZE = 200
ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / 'drivers'

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


def reference(driver: dict[str, str]) -> str:
    letters = lambda name: slugify(name).replace('-', '').upper()[:3]
    return f"{letters(driver['firstName'])}{letters(driver['lastName'])}01"


def sitemap_pages(sitemap_url: str, page_path: str) -> dict[str, str]:
    """slug of the page -> URL of its image, for the pages with an image whose URL has `page_path`"""
    pages = {}
    for block in re.findall(r'<url>(.*?)</url>', get(sitemap_url).decode(), flags=re.S):
        page = re.search(r'<loc>([^<]+)</loc>', block)
        image = re.search(r'<image:loc>([^<]+)</image:loc>', block)
        if page and image and page_path in urlparse(page.group(1)).path:
            slug = urlparse(page.group(1)).path.rstrip('/').rsplit('/', 1)[-1]
            pages[slug] = image.group(1).strip()
    return pages


def fetch_from_sitemaps(sitemap_urls: list[str], page_path: str, drivers: list[dict[str, str]], missing: set[str]) -> dict[str, bytes]:
    pages: dict[str, str] = {}
    for sitemap_url in sitemap_urls:
        pages |= sitemap_pages(sitemap_url, page_path)

    matches, unmatched = match_pages(sorted(pages), drivers)
    guessed = [f'{match.slug} -> {match.driver_id}' for match in matches if not match.exact and match.driver_id in missing]
    if guessed:
        print('matched by similarity, check them:', ', '.join(guessed))

    found = {}
    for match in matches:
        if match.driver_id in missing:
            data = try_get_image(pages[match.slug])
            if data:
                found[match.driver_id] = data
            else:
                print(f'  {match.slug}: not a valid transparent image')

    if unmatched:
        print(f'{len(unmatched)} pages without a driver in our data (add one with add_photo.py if it is a driver of ours):')
        for slug in unmatched:
            print(f'  {slug}  {pages[slug]}')
    return found


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
    parser.add_argument('--data', help='address of the folder with the CSV files of the API (a URL or a folder)')
    parser.add_argument('--attempts', type=int, default=3, help='seasons tried for {year}, from the last one back')
    args = parser.parse_args()

    load_env_file()
    sitemap_urls = os.environ.get('DRIVERS_SITEMAP_URL', '').split()
    templates = os.environ.get('DRIVERS_FALLBACK_URLS', '').split()
    if not sitemap_urls and not templates:
        sys.exit('Set DRIVERS_SITEMAP_URL and/or DRIVERS_FALLBACK_URLS (see the top of this file)')

    source = data_source(args.data)
    drivers = read_drivers(source)
    seasons = driver_seasons(source) if any('{year}' in template for template in templates) else {}

    OUT_DIR.mkdir(exist_ok=True)
    have = {path.stem for path in OUT_DIR.glob('*.webp')}
    missing = {driver['id'] for driver in drivers} - have
    originals: dict[str, bytes] = {}

    if sitemap_urls:
        originals = fetch_from_sitemaps(sitemap_urls, os.environ.get('DRIVERS_PAGE_PATH', '/drivers/'), drivers, missing)
        print(f'sitemap: {len(originals)} images')
    if templates:
        extra = fetch_from_templates(templates, drivers, missing - originals.keys(), seasons, args.attempts)
        originals |= extra
        print(f'fallback URLs: {len(extra)} images ({", ".join(sorted(extra)) or "-"})')

    for driver_id, data in normalize(originals).items():
        (OUT_DIR / f'{driver_id}.webp').write_bytes(data)

    covered = {path.stem for path in OUT_DIR.glob('*.webp')}
    print(f'drivers with image {len(covered)}/{len(drivers)}')


if __name__ == '__main__':
    main()
