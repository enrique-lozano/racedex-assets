"""Lists the drivers that have no photo in drivers/, the most recent ones first

Usage: python -I scripts/report_missing.py [--data <address of the CSV files>]
"""

import argparse
import sys
from pathlib import Path

# `python -I` doesn't add the script's directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from data import data_source, driver_seasons, load_env_file, read_drivers  # noqa: E402
from ui import console, ok, table  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--data', help='address of the folder with the CSV files of the API (a URL or a folder)')
    args = parser.parse_args()

    load_env_file()
    with console.status('Reading the drivers of RaceDex...'):
        source = data_source(args.data)
        drivers = read_drivers(source)
        seasons = driver_seasons(source)
    available = {path.stem for path in (ROOT / 'drivers').glob('*.webp')}

    missing = sorted(
        (driver for driver in drivers if driver['id'] not in available),
        key=lambda driver: (-seasons.get(driver['id'], (0, 0))[1], driver['id']),
    )
    if not missing:
        ok('Every driver has a photo')
        return

    listing = table('Id', 'Name', 'Seasons')
    for driver in missing:
        first, last = seasons.get(driver['id'], (None, None))
        listing.add_row(driver['id'], driver['fullName'], f'{first}-{last}' if first else '[dim]no entries[/dim]')
    console.print(listing)
    console.print(f'\n[bold]{len(missing)}[/bold] of {len(drivers)} drivers without a photo')


if __name__ == '__main__':
    main()
