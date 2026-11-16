"""Removes the background of a photo, with rembg (an AI model that runs on your computer)"""

import sys


def remove_background(data: bytes) -> bytes:
    try:
        from rembg import remove
    except ImportError:
        sys.exit('Removing the background needs rembg: pip install -r requirements-rembg.txt')
    return remove(data)
