"""Gives every driver cut-out the same framing: 440x440, the head `GAP` px below the top edge, the body anchored to the
bottom edge and the face at least `MIN_FACE_HEIGHT` px tall.

1. The non-transparent content is scaled to a fixed height (taller images lose the torso below, shorter ones are
   scaled up), so every head starts at the same line.
2. The face is detected (OpenCV YuNet, `models/`). If it is smaller than `MIN_FACE_HEIGHT` the image is zoomed in,
   centered on the face and keeping the head at `GAP`. Bigger faces are left alone: shrinking them would leave
   empty space.

Run it on the ORIGINAL images (they are encoded only once).

Usage: python -I scripts/normalize.py <directory with the originals> <output directory>
"""

import io
import os
import sys
from pathlib import Path

os.environ.setdefault('OPENCV_LOG_LEVEL', 'ERROR')  # before importing cv2
import cv2  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

SIZE = 440
GAP = 8
CONTENT_HEIGHT = SIZE - GAP
# Height of the box of YuNet, which is about 1.18 times the one of the face detector of macOS that was used to choose 150 px
MIN_FACE_HEIGHT = 177
MAX_ZOOM = 2.0
ALPHA_THRESHOLD = 16
FACE_MODEL = Path(__file__).resolve().parent / 'models' / 'face_detection_yunet_2023mar.onnx'


def has_transparency(image: Image.Image) -> bool:
    """Whether it has transparent pixels (also for palette images, like many PNGs)"""
    return image.convert('RGBA').getchannel('A').getextrema()[0] < ALPHA_THRESHOLD


def frame(data: bytes) -> Image.Image:
    image = Image.open(io.BytesIO(data)).convert('RGBA')
    box = image.getchannel('A').point(lambda value: 255 if value > ALPHA_THRESHOLD else 0).getbbox()
    content = image.crop(box)

    if content.height > CONTENT_HEIGHT:
        content = content.crop((0, 0, content.width, CONTENT_HEIGHT))
    elif content.height < CONTENT_HEIGHT:
        width = round(content.width * CONTENT_HEIGHT / content.height)
        content = content.resize((width, CONTENT_HEIGHT), Image.LANCZOS)

    # If it ends up wider than the canvas, the sides are cut evenly
    side = (content.width - SIZE) // 2
    if side > 0:
        content = content.crop((side, 0, side + SIZE, CONTENT_HEIGHT))

    canvas = Image.new('RGBA', (SIZE, SIZE), (0, 0, 0, 0))
    canvas.alpha_composite(content, ((SIZE - content.width) // 2, GAP))
    return canvas


def detect_faces(images: dict[str, Image.Image]) -> dict[str, tuple[float, float]]:
    """name -> (center x, height) of the largest face, in pixels of the canvas"""
    detector = cv2.FaceDetectorYN.create(str(FACE_MODEL), '', (SIZE, SIZE), 0.5, 0.3, 5000)

    faces = {}
    for name, image in images.items():
        background = Image.new('RGBA', image.size, (200, 200, 200, 255))
        background.alpha_composite(image)
        bgr = np.ascontiguousarray(np.array(background.convert('RGB'))[:, :, ::-1])

        detector.setInputSize((bgr.shape[1], bgr.shape[0]))
        _, found = detector.detect(bgr)
        if found is not None:
            x, _, width, height = max(found, key=lambda face: face[3])[:4]
            faces[name] = (float(x + width / 2), float(height))
    return faces


def zoom_to_face(image: Image.Image, center_x: float, face_height: float) -> Image.Image:
    zoom = min(MAX_ZOOM, MIN_FACE_HEIGHT / face_height)
    if zoom <= 1:
        return image

    side = round(SIZE * zoom)
    big = image.resize((side, side), Image.LANCZOS)
    left = min(max(round(center_x * zoom - SIZE / 2), 0), side - SIZE)
    top = round(GAP * zoom - GAP)  # keeps the head at GAP px from the top edge
    return big.crop((left, top, left + SIZE, top + SIZE))


def normalize(sources: dict[str, bytes]) -> dict[str, bytes]:
    """name -> original image  ==>  name -> normalized WebP"""
    framed = {name: frame(data) for name, data in sources.items()}
    faces = detect_faces(framed)

    result = {}
    for name, image in framed.items():
        if name in faces:
            image = zoom_to_face(image, faces[name][0], faces[name][1])
        else:
            print(f'  no face found in {name}, only framed')
        output = io.BytesIO()
        image.save(output, 'WEBP', quality=85, alpha_quality=100, method=4)
        result[name] = output.getvalue()
    return result


def main(originals: Path, output: Path) -> None:
    sources = {file.stem: file.read_bytes() for file in sorted(originals.glob('*.webp'))}
    output.mkdir(parents=True, exist_ok=True)
    for name, data in normalize(sources).items():
        (output / f'{name}.webp').write_bytes(data)
    print(f'normalized {len(sources)} images')


if __name__ == '__main__':
    main(Path(sys.argv[1]), Path(sys.argv[2]))
