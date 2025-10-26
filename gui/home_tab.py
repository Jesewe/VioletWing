import customtkinter as ctk
import threading
import orjson
import requests
import time
from datetime import datetime
from pathlib import Path
from classes.logger import Logger
from classes.utility import Utility
from classes.config_manager import ConfigManager
from dateutil.parser import parse as parse_date
from gui.theme import (
    FONT_TITLE, FONT_SUBTITLE, FONT_SECTION_TITLE, FONT_SECTION_DESCRIPTION,
    FONT_ITEM_LABEL, FONT_ITEM_DESCRIPTION, FONT_WIDGET,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_ACCENT_FG,
    SECTION_STYLE, BUTTON_STYLE_PRIMARY, BUTTON_STYLE_DANGER
)

# Cache the logger instance
logger = Logger.get_logger()

def populate_dashboard(main_window, frame):
    """Populate the dashboard frame with status cards, controls, and a quick start guide."""
    # Scrollable container for dashboard content
    dashboard = ctk.CTkScrollableFrame(
        frame,
        fg_color="transparent"
    )
    dashboard.pack(fill="both", expand=True, padx=40, pady=40)
    
    # Frame for page title and subtitle
    title_frame = ctk.CTkFrame(dashboard, fg_color="transparent")
    title_frame.pack(fill="x", pady=(0, 30))
    
    # Dashboard title with icon
    title_label = ctk.CTkLabel(
        title_frame,
        text="🎯 Dashboard",
        font=FONT_TITLE,
        text_color=COLOR_TEXT_PRIMARY
    )
    title_label.pack(side="left")
    
    # Subtitle providing context
    subtitle_label = ctk.CTkLabel(
        title_frame,
        text="Monitor and control your CS2 client",
        font=FONT_SUBTITLE,
        text_color=COLOR_TEXT_SECONDARY
    )
    subtitle_label.pack(side="left", padx=(20, 0), pady=(10, 0))
    
    # Frame for status cards - using grid layout for better responsiveness (now 3 columns)
    stats_frame = ctk.CTkFrame(dashboard, fg_color="transparent")
    stats_frame.pack(fill="x", pady=(0, 40))
    
    # Configure grid columns to be equal width (reduced to 3 columns)
    stats_frame.grid_columnconfigure(0, weight=1)
    stats_frame.grid_columnconfigure(1, weight=1)
    stats_frame.grid_columnconfigure(2, weight=1)
    
    # CS2 latest patch card - moved to first position
    cs2_patch_card, main_window.cs2_patch_label = create_stat_card(
        main_window,
        stats_frame,
        "🔔 CS2 Update",
        "Checking...",
        "#6b7280",
        "Latest Counter-Strike 2 patch"
    )
    cs2_patch_card.grid(row=0, column=0, sticky="ew", padx=(0, 10))

    # Last update card with stored label reference - moved to second position
    update_card, main_window.update_value_label = create_stat_card(
        main_window,
        stats_frame,
        "🔄 Offsets Update",
        "Checking...",
        "#6b7280",
        "Last offsets synchronization"
    )
    update_card.grid(row=0, column=1, sticky="ew", padx=(10, 10))

    # Version card - moved to third position
    version_card, version_value_label = create_stat_card(
        main_window,
        stats_frame,
        "📦 Version",
        f"{ConfigManager.VERSION}",
        "#D5006D",
        "Current application version"
    )
    version_card.grid(row=0, column=2, sticky="ew", padx=(10, 0))
    
    # Control panel section
    control_panel = ctk.CTkFrame(dashboard, **SECTION_STYLE)
    control_panel.pack(fill="x", pady=(0, 40))
    
    # Header for control panel
    control_header = ctk.CTkFrame(control_panel, fg_color="transparent")
    control_header.pack(fill="x", padx=40, pady=(40, 30))
    
    # Control center title
    ctk.CTkLabel(
        control_header,
        text="🎮 Control Center",
        font=FONT_SECTION_TITLE,
        text_color=COLOR_TEXT_PRIMARY
    ).pack(side="left")
    
    # Frame for control buttons
    control_buttons = ctk.CTkFrame(control_panel, fg_color="transparent")
    control_buttons.pack(fill="x", padx=40, pady=(0, 40))
    
    # Start button with play icon
    start_button = ctk.CTkButton(
        control_buttons,
        text="▶  Start Client",
        command=main_window.start_client,
        width=180,
        **BUTTON_STYLE_PRIMARY
    )
    start_button.pack(side="left", padx=(0, 20))
    
    # Stop button with stop icon
    stop_button = ctk.CTkButton(
        control_buttons,
        text="⏹  Stop Client",
        command=main_window.stop_client,
        width=180,
        **BUTTON_STYLE_DANGER
    )
    stop_button.pack(side="left")
    
    # Quick start guide section
    guide_card = ctk.CTkFrame(dashboard, **SECTION_STYLE)
    guide_card.pack(fill="x")
    
    # Header for quick start guide
    guide_header = ctk.CTkFrame(guide_card, fg_color="transparent")
    guide_header.pack(fill="x", padx=40, pady=(40, 30))
    
    # Guide title with icon
    ctk.CTkLabel(
        guide_header,
        text="🚀 Quick Start Guide",
        font=FONT_SECTION_TITLE,
        text_color=COLOR_TEXT_PRIMARY
    ).pack(side="left")
    
    # Guide subtitle
    ctk.CTkLabel(
        guide_header,
        text="Follow these steps to get started",
        font=FONT_SECTION_DESCRIPTION,
        text_color=COLOR_TEXT_SECONDARY
    ).pack(side="right")
    
    # List of guide steps
    steps = [
        ("1", "Launch CS2", "Open Counter-Strike 2 and ensure it's running"),
        ("2", "Configure Features", "Enable TriggerBot, Overlay (ESP), Bunnyhop, or NoFlash"),
        ("3", "Adjust Settings", "Customize trigger keys, delays, colors, and other preferences"),
        ("4", "Start VioletWing", "Click the Start Client button to activate your assistant"),
        ("5", "Monitor Status", "Check Dashboard status and Logs tab for real-time updates")
    ]
    
    # Create each step
    for i, (step_num, step_title, step_desc) in enumerate(steps):
        # Frame for the step
        step_frame = ctk.CTkFrame(guide_card, fg_color="transparent")
        step_frame.pack(fill="x", padx=40, pady=(0, 25 if i < len(steps)-1 else 40))
        
        # Step number badge
        step_badge = ctk.CTkFrame(
            step_frame,
            width=50,
            height=50,
            corner_radius=25,
            fg_color=COLOR_ACCENT_FG
        )
        step_badge.pack(side="left", padx=(0, 25))
        step_badge.pack_propagate(False)
        
        # Step number inside badge
        ctk.CTkLabel(
            step_badge,
            text=step_num,
            font=FONT_WIDGET,
            text_color="#ffffff"
        ).place(relx=0.5, rely=0.5, anchor="center")
        
        # Frame for step content
        step_content = ctk.CTkFrame(step_frame, fg_color="transparent")
        step_content.pack(side="left", fill="x", expand=True)
        
        # Step title
        ctk.CTkLabel(
            step_content,
            text=step_title,
            font=FONT_ITEM_LABEL,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w"
        ).pack(fill="x")
        
        # Step description
        ctk.CTkLabel(
            step_content,
            text=step_desc,
            font=FONT_ITEM_DESCRIPTION,
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w"
        ).pack(fill="x", pady=(4, 0))
        
        # Connector line between steps (except last)
        if i < len(steps) - 1:
            connector = ctk.CTkFrame(
                guide_card,
                width=2,
                height=20,
                fg_color=("#e2e8f0", "#374151")
            )
            connector.pack(padx=(65, 0), anchor="w")
    
    # Fetch last offset update and CS2 patch
    fetch_last_update(main_window)
    fetch_cs2_latest_patch(main_window)

def create_stat_card(main_window, parent, title, value, color, subtitle):
    """Create a modern stat card and return the card and value label."""
    # Card frame with enhanced modern styling
    card = ctk.CTkFrame(
        parent,
        corner_radius=25,
        fg_color=("#ffffff", "#1a1b23"),
        border_width=3,
        border_color=("#e2e8f0", "#2d3748")
    )
    
    # Content frame within card with more padding
    content = ctk.CTkFrame(card, fg_color="transparent")
    content.pack(fill="both", expand=True, padx=30, pady=30)
    
    # Card header with improved styling
    ctk.CTkLabel(
        content,
        text=title,
        font=FONT_ITEM_LABEL,
        text_color=COLOR_TEXT_SECONDARY,
        anchor="w"
    ).pack(fill="x", pady=(0, 15))
    
    # Value label with enhanced font and dynamic color
    value_label = ctk.CTkLabel(
        content,
        text=value,
        font=FONT_SECTION_TITLE,
        text_color=color,
        anchor="w"
    )
    value_label.pack(fill="x", pady=(0, 10))
    
    # Subtitle providing context with improved styling
    ctk.CTkLabel(
        content,
        text=subtitle,
        font=FONT_ITEM_DESCRIPTION,
        text_color=COLOR_TEXT_SECONDARY,
        anchor="w"
    ).pack(fill="x")
    
    return card, value_label

def fetch_last_update(main_window):
    """Fetch and display the last offset update time with retry, caching, and authentication."""
    def update_callback():
        max_retries = 3
        retry_delay = 5  # seconds
        cache_file = Path(ConfigManager.CONFIG_DIRECTORY) / "last_update_cache.txt"

        def load_cached_timestamp():
            try:
                with open(cache_file, 'r') as f:
                    return f.read().strip()
            except FileNotFoundError:
                return None

        def save_cached_timestamp(timestamp):
            try:
                with open(cache_file, 'w') as f:
                    f.write(timestamp)
            except IOError as e:
                logger.error("Failed to save cached timestamp: %s", e)

        def update_ui(text, color):
            # Schedule UI update in the main thread
            try:
                main_window.root.after(0, lambda: (
                    main_window.update_value_label.configure(text=text, text_color=color)
                    if main_window.root.winfo_exists() and hasattr(main_window, 'update_value_label')
                    else None
                ))
            except Exception as e:
                pass

        # Try loading cached timestamp first
        cached_timestamp = load_cached_timestamp()
        if cached_timestamp:
            logger.debug("Using cached timestamp: %s", cached_timestamp)
            update_ui(cached_timestamp, "#22c55e")

        # Load config to check for GitHub token
        config = ConfigManager.load_config()
        github_token = config.get("GitHub", {}).get("AccessToken", None)

        # Set up headers for GitHub API
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "VioletWing-App"
        }
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        for attempt in range(max_retries):
            try:
                response = requests.get(
                    "https://api.github.com/repos/a2x/cs2-dumper/commits/main",
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                commit_data = orjson.loads(response.content)
                commit_timestamp = commit_data["commit"]["committer"]["date"]

                # Parse and format the timestamp
                last_update_dt = parse_date(commit_timestamp)
                formatted_timestamp = last_update_dt.strftime("%m/%d/%Y %H:%M")

                # Cache the timestamp
                save_cached_timestamp(formatted_timestamp)

                # Update UI
                update_ui(formatted_timestamp, "#22c55e")
                logger.debug("Successfully fetched last update: %s", formatted_timestamp)
                return

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    logger.warning("GitHub API rate limit exceeded. Attempt %d/%d", attempt + 1, max_retries)
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error("Max retries reached for GitHub API rate limit.")
                        update_ui("Rate Limit Exceeded", "#ef4444")
                        return
                else:
                    logger.error("HTTP error fetching last update: %s", e)
                    update_ui("Error", "#ef4444")
                    return
            except Exception as e:
                logger.error("Failed to fetch last update: %s", e)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                update_ui("Error", "#ef4444")
                return

    # Run fetch in a separate thread
    threading.Thread(target=update_callback, daemon=True).start()

def fetch_cs2_latest_patch(main_window):
    """Fetch and display the latest Counter-Strike 2 patch date from Steam Web API."""
    def patch_callback():
        max_retries = 3
        retry_delay = 5  # seconds
        cache_file = Path(ConfigManager.CONFIG_DIRECTORY) / "cs2_patch_cache.txt"

        def load_cached_patch():
            try:
                with open(cache_file, 'r') as f:
                    return f.read().strip()
            except FileNotFoundError:
                return None

        def save_cached_patch(patch_date):
            try:
                with open(cache_file, 'w') as f:
                    f.write(patch_date)
            except IOError as e:
                logger.error("Failed to save cached patch date: %s", e)

        def update_ui(text, color):
            # Schedule UI update in the main thread
            try:
                main_window.root.after(0, lambda: (
                    main_window.cs2_patch_label.configure(text=text, text_color=color)
                    if main_window.root.winfo_exists() and hasattr(main_window, 'cs2_patch_label')
                    else None
                ))
            except Exception as e:
                pass

        # Try loading cached patch date first
        cached_patch = load_cached_patch()
        if cached_patch:
            logger.debug("Using cached CS2 patch date: %s", cached_patch)
            update_ui(cached_patch, "#22c55e")

        # Headers for Steam API request (minimal, as it's public)
        headers = {
            "User-Agent": "VioletWing-App"
        }

        for attempt in range(max_retries):
            try:
                response = requests.get(
                    "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=730&count=1&maxlength=1&format=json",
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                
                # Parse JSON response
                data = orjson.loads(response.content)
                
                if 'appnews' in data and 'newsitems' in data['appnews'] and data['appnews']['newsitems']:
                    news_item = data['appnews']['newsitems'][0]
                    timestamp = news_item['date']
                    
                    # Convert Unix timestamp to datetime
                    patch_date = datetime.fromtimestamp(timestamp)
                    formatted_date = patch_date.strftime("%m/%d/%Y")

                    # Cache the patch date
                    save_cached_patch(formatted_date)

                    # Update UI
                    update_ui(formatted_date, "#22c55e")
                    logger.debug("Successfully fetched CS2 patch date: %s", formatted_date)
                    return
                else:
                    raise ValueError("No news items found in Steam API response")

            except requests.exceptions.HTTPError as e:
                logger.error("HTTP error fetching CS2 patch: %s", e)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                update_ui("Error", "#ef4444")
                return
            except Exception as e:
                logger.error("Failed to fetch CS2 patch: %s", e)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                update_ui("Error", "#ef4444")
                return

    # Run fetch in a separate thread
    threading.Thread(target=patch_callback, daemon=True).start()

def update_client_status(self, status, color):
    """Update the client status indicators across the dashboard."""
    # Update header status label
    self.status_label.configure(text=status, text_color=color)

    # Update status dot color in header
    for widget in self.status_frame.winfo_children():
        if isinstance(widget, ctk.CTkFrame) and widget.cget("width") == 12:
            widget.configure(fg_color=color)
            break