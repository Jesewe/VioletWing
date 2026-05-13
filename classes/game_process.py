import time

import psutil
import pygetwindow as gw

from classes.logger import Logger

logger = Logger.get_logger(__name__)

_CS2_PROCESS = "cs2.exe"
_CS2_WINDOW_TITLE = "Counter-Strike 2"
_GAME_ACTIVE_TTL = 0.2  # seconds between window-focus polls

_cache_active: bool = False
_cache_last_check: float = 0.0

def is_game_active() -> bool:
    """
    Return True if the CS2 window currently has focus.

    Result is cached for _GAME_ACTIVE_TTL seconds to avoid hammering
    the window-enumeration API on every tight-loop iteration.
    """
    global _cache_active, _cache_last_check

    now = time.monotonic()
    if now - _cache_last_check < _GAME_ACTIVE_TTL:
        return _cache_active

    windows = gw.getWindowsWithTitle(_CS2_WINDOW_TITLE)
    result = any(w.isActive for w in windows)
    _cache_active = result
    _cache_last_check = now
    return result

def is_game_running() -> bool:
    """Return True if cs2.exe is present in the process list."""
    return any(
        proc.info["name"] == _CS2_PROCESS
        for proc in psutil.process_iter(attrs=["name"])
    )