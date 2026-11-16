# Scripts

Python scripts to build and maintain the images of `drivers/`. They work on Windows, macOS and Linux.

| Script | What it does |
|---|---|
| [`fetch_drivers.py`](fetch_drivers.py) | Downloads the images of the drivers that don't have one. |
| [`add_photo.py`](add_photo.py) | Adds or replaces the photo of a driver by hand. |
| [`report_missing.py`](report_missing.py) | Lists the drivers without a photo. |
| [`normalize.py`](normalize.py) | The framing that the first two give to every image. |

`drivers.csv` and `racedex.db` below are the files of the [RaceDex API](https://github.com/enrique-lozano/F1-World-API), where the driver ids come from.

## Getting started

You need Python 3.10+. Use a virtual environment, so the packages don't mix with the ones of your system:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

(`python` can be `py` on Windows.) Activate it again every time you open a new terminal.

To download images you also need to say where from:

```bash
cp .env.example .env             # Windows: copy .env.example .env
```

and fill `.env` (it is not committed). Then:

```bash
python -I scripts/fetch_drivers.py path/to/drivers.csv --db path/to/racedex.db
```

## Fetching the drivers that are missing

It only downloads the drivers that don't have an image, and normalizes them. To download one again, delete its image.

The sources are set in `.env`, and they are tried in this order:

| Variable | Meaning |
|---|---|
| `DRIVERS_SITEMAP_URL` | One or more sitemaps (separated by spaces) with a page per driver and an image in each. |
| `DRIVERS_PAGE_PATH` | Part of the URL that the pages of the drivers have in common, to ignore the other pages. `/drivers/` by default. |
| `DRIVERS_FALLBACK_URLS` | URL templates (separated by spaces) for the drivers that are still missing. The first one that returns a transparent image wins. |

Both `DRIVERS_SITEMAP_URL` and `DRIVERS_FALLBACK_URLS` are optional, but you need one.

A template can use:

| Placeholder | Value | Example |
|---|---|---|
| `{id}` | id of the driver | `verstappen` |
| `{tla}` | abbreviation, in capitals | `VER` |
| `{ref}` | 3 letters of the first name + 3 of the last name + `01`, in capitals | `MAXVER01` |
| `{year}` | a season of the driver, from the last one back | `2024` |

With `{year}` the last 3 seasons are tried (`--attempts` changes it) and the script needs the database: `--db racedex.db`.

**How the pages are matched to the drivers.** By name, without anything to configure. First the names that are exactly the same, then the ones that look alike: `geoff-crossley` is Geoffrey Crossley, `aj-foyt` is Anthony Joseph Foyt and `zhou-guanyu` is Guanyu Zhou. The ones matched like this are printed, so you can check them. If two drivers fit equally well, or the driver is not in our data, the page is left out and printed with the address of its image. If it is a driver of ours, add it by hand with `add_photo.py <driverId> <that address>`. The rules are in [`matching.py`](matching.py), and its tests run with `python -m unittest discover tests`.

## Adding a photo by hand

```bash
python -I scripts/add_photo.py prost ~/Downloads/prost.png
```

The image is framed like the rest and saved as `drivers/prost.webp`, replacing the previous one. `--drivers-csv drivers.csv` checks that the id exists.

The image has to be **transparent**. If it isn't, add `--remove-background`, which removes the background with [rembg](https://github.com/danielgatis/rembg), an AI model that runs on your computer:

```bash
pip install -r requirements-rembg.txt
python -I scripts/add_photo.py prost ~/Downloads/prost.jpg --remove-background
```

- It works with busy backgrounds and with other people behind: it keeps the main subject.
- The first run downloads a model of about 1 GB. After that, each photo takes about 20 seconds.
- It can leave halos or cut parts of hair, helmets or collars. **Always look at the result**, and if it is not good, crop the photo around the driver first.
- The face has to be visible, with the head and shoulders. The more resolution, the better.

## Listing the drivers without a photo

```bash
python -I scripts/report_missing.py path/to/racedex.db
```

## How the images are framed

[`normalize.py`](normalize.py) gives every image the same look: 440×440, the head 8 px below the top edge, the body cut at the bottom edge, and the face at least ~150 px tall (it zooms in on the ones that are smaller). The faces are found with the YuNet model of [OpenCV Zoo](https://github.com/opencv/opencv_zoo) (MIT license, in `models/`).
