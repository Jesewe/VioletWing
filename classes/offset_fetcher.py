import os
import subprocess
import sys
import tempfile
from pathlib import Path

import orjson
import requests
from packaging import version

from classes.config_manager import ConfigManager
from classes.logger import Logger
import classes.error_codes as EC

logger = Logger.get_logger(__name__)

_GITHUB_RELEASES_URL = "https://api.github.com/repos/{repo}/releases/latest"

# cs2-dumper is the sole offset source.
_CS2_DUMPER_REPO = "a2x/cs2-dumper"
_CS2_DUMPER_EXE_NAME = "cs2-dumper.exe"

# Binary is cached in the config directory so it persists across runs and
# can be refreshed independently of VioletWing releases.
_CS2_DUMPER_EXE_PATH = Path(ConfigManager.CONFIG_DIRECTORY) / _CS2_DUMPER_EXE_NAME

# Subprocess timeout in seconds -- cs2-dumper typically finishes in <10s.
_SUBPROCESS_TIMEOUT = 120

# Public API
def fetch_offsets() -> tuple[dict | None, dict | None, dict | None]:
    """Run cs2-dumper against the live CS2 process and return parsed offsets.

    Returns (offsets, client_data, buttons_data) on success, (None, None, None)
    on any failure. Failures are logged with structured error codes.
    """
    from classes.game_process import is_game_running

    if not is_game_running():
        Logger.error_code(EC.E4012)
        return None, None, None

    if not _ensure_binary():
        return None, None, None

    with tempfile.TemporaryDirectory(prefix="violetwing_dump_") as tmp:
        if not _run_cs2_dumper(tmp):
            return None, None, None

        return _load_output(tmp)

def fetch_latest_release(repo: str) -> "dict | None":
    """Fetch the latest VioletWing release metadata from the GitHub Releases API."""
    url = _GITHUB_RELEASES_URL.format(repo=repo)
    try:
        resp = requests.get(
            url,
            timeout=10,
            headers={"Accept": "application/vnd.github+json"},
        )
        resp.raise_for_status()
        data: dict = orjson.loads(resp.content)

        tag = data.get("tag_name")
        if not tag:
            logger.warning("GitHub releases response is missing 'tag_name'.")
            return None

        try:
            version.parse(tag)
        except version.InvalidVersion:
            logger.warning("Unparseable version tag from GitHub: %s", tag)
            return None

        # Locate the first .exe asset (binary release artifact)
        download_url: str | None = None
        for asset in data.get("assets", []):
            if asset.get("name", "").lower().endswith(".exe"):
                download_url = asset.get("browser_download_url")
                break

        logger.debug("Latest GitHub release: %s (prerelease=%s)", tag, data.get("prerelease"))
        return {
            "version":       tag,
            "download_url":  download_url,
            "html_url":      data.get("html_url", ""),
            "changelog":     data.get("body", ""),
            "is_prerelease": bool(data.get("prerelease", False)),
        }

    except requests.exceptions.RequestException as exc:
        logger.warning("Network error fetching GitHub release: %s", exc)
        return None
    except Exception:
        logger.exception("Unexpected error fetching GitHub release.")
        return None

# Binary management
def _ensure_binary() -> bool:
    """Return True if the cs2-dumper binary is ready to use.

    Downloads from GitHub Releases if not already cached.
    """
    if _CS2_DUMPER_EXE_PATH.exists():
        return True
    return _download_cs2_dumper()

def _download_cs2_dumper() -> bool:
    """Download the latest cs2-dumper.exe from GitHub Releases.

    Caches it at _CS2_DUMPER_EXE_PATH. Returns True on success.
    """
    api_url = _GITHUB_RELEASES_URL.format(repo=_CS2_DUMPER_REPO)
    try:
        logger.info("Fetching cs2-dumper release info from %s", api_url)
        resp = requests.get(
            api_url,
            timeout=15,
            headers={"Accept": "application/vnd.github+json"},
        )
        resp.raise_for_status()
        data = orjson.loads(resp.content)

        download_url: str | None = None
        for asset in data.get("assets", []):
            if asset.get("name", "").lower() == _CS2_DUMPER_EXE_NAME.lower():
                download_url = asset["browser_download_url"]
                break

        if not download_url:
            logger.error(
                "cs2-dumper release '%s' has no asset named '%s'. Available: %s",
                data.get("tag_name"),
                _CS2_DUMPER_EXE_NAME,
                [a["name"] for a in data.get("assets", [])],
            )
            Logger.error_code(EC.E4014)
            return False

        logger.info("Downloading cs2-dumper %s from %s", data.get("tag_name"), download_url)
        binary_resp = requests.get(download_url, timeout=60)
        binary_resp.raise_for_status()

        _CS2_DUMPER_EXE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CS2_DUMPER_EXE_PATH.write_bytes(binary_resp.content)
        logger.info(
            "cs2-dumper saved to %s (%d bytes).",
            _CS2_DUMPER_EXE_PATH,
            len(binary_resp.content),
        )
        return True

    except requests.exceptions.RequestException as exc:
        logger.error("Network error downloading cs2-dumper: %s", exc)
        Logger.error_code(EC.E4014)
        return False
    except Exception:
        logger.exception("Unexpected error downloading cs2-dumper.")
        Logger.error_code(EC.E4014)
        return False

# Subprocess
def _run_cs2_dumper(output_dir: str) -> bool:
    """Spawn cs2-dumper and wait for it to finish.

    Passes -f json so only JSON files are generated -- skipping cs/hpp/rs/zig
    cuts runtime noticeably. Returns True on clean exit (returncode 0).
    """
    cmd = [str(_CS2_DUMPER_EXE_PATH), "-o", output_dir, "-f", "json"]
    logger.debug("Running cs2-dumper: %s", " ".join(cmd))

    startupinfo = None
    creationflags = 0
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= getattr(subprocess, "STARTF_USESHOWWINDOW", 0)
        startupinfo.wShowWindow = getattr(subprocess, "SW_HIDE", 0)
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    proc = None
    stdout = ""
    stderr = ""

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            startupinfo=startupinfo,
            creationflags=creationflags,
        )
        stdout, stderr = proc.communicate(timeout=_SUBPROCESS_TIMEOUT)
    except subprocess.TimeoutExpired:
        if proc is not None and proc.poll() is None:
            proc.kill()
            stdout, stderr = proc.communicate()
        Logger.error_code(EC.E4013, "cs2-dumper timed out after %ds", _SUBPROCESS_TIMEOUT)
        return False
    except FileNotFoundError:
        Logger.error_code(EC.E4014, "Could not execute: %s", _CS2_DUMPER_EXE_PATH)
        return False
    except Exception as exc:
        Logger.error_code(EC.E4013, "%s", exc)
        return False

    if stdout:
        for line in stdout.splitlines():
            logger.debug("[cs2-dumper] %s", line)

    if proc.returncode != 0:
        if stderr:
            for line in stderr.splitlines():
                logger.error("[cs2-dumper stderr] %s", line)
        Logger.error_code(EC.E4013, "exit code %d", proc.returncode)
        return False

    return True

# Output parsing
def _load_output(output_dir: str) -> tuple[dict, dict, dict] | tuple[None, None, None]:
    """Read and validate the three JSON files cs2-dumper writes.

    cs2-dumper writes:
      offsets.json      -- {module: {offset_name: int}}
      buttons.json      -- {button_name: int}   (flat, no module namespace)
      client_dll.json   -- {client.dll: {classes: {...}}}  (slugified from client.dll)

    buttons.json is flat; extract_offsets() expects {"client.dll": {...}}.
    We wrap it here at the load boundary so the rest of the codebase is unaffected.
    """
    tmp = Path(output_dir)
    offsets_file = tmp / "offsets.json"
    client_file  = tmp / "client_dll.json"
    buttons_file = tmp / "buttons.json"

    missing = [f.name for f in [offsets_file, client_file, buttons_file] if not f.exists()]
    if missing:
        Logger.error_code(EC.E4015, "Missing output files: %s", ", ".join(missing))
        return None, None, None

    try:
        offsets     = orjson.loads(offsets_file.read_bytes())
        client      = orjson.loads(client_file.read_bytes())
        buttons_raw = orjson.loads(buttons_file.read_bytes())
    except (orjson.JSONDecodeError, IOError) as exc:
        Logger.error_code(EC.E4015, "JSON read error: %s", exc)
        return None, None, None

    # cs2-dumper buttons are flat {name: int}; wrap to match extract_offsets() contract.
    buttons = buttons_raw

    if not _validate(offsets, client, buttons):
        Logger.error_code(EC.E4015, "Validation failed")
        return None, None, None

    logger.info("cs2-dumper: offsets loaded and validated successfully.")
    return offsets, client, buttons

def _validate(offsets: dict, client: dict, buttons: dict) -> bool:
    from classes.utility import Utility
    return Utility.extract_offsets(offsets, client, buttons) is not None