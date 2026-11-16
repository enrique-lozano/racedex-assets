# Scripts

Python scripts to build and maintain the images of `drivers/`. They work on Windows, macOS and Linux.

| Script | What it does |
|---|---|
| [`fetch_drivers.py`](fetch_drivers.py) | Downloads the images of the drivers that don't have one. |
| [`add_photo.py`](add_photo.py) | Adds or replaces the photo of a driver by hand. |
| [`report_missing.py`](report_missing.py) | Lists the drivers without a photo. |
| [`normalize.py`](normalize.py) | The framing that the first two give to every image. |

The drivers (and the seasons they raced) are read from the CSV files of the [RaceDex API](https://github.com/enrique-lozano/F1-World-API) on GitHub, so you don't need to clone it. To read them from somewhere else (a fork, or a folder of your computer), use `--data <address of the folder with the CSV files>` or the `RACEDEX_DATA_URL` variable.

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
python -I scripts/fetch_drivers.py
```

## Fetching the drivers that are missing

```bash
python -I scripts/fetch_drivers.py
```

It only downloads the drivers that don't have an image yet, so running it again costs few requests: one per sitemap, the 3 CSV files of the API and one per driver that is missing. The new images are normalized before they are saved.

**Where the images come from.** You set it in `.env`, with one of these two options (or both):

| | When to use it | Example |
|---|---|---|
| **URL templates** (`DRIVERS_URL_TEMPLATES`) | The URL of the image follows a pattern, so it can be built with the data of the driver. The simple one. | `https://example.com/headshots/{year}/{TLA}.png` |
| **Sitemap** (`DRIVERS_SITEMAP_URL`) | The URLs don't follow a pattern. A sitemap is a file that many sites publish for search engines, with their pages and the images of each one (look for `/sitemap.xml` or `/robots.txt`). | `https://example.com/drivers-sitemap.xml` |

Several URLs are separated by spaces. With both, the sitemap goes first and the templates are used for the drivers that it doesn't have. A template can use these placeholders (the sitemap doesn't use any, because it is read as it is, and its pages are matched to the drivers by name):

| Placeholder | Value | Example |
|---|---|---|
| `{id}` | id of the driver | `max-verstappen` |
| `{tla}` | abbreviation | `ver` |
| `{first3}`, `{last3}` | first 3 letters of the first name and of the last name | `max`, `ver` |
| `{initial}` | first letter of the first name | `m` |
| `{first}`, `{last}` | first and last name without accents, with `_` between words | `max`, `verstappen` |
| `{year}` | a season of the driver, from the last one back | `2024` |

**The case of the placeholder sets the case of the value**, so the same placeholder works for any site: `{tla}` is `ver`, `{TLA}` is `VER`, `{First3}` is `Max` and `{First}_{Last}` is `Max_Verstappen`. Anything else is written in the URL as it is, like the `01` of `{first3}{last3}01`. A placeholder that doesn't exist stops the script before any request.

With `{year}` the last 3 seasons of the driver are tried (`--attempts` changes it). `DRIVERS_PAGE_PATH` (`/drivers/` by default) is the part of the URL that the pages of the drivers have in common in the sitemap, to ignore the other pages.

**Examples of `.env`**

```bash
# Only templates: sites with a pattern, in order. The first one that has the driver wins
DRIVERS_URL_TEMPLATES=https://example.com/drivers/{year}/{FIRST3}{LAST3}01.png https://example.org/headshots/{year}/{TLA}.png

# Only a sitemap: a site without a pattern, but with a list of its pages
DRIVERS_SITEMAP_URL=https://example.net/drivers-sitemap.xml

# A site that has the latest image of each driver, without a year (the URL has the name: .../M/MAXVER01_Max_Verstappen/maxver01.png)
DRIVERS_URL_TEMPLATES=https://example.com/drivers/{INITIAL}/{FIRST3}{LAST3}01_{First}_{Last}/{first3}{last3}01.png

# Both: the sitemap has the history and the templates complete the drivers of the last seasons
DRIVERS_SITEMAP_URL=https://example.net/drivers-sitemap.xml
DRIVERS_URL_TEMPLATES=https://example.com/drivers/{year}/{FIRST3}{LAST3}01.png
```

The images that a site has for the drivers of the last seasons usually follow a pattern, and the ones of the history usually don't: that is why using both works best.

**Options**

| Option | What it does |
|---|---|
| `--only <id> ...` | Only these drivers. |
| `--force` | Downloads again (and replaces) the images that already exist, also the ones added by hand. |
| `--yes` | With `--force`, doesn't ask before continuing. |
| `--remove-background` | Removes the background of the images that have one, instead of skipping them (see below). |
| `--verbose` | Shows the address of the images of the sitemap pages that are not drivers of ours. |
| `--data` | Where the drivers are read from (see above). |

`--force` for 20 drivers or more can mean hundreds of requests to the sites you set in `.env`, so it asks before:

```
--force downloads again (and replaces) the images of 901 drivers, also the ones added by hand.
That is hundreds of requests to: assets.example.com, www.example.com.
Check that those sites have no rate limits and that this is expected.
Continue? [y/N]
```

To download again only some drivers, use `--only` (`python -I scripts/fetch_drivers.py --only prost senna --force`).

**Sitemap only: how the pages are matched to the drivers.** The URL templates don't need this, because each URL is built from the data of a driver we already know. A sitemap only gives pages and images, so they are matched by name, without anything to configure. First the names that are exactly the same, then the ones that look alike: `geoff-crossley` is Geoffrey Crossley, `aj-foyt` is Anthony Joseph Foyt and `zhou-guanyu` is Guanyu Zhou. The ones matched like this are printed, so you can check them. If two drivers fit equally well, or the driver is not in our data, the page is left out and printed with the address of its image. If it is a driver of ours, add it by hand with `add_photo.py <driverId> <that address>`. The rules are in [`matching.py`](matching.py), and its tests run with `python -m unittest discover tests`.

The scripts show their progress with colors. Set `NO_COLOR=1` to turn the colors off (they are off by default when the output goes to a file). A run that looks for ~60 drivers makes about 200 requests, with a short pause between each one, so it takes a couple of minutes.

## Adding a photo by hand

```bash
python -I scripts/add_photo.py prost ~/Downloads/prost.png
```

The image is framed like the rest and saved as `drivers/prost.webp`. If the driver already has an image, add `--force` to replace it. It also checks that the id exists (`--skip-check` if you are offline).

The image has to be **transparent**. If it isn't, add `--remove-background`, which removes the background with [rembg](https://github.com/danielgatis/rembg), an AI model that runs on your computer:

```bash
pip install -r requirements-rembg.txt
python -I scripts/add_photo.py prost ~/Downloads/prost.jpg --remove-background
```

- It works with busy backgrounds and with other people behind: it keeps the main subject.
- The first run downloads a model of about 1 GB. After that, each photo takes about 20 seconds. `fetch_drivers.py` accepts the same `--remove-background`, for the images that it downloads with a background.
- It can leave halos or cut parts of hair, helmets or collars. **Always look at the result**, and if it is not good, crop the photo around the driver first.
- The face has to be visible, with the head and shoulders. The more resolution, the better.

## Listing the drivers without a photo

```bash
python -I scripts/report_missing.py
```

## How the images are framed

[`normalize.py`](normalize.py) gives every image the same look: 440×440, the head 8 px below the top edge, the body cut at the bottom edge, and the face at least ~150 px tall (it zooms in on the ones that are smaller). The faces are found with the YuNet model of [OpenCV Zoo](https://github.com/opencv/opencv_zoo) (MIT license, in `models/`).
