import customtkinter as ctk
import threading
import orjson
import requests
from datetime import datetime
from pathlib import Path
from src.gui.icon_loader import icon_label, load_icon
from src.utils.logger import Logger
from src.utils.config_manager import ConfigManager
from src.core.process_monitor import ProcessMonitor
from src.gui.theme import (
    COLOR_BACKGROUND,
    FONT_TITLE, FONT_SUBTITLE, FONT_SECTION_TITLE, FONT_SECTION_DESCRIPTION,
    FONT_ITEM_LABEL, FONT_ITEM_DESCRIPTION, FONT_WIDGET, FONT_TABULAR,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_ACCENT_FG,
    COLOR_BUTTON_DANGER_FG,
    SECTION_STYLE, BUTTON_STYLE_PRIMARY, BUTTON_STYLE_DANGER,
)

# cs2-dumper binary lives in the config directory.
_CS2_DUMPER_EXE_NAME = "cs2-dumper.exe"
_CS2_DUMPER_REPO     = "a2x/cs2-dumper"

_COLOR_OK  = "#22c55e"
_COLOR_ERR = "#ef4444"

logger = Logger.get_logger(__name__)

def populate_dashboard(main_window, frame):
    """Populate the dashboard frame."""
    dashboard = ctk.CTkScrollableFrame(frame, fg_color=COLOR_BACKGROUND)
    dashboard.pack(fill="both", expand=True, padx=40, pady=40)
    dashboard._parent_canvas.configure(yscrollincrement=5)

    title_frame = ctk.CTkFrame(dashboard, fg_color="transparent")
    title_frame.pack(fill="x", pady=(0, 30))
    icon_label(title_frame, "charts_icon.png", size=(38, 38), padx=(0, 16))
    ctk.CTkLabel(title_frame, text="Dashboard", font=FONT_TITLE,
                 text_color=COLOR_TEXT_PRIMARY).pack(side="left")
    ctk.CTkLabel(title_frame, text="Monitor and control your CS2 client",
                 font=FONT_SUBTITLE, text_color=COLOR_TEXT_SECONDARY).pack(
        side="left", padx=(20, 0), pady=(10, 0))

    # Stats banner
    stats_banner = ctk.CTkFrame(dashboard, **SECTION_STYLE)
    stats_banner.pack(fill="x", pady=(0, 30))
    sb_content = ctk.CTkFrame(stats_banner, fg_color="transparent")
    sb_content.pack(fill="x", padx=30, pady=15)

    cs2_item, main_window.cs2_patch_label = _stat_banner_item(
        sb_content, "CS2 Update", "Checking...", "#6b7280", "crosshairs_icon.png")
    cs2_item.pack(side="left", expand=True)

    dumper_item, main_window.dumper_version_label = _stat_banner_item(
        sb_content, "cs2-dumper", "Checking...", "#6b7280", "rotate_icon.png")
    dumper_item.pack(side="left", expand=True)

    ver_item, _ = _stat_banner_item(
        sb_content, "Version", ConfigManager.VERSION, "#8e44ad", "box_archive_icon.png")
    ver_item.pack(side="left", expand=True)

    # Control panel
    ctrl = ctk.CTkFrame(dashboard, **SECTION_STYLE)
    ctrl.pack(fill="x", pady=(0, 40))
    ctrl_header = ctk.CTkFrame(ctrl, fg_color="transparent")
    ctrl_header.pack(fill="x", padx=40, pady=(40, 30))
    icon_label(ctrl_header, "gamepad_icon.png", size=(22, 22), padx=(0, 10))
    ctk.CTkLabel(ctrl_header, text="Control Center", font=FONT_SECTION_TITLE,
                 text_color=COLOR_TEXT_PRIMARY).pack(side="left")

    btns = ctk.CTkFrame(ctrl, fg_color="transparent")
    btns.pack(fill="x", padx=40, pady=(0, 40))
    ctk.CTkButton(btns, text="Start Client", image=load_icon("play_icon.png", (16, 16)),
                  compound="left", command=main_window.start_client,
                  width=180, **BUTTON_STYLE_PRIMARY).pack(side="left", padx=(0, 20))
    ctk.CTkButton(btns, text="Stop Client", image=load_icon("stop_icon.png", (16, 16)),
                  compound="left", command=main_window.stop_client,
                  width=180, **BUTTON_STYLE_DANGER).pack(side="left")

    # System monitor card
    monitor = ctk.CTkFrame(dashboard, **SECTION_STYLE)
    monitor.pack(fill="x", pady=(0, 40))
    mh = ctk.CTkFrame(monitor, fg_color="transparent")
    mh.pack(fill="x", padx=40, pady=(40, 30))
    icon_label(mh, "charts_icon.png", size=(22, 22), padx=(0, 10))
    ctk.CTkLabel(mh, text="System Monitor", font=FONT_SECTION_TITLE,
                 text_color=COLOR_TEXT_PRIMARY).pack(side="left")
    ctk.CTkLabel(mh, text="Refreshes every 5 seconds",
                 font=FONT_SECTION_DESCRIPTION, text_color=COLOR_TEXT_SECONDARY).pack(side="right")

    def _sysmon_row(parent, icon_file, label_text, is_last=False):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=40, pady=(0, 25 if not is_last else 40))
        icon_label(row, icon_file, size=(18, 18), padx=(0, 12))
        ctk.CTkLabel(row, text=label_text, font=FONT_ITEM_LABEL,
                     text_color=COLOR_TEXT_SECONDARY, anchor="w", width=140).pack(side="left")
        val_frame = ctk.CTkFrame(row, fg_color="transparent")
        val_frame.pack(side="left")
        ctk.CTkLabel(val_frame, text="Loading...", font=FONT_ITEM_DESCRIPTION,
                     text_color=COLOR_TEXT_SECONDARY).pack(side="left")
        return val_frame

    main_window._sysmon_cs2_frame  = _sysmon_row(monitor, "crosshairs_icon.png", "CS2")
    main_window._sysmon_self_frame = _sysmon_row(monitor, "bolt_icon.png",        "VioletWing")
    main_window._sysmon_ram_frame  = _sysmon_row(monitor, "gear_icon.png",        "System RAM", is_last=True)

    fetch_cs2_latest_patch(main_window)
    fetch_cs2_dumper_version(main_window)
    start_process_monitor_poll(main_window)


def start_process_monitor_poll(main_window) -> None:
    _DOT = "·"
    _RAM_COLOR_OK    = "#22c55e"
    _RAM_COLOR_AMBER = "#f59e0b"
    _RAM_COLOR_RED   = COLOR_BUTTON_DANGER_FG[1]

    def _set_chips(frame_attr: str, chips: list[tuple[str, str]]) -> None:
        def _apply():
            try:
                frame = getattr(main_window, frame_attr, None)
                if not frame or not frame.winfo_exists():
                    return
                for child in frame.winfo_children():
                    child.destroy()
                for text, color in chips:
                    ctk.CTkLabel(
                        frame, text=text,
                        font=FONT_ITEM_DESCRIPTION,
                        text_color=color, anchor="w",
                    ).pack(side="left")
            except Exception:
                pass
        main_window.ui_queue_put(_apply)

    def _dot():
        return (f"  {_DOT}  ", COLOR_TEXT_SECONDARY)

    def _poll() -> None:
        if getattr(main_window, "current_view", None) == "dashboard":
            cs2 = ProcessMonitor.get_cs2_stats()
            if cs2:
                _set_chips("_sysmon_cs2_frame", [
                    (f"PID {cs2['pid']}",          COLOR_TEXT_SECONDARY),
                    _dot(),
                    (f"{cs2['mem_mb']:.0f}",        COLOR_TEXT_PRIMARY),
                    (" MB",                          COLOR_TEXT_SECONDARY),
                    _dot(),
                    (f"{cs2['cpu_percent']:.1f}%",  COLOR_TEXT_PRIMARY),
                    (" CPU",                         COLOR_TEXT_SECONDARY),
                ])
            else:
                _set_chips("_sysmon_cs2_frame", [("Not running", _RAM_COLOR_RED)])

            slf = ProcessMonitor.get_self_stats()
            if slf:
                _set_chips("_sysmon_self_frame", [
                    (f"{slf['mem_mb']:.0f}",         COLOR_TEXT_PRIMARY),
                    (" MB",                           COLOR_TEXT_SECONDARY),
                    _dot(),
                    (f"{slf['cpu_percent']:.1f}%",   COLOR_TEXT_PRIMARY),
                    (" CPU",                          COLOR_TEXT_SECONDARY),
                ])
            else:
                _set_chips("_sysmon_self_frame", [("-", COLOR_TEXT_SECONDARY)])

            ram = ProcessMonitor.get_system_ram()
            if ram:
                pct = ram["percent"]
                pct_color = (
                    _RAM_COLOR_RED   if pct >= 85 else
                    _RAM_COLOR_AMBER if pct >= 70 else
                    _RAM_COLOR_OK
                )
                _set_chips("_sysmon_ram_frame", [
                    (f"{ram['used_gb']:.1f}",         COLOR_TEXT_PRIMARY),
                    (f" / {ram['total_gb']:.1f} GB",  COLOR_TEXT_SECONDARY),
                    _dot(),
                    (f"{pct:.0f}%",                   pct_color),
                ])
            else:
                _set_chips("_sysmon_ram_frame", [("-", COLOR_TEXT_SECONDARY)])

        if main_window.root.winfo_exists():
            main_window._process_monitor_timer = main_window.root.after(5000, _poll)

    main_window._process_monitor_timer = main_window.root.after(5000, _poll)


def _stat_banner_item(parent, title, value, color, icon_file=None):
    item = ctk.CTkFrame(parent, fg_color="transparent")
    if icon_file:
        icon_label(item, icon_file, size=(18, 18), padx=(0, 8))
    ctk.CTkLabel(item, text=f"{title}:", font=FONT_ITEM_LABEL,
                 text_color=COLOR_TEXT_SECONDARY).pack(side="left", padx=(0, 6))
    val_label = ctk.CTkLabel(item, text=value, font=FONT_TABULAR, text_color=color)
    val_label.pack(side="left")
    return item, val_label


def fetch_cs2_dumper_version(main_window) -> None:
    """Show the cached cs2-dumper version if the binary exists, otherwise fetch from GitHub.

    Two cases:
      - Binary already downloaded: read the version from the GitHub Releases API and
        compare against the cached filename tag (stored alongside the binary).
      - Binary not yet downloaded: show "Not downloaded" in amber.

    This is informational only -- the actual download happens in offset_fetcher.py
    when the user clicks Start Client.
    """
    stop_event = threading.Event()
    main_window._fetch_dumper_stop = stop_event

    def _update_ui(text: str, color: str) -> None:
        def _apply():
            try:
                if main_window.root.winfo_exists() and hasattr(main_window, "dumper_version_label"):
                    main_window.dumper_version_label.configure(text=text, text_color=color)
            except Exception:
                pass
        main_window.ui_queue_put(_apply)

    def _run() -> None:
        exe_path = Path(ConfigManager.CONFIG_DIRECTORY) / _CS2_DUMPER_EXE_NAME

        if not exe_path.exists():
            _update_ui("Not downloaded", "#f59e0b")
            return

        # Binary present -- fetch the latest tag from GitHub so we can show the version.
        # We don't force an update here; that happens on next Start Client if needed.
        if stop_event.is_set():
            return
        try:
            resp = requests.get(
                f"https://api.github.com/repos/{_CS2_DUMPER_REPO}/releases/latest",
                timeout=10,
                headers={"Accept": "application/vnd.github+json"},
            )
            resp.raise_for_status()
            data = orjson.loads(resp.content)
            tag = data.get("tag_name", "unknown")
            _update_ui(tag, _COLOR_OK)
        except Exception as exc:
            logger.warning("Could not fetch cs2-dumper version from GitHub: %s", exc)
            # Binary exists but we couldn't check version -- show generic ready state.
            _update_ui("Ready", _COLOR_OK)

    threading.Thread(target=_run, daemon=True).start()


def fetch_cs2_latest_patch(main_window) -> None:
    """Fetch the latest CS2 patch date from the Steam news API."""
    stop_event = threading.Event()
    main_window._fetch_patch_stop = stop_event

    def _update_ui(text: str, color: str) -> None:
        def _apply():
            try:
                if main_window.root.winfo_exists() and hasattr(main_window, "cs2_patch_label"):
                    main_window.cs2_patch_label.configure(text=text, text_color=color)
            except Exception:
                logger.exception("cs2_patch_label update failed")
        main_window.ui_queue_put(_apply)

    cache_file = Path(ConfigManager.CONFIG_DIRECTORY) / "cs2_patch_cache.txt"

    def _run() -> None:
        # Show cached value immediately while the network request is in flight.
        if cache_file.exists():
            try:
                _update_ui(cache_file.read_text().strip(), _COLOR_OK)
            except OSError:
                pass

        url = (
            "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"
            "?appid=730&count=1&maxlength=1&format=json"
        )
        for attempt in range(3):
            if stop_event.is_set():
                return
            try:
                resp = requests.get(
                    url, headers={"User-Agent": "VioletWing-App"}, timeout=10
                )
                resp.raise_for_status()
                data  = orjson.loads(resp.content)
                items = data.get("appnews", {}).get("newsitems", [])
                if not items:
                    raise ValueError("No news items in Steam API response")
                date_str = datetime.fromtimestamp(items[0]["date"]).strftime("%m/%d/%Y")
                try:
                    cache_file.write_text(date_str)
                except OSError:
                    pass
                _update_ui(date_str, _COLOR_OK)
                return
            except Exception as exc:
                logger.error("Failed to fetch CS2 patch date (attempt %d): %s", attempt + 1, exc)
                if attempt < 2:
                    import time
                    for _ in range(50):
                        if stop_event.is_set():
                            return
                        time.sleep(0.1)

        _update_ui("Error", _COLOR_ERR)

    threading.Thread(target=_run, daemon=True).start()