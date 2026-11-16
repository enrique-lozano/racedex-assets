"""Adds or replaces by hand the photo of a driver: drivers/{driverId}.webp

Usage: python -I scripts/add_photo.py <driverId> <image file or URL> [--remove-background] [--drivers-csv drivers.csv]

The image is normalized like the rest (see normalize.py). It has to be transparent; if it isn't, use
--remove-background (needs `pip install -r requirements-rembg.txt`, see the README). If the driver already has an
image it is replaced, and the fetch script never replaces an existing image.

Afterwards, push the image: the API finds it with its own `npm run set-driver-photos`.
"""

import argparse
import csv
import io
import sys
from pathlib import Path

from PIL import Image

# `python -I` doesn't add the script's directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_drivers import get  # noqa: E402
from normalize import has_transparency, normalize  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def read_source(source: str) -> bytes:
    return get(source) if source.startswith(('http://', 'https://')) else Path(source).read_bytes()


def remove_background(data: bytes) -> bytes:
    try:
        from rembg import remove
    except ImportError:
        sys.exit('--remove-background needs rembg: pip install -r requirements-rembg.txt')
    return remove(data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('driver_id')
    parser.add_argument('source', help='image file or URL')
    parser.add_argument('--remove-background', action='store_true')
    parser.add_argument('--drivers-csv', type=Path, help='drivers.csv of the API, to check that the id exists')
    args = parser.parse_args()

    if args.drivers_csv:
        with open(args.drivers_csv, newline='', encoding='utf-8') as file:
            if args.driver_id not in {row['id'] for row in csv.DictReader(file)}:
                sys.exit(f'{args.driver_id} is not a driver id of {args.drivers_csv}')

    data = read_source(args.source)
    if args.remove_background:
        data = remove_background(data)

    image = Image.open(io.BytesIO(data))
    if not has_transparency(image):
        sys.exit('The image has no transparent background: use --remove-background')

    (ROOT / 'drivers' / f'{args.driver_id}.webp').write_bytes(normalize({args.driver_id: data})[args.driver_id])
    print(f'drivers/{args.driver_id}.webp written')


if __name__ == '__main__':
    main()
