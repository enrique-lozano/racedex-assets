<h1 align="center">RaceDex assets</h1>

<p align="center">
  <img src="https://enrique-lozano.github.io/racedex-assets/drivers/prost.webp" width="90" alt="">
  <img src="https://enrique-lozano.github.io/racedex-assets/drivers/ayrton-senna.webp" width="90" alt="">
  <img src="https://enrique-lozano.github.io/racedex-assets/drivers/raikkonen.webp" width="90" alt="">
  <img src="https://enrique-lozano.github.io/racedex-assets/drivers/charles-pic.webp" width="90" alt="">
  <img src="https://enrique-lozano.github.io/racedex-assets/drivers/arnoux.webp" width="90" alt="">
</p>

<p align="center">
  Transparent cut-outs of Formula 1 drivers, ready to use in any project. Served with GitHub Pages.
</p>

## Driver photos

```
https://enrique-lozano.github.io/racedex-assets/drivers/{driverId}.webp
```

`{driverId}` is the id of the driver (`raikkonen`, `ayrton-senna`...), the same one used by the RaceDex API.

- **Transparent 440×440 WebP**, about 27 KB each.
- **Same framing for all**: head at the top, body cut at the bottom edge and faces of a similar size. Add your own crop where you use them.
- **Not every driver has one**: the API only returns the URL of the ones that exist.

The images come from several public sources, and their original authors are not always known. They are not licensed under this repository's terms and their copyright belongs to their respective owners. If you own one and want it removed, open an issue.

## Scripts

They work on Windows, macOS and Linux (Python 3.10+). Use a virtual environment, so the packages don't mix with the ones of your system:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

| Command | What it does |
|---|---|
| `python -I scripts/fetch_drivers.py <drivers.csv>` | Downloads the drivers that don't have an image. Copy `.env.example` to `.env` to set where from. |
| `python -I scripts/add_photo.py <driverId> <image>` | Adds or replaces a photo by hand. |
| `python -I scripts/report_missing.py <racedex.db>` | Lists the drivers without a photo. |

`drivers.csv` and `racedex.db` are the files of the RaceDex API, where the driver ids come from.

### Adding a photo by hand

```bash
python -I scripts/add_photo.py prost ~/Downloads/prost.png
```

The image is framed like the rest and saved as `drivers/prost.webp`, replacing the previous one. It has to be a **transparent** image. If it isn't, add `--remove-background`, which removes the background with [rembg](https://github.com/danielgatis/rembg), an AI model that runs on your computer:

```bash
pip install -r requirements-rembg.txt
python -I scripts/add_photo.py prost ~/Downloads/prost.jpg --remove-background
```

- It works with busy backgrounds and with other people behind: it keeps the main subject.
- The first run downloads a model of about 1 GB. After that, each photo takes about 20 seconds.
- It can leave halos or cut parts of hair, helmets or collars. **Always look at the result**, and if it is not good, crop the photo around the driver first.
- The face has to be visible, with the head and shoulders. The more resolution, the better.

## Used by

- [RaceDex](https://github.com/enrique-lozano/F1-World-API)

Using these images in your project? Open a pull request to add it here.
