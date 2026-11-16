"""Removes the background of a photo, with rembg (an AI model that runs on your computer)"""

from ui import fail


def remove_background(data: bytes) -> bytes:
    try:
        from rembg import remove
    except ImportError:
        fail('Removing the background needs rembg: pip install -r requirements-rembg.txt')
    return remove(data)
