import json
import random
import sys
import os
import shutil
import tempfile
import subprocess

from src.utils.logger import Logger
from src.utils.utility import Utility
from src.utils.config_manager import ConfigManager
import src.utils.error_codes as EC

logger = Logger.get_logger(__name__)

_GHOSTS_PATH = "assets/ghosts.json"

_REQUIRED_KEYS = {"id", "name"}

def _load() -> list[dict]:
    """Read and validate ghost profiles from ghosts.json."""
    path = Utility.resource_path(_GHOSTS_PATH)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        logger.warning("ghosts.json not found at %s - disguise disabled.", path)
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
        logger.warning("No valid ghost profiles found - disguise disabled.")

    return valid

def setup_disguise() -> dict | None:
    """Check if disguise is enabled, clone executable if needed, and return the ghost profile."""
    config = ConfigManager.load_config()
    if not config["General"].get("Disguise", False):
        return None

    ghosts = _load()
    if not ghosts:
        return None

    is_frozen = getattr(sys, 'frozen', False)
    if not is_frozen:
        # Not a compiled executable, just return a random ghost
        ghost = random.choice(ghosts)
        logger.debug("Running from source. Selected ghost profile: %s", ghost["name"])
        return ghost

    current_exe = sys.executable
    current_name = os.path.basename(current_exe).lower()

    # Check if we are already running as one of the ghosts
    for g in ghosts:
        expected_name = f"{g['name']}.exe".lower()
        if current_name == expected_name:
            logger.debug("Already disguised as %s", g['name'])
            return g

    # We are not disguised. Pick a random one and relaunch.
    ghost = random.choice(ghosts)
    target_name = f"{ghost['name']}.exe"
    temp_dir = tempfile.gettempdir()
    target_exe = os.path.join(temp_dir, target_name)

    try:
        # If the target already exists (e.g., from a previous run), we overwrite it.
        # But if it's currently running, copy2 might raise PermissionError.
        # We can try to delete it first, and if it fails, pick another ghost or ignore.
        try:
            if os.path.exists(target_exe):
                os.remove(target_exe)
        except Exception:
            pass # Try to copy anyway, shutil.copy2 might succeed or raise below

        shutil.copy2(current_exe, target_exe)
        logger.info("Disguising as %s. Relaunching %s...", ghost['name'], target_exe)
        subprocess.Popen([target_exe] + sys.argv[1:])
        sys.exit(0)
    except Exception as exc:
        logger.error("Failed to copy/relaunch for disguise: %s", exc)
        return ghost # fallback to returning the ghost for partial disguise