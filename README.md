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

## Add a photo

Missing a driver, or have a better photo? With the [scripts](scripts/README.md) it is one command (Python 3.10+):

```bash
pip install -r requirements.txt
python -I scripts/add_photo.py <driverId> path/or/url/to/photo.png
```

The photo is framed like the rest and saved in `drivers/`. If it has a background, add `--remove-background`; to replace an existing one, add `--force`. Then open a pull request. There are more scripts, like `fetch_drivers.py`, in [`scripts/README.md`](scripts/README.md).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the format of the commits and how to add images.

## Used by

- [RaceDex](https://github.com/enrique-lozano/F1-World-API)

Using these images in your project? Open a pull request to add it here.
