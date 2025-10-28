import os
import threading
import sys
import subprocess
import requests
from tkinter import messagebox
from classes.config_manager import ConfigManager
from classes.logger import Logger
from classes.utility import Utility

logger = Logger.get_logger(__name__)

class Updater:
    def __init__(self, main_window):
        self.main_window = main_window
        self.download_url = None
        self.is_prerelease = False

    def check_for_updates(self):
        if getattr(sys, 'frozen', False):
            logger.info("Running from executable. Checking for updates...")
            download_url, is_prerelease = Utility.check_for_updates(ConfigManager.VERSION)
            if download_url:
                self.download_url = download_url
                self.is_prerelease = is_prerelease
                return True
        else:
            logger.info("Running from source code. Auto-update disabled.")
        return False

    def handle_update(self):
        if not self.download_url:
            messagebox.showerror("Error", "No update available.")
            return

        update_type = "pre-release" if self.is_prerelease else "stable release"
        response = messagebox.askyesno("Update Available", f"A new {update_type} is available. Are you ready to update?")
        if response:
            messagebox.showinfo("Updating", "Downloading update in background. You will be notified when the update is complete.")
            threading.Thread(target=self.download_and_update, args=(self.download_url,)).start()

    def download_and_update(self, download_url):
        try:
            logger.info(f"Downloading update from {download_url}")
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            current_exe = sys.executable
            exe_name = os.path.basename(current_exe)
            temp_exe = os.path.join(ConfigManager.UPDATE_DIRECTORY, "new_VioletWing.exe")
            bat_file = os.path.join(ConfigManager.UPDATE_DIRECTORY, "update.bat")
            
            with open(temp_exe, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info("Update downloaded successfully")
            
            with open(bat_file, 'w') as f:
                f.write(f'''@echo off
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
''')
            
            logger.info(f".bat file created at {bat_file}")
            
            subprocess.Popen(bat_file, shell=True)
            self.main_window.root.quit()
        except Exception as e:
            logger.error(f"Failed to update: {e}")
            messagebox.showerror("Update Error", f"Failed to update: {str(e)}")