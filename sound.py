# -*- coding: utf-8 -*-
# Sound wrapper for XP. Uses winsound (stdlib, Windows only).
# Sounds live in sounds/ subfolder near this file.
# Turn off via set_enabled(False).

import os

try:
    import winsound
    HAVE_WINSOUND = True
except ImportError:
    HAVE_WINSOUND = False


HERE = os.path.dirname(os.path.abspath(__file__))
SOUNDS_DIR = os.path.join(HERE, "sounds")

_enabled = True


def is_available():
    return HAVE_WINSOUND


def set_enabled(on):
    global _enabled
    _enabled = bool(on)


def is_enabled():
    return _enabled


def _path(name):
    if not name.endswith(".wav"):
        name = name + ".wav"
    return os.path.join(SOUNDS_DIR, name)


def play(name):
    """Play WAV async. Overrides currently playing (as in ICQ 99b).
    Returns True if attempt made."""
    if not _enabled or not HAVE_WINSOUND:
        return False
    p = _path(name)
    if not os.path.isfile(p):
        return False
    try:
        winsound.PlaySound(p, winsound.SND_FILENAME | winsound.SND_ASYNC)
        return True
    except Exception:
        return False


# Convenience
def startup():
    return play("Startup")


def message():
    return play("Message")


def typekey():
    return play("MsgType")


def sent():
    return play("MsgSent")


def notify():
    return play("Notify")


def online():
    return play("Online")


def global_():
    return play("Global")


def list_available():
    if not os.path.isdir(SOUNDS_DIR):
        return []
    return sorted(f for f in os.listdir(SOUNDS_DIR) if f.lower().endswith(".wav"))