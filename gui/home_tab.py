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
from dateutil.parser import parse as parse_date
from gui.theme import (
    FONT_TITLE, FONT_SUBTITLE, FONT_SECTION_TITLE, FONT_SECTION_DESCRIPTION,
    FONT_ITEM_LABEL, FONT_ITEM_DESCRIPTION, FONT_WIDGET,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_ACCENT_FG,
    SECTION_STYLE, BUTTON_STYLE_PRIMARY, BUTTON_STYLE_DANGER,
)

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

    stats_frame = ctk.CTkFrame(dashboard, fg_color="transparent")
    stats_frame.pack(fill="x", pady=(0, 40))
    for col in range(3):
        stats_frame.grid_columnconfigure(col, weight=1)

    cs2_card, main_window.cs2_patch_label = _stat_card(
        main_window, stats_frame, "CS2 Update", "Checking...", "#6b7280",
        "Latest Counter-Strike 2 patch", "crosshairs_icon.png")
    cs2_card.grid(row=0, column=0, sticky="ew", padx=(0, 10))

    upd_card, main_window.update_value_label = _stat_card(
        main_window, stats_frame, "Offsets Update", "Checking...", "#6b7280",
        "Last offsets synchronisation", "rotate_icon.png")
    upd_card.grid(row=0, column=1, sticky="ew", padx=(10, 10))

    ver_card, _ = _stat_card(
        main_window, stats_frame, "Version", ConfigManager.VERSION, "#8e44ad",
        "Current application version", "box_archive_icon.png")
    ver_card.grid(row=0, column=2, sticky="ew", padx=(10, 0))

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

    # Quick-start guide
    guide = ctk.CTkFrame(dashboard, **SECTION_STYLE)
    guide.pack(fill="x")
    gh = ctk.CTkFrame(guide, fg_color="transparent")
    gh.pack(fill="x", padx=40, pady=(40, 30))
    icon_label(gh, "rocket_icon.png", size=(22, 22), padx=(0, 10))
    ctk.CTkLabel(gh, text="Quick Start Guide", font=FONT_SECTION_TITLE,
                 text_color=COLOR_TEXT_PRIMARY).pack(side="left")
    ctk.CTkLabel(gh, text="Follow these steps to get started",
                 font=FONT_SECTION_DESCRIPTION, text_color=COLOR_TEXT_SECONDARY).pack(side="right")

    steps = [
        ("1", "Launch CS2",          "Open Counter-Strike 2 and ensure it's running"),
        ("2", "Configure Features",  "Enable TriggerBot, Overlay (ESP), Bunnyhop, or NoFlash"),
        ("3", "Adjust Settings",     "Customise trigger keys, delays, colours, and preferences"),
        ("4", "Start VioletWing",    "Click the Start Client button to activate your assistant"),
        ("5", "Monitor Status",      "Check Dashboard status and Logs tab for real-time updates"),
    ]
    for i, (num, title, desc) in enumerate(steps):
        sf = ctk.CTkFrame(guide, fg_color="transparent")
        sf.pack(fill="x", padx=40, pady=(0, 25 if i < len(steps) - 1 else 40))
        badge = ctk.CTkFrame(sf, width=50, height=50, corner_radius=25, fg_color=COLOR_ACCENT_FG)
        badge.pack(side="left", padx=(0, 25))
        badge.pack_propagate(False)
        ctk.CTkLabel(badge, text=num, font=FONT_WIDGET, text_color="#ffffff").place(
            relx=0.5, rely=0.5, anchor="center")
        sc = ctk.CTkFrame(sf, fg_color="transparent")
        sc.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(sc, text=title, font=FONT_ITEM_LABEL,
                     text_color=COLOR_TEXT_PRIMARY, anchor="w").pack(fill="x")
        ctk.CTkLabel(sc, text=desc, font=FONT_ITEM_DESCRIPTION,
                     text_color=COLOR_TEXT_SECONDARY, anchor="w").pack(fill="x", pady=(4, 0))
        if i < len(steps) - 1:
            ctk.CTkFrame(guide, width=2, height=20,
                         fg_color=("#c4b5fd", "#2a1d4e")).pack(padx=(65, 0), anchor="w")

    fetch_last_update(main_window)
    fetch_cs2_latest_patch(main_window)

def _stat_card(main_window, parent, title, value, color, subtitle, icon_file=None):
    card = ctk.CTkFrame(parent, corner_radius=20, fg_color=("#f5f3ff", "#0d0a1a"),
                        border_width=1, border_color=("#c4b5fd", "#2a1d4e"))
    content = ctk.CTkFrame(card, fg_color="transparent")
    content.pack(fill="both", expand=True, padx=30, pady=30)

    hr = ctk.CTkFrame(content, fg_color="transparent")
    hr.pack(fill="x", pady=(0, 15))
    if icon_file:
        icon_label(hr, icon_file, size=(18, 18), padx=(0, 8))
    ctk.CTkLabel(hr, text=title, font=FONT_ITEM_LABEL,
                 text_color=COLOR_TEXT_SECONDARY, anchor="w").pack(side="left", fill="x", expand=True)

    val_label = ctk.CTkLabel(content, text=value, font=FONT_SECTION_TITLE,
                             text_color=color, anchor="w")
    val_label.pack(fill="x", pady=(0, 10))
    ctk.CTkLabel(content, text=subtitle, font=FONT_ITEM_DESCRIPTION,
                 text_color=COLOR_TEXT_SECONDARY, anchor="w").pack(fill="x")
    return card, val_label

def fetch_last_update(main_window):
    """Fetch last offset commit date in a background thread."""
    stop_event = threading.Event()
    main_window._fetch_update_stop = stop_event

    def _run():
        max_retries = 3
        retry_delay = 5
        cache_file = Path(ConfigManager.CONFIG_DIRECTORY) / "last_update_cache.txt"

        def _update_ui(text, color):
            try:
                if main_window.root.winfo_exists() and hasattr(main_window, "update_value_label"):
                    main_window.root.after(
                        0, lambda: main_window.update_value_label.configure(
                            text=text, text_color=color))
            except Exception:
                pass

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
                _update_ui(ts, "#22c55e")
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
                ts = parse_date(data["commit"]["committer"]["date"]).strftime("%m/%d/%Y %H:%M")
                _save_cache(ts)
                _update_ui(ts, "#22c55e")
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
            try:
                if main_window.root.winfo_exists() and hasattr(main_window, "cs2_patch_label"):
                    main_window.root.after(
                        0, lambda: main_window.cs2_patch_label.configure(
                            text=text, text_color=color))
            except Exception:
                pass

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
                date_str = datetime.fromtimestamp(items[0]["date"]).strftime("%m/%d/%Y")
                cache_file.write_text(date_str)
                _update_ui(date_str, "#22c55e")
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