"""Removes the background of a photo, with rembg (an AI model that runs on your computer)"""

import threading

from ui import fail

_lock = threading.Lock()
_session = None


def remove_background(data: bytes) -> bytes:
    global _session
    try:
        from rembg import new_session, remove
    except ImportError:
        fail('Removing the background needs rembg: pip install -r requirements-rembg.txt')

    # One at a time (it uses the whole processor anyway), and the model is loaded once, not for every image
    with _lock:
        if _session is None:
            _session = new_session()
        return remove(data, session=_session)
