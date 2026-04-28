import os
import copy
import threading
import time
import webbrowser
import subprocess
import platform
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk
import requests
import sys

from watchdog.observers import Observer

from classes.updater import Updater
from classes.utility import Utility
from classes.trigger_bot import CS2TriggerBot
from classes.esp import CS2Overlay
from classes.bunnyhop import CS2Bunnyhop
from classes.noflash import CS2NoFlash
from classes.config_manager import ConfigManager, COLOR_CHOICES
from classes.file_watcher import ConfigFileChangeHandler
from classes.logger import Logger
from classes.memory_manager import MemoryManager
from classes.client_manager import ClientManager

from gui.ui_config_bridge import UIConfigBridge
from gui.home_tab import populate_dashboard
from gui.general_settings_tab import populate_general_settings
from gui.trigger_settings_tab import populate_trigger_settings
from gui.overlay_settings_tab import populate_overlay_settings
from gui.additional_settings_tab import populate_additional_settings
from gui.logs_tab import populate_logs
from gui.faq_tab import populate_faq
from gui.notifications_tab import populate_notifications
from gui.supporters_tab import populate_supporters
from gui.theme import (FONT_FAMILY_BOLD, FONT_FAMILY_REGULAR, FONT_SIZE_H2, FONT_SIZE_H4, FONT_SIZE_P,
                         COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_BACKGROUND, COLOR_WIDGET_BACKGROUND,
                         COLOR_ACCENT_FG, COLOR_HEADER_BG, COLOR_SIDEBAR_BG, COLOR_SIDEBAR_ACTIVE_BG,
                         COLOR_SIDEBAR_INDICATOR, COLOR_VIOLET_SUBTLE, COLOR_VIOLET,
                         BUTTON_STYLE_PRIMARY, BUTTON_STYLE_DANGER)

# Get a logger instance for this module
logger = Logger.get_logger(__name__)

class MainWindow:
    def __init__(self):
        """Initialize the main application window and setup UI components."""
        # Define repository URL for reference
        self.repo_url = "github.com/Jesewe/VioletWing"
        # Initialize threads, observer, and log timer as None until set up
        self.trigger_thread = None
        self.overlay_thread = None
        self.bunnyhop_thread = None
        self.noflash_thread = None
        self.observer = None
        self.log_timer = None
        self._log_file_pos = 0  # track read position so we only read new bytes each poll

        # Configure CustomTkinter with a modern dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Create the main window first to avoid a phantom Tk root window
        self.root = ctk.CTk()

        # Offsets are fetched in a background thread so the window can render
        # immediately. Features and the client manager are initialized once loading
        # completes via _on_offsets_ready().
        self.offsets, self.client_data, self.buttons_data = {}, {}, {}
        self.memory_manager = MemoryManager(self.offsets, self.client_data, self.buttons_data)
        self.initialize_features()
        self.ui_bridge = UIConfigBridge()
        self.root.title(f"VioletWing")
        self.root.resizable(True, True)
        self.root.minsize(1400, 800)

        # Center the window on the screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1400 // 2)
        y = (self.root.winfo_screenheight() // 2) - (800 // 2)
        self.root.geometry(f"1400x800+{x}+{y}")
        
        # Set the window icon using a resource path utility
        self.root.iconbitmap(Utility.resource_path('src/img/icon.ico'))
        
        # Load custom fonts on Windows systems
        if platform.system() == "Windows":
            import ctypes
            gdi32 = ctypes.WinDLL('gdi32')
            font_files = [
                'src/fonts/Outfit-Regular.ttf',
                'src/fonts/Outfit-Bold.ttf',
                'src/fonts/JetBrainsMono-Regular.ttf',
                'src/fonts/JetBrainsMono-Bold.ttf'
            ]
            for font_file in font_files:
                font_path = Utility.resource_path(font_file)
                if os.path.exists(font_path):
                    gdi32.AddFontResourceW(font_path)
                else:
                    logger.warning(f"Font file not found: {font_path}")
        
        # Configure grid layout to make the UI responsive
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)
        
        # Initialize the updater
        self.updater = Updater(self)
        
        # Initialize UI components like header and content
        self.setup_ui()
        
        # Set up configuration file watcher and log update timer
        self.init_config_watcher()
        self.start_log_timer()
        
        # Bind window close event to cleanup resources
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Initialize the client manager
        self.client_manager = ClientManager(self)

        # Kick off offset loading - window is already visible at this point
        self.fetch_offsets_async()

    def initialize_features(self):
        """Initialize all feature instances and create a centralized feature registry."""
        try:
            self.triggerbot = CS2TriggerBot(self.memory_manager)
            self.overlay = CS2Overlay(self.memory_manager)
            self.bunnyhop = CS2Bunnyhop(self.memory_manager)
            self.noflash = CS2NoFlash(self.memory_manager)

            self.features = {
                "Trigger": {"name": "TriggerBot", "instance": self.triggerbot, "class": CS2TriggerBot},
                "Overlay": {"name": "Overlay", "instance": self.overlay, "class": CS2Overlay},
                "Bunnyhop": {"name": "Bunnyhop", "instance": self.bunnyhop, "class": CS2Bunnyhop},
                "Noflash": {"name": "Noflash", "instance": self.noflash, "class": CS2NoFlash},
            }
            logger.info("All features initialized successfully.")
        except Exception:
            logger.exception("Failed to initialize features.")
            messagebox.showerror("Initialization Error", "Failed to initialize features. Check logs for details.")

    def setup_ui(self):
        """Setup the modern user interface components."""
        # Create a modern header with branding and controls
        self.create_modern_header()
        
        # Create the main content area including sidebar navigation
        self.create_main_content()

    def create_modern_header(self):
        """Create a sleek modern header with gradient-like appearance."""
        header_container = ctk.CTkFrame(self.root, height=80, corner_radius=0, fg_color=COLOR_HEADER_BG)
        header_container.grid(row=0, column=0, sticky="ew")
        header_container.grid_propagate(False)
        header_container.grid_columnconfigure(1, weight=1)

        self.create_header_left(header_container)
        self.create_header_right(header_container)

    def create_header_left(self, parent):
        """Create the left side of the header with title and version badge."""
        left_frame = ctk.CTkFrame(parent, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="w", padx=30, pady=15)
        
        # Title container
        title_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        title_frame.pack(side="left")
        
        # Title name
        ctk.CTkLabel(
            title_frame, 
            text="Violet", 
            font=(FONT_FAMILY_BOLD[0], FONT_SIZE_H2, "bold"), 
            text_color="#a78bfa"
        ).pack(side="left")
        
        ctk.CTkLabel(
            title_frame, 
            text="Wing", 
            font=(FONT_FAMILY_BOLD[0], FONT_SIZE_H2, "bold"), 
            text_color="#f0ebff"
        ).pack(side="left", padx=(5, 0))
        
        # Version badge
        version_badge = ctk.CTkFrame(
            left_frame,
            fg_color=COLOR_VIOLET_SUBTLE,
            corner_radius=8,
            height=26
        )
        version_badge.pack(side="left", padx=(15, 0))
        
        ctk.CTkLabel(
            version_badge,
            text=f"{ConfigManager.VERSION}",
            font=(FONT_FAMILY_BOLD[0], 12, "bold"),
            text_color="#a78bfa",
            padx=10,
            pady=3
        ).pack()

    def create_header_right(self, parent):
        """Create the right side of the header with status, social buttons, and update button."""
        right_frame = ctk.CTkFrame(parent, fg_color="transparent")
        right_frame.grid(row=0, column=2, sticky="e", padx=30, pady=15)
        
        self.create_status_indicator(right_frame)
        social_frame = self.create_social_buttons(right_frame)
        self.create_update_button(social_frame)

    def create_status_indicator(self, parent):
        """Create the status indicator widget."""
        self.status_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.status_frame.pack(side="right", padx=(20, 0))
        
        self.status_dot = ctk.CTkFrame(self.status_frame, width=12, height=12, corner_radius=6, fg_color="#ef4444")
        self.status_dot.pack(side="left", pady=(0, 2))
        self.status_label = ctk.CTkLabel(self.status_frame, text="Inactive", font=(FONT_FAMILY_BOLD[0], FONT_SIZE_H4, "bold"), text_color=BUTTON_STYLE_DANGER["fg_color"][0])
        self.status_label.pack(side="left", padx=(8, 0))

    def create_social_buttons(self, parent):
        """Create and pack the social media buttons in a unified ghost style."""
        social_frame = ctk.CTkFrame(parent, fg_color="transparent")
        social_frame.pack(side="right")

        social_buttons_data = [
            {"text": "GitHub",        "icon_file": "github_icon.png",    "url": "https://github.com/Jesewe/VioletWing"},
            {"text": "Telegram",      "icon_file": "telegram_icon.png",  "url": "https://t.me/cs2_jesewe"},
            {"text": "Documentation", "icon_file": "readme_icon.png",    "url": "https://violetwing.vercel.app/"},
        ]

        for i, data in enumerate(social_buttons_data):
            try:
                image = Image.open(Utility.resource_path(f'src/img/{data["icon_file"]}'))
                ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=(18, 18))
            except FileNotFoundError:
                ctk_image = None

            btn = ctk.CTkButton(
                social_frame,
                text=data["text"],
                image=ctk_image,
                compound="left",
                command=lambda u=data["url"]: webbrowser.open(u),
                height=36,
                corner_radius=10,
                fg_color="transparent",
                hover_color=COLOR_SIDEBAR_ACTIVE_BG,
                border_width=1,
                border_color=("#c4b5fd", "#3d2a6e"),
                text_color=("#7c3aed", "#a78bfa"),
                font=(FONT_FAMILY_BOLD[0], FONT_SIZE_P, "bold"),
            )
            btn.pack(side="left", padx=(0, 8) if i < len(social_buttons_data) - 1 else (0, 0))

        return social_frame

    def create_update_button(self, parent):
        """Create the update button if an update is available."""
        try:
            image = Image.open(Utility.resource_path('src/img/update_icon.png'))
            ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=(18, 18))
        except FileNotFoundError:
            ctk_image = None

        if self.updater.check_for_updates():
            is_pre = self.updater.is_prerelease
            update_btn = ctk.CTkButton(
                parent,
                text="Pre-release Available!" if is_pre else "Update Available!",
                image=ctk_image,
                compound="left",
                command=self.updater.handle_update,
                height=36,
                corner_radius=10,
                fg_color="#f59e0b" if is_pre else "#ef4444",
                hover_color="#d97706" if is_pre else "#dc2626",
                border_width=0,
                text_color="#ffffff",
                font=(FONT_FAMILY_BOLD[0], FONT_SIZE_P, "bold"),
            )
            update_btn.pack(side="left", padx=(8, 0))

    def create_main_content(self):
        """Create the main content area with a modern layout."""
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.grid(row=1, column=0, sticky="nsew")
        main_container.grid_columnconfigure(1, weight=1)
        main_container.grid_rowconfigure(0, weight=1)

        self.create_sidebar(main_container)

        self.content_frame = ctk.CTkFrame(main_container, corner_radius=0, fg_color=COLOR_BACKGROUND)
        self.content_frame.grid(row=0, column=1, sticky="nsew")

        self.tab_views = {
            "dashboard": self.populate_dashboard,
            "general_settings": self.populate_general_settings,
            "trigger_settings": self.populate_trigger_settings,
            "overlay_settings": self.populate_overlay_settings,
            "additional_settings": self.populate_additional_settings,
            "logs": self.populate_logs,
            "faq": self.populate_faq,
            "notifications": self.populate_notifications,
            "supporters": self.populate_supporters,
        }

        self.tab_frames = {}
        for key, populate_func in self.tab_views.items():
            frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            self.tab_frames[key] = frame
            populate_func(frame)

        self.current_view = None
        self.switch_view("dashboard")

    def create_sidebar(self, parent):
        """Create modern sidebar navigation."""
        sidebar = ctk.CTkFrame(parent, width=280, corner_radius=0, fg_color=COLOR_SIDEBAR_BG)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        self.nav_items = [
            ("Dashboard", "dashboard", "🏠"),
            ("General Settings", "general_settings", "⚙️"),
            ("Trigger Settings", "trigger_settings", "🔫"),
            ("Overlay Settings", "overlay_settings", "🌍"),
            ("Additional Settings", "additional_settings", "⚡"),
            ("Logs", "logs", "📋"),
            ("FAQ", "faq", "❓"),
            ("Notifications", "notifications", "🔔"),
            ("Supporters", "supporters", "🤝"),
        ]

        # Thin separator line between header and sidebar content area
        ctk.CTkFrame(sidebar, height=1, fg_color=("#c4b5fd", "#2a1d4e")).pack(fill="x")
        ctk.CTkFrame(sidebar, height=20, fg_color="transparent").pack(fill="x")

        self.nav_buttons = {}
        self.nav_indicators = {}

        for name, key, icon in self.nav_items:
            # Row wrapper holds the indicator bar + button side by side
            row = ctk.CTkFrame(sidebar, fg_color="transparent", height=50)
            row.pack(fill="x", padx=0, pady=(0, 4))
            row.pack_propagate(False)

            # 3px left indicator bar - hidden by default, shown when active
            indicator = ctk.CTkFrame(row, width=3, corner_radius=2, fg_color="transparent")
            indicator.pack(side="left", fill="y", padx=(8, 0))

            btn = ctk.CTkButton(
                row,
                text=f"{icon}  {name}",
                command=lambda k=key: self.switch_view(k),
                height=46,
                corner_radius=10,
                fg_color="transparent",
                hover_color=COLOR_SIDEBAR_ACTIVE_BG,
                text_color=COLOR_TEXT_SECONDARY,
                font=(FONT_FAMILY_BOLD[0], FONT_SIZE_H4),
                anchor="w",
            )
            btn.pack(side="left", fill="x", expand=True, padx=(6, 12))

            self.nav_buttons[key] = btn
            self.nav_indicators[key] = indicator

        self.set_active_nav("dashboard")

    def set_active_nav(self, active_key):
        """Set the active navigation button with indicator bar visual feedback."""
        for key, btn in self.nav_buttons.items():
            indicator = self.nav_indicators[key]
            if key == active_key:
                btn.configure(
                    fg_color=COLOR_SIDEBAR_ACTIVE_BG,
                    text_color=COLOR_TEXT_PRIMARY,
                )
                indicator.configure(fg_color=COLOR_SIDEBAR_INDICATOR)
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLOR_TEXT_SECONDARY,
                    hover_color=COLOR_SIDEBAR_ACTIVE_BG,
                )
                indicator.configure(fg_color="transparent")

    def switch_view(self, view_key):
        """Switch between different views by showing the appropriate frame."""
        if self.current_view == view_key:
            return

        if self.current_view and self.current_view in self.tab_frames:
            self.tab_frames[self.current_view].pack_forget()

        self.current_view = view_key
        self.set_active_nav(view_key)

        if view_key in self.tab_frames:
            self.tab_frames[view_key].pack(fill="both", expand=True)

    def populate_dashboard(self, frame):
        """Populate the dashboard frame with controls and stats."""
        populate_dashboard(self, frame)

    def populate_general_settings(self, frame):
        """Populate the general settings frame with configuration options."""
        populate_general_settings(self, frame)

    def populate_trigger_settings(self, frame):
        """Populate the trigger settings frame with configuration options."""
        populate_trigger_settings(self, frame)

    def populate_overlay_settings(self, frame):
        """Populate the overlay settings frame with configuration options."""
        populate_overlay_settings(self, frame)

    def populate_additional_settings(self, frame):
        """Populate the additional settings frame with configuration options for Bunnyhop and NoFlash."""
        populate_additional_settings(self, frame)

    def populate_logs(self, frame):
        """Populate the logs frame with log display."""
        populate_logs(self, frame)

    def populate_faq(self, frame):
        """Populate the FAQ frame with questions and answers."""
        populate_faq(self, frame)
    
    def populate_notifications(self, frame):
        """Populate the notifications frame with notification settings."""
        populate_notifications(self, frame)

    def populate_supporters(self, frame):
        """Populate the supporters frame with supporter data."""
        populate_supporters(self, frame)

    def fetch_offsets_async(self):
        """Fetch offsets in a background thread so the UI remains responsive."""
        def _worker():
            try:
                offsets, client_data, buttons_data = Utility.fetch_offsets()
                if offsets is None or client_data is None or buttons_data is None:
                    raise ValueError("Utility.fetch_offsets() returned None.")
                self.root.after(0, lambda: self._on_offsets_ready(offsets, client_data, buttons_data))
            except Exception:
                logger.exception("Failed to fetch offsets from the server.")
                self.root.after(0, self._on_offsets_failed)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_offsets_ready(self, offsets, client_data, buttons_data):
        """Called on the main thread once offsets have loaded successfully."""
        self.offsets = offsets
        self.client_data = client_data
        self.buttons_data = buttons_data
        self.memory_manager.offsets = offsets
        self.memory_manager.client_data = client_data
        self.memory_manager.buttons_data = buttons_data
        # Re-derive the offset attributes now that data is available
        if hasattr(self.memory_manager, '_apply_offsets'):
            self.memory_manager._apply_offsets()
        if hasattr(self, 'loading_label'):
            self.loading_label.destroy()
            del self.loading_label

    def _on_offsets_failed(self):
        """Called on the main thread when offset fetching fails."""
        messagebox.showerror("Offset Error", "Failed to fetch offsets. Check logs for details.")
        if hasattr(self, 'loading_label'):
            self.loading_label.configure(text="⚠ Failed to load offsets. Check logs.", text_color="#ef4444")

    def update_client_status(self, status, color):
        """Update client status in header and dashboard."""
        # Update header status label
        self.status_label.configure(text=status, text_color=color)
    
        # Update header status dot color
        self.status_dot.configure(fg_color=color)
        
        # Update dashboard status label if it exists
        if hasattr(self, 'bot_status_label'):
            self.bot_status_label.configure(text=status, text_color=color)

    def start_client(self):
        """Start selected features using the client manager."""
        self.client_manager.start_client()

    def stop_client(self):
        """Stop all running features using the client manager."""
        self.client_manager.stop_client()

    def update_weapon_settings_display(self):
        """Update weapon delay fields when weapon type selection changes."""
        weapon_type = self.ui_bridge.get_value("active_weapon_type")
        if weapon_type is None:
            return
        # Read from the live config cache so values reflect the latest save,
        # not the stale in-memory config that only updates when the bot runs.
        config = ConfigManager.load_config()
        settings = config["Trigger"]["WeaponSettings"].get(weapon_type, {})
        self.ui_bridge.set_value("ShotDelayMin", str(settings.get("ShotDelayMin", 0.01)))
        self.ui_bridge.set_value("ShotDelayMax", str(settings.get("ShotDelayMax", 0.03)))
        self.ui_bridge.set_value("PostShotDelay", str(settings.get("PostShotDelay", 0.1)))

    def save_settings(self, show_message=False):
        """Save the configuration settings and apply to relevant features in real-time."""
        try:
            self.validate_inputs()
            
            # Load the current configuration to ensure all parts are present
            config = ConfigManager.load_config()
            old_config = copy.deepcopy(config)

            # Update the configuration from the UI
            self.update_config_from_ui(config)
            
            # Save the updated configuration
            ConfigManager.save_config(config, log_info=False)
            
            # Apply changes to running features
            self.client_manager.apply_feature_state_changes(old_config, config)
            self.client_manager.update_running_feature_configs(config)

            if show_message:
                messagebox.showinfo("Settings Saved", "Configuration has been saved successfully.")
        except ValueError as e:
            logger.warning(f"Invalid input during settings save: {e}")
            messagebox.showerror("Invalid Input", str(e))
        except Exception:
            logger.exception("An unexpected error occurred while saving settings.")
            messagebox.showerror("Error", "An unexpected error occurred. Check logs for details.")

    def update_config_from_ui(self, config):
        """Update the configuration from the UI elements by calling granular update methods."""
        self._update_general_config_from_ui(config)
        self._update_trigger_config_from_ui(config)
        self._update_overlay_config_from_ui(config)
        self._update_additional_config_from_ui(config)

    def _update_general_config_from_ui(self, config):
        """Update General settings from the UI."""
        settings = config["General"]
        for key in ("Trigger", "Overlay", "Bunnyhop", "Noflash"):
            val = self.ui_bridge.get_value(key)
            if val is not None:
                settings[key] = val

        if self.ui_bridge.registered("OffsetSource"):
            display_name = self.ui_bridge.get_value("OffsetSource")
            source_id = getattr(self, "offset_source_mapping", {}).get(display_name, "a2x")
            settings["OffsetSource"] = source_id

    def _update_trigger_config_from_ui(self, config):
        """Update Trigger settings from the UI."""
        settings = config["Trigger"]
        for key in ("TriggerKey", "ToggleMode", "AttackOnTeammates"):
            val = self.ui_bridge.get_value(key)
            if val is not None:
                settings[key] = val if key != "TriggerKey" else val.strip()

        if self.ui_bridge.registered("active_weapon_type"):
            weapon_type = self.ui_bridge.get_value("active_weapon_type")
            settings["active_weapon_type"] = weapon_type
            weapon_settings = settings["WeaponSettings"].get(weapon_type, {})
            for delay_key in ("ShotDelayMin", "ShotDelayMax", "PostShotDelay"):
                raw = self.ui_bridge.get_value(delay_key)
                if raw is not None:
                    try:
                        weapon_settings[delay_key] = float(raw)
                    except ValueError:
                        pass
            settings["WeaponSettings"][weapon_type] = weapon_settings

    def _update_overlay_config_from_ui(self, config):
        """Update Overlay settings from the UI via the overlay_widgets registry."""
        settings = config["Overlay"]
        widgets = self.overlay_widgets

        checkbox_keys = (
            "enable_box", "enable_skeleton", "draw_snaplines",
            "draw_health_numbers", "draw_nicknames", "use_transliteration", "draw_teammates",
        )
        for key in checkbox_keys:
            info = widgets.get(key)
            if info and "variable" in info:
                settings[key] = info["variable"].get()

        for key in ("box_line_thickness", "target_fps"):
            info = widgets.get(key)
            if info and "widget" in info:
                settings[key] = info["widget"].get()

        color_defaults = {
            "box_color_hex": "#FFA500",
            "snaplines_color_hex": "#FFFFFF",
            "text_color_hex": "#FFFFFF",
            "teammate_color_hex": "#00FFFF",
        }
        for key, default in color_defaults.items():
            info = widgets.get(key)
            if info and "widget" in info:
                settings[key] = COLOR_CHOICES.get(info["widget"].get(), default)

    def _update_additional_config_from_ui(self, config):
        """Update Additional (Bunnyhop, NoFlash) settings from the UI."""
        bunnyhop = config.get("Bunnyhop", {})
        jump_key = self.ui_bridge.get_value("JumpKey")
        if jump_key is not None:
            bunnyhop["JumpKey"] = jump_key.strip()
        jump_delay = self.ui_bridge.get_value("JumpDelay")
        if jump_delay is not None:
            try:
                bunnyhop["JumpDelay"] = float(jump_delay)
            except ValueError:
                pass

        noflash = config.get("NoFlash", {})
        strength = self.ui_bridge.get_value("FlashSuppressionStrength")
        if strength is not None:
            noflash["FlashSuppressionStrength"] = strength

    def validate_inputs(self):
        """Validate user input fields."""
        trigger_key = self.ui_bridge.get_value("TriggerKey")
        if trigger_key is not None and not trigger_key.strip():
            raise ValueError("Trigger key cannot be empty.")

        min_delay = None
        raw_min = self.ui_bridge.get_value("ShotDelayMin")
        if raw_min is not None:
            try:
                min_delay = float(raw_min)
            except ValueError:
                raise ValueError("Minimum shot delay must be a valid number.")
            if min_delay < 0:
                raise ValueError("Minimum shot delay must be non-negative.")

        raw_max = self.ui_bridge.get_value("ShotDelayMax")
        if raw_max is not None:
            try:
                max_delay = float(raw_max)
            except ValueError:
                raise ValueError("Maximum shot delay must be a valid number.")
            if max_delay < 0:
                raise ValueError("Maximum shot delay must be non-negative.")
            if min_delay is not None and min_delay > max_delay:
                raise ValueError("Minimum delay cannot be greater than maximum delay.")

        raw_post = self.ui_bridge.get_value("PostShotDelay")
        if raw_post is not None:
            try:
                post_delay = float(raw_post)
            except ValueError:
                raise ValueError("Post-shot delay must be a valid number.")
            if post_delay < 0:
                raise ValueError("Post-shot delay must be non-negative.")

        fps_info = self.overlay_widgets.get("target_fps")
        if fps_info and "widget" in fps_info:
            try:
                target_fps = float(fps_info["widget"].get())
                if not (60 <= target_fps <= 420):
                    raise ValueError("Target FPS must be between 60 and 420.")
            except ValueError as e:
                if "Target FPS" in str(e):
                    raise
                raise ValueError("Target FPS must be a valid number.")

        jump_key = self.ui_bridge.get_value("JumpKey")
        if jump_key is not None and not jump_key.strip():
            raise ValueError("Jump key cannot be empty.")

        raw_jump_delay = self.ui_bridge.get_value("JumpDelay")
        if raw_jump_delay is not None:
            try:
                jump_delay = float(raw_jump_delay)
            except ValueError:
                raise ValueError("Jump delay must be a valid number.")
            if jump_delay < 0.01 or jump_delay > 0.5:
                raise ValueError("Jump delay must be between 0.01 and 0.5 seconds.")

        strength = self.ui_bridge.get_value("FlashSuppressionStrength")
        if strength is not None and not (0.0 <= strength <= 100.0):
            raise ValueError("Flash suppression strength must be between 0.0 and 100.0.")

    def reset_to_default_settings(self):
        """Reset all settings to their default values."""
        if not messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to their default values? This will stop all active features."):
            return

        try:
            # Stop all running features to ensure a clean state
            self.stop_client()

            new_config = ConfigManager.reset_to_default()

            # Sync all feature instances to the reset config via update_config so
            # internal caches (VK codes, weapon settings, etc.) are also reset.
            for feature_data in self.features.values():
                feature_data["instance"].update_config(new_config)

            self.update_ui_from_config()

            messagebox.showinfo("Settings Reset", "All settings have been reset to their default values. You can now start the client again.")
        except Exception:
            logger.exception("Failed to reset settings to default.")
            messagebox.showerror("Error", "Failed to reset settings. Check logs for details.")

    def update_ui_from_config(self):
        """Update the UI elements from the configuration by calling granular update methods."""
        config = ConfigManager.load_config()
        self._update_general_settings_ui_from_config(config)
        self._update_trigger_settings_ui_from_config(config)
        self._update_overlay_settings_ui_from_config(config)
        self._update_additional_settings_ui_from_config(config)

    def _update_general_settings_ui_from_config(self, config):
        """Update General settings UI from the configuration."""
        settings = config["General"]
        for key in ("Trigger", "Overlay", "Bunnyhop", "Noflash"):
            self.ui_bridge.set_value(key, settings.get(key, False))

    def _update_trigger_settings_ui_from_config(self, config):
        """Update Trigger settings UI from the configuration."""
        settings = config["Trigger"]
        self.ui_bridge.set_value("TriggerKey", settings.get("TriggerKey", "x"))
        self.ui_bridge.set_value("ToggleMode", settings.get("ToggleMode", False))
        self.ui_bridge.set_value("AttackOnTeammates", settings.get("AttackOnTeammates", False))
        if self.ui_bridge.registered("active_weapon_type"):
            self.ui_bridge.set_value("active_weapon_type", settings.get("active_weapon_type", "Rifles"))
            self.update_weapon_settings_display()

    def _update_overlay_settings_ui_from_config(self, config):
        """Update Overlay settings UI from the configuration via overlay_widgets registry."""
        settings = config["Overlay"]
        widgets = self.overlay_widgets

        for key in ("enable_box", "enable_skeleton", "draw_snaplines",
                    "draw_health_numbers", "draw_nicknames", "use_transliteration", "draw_teammates"):
            info = widgets.get(key)
            if info and "variable" in info:
                info["variable"].set(settings.get(key, False))

        for key, fmt in (("box_line_thickness", ".1f"), ("target_fps", ".0f")):
            info = widgets.get(key)
            if info:
                if "widget" in info:
                    info["widget"].set(settings.get(key, 0))
                if "value_label" in info:
                    info["value_label"].configure(text=f"{settings.get(key, 0):{fmt}}")

        for key in ("box_color_hex", "snaplines_color_hex", "text_color_hex", "teammate_color_hex"):
            info = widgets.get(key)
            if info and "widget" in info:
                info["widget"].set(Utility.get_color_name_from_hex(settings.get(key, "#FFFFFF")))

    def _update_additional_settings_ui_from_config(self, config):
        """Update Additional (Bunnyhop, NoFlash) settings UI from the configuration."""
        bunnyhop = config.get("Bunnyhop", {})
        self.ui_bridge.set_value("JumpKey", bunnyhop.get("JumpKey", "space"))
        self.ui_bridge.set_value("JumpDelay", str(bunnyhop.get("JumpDelay", 0.01)))

        noflash = config.get("NoFlash", {})
        self.ui_bridge.set_value("FlashSuppressionStrength", noflash.get("FlashSuppressionStrength", 0.0))

    def open_config_directory(self):
        """Open the configuration directory in the file explorer."""
        path = ConfigManager.CONFIG_DIRECTORY
        if platform.system() == "Windows":
            os.startfile(path)

    def init_config_watcher(self):
        """Initialize file watcher for configuration changes."""
        try:
            # Set up a watcher for config file changes
            event_handler = ConfigFileChangeHandler(self)
            self.observer = Observer()
            self.observer.schedule(event_handler, path=ConfigManager.CONFIG_DIRECTORY, recursive=False)
            self.observer.start()
            logger.info("Config file watcher started successfully.")
        except Exception:
            logger.exception("Failed to initialize config file watcher.")

    def start_log_timer(self):
        """Starts a timer to periodically update the log display in the GUI."""
        def read_log_file():
            try:
                log_path = Logger.LOG_FILE()
                if hasattr(self, 'log_text') and os.path.exists(log_path):
                    with open(log_path, 'r', encoding='utf-8') as f:
                        f.seek(self._log_file_pos)
                        new_bytes = f.read()
                        self._log_file_pos = f.tell()

                    if new_bytes:
                        self.root.after(0, self.append_log_display, new_bytes)
            except Exception:
                logger.exception("Error reading log file for GUI display.")

            self.log_timer = self.root.after(2000, read_log_file)

        read_log_file()

    def update_log_display(self, log_content):
        """Replaces the full log display content. Used for initial population."""
        try:
            if hasattr(self, 'log_text') and self.log_text.winfo_exists():
                self.log_text.configure(state="normal")
                self.log_text.delete("1.0", "end")
                self.log_text.insert("1.0", log_content)
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except Exception:
            logger.exception("Failed to update log display in the GUI.")

    def append_log_display(self, new_content):
        """Appends only newly written log lines to the display widget."""
        try:
            if hasattr(self, 'log_text') and self.log_text.winfo_exists():
                self.log_text.configure(state="normal")
                self.log_text.insert("end", new_content)
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except Exception:
            logger.exception("Failed to append log display in the GUI.")

    def run(self):
        """Start the application main loop."""
        self.root.mainloop()

    def on_closing(self):
        """Handle window close event by cleaning up resources."""
        self.cleanup()
        self.root.destroy()

    def cleanup(self):
        """Cleanup resources before closing the application."""
        try:
            # Stop all running features
            self.stop_client()
            
            # Stop the file watcher if it exists
            if hasattr(self, 'observer') and self.observer:
                self.observer.stop()
                self.observer.join()
            
            # Cancel the log timer if it's running
            if self.log_timer:
                self.root.after_cancel(self.log_timer)
        except Exception:
            logger.exception("An error occurred during application cleanup.")
