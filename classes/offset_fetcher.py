import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import orjson
import requests
from packaging import version

from classes.config_manager import ConfigManager
from classes.logger import Logger
import classes.error_codes as EC

logger = Logger.get_logger(__name__)

_REMOTE_SOURCES_URL = "https://violetwing.vercel.app/data/offsets.json"
_STATUS_URL = "https://violetwing.vercel.app/data/status.json"
_REQUIRED_SOURCE_KEYS = {"name", "author", "repository", "offsets_url", "client_dll_url", "buttons_url"}

_DEFAULT_SOURCES: dict = {
    "a2x": {
        "name": "A2X Source",
        "author": "a2x",
        "repository": "a2x/cs2-dumper",
        "offsets_url": "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json",
        "client_dll_url": "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json",
        "buttons_url": "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/buttons.json",
    }
}

_sources_cache: dict | None = None

def load_offset_sources() -> dict:
    """
    Load available offset sources from the remote catalogue.

    Result is cached for the lifetime of the process. Falls back to
    _DEFAULT_SOURCES on any network or parse failure.
    """
    global _sources_cache
    if _sources_cache is not None:
        return _sources_cache

    try:
        resp = requests.get(_REMOTE_SOURCES_URL, timeout=10)
        resp.raise_for_status()
        raw: dict = orjson.loads(resp.content)

        valid = {sid: cfg for sid, cfg in raw.items() if _REQUIRED_SOURCE_KEYS.issubset(cfg)}
        for sid in raw:
            if sid not in valid:
                logger.error("Source '%s' missing required keys - skipped.", sid)

        logger.debug("Loaded %d offset sources from remote.", len(valid))
        _sources_cache = valid
        return valid

    except Exception as exc:
        logger.warning("Could not load remote offset sources (%s) - using defaults.", exc)
        _sources_cache = _DEFAULT_SOURCES
        return _DEFAULT_SOURCES

def get_available_offset_sources() -> list[dict]:
    """Return a UI-friendly list of available sources including the local-files option."""
    sources = load_offset_sources()
    result = [
        {
            "id": sid,
            "name": cfg["name"],
            "author": cfg["author"],
            "display": f"{cfg['name']} ({cfg['author']})",
        }
        for sid, cfg in sources.items()
    ]
    result.append({"id": "local", "name": "Local Files", "author": "User", "display": "Local Files"})
    return result

def fetch_offsets() -> tuple[dict | None, dict | None, dict | None]:
    """
    Fetch and validate the three offset JSON files.

    Reads the configured source from ConfigManager. Falls back from
    local → a2x on any failure. Returns (None, None, None) if all
    sources are exhausted.
    """
    config = ConfigManager.load_config()
    source = config["General"].get("OffsetSource", "a2x")
    tried: set[str] = set()

    while source not in tried:
        tried.add(source)

        if source == "local":
            result = _fetch_local(config)
            if result is not None:
                return result
            Logger.error_code(EC.E4009)
            source = "a2x"
            config["General"]["OffsetSource"] = source
            ConfigManager.save_config(config)
            continue

        result = _fetch_remote(source)
        if result is not None:
            return result
        return None, None, None

    Logger.error_code(EC.E4001)
    return None, None, None

def _fetch_local(config: dict) -> tuple | None:
    config_dir = Path(ConfigManager.CONFIG_DIRECTORY)
    offsets_path = Path(config.get("General", {}).get("OffsetsFile", config_dir / "offsets.json"))
    client_path = Path(config.get("General", {}).get("ClientDLLFile", config_dir / "client_dll.json"))
    buttons_path = Path(config.get("General", {}).get("ButtonsFile", config_dir / "buttons.json"))

    try:
        missing = [f.name for f in [offsets_path, client_path, buttons_path] if not f.exists()]
        if missing:
            Logger.error_code(EC.E4002, "Missing: %s", ", ".join(missing))
            return None

        offsets = orjson.loads(offsets_path.read_bytes())
        client = orjson.loads(client_path.read_bytes())
        buttons = orjson.loads(buttons_path.read_bytes())

        if not _validate(offsets, client, buttons):
            Logger.error_code(EC.E4003)
            return None

        logger.info("Loaded and validated local offsets.")
        return offsets, client, buttons

    except (orjson.JSONDecodeError, IOError) as exc:
        Logger.error_code(EC.E4004, "%s", exc)
        return None
    except Exception:
        logger.exception("Unexpected error loading local offsets.")
        return None

def _fetch_remote(source: str) -> tuple | None:
    available = load_offset_sources()
    if source not in available:
        Logger.error_code(EC.E4005, "Source id: '%s'", source)
        return None

    cfg = available[source]
    urls = {
        "offsets":    os.getenv("OFFSETS_URL", cfg["offsets_url"]),
        "client_dll": os.getenv("CLIENT_DLL_URL", cfg["client_dll_url"]),
        "buttons":    os.getenv("BUTTONS_URL", cfg["buttons_url"]),
    }

    try:
        logger.debug("Fetching offsets from %s (%s)…", cfg["name"], cfg["author"])
        with ThreadPoolExecutor(max_workers=3) as ex:
            futures = {k: ex.submit(requests.get, url) for k, url in urls.items()}
            responses = {k: f.result() for k, f in futures.items()}

        for label, resp in responses.items():
            if resp.status_code != 200:
                Logger.error_code(EC.E4006, "HTTP %d fetching %s from %s", resp.status_code, label, cfg["name"])
                return None

        offsets = orjson.loads(responses["offsets"].content)
        client = orjson.loads(responses["client_dll"].content)
        buttons = orjson.loads(responses["buttons"].content)

        if not _validate(offsets, client, buttons):
            Logger.error_code(EC.E4007, "Source: %s", cfg["name"])
            return None

        logger.info("Successfully loaded offsets from %s.", cfg["name"])
        return offsets, client, buttons

    except (orjson.JSONDecodeError, requests.exceptions.RequestException) as exc:
        Logger.error_code(EC.E4008, "Source: %s — %s", cfg["name"], exc)
        return None
    except Exception:
        logger.exception("Unexpected error fetching from %s.", cfg["name"])
        return None

def _validate(offsets: dict, client: dict, buttons: dict) -> bool:
    """Return True if extract_offsets succeeds on the given data."""
    # Import here to avoid circular dependency at module load time.
    from classes.utility import Utility
    return Utility.extract_offsets(offsets, client, buttons) is not None

def check_for_updates(current_version: str) -> tuple[str | None, bool]:
    """
    Check the Vercel status endpoint for a newer release.

    Returns (download_url, is_prerelease) or (None, False).
    """
    try:
        resp = requests.get(_STATUS_URL, timeout=10)
        resp.raise_for_status()
        data: dict = orjson.loads(resp.content)

        remote_str = data.get("version")
        download_url = data.get("download_url") or None

        if not remote_str:
            logger.warning("status.json is missing 'version' field.")
            return None, False

        try:
            remote = version.parse(remote_str)
        except version.InvalidVersion:
            logger.warning("Invalid remote version format: %s", remote_str)
            return None, False

        if remote > version.parse(current_version):
            logger.info("New version available: %s", remote_str)
            return download_url, False

        logger.info("No new updates available.")
        return None, False

    except requests.exceptions.RequestException as exc:
        Logger.error_code(EC.E4010, "%s", exc)
        return None, False
    except Exception:
        logger.exception("Unexpected error during update check.")
        return None, False