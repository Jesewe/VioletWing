import os
import subprocess
import sys
import threading
import time

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

    Tracks progress percentage, download size, transfer speed, and allows cancellation.
    """

    _WIDTH  = 440
    _HEIGHT = 220

    def __init__(self, root: ctk.CTk, url: str, on_done: callable) -> None:
        self._root         = root
        self._url          = url
        self._on_done      = on_done  # (success: bool, exc: Exception|None) on main thread
        self._cancel_event = threading.Event()
        self._is_cancelled = False

        self._win = ctk.CTkToplevel(root)
        self._win.title("Updating VioletWing")
        self._win.resizable(False, False)
        self._win.protocol("WM_DELETE_WINDOW", self._on_cancel_click)

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
            COLOR_ACCENT_FG, COLOR_BORDER,
        )

        outer = ctk.CTkFrame(self._win, fg_color=COLOR_BACKGROUND, corner_radius=0)
        outer.pack(fill="both", expand=True)

        ctk.CTkLabel(
            outer,
            text="Downloading update\u2026",
            font=(FONT_FAMILY_BOLD[0], FONT_SIZE_H4, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(pady=(20, 4))

        self._status_label = ctk.CTkLabel(
            outer,
            text="Connecting\u2026",
            font=(FONT_FAMILY_REGULAR[0], FONT_SIZE_P),
            text_color="#E2E8F0",
        )
        self._status_label.pack(pady=(0, 10))

        self._bar = ctk.CTkProgressBar(
            outer,
            width=380,
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
            text_color="#94A3B8",
        )
        self._pct_label.pack(pady=(6, 10))

        self._cancel_btn = ctk.CTkButton(
            outer,
            text="Cancel",
            width=110,
            height=32,
            corner_radius=8,
            fg_color="transparent",
            hover_color=COLOR_BACKGROUND,
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_SECONDARY,
            font=(FONT_FAMILY_BOLD[0], FONT_SIZE_P),
            command=self._on_cancel_click,
        )
        self._cancel_btn.pack(pady=(0, 16))

    def _on_cancel_click(self) -> None:
        if not self._is_cancelled:
            self._is_cancelled = True
            self._cancel_event.set()
            self._status_label.configure(text="Cancelling download\u2026")
            self._cancel_btn.configure(state="disabled", text="Cancelling\u2026")

    def _set_indeterminate(self) -> None:
        self._bar.configure(mode="indeterminate")
        self._bar.start()

    def _update_progress(self, downloaded: int, total: int | None, speed_bytes_per_sec: float) -> None:
        if self._is_cancelled:
            return
        speed_mb = speed_bytes_per_sec / 1_048_576
        speed_str = f"{speed_mb:.1f} MB/s" if speed_mb >= 0.1 else f"{speed_bytes_per_sec / 1024:.0f} KB/s" if speed_bytes_per_sec > 0 else ""

        if total:
            fraction = min(downloaded / total, 1.0)
            self._bar.set(fraction)
            downloaded_mb = downloaded / 1_048_576
            total_mb = total / 1_048_576
            self._status_label.configure(
                text=f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB"
            )
            pct_str = f"{fraction * 100:.0f}%"
            if speed_str:
                self._pct_label.configure(text=f"{pct_str}  ·  {speed_str}")
            else:
                self._pct_label.configure(text=pct_str)
        else:
            downloaded_mb = downloaded / 1_048_576
            self._status_label.configure(
                text=f"{downloaded_mb:.1f} MB downloaded"
            )
            if speed_str:
                self._pct_label.configure(text=speed_str)

    def _close(self) -> None:
        try:
            self._bar.stop()
        except Exception:
            pass
        self._win.grab_release()
        self._win.destroy()

    def _worker(self) -> None:
        temp_exe = None
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
            start_time = time.time()
            last_sample_time = start_time
            last_sample_bytes = 0
            current_speed = 0.0

            with open(temp_exe, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=8192):
                    if self._cancel_event.is_set():
                        logger.info("Update download cancelled by user.")
                        break
                    fh.write(chunk)
                    downloaded += len(chunk)

                    now = time.time()
                    dt = now - last_sample_time
                    if dt >= 0.3:
                        current_speed = (downloaded - last_sample_bytes) / dt
                        last_sample_time = now
                        last_sample_bytes = downloaded

                    _d, _t, _s = downloaded, total_bytes, current_speed
                    self._root.after(0, lambda d=_d, t=_t, s=_s: self._update_progress(d, t, s))

            if self._cancel_event.is_set():
                if temp_exe and os.path.exists(temp_exe):
                    try:
                        os.remove(temp_exe)
                    except Exception as e:
                        logger.debug("Failed to remove temporary update file: %s", e)
                self._root.after(0, lambda: self._finish(success=False, exc=Exception("Download cancelled")))
                return

            logger.info("Update downloaded - writing updater script.")
            logger.info("bat_file path: %s", bat_file)
            logger.info("current_exe:   %s", current_exe)
            logger.info("temp_exe:      %s", temp_exe)

            # Batch files on Windows require CRLF line endings.
            # Unix newlines (\n only) cause `goto` label resolution to fail
            # silently - the script runs but jumps never land.
            # Crucially, _MEIPASS and _MEIPASS2 must be cleared so the re-launched
            # PyInstaller binary does not attempt to load Python DLLs from the
            # defunct temporary directory of the parent process.
            bat_content = "\r\n".join([
                "@echo off",
                "title VioletWing Updater",
                "echo Updating VioletWing...",
                "echo.",
                "set _MEIPASS=",
                "set _MEIPASS2=",
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
                "set _MEIPASS=",
                "set _MEIPASS2=",
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
            # Sanitize environment variables so PyInstaller temp paths aren't inherited.
            proc_env = os.environ.copy()
            proc_env.pop("_MEIPASS", None)
            proc_env.pop("_MEIPASS2", None)

            proc = subprocess.Popen(
                ["cmd.exe", "/c", bat_file],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                env=proc_env,
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
            return

        has_update = False
        release = fetch_latest_release(_GITHUB_REPO)
        if release and "version" in release:
            self._latest_version = release["version"]
            self.download_url    = release.get("download_url")
            self.html_url        = release.get("html_url")
            self.changelog       = release.get("changelog")
            self.is_prerelease   = release.get("is_prerelease", False)

            try:
                remote_v = version.parse(release["version"])
                local_v  = version.parse(ConfigManager.VERSION)
                has_update = remote_v > local_v
                logger.info(
                    "Version check: remote=%s local=%s has_update=%s",
                    remote_v, local_v, has_update
                )
            except Exception as exc:
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

        ver = self._latest_version
        if ver:
            ver_str = ver if ver.startswith("v") else f"v{ver}"
            title_text = f"Version {ver_str} is ready to install"
            message_text = f"Version {ver_str} includes stability fixes and performance updates.\n\nWould you like to install it now?"
        else:
            label = "pre-release" if self.is_prerelease else "stable release"
            title_text = "Update Available"
            message_text = f"A new {label} is available.\n\nWould you like to install it now?"

        if not AppModal.confirm(
            root,
            title_text,
            message_text,
            confirm_text="Update Now",
            cancel_text="Later",
            glyph="\u2913",
        ):
            return

        def _on_download_done(success: bool, exc: Exception | None) -> None:
            if success:
                root.quit()
            elif exc and "cancelled" in str(exc).lower():
                logger.info("Update download was cancelled by user.")
            else:
                AppModal.error(root, "Update Error", f"Failed to download update:\n{exc}")

        DownloadProgressModal(root, self.download_url, _on_download_done)