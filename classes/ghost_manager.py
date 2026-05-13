import json
import random

from classes.logger import Logger
from classes.utility import Utility
import classes.error_codes as EC

logger = Logger.get_logger(__name__)

_GHOSTS_PATH = "src/ghosts.json"

_REQUIRED_KEYS = {"id", "name"}

def _load() -> list[dict]:
    """Read and validate ghost profiles from ghosts.json."""
    path = Utility.resource_path(_GHOSTS_PATH)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        logger.warning("ghosts.json not found at %s — disguise disabled.", path)
        return []
    except json.JSONDecodeError as exc:
        Logger.error_code(EC.E1004, "%s", exc)
        return []

    if not isinstance(data, list):
        Logger.error_code(EC.E1005)
        return []

    valid = []
    for entry in data:
        missing = _REQUIRED_KEYS - entry.keys()
        if missing:
            logger.warning("Skipping ghost entry missing keys %s: %s", missing, entry)
            continue
        valid.append(entry)

    if not valid:
        logger.warning("No valid ghost profiles found — disguise disabled.")

    return valid

def pick() -> dict | None:
    """Return a random ghost profile, or None if none are available."""
    ghosts = _load()
    if not ghosts:
        return None
    ghost = random.choice(ghosts)
    logger.debug("Selected ghost profile: %s (id=%s)", ghost["name"], ghost["id"])
    return ghost