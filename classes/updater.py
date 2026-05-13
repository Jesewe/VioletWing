import os
import subprocess
import sys
import threading

import requests
from tkinter import messagebox

from classes.config_manager import ConfigManager
from classes.logger import Logger
from classes.offset_fetcher import check_for_updates

logger = Logger.get_logger(__name__)

class Updater:
    def __init__(self, main_window) -> None:
        self.main_window = main_window
        self.download_url: str | None = None
        self.is_prerelease: bool = False

    def check_for_updates(self) -> bool:
        if not getattr(sys, "frozen", False):
            logger.info("Running from source - auto-update disabled.")
            return False

        logger.info("Running from executable - checking for updates…")
        url, is_pre = check_for_updates(ConfigManager.VERSION)
        if url:
            self.download_url = url
            self.is_prerelease = is_pre
            return True
        return False

    def handle_update(self) -> None:
        if not self.download_url:
            messagebox.showerror("Error", "No update available.")
            return
        label = "pre-release" if self.is_prerelease else "stable release"
        if messagebox.askyesno("Update Available",
                               f"A new {label} is available. Ready to update?"):
            messagebox.showinfo("Updating",
                                "Downloading update in the background. "
                                "You will be notified when complete.")
            threading.Thread(target=self._download_and_apply,
                             args=(self.download_url,), daemon=True).start()

    def _download_and_apply(self, url: str) -> None:
        try:
            logger.info("Downloading update from %s", url)
            resp = requests.get(url, stream=True)
            resp.raise_for_status()

            current_exe = sys.executable
            exe_name = os.path.basename(current_exe)
            temp_exe = os.path.join(ConfigManager.UPDATE_DIRECTORY, "new_VioletWing.exe")
            bat_file = os.path.join(ConfigManager.UPDATE_DIRECTORY, "update.bat")

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
            logger.error("Update failed: %s", exc)
            messagebox.showerror("Update Error", f"Failed to update: {exc}")