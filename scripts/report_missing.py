"""Lists the drivers of the RaceDex database that have no photo in drivers/, the most recent ones first

Usage: python -I scripts/report_missing.py <racedex.db of the RaceDex API>
"""

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main(database: Path) -> None:
    sys.stdout.reconfigure(encoding='utf-8')  # the console of Windows can't print every name
    available = {path.stem for path in (ROOT / 'drivers').glob('*.webp')}

    with sqlite3.connect(f'file:{database}?mode=ro', uri=True) as connection:
        rows = connection.execute(
            """
            SELECT d.id, d.fullName, MIN(es.season), MAX(es.season)
            FROM drivers d
            LEFT JOIN entries e ON e.driverId = d.id
            LEFT JOIN entrantSeasons es ON es.id = e.entrantSeasonId
            GROUP BY d.id
            ORDER BY MAX(es.season) DESC, d.id
            """
        ).fetchall()

    missing = [row for row in rows if row[0] not in available]
    for driver_id, name, first, last in missing:
        seasons = f'{first}-{last}' if first else 'no entries'
        print(f'{driver_id:<24} {name:<40} {seasons}')
    print(f'\n{len(missing)} of {len(rows)} drivers without photo')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]))
