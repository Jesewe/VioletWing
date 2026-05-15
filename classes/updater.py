import os
import subprocess
import sys
import threading

import requests
from packaging import version
from tkinter import messagebox

from classes.config_manager import ConfigManager
from classes.logger import Logger
import classes.error_codes as EC
from classes.offset_fetcher import fetch_latest_release

logger = Logger.get_logger(__name__)

_GITHUB_REPO = "Jesewe/VioletWing"

class Updater:
    def __init__(self, main_window) -> None:
        self.main_window = main_window
        self.download_url: str | None = None
        self.html_url: str | None = None
        self.changelog: str | None = None
        self.is_prerelease: bool = False
        self._latest_version: str | None = None

    def fetch_in_background(self, on_complete: callable) -> None:
        """Kick off a daemon thread that calls the GitHub API."""
        threading.Thread(
            target=self._fetch_worker,
            args=(on_complete,),
            daemon=True,
        ).start()

    def _fetch_worker(self, on_complete: callable) -> None:
        if not getattr(sys, "frozen", False):
            # Changelog display still works from source; update download skipped.
            logger.info("Running from source - update download disabled; changelog check proceeds.")

        logger.info("Fetching latest release from GitHub (%s)...", _GITHUB_REPO)
        release = fetch_latest_release(_GITHUB_REPO)
        has_update = False

        if release:
            self._latest_version = release["version"]
            self.download_url    = release["download_url"]
            self.html_url        = release["html_url"]
            self.changelog       = release["changelog"]
            self.is_prerelease   = release["is_prerelease"]

            try:
                has_update = (
                    version.parse(release["version"]) > version.parse(ConfigManager.VERSION)
                    and getattr(sys, "frozen", False)
                )
            except version.InvalidVersion:
                logger.warning(
                    "Version comparison failed: remote=%s local=%s",
                    release["version"],
                    ConfigManager.VERSION,
                )
        else:
            logger.warning("Could not retrieve release info from GitHub.")

        self.main_window.root.after(0, lambda: on_complete(has_update, release))

    def changelog_already_seen(self) -> bool:
        """True if the user has already dismissed the changelog for this version."""
        if not self._latest_version:
            return True
        config = ConfigManager.load_config()
        return config.get("seen_changelog_version") == self._latest_version

    def mark_changelog_seen(self) -> None:
        """Persist the current version tag so the changelog is not shown again."""
        if not self._latest_version:
            return
        config = ConfigManager.load_config()
        config["seen_changelog_version"] = self._latest_version
        ConfigManager.save_config(config, log_info=False)

    def handle_update(self) -> None:
        if not self.download_url:
            messagebox.showerror("Error", "No download URL is available for this release.")
            return
        label = "pre-release" if self.is_prerelease else "stable release"
        if messagebox.askyesno(
            "Update Available",
            f"A new {label} is available. Ready to update?",
        ):
            messagebox.showinfo(
                "Updating",
                "Downloading update in the background. "
                "You will be notified when complete.",
            )
            threading.Thread(
                target=self._download_and_apply,
                args=(self.download_url,),
                daemon=True,
            ).start()

    def _download_and_apply(self, url: str) -> None:
        try:
            logger.info("Downloading update from %s", url)
            resp = requests.get(url, stream=True)
            resp.raise_for_status()

            current_exe = sys.executable
            exe_name    = os.path.basename(current_exe)
            temp_exe    = os.path.join(ConfigManager.UPDATE_DIRECTORY, "new_VioletWing.exe")
            bat_file    = os.path.join(ConfigManager.UPDATE_DIRECTORY, "update.bat")

            os.makedirs(ConfigManager.UPDATE_DIRECTORY, exist_ok=True)
            with open(temp_exe, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=8192):
                    fh.write(chunk)

            logger.info("Update downloaded - writing updater script.")
            with open(bat_file, "w") as fh:
                fh.write(f"""@echo off
title VioletWing Updater
echo Updating VioletWing...
echo.
echo Waiting for application to close...
timeout /t 3 /nobreak >nul

:WAIT_LOOP
tasklist /FI "IMAGENAME eq {exe_name}" 2>NUL | find /I /N "{exe_name}">NUL
if "%ERRORLEVEL%"=="0" (
    echo Application is still running, waiting...
    timeout /t 2 /nobreak >nul
    goto WAIT_LOOP
)

echo Backing up current version...
if exist "{current_exe}.backup" del "{current_exe}.backup"
move "{current_exe}" "{current_exe}.backup"

echo Installing new version...
move "{temp_exe}" "{current_exe}"

echo Starting updated application...
start "" "{current_exe}"

echo Update completed successfully!
timeout /t 3 /nobreak >nul

echo Cleaning up...
del "{current_exe}.backup" 2>nul
del "%~f0" 2>nul
""")

            subprocess.Popen(bat_file, shell=True)
            self.main_window.root.quit()

        except Exception as exc:
            Logger.error_code(EC.E4011, "%s", exc)
            messagebox.showerror("Update Error", f"Failed to update: {exc}")