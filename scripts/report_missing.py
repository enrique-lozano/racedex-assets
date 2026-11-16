"""Lists the drivers that have no photo in drivers/, the most recent ones first

Usage: python -I scripts/report_missing.py [--data <address of the CSV files>]
"""

import argparse
import sys
from pathlib import Path

# `python -I` doesn't add the script's directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from data import data_source, driver_seasons, load_env_file, read_drivers  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--data', help='address of the folder with the CSV files of the API (a URL or a folder)')
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')  # the console of Windows can't print every name

    load_env_file()
    source = data_source(args.data)
    drivers = read_drivers(source)
    seasons = driver_seasons(source)
    available = {path.stem for path in (ROOT / 'drivers').glob('*.webp')}

    missing = sorted(
        (driver for driver in drivers if driver['id'] not in available),
        key=lambda driver: (-seasons.get(driver['id'], (0, 0))[1], driver['id']),
    )
    for driver in missing:
        first, last = seasons.get(driver['id'], (None, None))
        print(f"{driver['id']:<24} {driver['fullName']:<40} {f'{first}-{last}' if first else 'no entries'}")
    print(f'\n{len(missing)} of {len(drivers)} drivers without photo')


if __name__ == '__main__':
    main()
