import customtkinter as ctk
import threading
import orjson
import requests
import time
from datetime import datetime
from pathlib import Path
from PIL import Image
from gui.icon_loader import icon_label, load_icon
from classes.logger import Logger
from classes.utility import Utility
from classes.config_manager import ConfigManager
from classes.process_monitor import ProcessMonitor
from dateutil.parser import parse as parse_date
from gui.theme import (
    FONT_TITLE, FONT_SUBTITLE, FONT_SECTION_TITLE, FONT_SECTION_DESCRIPTION,
    FONT_ITEM_LABEL, FONT_ITEM_DESCRIPTION, FONT_WIDGET,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_ACCENT_FG,
    COLOR_BUTTON_DANGER_FG,
    SECTION_STYLE, BUTTON_STYLE_PRIMARY, BUTTON_STYLE_DANGER,
)

# Days-stale thresholds for the Offsets card warning colours.
_STALENESS_AMBER_DAYS = 1
_STALENESS_RED_DAYS   = 3

_COLOR_STALE_AMBER = "#f59e0b"
_COLOR_STALE_RED   = "#ef4444"
_COLOR_FRESH       = "#22c55e"

# Guards concurrent writes to main_window._cs2_patch_dt / ._offsets_dt.
_staleness_lock = threading.Lock()

logger = Logger.get_logger(__name__)

def populate_dashboard(main_window, frame):
    """Populate the dashboard frame."""
    dashboard = ctk.CTkScrollableFrame(frame, fg_color="transparent")
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

    stats_banner = ctk.CTkFrame(dashboard, **SECTION_STYLE)
    stats_banner.pack(fill="x", pady=(0, 30))
    sb_content = ctk.CTkFrame(stats_banner, fg_color="transparent")
    sb_content.pack(fill="x", padx=30, pady=15)

    cs2_item, main_window.cs2_patch_label = _stat_banner_item(
        sb_content, "CS2 Update", "Checking...", "#6b7280", "crosshairs_icon.png")
    cs2_item.pack(side="left", expand=True)

    upd_item, main_window.update_value_label = _stat_banner_item(
        sb_content, "Offsets Update", "Checking...", "#6b7280", "rotate_icon.png")
    upd_item.pack(side="left", expand=True)

    # Warning label hidden until staleness is detected
    main_window._offsets_warning_label = ctk.CTkLabel(
        upd_item, text="", font=FONT_ITEM_DESCRIPTION,
        text_color=_COLOR_STALE_AMBER, anchor="w")

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
        # Value frame: populated by _poll with inline chip labels
        val_frame = ctk.CTkFrame(row, fg_color="transparent")
        val_frame.pack(side="left")
        
        # Add a placeholder so it doesn't stretch to 200x200 before the first poll
        ctk.CTkLabel(val_frame, text="Loading...", font=FONT_ITEM_DESCRIPTION, text_color=COLOR_TEXT_SECONDARY).pack(side="left")
        
        return val_frame

    main_window._sysmon_cs2_frame  = _sysmon_row(monitor, "crosshairs_icon.png", "CS2")
    main_window._sysmon_self_frame = _sysmon_row(monitor, "bolt_icon.png",        "VioletWing")
    main_window._sysmon_ram_frame  = _sysmon_row(monitor, "gear_icon.png",        "System RAM", is_last=True)



    fetch_last_update(main_window)
    fetch_cs2_latest_patch(main_window)
    start_process_monitor_poll(main_window)

def start_process_monitor_poll(main_window) -> None:
    """Schedule a recurring 5-second poll that updates the System Monitor card.

    Runs on the main thread via root.after — psutil calls for 2-3 processes
    are sub-millisecond, so no background thread is needed. The after handle
    is stored on main_window so cleanup() can cancel it on exit.
    """
    _DOT = "·"
    _RAM_COLOR_OK    = "#22c55e"
    _RAM_COLOR_AMBER = "#f59e0b"
    _RAM_COLOR_RED   = COLOR_BUTTON_DANGER_FG[1]  # dark-mode danger red

    def _set_chips(frame_attr: str, chips: list[tuple[str, str]]) -> None:
        """Replace the children of a value frame with inline chip labels.

        chips: list of (text, color) pairs rendered left-to-right with no gap.
        Existing children are destroyed on each call — frames hold only a
        handful of labels so the churn is negligible.
        """
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
                    (f"PID {cs2['pid']}",            COLOR_TEXT_SECONDARY),
                    _dot(),
                    (f"{cs2['mem_mb']:.0f}",          COLOR_TEXT_PRIMARY),
                    (" MB",                            COLOR_TEXT_SECONDARY),
                    _dot(),
                    (f"{cs2['cpu_percent']:.1f}%",    COLOR_TEXT_PRIMARY),
                    (" CPU",                           COLOR_TEXT_SECONDARY),
                ])
            else:
                _set_chips("_sysmon_cs2_frame", [
                    ("Not running", _RAM_COLOR_RED),
                ])

            slf = ProcessMonitor.get_self_stats()
            if slf:
                _set_chips("_sysmon_self_frame", [
                    (f"{slf['mem_mb']:.0f}",          COLOR_TEXT_PRIMARY),
                    (" MB",                            COLOR_TEXT_SECONDARY),
                    _dot(),
                    (f"{slf['cpu_percent']:.1f}%",    COLOR_TEXT_PRIMARY),
                    (" CPU",                           COLOR_TEXT_SECONDARY),
                ])
            else:
                _set_chips("_sysmon_self_frame", [("—", COLOR_TEXT_SECONDARY)])

            ram = ProcessMonitor.get_system_ram()
            if ram:
                pct = ram["percent"]
                pct_color = (
                    _RAM_COLOR_RED   if pct >= 85 else
                    _RAM_COLOR_AMBER if pct >= 70 else
                    _RAM_COLOR_OK
                )
                _set_chips("_sysmon_ram_frame", [
                    (f"{ram['used_gb']:.1f}",          COLOR_TEXT_PRIMARY),
                    (f" / {ram['total_gb']:.1f} GB",   COLOR_TEXT_SECONDARY),
                    _dot(),
                    (f"{pct:.0f}%",                    pct_color),
                ])
            else:
                _set_chips("_sysmon_ram_frame", [("—", COLOR_TEXT_SECONDARY)])

        if main_window.root.winfo_exists():
            main_window._process_monitor_timer = main_window.root.after(5000, _poll)

    # Deferred so the first poll runs after __init__ sets current_view.
    main_window._process_monitor_timer = main_window.root.after(5000, _poll)


def _stat_banner_item(parent, title, value, color, icon_file=None):
    item = ctk.CTkFrame(parent, fg_color="transparent")
    
    if icon_file:
        icon_label(item, icon_file, size=(18, 18), padx=(0, 8))
        
    ctk.CTkLabel(item, text=f"{title}:", font=FONT_ITEM_LABEL,
                 text_color=COLOR_TEXT_SECONDARY).pack(side="left", padx=(0, 6))
                 
    val_label = ctk.CTkLabel(item, text=value, font=FONT_WIDGET, text_color=color)
    val_label.pack(side="left")
    
    return item, val_label

def _check_offsets_staleness(main_window):
    """
    Called (under _staleness_lock) after either date thread resolves its value.
    Does nothing until both datetimes are available.
    Recolours the Offsets card and appends a warning label when the patch date
    is strictly newer than the offsets commit date.
    """
    cs2_dt     = getattr(main_window, "_cs2_patch_dt", None)
    offsets_dt = getattr(main_window, "_offsets_dt", None)
    if cs2_dt is None or offsets_dt is None:
        return

    delta_days = (cs2_dt.date() - offsets_dt.date()).days

    if delta_days <= 0:
        color   = _COLOR_FRESH
        warning = None
    elif delta_days <= _STALENESS_AMBER_DAYS:
        color   = _COLOR_STALE_AMBER
        warning = f"\u26a0 May be outdated ({delta_days}d behind patch)"
    elif delta_days <= _STALENESS_RED_DAYS:
        color   = _COLOR_STALE_AMBER
        warning = f"\u26a0 Likely outdated ({delta_days}d behind patch)"
    else:
        color   = _COLOR_STALE_RED
        warning = f"\u2715 Stale \u2014 {delta_days}d behind last CS2 patch"

    def _apply():
        try:
            if not main_window.root.winfo_exists():
                return
            if hasattr(main_window, "update_value_label"):
                main_window.update_value_label.configure(text_color=color)
            if hasattr(main_window, "_offsets_warning_label"):
                if warning:
                    main_window._offsets_warning_label.configure(
                        text=warning, text_color=color)
                    main_window._offsets_warning_label.pack(side="left", padx=(8, 0))
                else:
                    main_window._offsets_warning_label.pack_forget()
        except Exception:
            pass

    main_window.ui_queue_put(_apply)


def fetch_last_update(main_window):
    """Fetch last offset commit date in a background thread."""
    stop_event = threading.Event()
    main_window._fetch_update_stop = stop_event

    def _run():
        max_retries = 3
        retry_delay = 5
        cache_file = Path(ConfigManager.CONFIG_DIRECTORY) / "last_update_cache.txt"

        def _update_ui(text, color):
            def _apply():
                try:
                    if main_window.root.winfo_exists() and hasattr(main_window, "update_value_label"):
                        main_window.update_value_label.configure(text=text, text_color=color)
                except Exception:
                    logger.exception("update_value_label update failed")
            main_window.ui_queue_put(_apply)

        def _load_cache():
            try:
                return cache_file.read_text().strip()
            except FileNotFoundError:
                return None

        def _save_cache(ts):
            try:
                cache_file.write_text(ts)
            except IOError as exc:
                logger.error("Failed to save update cache: %s", exc)

        cached = _load_cache()
        if cached:
            _update_ui(cached, "#22c55e")

        config = ConfigManager.load_config()
        source = config.get("General", {}).get("OffsetSource", "a2x")

        if source == "local":
            offsets_file = Path(config.get("General", {}).get("OffsetsFile", ""))
            if offsets_file.exists():
                mtime = datetime.fromtimestamp(offsets_file.stat().st_mtime)
                ts = mtime.strftime("%m/%d/%Y %H:%M")
                _save_cache(ts)
                _update_ui(ts, _COLOR_FRESH)
                with _staleness_lock:
                    main_window._offsets_dt = mtime
                    _check_offsets_staleness(main_window)
            else:
                _update_ui("No Local File", "#ef4444")
            return

        sources = Utility.load_offset_sources()
        if source not in sources:
            _update_ui("Unknown Source", "#ef4444")
            return

        repo = sources[source].get("repository", "a2x/cs2-dumper")
        github_token = config.get("GitHub", {}).get("AccessToken")
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "VioletWing-App",
        }
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        for attempt in range(max_retries):
            if stop_event.is_set():
                return
            try:
                resp = requests.get(
                    f"https://api.github.com/repos/{repo}/commits/main",
                    headers=headers, timeout=10)
                resp.raise_for_status()
                data = orjson.loads(resp.content)
                commit_dt = parse_date(data["commit"]["committer"]["date"])
                ts = commit_dt.strftime("%m/%d/%Y %H:%M")
                _save_cache(ts)
                _update_ui(ts, _COLOR_FRESH)
                with _staleness_lock:
                    main_window._offsets_dt = commit_dt
                    _check_offsets_staleness(main_window)
                return
            except requests.exceptions.HTTPError as exc:
                if exc.response.status_code == 403 and attempt < max_retries - 1:
                    for _ in range(retry_delay * 10):
                        if stop_event.is_set():
                            return
                        time.sleep(0.1)
                    continue
                _update_ui("Rate Limit" if getattr(exc.response, "status_code", 0) == 403
                           else "Error", "#ef4444")
                return
            except Exception as exc:
                logger.error("Failed to fetch last update: %s", exc)
                if attempt < max_retries - 1:
                    for _ in range(retry_delay * 10):
                        if stop_event.is_set():
                            return
                        time.sleep(0.1)
                    continue
                _update_ui("Error", "#ef4444")

    threading.Thread(target=_run, daemon=True).start()

def fetch_cs2_latest_patch(main_window):
    """Fetch latest CS2 patch date from Steam API in a background thread."""
    stop_event = threading.Event()
    main_window._fetch_patch_stop = stop_event

    def _run():
        max_retries = 3
        retry_delay = 5
        cache_file = Path(ConfigManager.CONFIG_DIRECTORY) / "cs2_patch_cache.txt"

        def _update_ui(text, color):
            def _apply():
                try:
                    if main_window.root.winfo_exists() and hasattr(main_window, "cs2_patch_label"):
                        main_window.cs2_patch_label.configure(text=text, text_color=color)
                except Exception:
                    logger.exception("cs2_patch_label update failed")
            main_window.ui_queue_put(_apply)

        cached = cache_file.read_text().strip() if cache_file.exists() else None
        if cached:
            _update_ui(cached, "#22c55e")

        url = ("https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/"
               "?appid=730&count=1&maxlength=1&format=json")

        for attempt in range(max_retries):
            if stop_event.is_set():
                return
            try:
                resp = requests.get(url, headers={"User-Agent": "VioletWing-App"}, timeout=10)
                resp.raise_for_status()
                data = orjson.loads(resp.content)
                items = data.get("appnews", {}).get("newsitems", [])
                if not items:
                    raise ValueError("No news items in Steam API response")
                patch_dt = datetime.fromtimestamp(items[0]["date"])
                date_str = patch_dt.strftime("%m/%d/%Y")
                cache_file.write_text(date_str)
                _update_ui(date_str, _COLOR_FRESH)
                with _staleness_lock:
                    main_window._cs2_patch_dt = patch_dt
                    _check_offsets_staleness(main_window)
                return
            except Exception as exc:
                logger.error("Failed to fetch CS2 patch date: %s", exc)
                if attempt < max_retries - 1:
                    for _ in range(retry_delay * 10):
                        if stop_event.is_set():
                            return
                        time.sleep(0.1)
                    continue
                _update_ui("Error", "#ef4444")

    threading.Thread(target=_run, daemon=True).start()