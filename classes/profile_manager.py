import copy
import re
from pathlib import Path
from typing import List, Optional

import orjson

from classes.config_manager import ConfigManager
from classes.logger import Logger
import classes.error_codes as EC

logger = Logger.get_logger(__name__)

# Keys excluded from profiles — they are identity/env-specific, not playstyle.
_EXCLUDED_TOP_LEVEL = {"user_id", "seen_changelog_version", "GitHub"}
# Inside General, these are env-specific and should not roam with a profile.
_EXCLUDED_GENERAL = {"OffsetSource", "OffsetsFile", "ClientDLLFile", "ButtonsFile"}

# Only alphanumeric, spaces, dashes, underscores — avoids path traversal entirely.
# Allows letters, digits, underscores, single spaces, and hyphens only.
# Literal space (not \s) intentionally excludes tabs and newlines.
_VALID_NAME_RE = re.compile(r'^[\w \-]{1,64}$')

_PROFILES_DIR = Path(ConfigManager.CONFIG_DIRECTORY) / "profiles"

def _profiles_dir() -> Path:
    """Ensure the profiles directory exists and return its path."""
    _PROFILES_DIR.mkdir(parents=True, exist_ok=True)
    return _PROFILES_DIR

def _profile_path(name: str) -> Path:
    return _profiles_dir() / f"{name}.json"

def validate_name(name: str) -> Optional[str]:
    """Return an error message if name is invalid, or None if it is acceptable."""
    stripped = name.strip()
    if not stripped:
        return "Profile name cannot be empty."
    if not _VALID_NAME_RE.match(stripped):
        return "Profile name may only contain letters, numbers, spaces, hyphens, and underscores (max 64 chars)."
    return None

def list_profiles() -> List[str]:
    """Return sorted profile names (without .json extension)."""
    try:
        return sorted(p.stem for p in _profiles_dir().glob("*.json"))
    except OSError:
        return []

def save_profile(name: str, config: dict) -> bool:
    """
    Persist a profile snapshot derived from the current full config.

    Excludes identity/env keys so profiles stay playstyle-only.
    Returns True on success.
    """
    try:
        snapshot = {}
        for key, value in config.items():
            if key in _EXCLUDED_TOP_LEVEL:
                continue
            if key == "General" and isinstance(value, dict):
                snapshot["General"] = {
                    k: v for k, v in value.items()
                    if k not in _EXCLUDED_GENERAL
                }
            else:
                snapshot[key] = copy.deepcopy(value)

        data = orjson.dumps(snapshot, option=orjson.OPT_INDENT_2)
        _profile_path(name.strip()).write_bytes(data)
        logger.info("Saved profile '%s'.", name)
        return True
    except (OSError, IOError) as e:
        Logger.error_code(EC.E1006, "%s", e)
        return False

def load_profile(name: str) -> Optional[dict]:
    """
    Load a profile and return a full merged config ready for use.

    Merges profile data on top of the current live config so that excluded
    keys (user_id, offsets paths, etc.) are always preserved from live config.
    Returns None on failure.
    """
    path = _profile_path(name.strip())
    try:
        data = orjson.loads(path.read_bytes())
        if not isinstance(data, dict):
            raise ValueError("Profile root must be a JSON object.")
    except (orjson.JSONDecodeError, OSError, ValueError) as e:
        Logger.error_code(EC.E1007, "%s", e)
        return None

    # Start from current live config so excluded keys are untouched.
    merged = ConfigManager.load_config()

    for key, value in data.items():
        if key == "General" and isinstance(value, dict):
            # Merge only the non-excluded General keys.
            for gk, gv in value.items():
                if gk not in _EXCLUDED_GENERAL:
                    merged["General"][gk] = gv
        elif isinstance(value, dict) and isinstance(merged.get(key), dict):
            # Deep-merge nested sections (Trigger, Overlay, etc.)
            merged[key].update(value)
        else:
            merged[key] = value

    return merged

def delete_profile(name: str) -> bool:
    """Delete a profile file. Returns True on success."""
    path = _profile_path(name.strip())
    try:
        path.unlink()
        logger.info("Deleted profile '%s'.", name)
        return True
    except OSError as e:
        Logger.error_code(EC.E1006, "%s", e)
        return False