import os
import subprocess
import sys
import threading

import customtkinter as ctk
import requests
from packaging import version

from src.utils.config_manager import ConfigManager
from src.utils.logger import Logger
import src.utils.error_codes as EC
from src.core.offset_fetcher import fetch_latest_release

logger = Logger.get_logger(__name__)

_GITHUB_REPO = "Jesewe/VioletWing"


class DownloadProgressModal:
    """Modal that owns the download thread and shows a live progress bar.

    Determinate when Content-Length is present; indeterminate otherwise.
    grab_set() blocks the parent without blocking the event loop, so
    root.after() callbacks keep firing to update the bar.
    """

    _WIDTH  = 420
    _HEIGHT = 170

    def __init__(self, root: ctk.CTk, url: str, on_done: callable) -> None:
        self._root    = root
        self._url     = url
        self._on_done = on_done  # (success: bool, exc: Exception|None) on main thread

        self._win = ctk.CTkToplevel(root)
        self._win.title("Updating VioletWing")
        self._win.resizable(False, False)
        self._win.protocol("WM_DELETE_WINDOW", lambda: None)  # no close during download

        self._win.update_idletasks()
        x = root.winfo_x() + (root.winfo_width()  // 2) - (self._WIDTH  // 2)
        y = root.winfo_y() + (root.winfo_height() // 2) - (self._HEIGHT // 2)
        self._win.geometry(f"{self._WIDTH}x{self._HEIGHT}+{x}+{y}")

        self._build_ui()

        # CTkToplevel on Windows drops iconbitmap set before the first draw.
        self._win.after(200, self._apply_icon)

        self._win.grab_set()
        self._win.lift()
        self._win.focus_force()

        threading.Thread(target=self._worker, daemon=True).start()

    def _apply_icon(self) -> None:
        try:
            from src.utils.utility import Utility
            from src.gui.icon_loader import ASSETS_DIR
            self._win.iconbitmap(Utility.resource_path(f"{ASSETS_DIR}/icon.ico"))
        except Exception:
            pass

    def _build_ui(self) -> None:
        from src.gui.theme import (
            FONT_FAMILY_BOLD, FONT_FAMILY_REGULAR,
            FONT_SIZE_H4, FONT_SIZE_P,
            COLOR_BACKGROUND, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
            COLOR_ACCENT_FG,
        )

        outer = ctk.CTkFrame(self._win, fg_color=COLOR_BACKGROUND, corner_radius=0)
        outer.pack(fill="both", expand=True)

        ctk.CTkLabel(
            outer,
            text="Downloading update\u2026",
            font=(FONT_FAMILY_BOLD[0], FONT_SIZE_H4, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(pady=(24, 6))

        self._status_label = ctk.CTkLabel(
            outer,
            text="Connecting\u2026",
            font=(FONT_FAMILY_REGULAR[0], FONT_SIZE_P),
            text_color=COLOR_TEXT_SECONDARY,
        )
        self._status_label.pack(pady=(0, 10))

        self._bar = ctk.CTkProgressBar(
            outer,
            width=360,
            height=14,
            corner_radius=7,
            progress_color=COLOR_ACCENT_FG,
        )
        self._bar.set(0)
        self._bar.pack()

        self._pct_label = ctk.CTkLabel(
            outer,
            text="",
            font=(FONT_FAMILY_REGULAR[0], FONT_SIZE_P),
            text_color=COLOR_TEXT_SECONDARY,
        )
        self._pct_label.pack(pady=(6, 0))

    def _set_indeterminate(self) -> None:
        self._bar.configure(mode="indeterminate")
        self._bar.start()

    def _update_progress(self, downloaded: int, total: int | None) -> None:
        if total:
            fraction = min(downloaded / total, 1.0)
            self._bar.set(fraction)
            self._status_label.configure(
                text=f"{downloaded / 1_048_576:.1f} MB / {total / 1_048_576:.1f} MB"
            )
            self._pct_label.configure(text=f"{fraction * 100:.0f}%")
        else:
            self._status_label.configure(
                text=f"{downloaded / 1_048_576:.1f} MB downloaded"
            )

    def _close(self) -> None:
        try:
            self._bar.stop()
        except Exception:
            pass
        self._win.grab_release()
        self._win.destroy()

    def _worker(self) -> None:
        try:
            logger.info("Downloading update from %s", self._url)
            resp = requests.get(self._url, stream=True, timeout=60)
            resp.raise_for_status()

            raw_cl = resp.headers.get("Content-Length")
            total_bytes = int(raw_cl) if (raw_cl and raw_cl.isdigit()) else None
            if total_bytes is None:
                self._root.after(0, self._set_indeterminate)

            current_exe = sys.executable
            exe_name    = os.path.basename(current_exe)
            temp_exe    = os.path.join(ConfigManager.UPDATE_DIRECTORY, "new_VioletWing.exe")
            bat_file    = os.path.join(ConfigManager.UPDATE_DIRECTORY, "update.bat")

            os.makedirs(ConfigManager.UPDATE_DIRECTORY, exist_ok=True)

            downloaded = 0
            with open(temp_exe, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=8192):
                    fh.write(chunk)
                    downloaded += len(chunk)
                    # Default-arg capture prevents the closure from seeing the
                    # final loop value of `downloaded` on every callback.
                    _d, _t = downloaded, total_bytes
                    self._root.after(0, lambda d=_d, t=_t: self._update_progress(d, t))

            logger.info("Update downloaded - writing updater script.")
            logger.info("bat_file path: %s", bat_file)
            logger.info("current_exe:   %s", current_exe)
            logger.info("temp_exe:      %s", temp_exe)

            # Batch files on Windows require CRLF line endings.
            # Unix newlines (\n only) cause `goto` label resolution to fail
            # silently - the script runs but jumps never land.
            bat_content = "\r\n".join([
                "@echo off",
                "title VioletWing Updater",
                "echo Updating VioletWing...",
                "echo.",
                "echo Waiting for application to close...",
                "timeout /t 3 /nobreak >nul",
                "",
                ":WAIT_LOOP",
                f'tasklist /FI "IMAGENAME eq {exe_name}" 2>NUL | find /I /N "{exe_name}">NUL',
                'if "%ERRORLEVEL%"=="0" (',
                "    echo Application is still running, waiting...",
                "    timeout /t 2 /nobreak >nul",
                "    goto WAIT_LOOP",
                ")",
                "",
                "echo Process exited, allowing cleanup to finish...",
                "timeout /t 2 /nobreak >nul",
                "",
                "echo Backing up current version...",
                f'if exist "{current_exe}.backup" del "{current_exe}.backup"',
                f'move "{current_exe}" "{current_exe}.backup"',
                "",
                "echo Installing new version...",
                f'move "{temp_exe}" "{current_exe}"',
                "",
                "echo Starting updated application...",
                f'start "" "{current_exe}"',
                "",
                "echo Update completed successfully!",
                "timeout /t 3 /nobreak >nul",
                "",
                "echo Cleaning up...",
                f'del "{current_exe}.backup" 2>nul',
                'del "%~f0" 2>nul',
                "",
            ])

            with open(bat_file, "w", newline="") as fh:
                fh.write(bat_content)

            logger.info("Bat content:\n%s", bat_content.replace("\r\n", "\n"))

            # CREATE_NEW_CONSOLE opens a visible updater window so the user
            # can see progress and we can diagnose if the bat runs at all.
            proc = subprocess.Popen(
                ["cmd.exe", "/c", bat_file],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            logger.info("Updater process launched - pid %d", proc.pid)
            self._root.after(0, lambda: self._finish(success=True, exc=None))

        except Exception as exc:
            Logger.error_code(EC.E4011, "%s", exc)
            self._root.after(0, lambda e=exc: self._finish(success=False, exc=e))

    def _finish(self, success: bool, exc: Exception | None) -> None:
        self._close()
        self._on_done(success, exc)


class Updater:
    def __init__(self, main_window) -> None:
        self.main_window = main_window
        self.download_url: str | None    = None
        self.html_url: str | None        = None
        self.changelog: str | None       = None
        self.is_prerelease: bool         = False
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
        from src.gui.modal import AppModal
        root = self.main_window.root

        if not self.download_url:
            AppModal.error(root, "Error", "No download URL is available for this release.")
            return

        label = "pre-release" if self.is_prerelease else "stable release"
        if not AppModal.confirm(
            root,
            "Update Available",
            f"A new {label} is available. Ready to update?",
        ):
            return

        def _on_download_done(success: bool, exc: Exception | None) -> None:
            if success:
                root.quit()
            else:
                AppModal.error(root, "Update Error", f"Failed to download update:\n{exc}")

        DownloadProgressModal(root, self.download_url, _on_download_done)