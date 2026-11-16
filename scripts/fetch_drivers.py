"""Downloads the driver cut-outs that are missing into drivers/{driverId}.webp, normalizing them (see normalize.py)

Usage: python -I scripts/fetch_drivers.py [--only <driverId> ...] [--force] [--remove-background] [--yes]
                                          [--data <address of the CSV files>] [--attempts 3]

Drivers that already have an image are skipped (also the ones added by hand with add_photo.py), so the script can be
re-run to pick up new drivers with few requests. Options:
  --only ID ...        only these drivers
  --force              download again (and replace) the images that already exist. It can mean hundreds of requests
                       to the sites of the sources, so it asks before, unless there are only a few drivers or --yes
  --remove-background  remove the background of the images that are not transparent, instead of skipping them
                       (needs requirements-rembg.txt; about 20 seconds per image)

The images come from these sources. Both are optional, but at least one is needed. See scripts/README.md.

1. DRIVERS_URL_TEMPLATES: URL templates separated by spaces, tried in order for each driver. The first one that returns
   a transparent image wins. A template can use:
     {id}     id of the driver in RaceDex
     {tla}    abbreviation of the driver (ver)
     {initial}        first letter of the first name (m)
     {first3}, {last3}  first 3 letters of the first and of the last name (max, ver)
     {first}, {last}  first and last name without accents, with `_` between words (max, verstappen)
     {year}   a season of the driver: from the last one back, `--attempts` seasons
   The case of the placeholder sets the case of the value: {tla} ver, {TLA} VER, {First3} Max, {First} Max.
2. DRIVERS_SITEMAP_URL: for sites whose image URLs can't be built from a pattern. A sitemap is a file that many sites
   publish, with their pages and the images of each one. Sitemap(s) with one page per driver and an image in each
   (separated by spaces, if there are several). The pages are matched to our drivers by name (see matching.py).
   DRIVERS_PAGE_PATH is the part of the URL that the driver pages have in common, `/drivers/` by default.
   The sitemap goes first, and the templates are used for the drivers that it doesn't have.

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
from background import remove_background  # noqa: E402
from data import data_source, driver_seasons, load_env_file, read_drivers  # noqa: E402
from matching import match_pages, slugify  # noqa: E402
from normalize import has_transparency, normalize  # noqa: E402

from data import USER_AGENT  # noqa: E402
DELAY_SECONDS = 0.3
CONFIRM_FROM = 20  # --force asks for confirmation from this number of drivers
MIN_IMAGE_SIZE = 200
ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / 'drivers'

def get(url: str) -> bytes:
    response = requests.get(url, headers={'User-Agent': USER_AGENT}, timeout=30)
    response.raise_for_status()
    return response.content


def try_get_image(url: str, remove_bg: bool = False) -> bytes | None:
    """The image if the URL exists and is a big enough transparent image (or it can be made transparent), otherwise None"""
    try:
        data = get(url)
        image = Image.open(io.BytesIO(data))
        image.load()
    except (requests.RequestException, OSError):
        return None
    finally:
        time.sleep(DELAY_SECONDS)

    if min(image.size) < MIN_IMAGE_SIZE:
        return None
    if not has_transparency(image):
        if not remove_bg:
            return None
        data = remove_background(data)
    return data


PLACEHOLDER = re.compile(r'\{(\w+)\}')


def template_values(driver: dict[str, str]) -> dict[str, str]:
    """What a URL template can use of a driver, in lowercase (the template decides the case)"""
    words = lambda name: slugify(name).split('-')
    letters = lambda name: ''.join(words(name))[:3]
    return {
        'id': driver['id'],
        'tla': driver['abbreviation'],
        'first3': letters(driver['firstName']),
        'last3': letters(driver['lastName']),
        'initial': words(driver['firstName'])[0][:1],
        'first': '_'.join(words(driver['firstName'])),
        'last': '_'.join(words(driver['lastName'])),
    }


def apply_case(value: str, spelled: str) -> str:
    """The case of a placeholder sets the case of its value: {first3} max, {FIRST3} MAX, {First3} Max"""
    if spelled.isupper():
        return value.upper()
    if spelled.islower():
        return value.lower()
    return '_'.join(word.capitalize() for word in value.split('_'))


def render_template(template: str, values: dict[str, str]) -> str:
    return PLACEHOLDER.sub(lambda match: apply_case(values[match.group(1).lower()], match.group(1)), template)


def check_templates(templates: list[str]) -> None:
    valid = set(template_values({'id': '', 'abbreviation': '', 'firstName': 'a', 'lastName': 'a'})) | {'year'}
    for template in templates:
        unknown = {name for name in PLACEHOLDER.findall(template) if name.lower() not in valid}
        if unknown:
            sys.exit(f'Unknown placeholder {{{sorted(unknown)[0]}}} in {template}\nThe valid ones are: {", ".join(sorted(valid))}')


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


def fetch_from_sitemaps(
    sitemap_urls: list[str], page_path: str, drivers: list[dict[str, str]], missing: set[str], remove_bg: bool
) -> dict[str, bytes]:
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
            data = try_get_image(pages[match.slug], remove_bg)
            if data:
                found[match.driver_id] = data
            else:
                print(f'  {match.slug}: not a valid image (or not transparent: use --remove-background)')

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
    remove_bg: bool,
) -> dict[str, bytes]:
    found = {}
    for driver in drivers:
        if driver['id'] not in missing:
            continue

        values = template_values(driver)
        years = []
        if driver['id'] in seasons:
            first, last = seasons[driver['id']]
            years = list(range(last, max(first, last - attempts + 1) - 1, -1))

        for template in templates:
            if any(name.lower() == 'year' for name in PLACEHOLDER.findall(template)):
                urls = [render_template(template, values | {'year': str(year)}) for year in years]
            else:
                urls = [render_template(template, values)]
            data = next(filter(None, (try_get_image(url, remove_bg) for url in urls)), None)
            if data:
                found[driver['id']] = data
                break
    return found


def confirm_force(count: int, hosts: set[str]) -> None:
    """Asks before downloading again many images, which are many requests to the sites of the sources"""
    print(
        f'--force downloads again (and replaces) the images of {count} drivers, also the ones added by hand.\n'
        f'That is hundreds of requests to: {", ".join(sorted(hosts))}.\n'
        'Check that those sites have no rate limits and that this is expected.'
    )
    if not sys.stdin.isatty():
        sys.exit('Not an interactive terminal: use --yes to continue')
    try:
        answer = input('Continue? [y/N] ')
    except EOFError:
        answer = ''
    if answer.strip().lower() != 'y':
        sys.exit('Cancelled')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--data', help='address of the folder with the CSV files of the API (a URL or a folder)')
    parser.add_argument('--attempts', type=int, default=3, help='seasons tried for {year}, from the last one back')
    parser.add_argument('--only', nargs='+', metavar='ID', help='only these drivers')
    parser.add_argument('--force', action='store_true', help='download again the images that already exist')
    parser.add_argument('--remove-background', action='store_true', help='remove the background of the images that have one')
    parser.add_argument('--yes', action='store_true', help='do not ask before --force')
    args = parser.parse_args()

    load_env_file()
    sitemap_urls = os.environ.get('DRIVERS_SITEMAP_URL', '').split()
    templates = os.environ.get('DRIVERS_URL_TEMPLATES', '').split()
    check_templates(templates)
    if not sitemap_urls and not templates:
        sys.exit('Set DRIVERS_SITEMAP_URL and/or DRIVERS_URL_TEMPLATES (see the top of this file)')

    source = data_source(args.data)
    drivers = read_drivers(source)
    seasons = driver_seasons(source) if any('{year}' in template.lower() for template in templates) else {}

    OUT_DIR.mkdir(exist_ok=True)
    targets = {driver['id'] for driver in drivers}
    if args.only:
        unknown = set(args.only) - targets
        if unknown:
            sys.exit(f'Not drivers of RaceDex: {", ".join(sorted(unknown))}')
        targets = set(args.only)
    if not args.force:
        targets -= {path.stem for path in OUT_DIR.glob('*.webp')}
    elif len(targets) >= CONFIRM_FROM and not args.yes:
        confirm_force(len(targets), {urlparse(url).netloc for url in sitemap_urls + templates})

    originals: dict[str, bytes] = {}
    if sitemap_urls:
        originals = fetch_from_sitemaps(sitemap_urls, os.environ.get('DRIVERS_PAGE_PATH', '/drivers/'), drivers, targets, args.remove_background)
        print(f'sitemap: {len(originals)} images')
    if templates:
        extra = fetch_from_templates(templates, drivers, targets - originals.keys(), seasons, args.attempts, args.remove_background)
        originals |= extra
        print(f'URL templates: {len(extra)} images ({", ".join(sorted(extra)) or "-"})')

    for driver_id, data in normalize(originals).items():
        (OUT_DIR / f'{driver_id}.webp').write_bytes(data)

    covered = {path.stem for path in OUT_DIR.glob('*.webp')}
    print(f'drivers with image {len(covered)}/{len(drivers)}')


if __name__ == '__main__':
    main()
