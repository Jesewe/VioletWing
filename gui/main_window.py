import os
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
                         COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_BACKGROUND, COLOR_WIDGET_BACKGROUND, COLOR_ACCENT_FG,
                         BUTTON_STYLE_PRIMARY, BUTTON_STYLE_DANGER)

# Cache the logger instance for consistent logging throughout the application
logger = Logger.get_logger()

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
        # Track the last position in the log file for incremental updates
        self.last_log_position = 0

        # Configure CustomTkinter with a modern dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Fetch offsets and client data
        self.offsets, self.client_data, self.buttons_data = self.fetch_offsets_or_warn()

        # Create a single MemoryManager instance
        self.memory_manager = MemoryManager(self.offsets, self.client_data, self.buttons_data)

        # Initialize feature instances
        self.initialize_features()
        
        # Create the main window with a title and initial size
        self.root = ctk.CTk()
        self.root.title(f"VioletWing {ConfigManager.VERSION}")
        self.root.geometry("1400x800")
        self.root.resizable(True, True)
        self.root.minsize(1400, 800)

        # Center the window on the screen
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
                'src/fonts/Chivo-Regular.ttf',
                'src/fonts/Chivo-Bold.ttf',
                'src/fonts/Gambetta-Regular.ttf',
                'src/fonts/Gambetta-Bold.ttf'
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
        except Exception as e:
            logger.error(f"Failed to initialize features: {e}")
            messagebox.showerror("Initialization Error", f"Failed to initialize features: {str(e)}")

    def setup_ui(self):
        """Setup the modern user interface components."""
        # Create a modern header with branding and controls
        self.create_modern_header()
        
        # Create the main content area including sidebar navigation
        self.create_main_content()

    def create_modern_header(self):
        """Create a sleek modern header with gradient-like appearance."""
        header_container = ctk.CTkFrame(self.root, height=80, corner_radius=0, fg_color=("#1a1a1a", "#0d1117"))
        header_container.grid(row=0, column=0, sticky="ew")
        header_container.grid_propagate(False)
        header_container.grid_columnconfigure(1, weight=1)

        self.create_header_left(header_container)
        self.create_header_right(header_container)

    def create_header_left(self, parent):
        """Create the left side of the header with title and version."""
        left_frame = ctk.CTkFrame(parent, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="w", padx=30, pady=15)
        
        title_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        title_frame.pack(side="left")
        
        ctk.CTkLabel(title_frame, text="Violet", font=(FONT_FAMILY_BOLD[0], FONT_SIZE_H2, "bold"), text_color=COLOR_ACCENT_FG[0]).pack(side="left")
        ctk.CTkLabel(title_frame, text="Wing", font=(FONT_FAMILY_BOLD[0], FONT_SIZE_H2, "bold"), text_color=COLOR_TEXT_PRIMARY[1]).pack(side="left", padx=(5, 0))
        ctk.CTkLabel(title_frame, text=f"{ConfigManager.VERSION}", font=(FONT_FAMILY_REGULAR[0], FONT_SIZE_P), text_color=COLOR_TEXT_SECONDARY[0]).pack(side="left", padx=(10, 0), pady=(8, 0))

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
        
        ctk.CTkFrame(self.status_frame, width=12, height=12, corner_radius=6, fg_color="#ef4444").pack(side="left", pady=(0, 2))
        self.status_label = ctk.CTkLabel(self.status_frame, text="Inactive", font=(FONT_FAMILY_BOLD[0], FONT_SIZE_H4, "bold"), text_color=BUTTON_STYLE_DANGER["fg_color"][0])
        self.status_label.pack(side="left", padx=(8, 0))

    def create_social_buttons(self, parent):
        """Create and pack the social media buttons."""
        social_frame = ctk.CTkFrame(parent, fg_color="transparent")
        social_frame.pack(side="right")

        social_buttons_data = [
            {"text": "GitHub", "icon": "github", "url": "https://github.com/Jesewe/VioletWing", "fg_color": "#21262d", "hover_color": "#30363d", "border_color": "#30363d"},
            {"text": "Telegram", "icon": "telegram", "url": "https://t.me/cs2_jesewe", "fg_color": "#0088cc", "hover_color": "#006bb3"},
            {"text": "Help Center", "icon": "violetwing", "url": "https://violetwing.featurebase.app/en/help", "fg_color": "#d5006d", "hover_color": "#97004e"}
        ]

        for i, data in enumerate(social_buttons_data):
            try:
                image = Image.open(Utility.resource_path(f'src/img/{data["icon"]}_icon.png'))
                ctk_image = ctk.CTkImage(light_image=image, dark_image=image, size=(24, 24))
            except FileNotFoundError:
                ctk_image = None

            btn = ctk.CTkButton(
                social_frame,
                text=data["text"],
                image=ctk_image,
                compound="left",
                command=lambda u=data["url"]: webbrowser.open(u),
                height=32,
                corner_radius=16,
                fg_color=data["fg_color"],
                hover_color=data["hover_color"],
                border_width=1 if "border_color" in data else 0,
                border_color=data.get("border_color"),
                font=(FONT_FAMILY_BOLD[0], FONT_SIZE_H4)
            )
            btn.pack(side="left", padx=(0, 8) if i < len(social_buttons_data) - 1 else (0, 0))
        
        return social_frame

    def create_update_button(self, parent):
        """Create the update button if an update is available."""
        if self.updater.check_for_updates():
            update_btn = ctk.CTkButton(
                parent,
                text="Pre-release Available!" if self.updater.is_prerelease else "Update Available!",
                command=self.updater.handle_update,
                width=120,
                height=32,
                corner_radius=16,
                fg_color="#ef4444" if not self.updater.is_prerelease else "#f59e0b",
                hover_color="#dc2626" if not self.updater.is_prerelease else "#d97706",
                font=("Chivo", 14)
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
        sidebar = ctk.CTkFrame(parent, width=280, corner_radius=0, fg_color=COLOR_BACKGROUND)
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

        self.nav_buttons = {}
        ctk.CTkFrame(sidebar, height=30, fg_color="transparent").pack(fill="x")

        for name, key, icon in self.nav_items:
            btn = ctk.CTkButton(
                sidebar,
                text=f"{icon}  {name}",
                command=lambda k=key: self.switch_view(k),
                width=240,
                height=50,
                corner_radius=12,
                fg_color="transparent",
                hover_color=COLOR_WIDGET_BACKGROUND,
                text_color=COLOR_TEXT_SECONDARY,
                font=(FONT_FAMILY_BOLD[0], FONT_SIZE_H4),
                anchor="w",
            )
            btn.pack(pady=(0, 8), padx=20, fill="x")
            self.nav_buttons[key] = btn

        self.set_active_nav("dashboard")

    def set_active_nav(self, active_key):
        """Set the active navigation button with visual feedback."""
        for key, btn in self.nav_buttons.items():
            if key == active_key:
                # Highlight the active button
                btn.configure(
                    fg_color=COLOR_ACCENT_FG,
                    text_color=COLOR_TEXT_PRIMARY[1]
                )
            else:
                # Reset inactive buttons to default style
                btn.configure(
                    fg_color="transparent",
                    text_color=COLOR_TEXT_SECONDARY,
                    hover_color=COLOR_WIDGET_BACKGROUND
                )

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

    def fetch_offsets_or_warn(self):
        """Attempt to fetch offsets; warn the user and return empty dictionaries on failure."""
        try:
            offsets, client_data, buttons_data = Utility.fetch_offsets()
            if offsets is None or client_data is None or buttons_data is None:
                raise ValueError("Failed to fetch offsets from the server.")
            return offsets, client_data, buttons_data
        except Exception as e:
            logger.error("Offsets fetch error: %s", e)
            messagebox.showerror("Offset Error", f"Failed to fetch offsets: {str(e)}")
            return {}, {}, {}

    def update_client_status(self, status, color):
        """Update client status in header and dashboard."""
        # Update header status label
        self.status_label.configure(text=status, text_color=color)
    
        # Update header status dot color
        for widget in self.status_frame.winfo_children():
            if isinstance(widget, ctk.CTkFrame) and widget.cget("width") == 12:
                widget.configure(fg_color=color)
                break
        
        # Update dashboard status label if it exists
        if hasattr(self, 'bot_status_label'):
            self.bot_status_label.configure(text=status, text_color=color)

    def _start_feature(self, feature_name, feature_obj, config):
        """Helper method to start a single feature."""
        if not getattr(feature_obj, 'is_running', False):
            try:
                # Ensure the feature object has the latest config
                feature_obj.config = config
                feature_obj.is_running = True
                thread = threading.Thread(target=feature_obj.start, daemon=True)
                thread.start()
                setattr(self, f'{feature_name.lower()}_thread', thread)
                logger.info(f"{feature_name} started.")
                return True
            except Exception as e:
                # Reset running state on failure
                feature_obj.is_running = False
                logger.error(f"Failed to start {feature_name}: {e}")
                messagebox.showerror(f"{feature_name} Error", f"Failed to start {feature_name}: {str(e)}")
        return False

    def _stop_feature(self, feature_name, feature_obj):
        """Helper method to stop a single feature."""
        if feature_obj and getattr(feature_obj, 'is_running', False):
            try:
                feature_obj.stop()
                thread = getattr(self, f'{feature_name.lower()}_thread', None)
                if thread and thread.is_alive():
                    thread.join(timeout=2.0)
                    if thread.is_alive():
                        logger.warning(f"{feature_name} thread did not terminate cleanly.")
                    else:
                        logger.info(f"{feature_name} thread terminated successfully.")
                setattr(self, f'{feature_name.lower()}_thread', None)
                feature_obj.is_running = False
                logger.debug(f"{feature_name} stopped.")
                return True
            except Exception as e:
                logger.error(f"Failed to stop {feature_name}: {e}", exc_info=True)
                # Force reset the running state even if stop failed
                feature_obj.is_running = False
        return False

    def start_client(self):
        """Start selected features based on General settings, ensuring no duplicates."""
        if not Utility.is_game_running():
            messagebox.showerror("Game Not Running", "Could not find cs2.exe process. Make sure the game is running.")
            return

        # Initialize the MemoryManager once before starting any features
        if not self.memory_manager.initialize():
            messagebox.showerror("Initialization Error", "Failed to initialize memory manager. Please check the logs for details.")
            return

        config = ConfigManager.load_config()
        any_feature_started = False

        # Start features based on General settings
        for config_key, feature_data in self.features.items():
            if config["General"][config_key]:
                feature_name = feature_data["name"]
                feature_obj = feature_data["instance"]
                if not getattr(feature_obj, 'is_running', False):
                    if self._start_feature(feature_name, feature_obj, config):
                        any_feature_started = True
                else:
                    logger.info(f"{feature_name} is already running.")
                    any_feature_started = True

        if any_feature_started:
            self.update_client_status("Active", "#22c55e")
        else:
            logger.warning("No features enabled in General settings.")
            messagebox.showwarning("No Features Enabled", "Please enable at least one feature in General Settings.")

    def stop_client(self):
        """Stop all running features and ensure threads are terminated."""
        features_stopped = False

        # Stop all features
        for feature_data in self.features.values():
            if self._stop_feature(feature_data["name"], feature_data["instance"]):
                features_stopped = True

        if features_stopped:
            self.update_client_status("Inactive", "#ef4444")
        else:
            logger.debug("No features were running to stop.")

    def update_weapon_settings_display(self):
        """Update UI fields based on the selected weapon type."""
        weapon_type = self.active_weapon_type.get()
        settings = self.triggerbot.config['Trigger']['WeaponSettings'].get(weapon_type, {})
        
        if hasattr(self, 'min_delay_entry'):
            self.min_delay_entry.delete(0, "end")
            self.min_delay_entry.insert(0, str(settings.get('ShotDelayMin', 0.01)))
        if hasattr(self, 'max_delay_entry'):
            self.max_delay_entry.delete(0, "end")
            self.max_delay_entry.insert(0, str(settings.get('ShotDelayMax', 0.03)))
        if hasattr(self, 'post_shot_delay_entry'):
            self.post_shot_delay_entry.delete(0, "end")
            self.post_shot_delay_entry.insert(0, str(settings.get('PostShotDelay', 0.1)))

    def save_settings(self, show_message=False):
        """Save the configuration settings and apply to relevant features in real-time."""
        try:
            self.validate_inputs()
            
            # Load the current configuration to ensure all parts are present
            config = ConfigManager.load_config()
            old_config = config.copy()

            # Update the configuration from the UI
            self.update_config_from_ui(config)
            
            # Save the updated configuration
            ConfigManager.save_config(config, log_info=True)
            
            # Apply changes to running features
            self.apply_feature_state_changes(old_config, config)
            self.update_running_feature_configs(config)

            if show_message:
                messagebox.showinfo("Settings Saved", "Configuration has been saved successfully.")
        except ValueError as e:
            logger.error(f"Invalid input: {e}")
            messagebox.showerror("Invalid Input", str(e))
        except Exception as e:
            logger.error(f"Unexpected error during save_settings: {e}", exc_info=True)
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

    def apply_feature_state_changes(self, old_config, new_config):
        """Start or stop features based on configuration changes."""
        game_running = Utility.is_game_running()

        for key, feature_data in self.features.items():
            old_enabled = old_config["General"].get(key, False)
            new_enabled = new_config["General"].get(key, False)
            is_running = getattr(feature_data["instance"], 'is_running', False)

            if old_enabled == new_enabled:
                continue

            if new_enabled and not is_running:
                if game_running:
                    if self.memory_manager.initialize():
                        self._start_feature(feature_data["name"], feature_data["instance"], new_config)
                    else:
                        logger.error(f"Failed to initialize memory manager for {feature_data['name']}")
                else:
                    logger.warning(f"Cannot start {feature_data['name']}: Game is not running")
            elif not new_enabled and is_running:
                self._stop_feature(feature_data["name"], feature_data["instance"])

    def update_running_feature_configs(self, new_config):
        """Update the configuration for all currently running features and update UI status."""
        any_feature_running = False
        for feature_data in self.features.values():
            instance = feature_data["instance"]
            if getattr(instance, 'is_running', False):
                instance.update_config(new_config)
                logger.debug(f"Configuration updated for {feature_data['name']}.")
                any_feature_running = True
        
        status = "Active" if any_feature_running else "Inactive"
        color = "#22c55e" if any_feature_running else "#ef4444"
        self.update_client_status(status, color)

    def _restart_feature(self, feature_name, feature_obj, feature_class, config_section, new_config):
        """Helper method to restart a single feature."""
        try:
            # Stop the feature
            feature_obj.stop()
            thread = getattr(self, f'{feature_name.lower()}_thread', None)
            if thread and thread.is_alive():
                thread.join(timeout=2.0)
            setattr(self, f'{feature_name.lower()}_thread', None)
            
            # Restart if enabled in General config
            if new_config["General"][config_section]:
                new_feature = feature_class(self.memory_manager)
                new_feature.config = new_config
                setattr(self, feature_name.lower(), new_feature)
                
                new_thread = threading.Thread(target=new_feature.start, daemon=True)
                new_thread.start()
                setattr(self, f'{feature_name.lower()}_thread', new_thread)
                logger.info(f"{feature_name} restarted with new configuration.")
            
            return True
        except Exception as e:
            logger.error(f"Failed to restart {feature_name}: {e}")
            return False

    def restart_affected_features(self, old_config, new_config):
        """Restart only features affected by configuration changes."""
        any_feature_running = False

        def config_changed(section):
            return old_config.get(section, {}) != new_config.get(section, {})

        # Restart features if their config changed and they're running
        for config_section, feature_data in self.features.items():
            feature_obj = feature_data["instance"]
            if hasattr(feature_obj, 'is_running') and feature_obj.is_running and \
               (config_changed(config_section) or config_changed("General")):
                
                feature_name = feature_data["name"]
                feature_class = feature_data["class"]
                if self._restart_feature(feature_name, feature_obj, feature_class, config_section, new_config):
                    any_feature_running = True

        # Update UI status
        if any_feature_running:
            self.update_client_status("Active", "#22c55e")
        else:
            self.update_client_status("Inactive", "#ef4444")

    def update_config_from_ui(self, config):
        """Update the configuration from the UI elements by calling granular update methods."""
        self._update_general_config_from_ui(config)
        self._update_trigger_config_from_ui(config)
        self._update_overlay_config_from_ui(config)
        self._update_additional_config_from_ui(config)

    def _update_general_config_from_ui(self, config):
        """Update General settings from the UI."""
        settings = config["General"]
        if hasattr(self, 'trigger_var'): settings["Trigger"] = self.trigger_var.get()
        if hasattr(self, 'overlay_var'): settings["Overlay"] = self.overlay_var.get()
        if hasattr(self, 'bunnyhop_var'): settings["Bunnyhop"] = self.bunnyhop_var.get()
        if hasattr(self, 'noflash_var'): settings["Noflash"] = self.noflash_var.get()

    def _update_trigger_config_from_ui(self, config):
        """Update Trigger settings from the UI."""
        settings = config["Trigger"]
        if hasattr(self, 'trigger_key_entry'): settings["TriggerKey"] = self.trigger_key_entry.get().strip()
        if hasattr(self, 'toggle_mode_var'): settings["ToggleMode"] = self.toggle_mode_var.get()
        if hasattr(self, 'attack_teammates_var'): settings["AttackOnTeammates"] = self.attack_teammates_var.get()

        if hasattr(self, 'active_weapon_type'):
            weapon_type = self.active_weapon_type.get()
            settings['active_weapon_type'] = weapon_type
            weapon_settings = settings['WeaponSettings'].get(weapon_type, {})
            
            try:
                if hasattr(self, 'min_delay_entry'): weapon_settings['ShotDelayMin'] = float(self.min_delay_entry.get())
                if hasattr(self, 'max_delay_entry'): weapon_settings['ShotDelayMax'] = float(self.max_delay_entry.get())
                if hasattr(self, 'post_shot_delay_entry'): weapon_settings['PostShotDelay'] = float(self.post_shot_delay_entry.get())
            except ValueError:
                pass
            
            settings['WeaponSettings'][weapon_type] = weapon_settings

    def _update_overlay_config_from_ui(self, config):
        """Update Overlay settings from the UI."""
        settings = config["Overlay"]
        if hasattr(self, 'enable_box_var'): settings["enable_box"] = self.enable_box_var.get()
        if hasattr(self, 'enable_skeleton_var'): settings["enable_skeleton"] = self.enable_skeleton_var.get()
        if hasattr(self, 'box_line_thickness_slider'): settings["box_line_thickness"] = self.box_line_thickness_slider.get()
        if hasattr(self, 'box_color_hex_combo'): settings["box_color_hex"] = COLOR_CHOICES.get(self.box_color_hex_combo.get(), "#FFA500")
        if hasattr(self, 'draw_snaplines_var'): settings["draw_snaplines"] = self.draw_snaplines_var.get()
        if hasattr(self, 'snaplines_color_hex_combo'): settings["snaplines_color_hex"] = COLOR_CHOICES.get(self.snaplines_color_hex_combo.get(), "#FFFFFF")
        if hasattr(self, 'text_color_hex_combo'): settings["text_color_hex"] = COLOR_CHOICES.get(self.text_color_hex_combo.get(), "#FFFFFF")
        if hasattr(self, 'draw_health_numbers_var'): settings["draw_health_numbers"] = self.draw_health_numbers_var.get()
        if hasattr(self, 'draw_nicknames_var'): settings["draw_nicknames"] = self.draw_nicknames_var.get()
        if hasattr(self, 'use_transliteration_var'): settings["use_transliteration"] = self.use_transliteration_var.get()
        if hasattr(self, 'draw_teammates_var'): settings["draw_teammates"] = self.draw_teammates_var.get()
        if hasattr(self, 'teammate_color_hex_combo'): settings["teammate_color_hex"] = COLOR_CHOICES.get(self.teammate_color_hex_combo.get(), "#00FFFF")
        if hasattr(self, 'target_fps_slider'): settings["target_fps"] = self.target_fps_slider.get()

    def _update_additional_config_from_ui(self, config):
        """Update Additional (Bunnyhop, NoFlash) settings from the UI."""
        bunnyhop_settings = config.get("Bunnyhop", {})
        if hasattr(self, 'jump_key_entry'): bunnyhop_settings["JumpKey"] = self.jump_key_entry.get().strip()
        try:
            if hasattr(self, 'jump_delay_entry'): bunnyhop_settings["JumpDelay"] = float(self.jump_delay_entry.get())
        except ValueError:
            pass
        
        noflash_settings = config.get("NoFlash", {})
        if hasattr(self, 'FlashSuppressionStrength_slider'): noflash_settings["FlashSuppressionStrength"] = self.FlashSuppressionStrength_slider.get()

    def validate_inputs(self):
        """Validate user input fields."""
        # Validate Trigger settings
        if hasattr(self, 'trigger_key_entry'):
            trigger_key = self.trigger_key_entry.get().strip()
            if not trigger_key:
                raise ValueError("Trigger key cannot be empty.")

        # Validate delay fields as numbers
        if hasattr(self, 'min_delay_entry'):
            try:
                min_delay = float(self.min_delay_entry.get())
            except ValueError:
                raise ValueError("Minimum shot delay must be a valid number.")
            if min_delay < 0:
                raise ValueError("Minimum shot delay must be non-negative.")
        else:
            min_delay = None

        if hasattr(self, 'max_delay_entry'):
            try:
                max_delay = float(self.max_delay_entry.get())
            except ValueError:
                raise ValueError("Maximum shot delay must be a valid number.")
            if max_delay < 0:
                raise ValueError("Maximum shot delay must be non-negative.")
            if min_delay is not None and min_delay > max_delay:
                raise ValueError("Minimum delay cannot be greater than maximum delay.")
        else:
            max_delay = None

        if hasattr(self, 'post_shot_delay_entry'):
            try:
                post_delay = float(self.post_shot_delay_entry.get())
            except ValueError:
                raise ValueError("Post-shot delay must be a valid number.")
            if post_delay < 0:
                raise ValueError("Post-shot delay must be non-negative.")


        if hasattr(self, 'target_fps_slider'):
            try:
                target_fps = float(self.target_fps_slider.get())
                if not (60 <= target_fps <= 420):
                    raise ValueError("Target FPS must be between 60 and 420.")
            except ValueError:
                raise ValueError("Target FPS must be a valid number.")
            
        # Validate Bunnyhop settings
        if hasattr(self, 'jump_key_entry'):
            jump_key = self.jump_key_entry.get().strip()
            if not jump_key:
                raise ValueError("Jump key cannot be empty.")

        if hasattr(self, 'jump_delay_entry'):
            try:
                jump_delay = float(self.jump_delay_entry.get())
            except ValueError:
                raise ValueError("Jump delay must be a valid number.")
            if jump_delay < 0.01 or jump_delay > 0.5:
                raise ValueError("Jump delay must be between 0.01 and 0.5 seconds.")

        # Validate NoFlash settings
        if hasattr(self, 'FlashSuppressionStrength_slider'):
            strength = self.FlashSuppressionStrength_slider.get()
            if not (0.0 <= strength <= 1.0):
                raise ValueError("Flash suppression strength must be between 0.0 and 1.0.")

    def reset_to_default_settings(self):
        """Reset all settings to their default values."""
        if not messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to their default values? This will stop all active features."):
            return

        try:
            # Stop all running features to ensure a clean state
            self.stop_client()

            # Get a fresh copy of the default configuration
            new_config = ConfigManager.DEFAULT_CONFIG.copy()
            
            # Update the config for all feature instances
            self.triggerbot.config = new_config
            self.overlay.config = new_config
            self.bunnyhop.config = new_config
            self.noflash.config = new_config
            
            # Update the UI to reflect the new default settings
            self.update_ui_from_config()

            # Save the new default configuration to the file
            ConfigManager.save_config(new_config)
            
            messagebox.showinfo("Settings Reset", "All settings have been reset to their default values. You can now start the client again.")
        except Exception as e:
            logger.error(f"Failed to reset settings: {e}")
            messagebox.showerror("Error", f"Failed to reset settings: {str(e)}")

    def update_ui_from_config(self):
        """Update the UI elements from the configuration by calling granular update methods."""
        self._update_general_settings_ui_from_config()
        self._update_trigger_settings_ui_from_config()
        self._update_overlay_settings_ui_from_config()
        self._update_additional_settings_ui_from_config()

    def _update_general_settings_ui_from_config(self):
        """Update General settings UI from the configuration."""
        settings = self.triggerbot.config["General"]
        if hasattr(self, 'trigger_var'): self.trigger_var.set(settings["Trigger"])
        if hasattr(self, 'overlay_var'): self.overlay_var.set(settings["Overlay"])
        if hasattr(self, 'bunnyhop_var'): self.bunnyhop_var.set(settings["Bunnyhop"])
        if hasattr(self, 'noflash_var'): self.noflash_var.set(settings["Noflash"])

    def _update_trigger_settings_ui_from_config(self):
        """Update Trigger settings UI from the configuration."""
        settings = self.triggerbot.config["Trigger"]
        if hasattr(self, 'trigger_key_entry'):
            self.trigger_key_entry.delete(0, "end")
            self.trigger_key_entry.insert(0, settings["TriggerKey"])
        if hasattr(self, 'toggle_mode_var'): self.toggle_mode_var.set(settings["ToggleMode"])
        if hasattr(self, 'attack_teammates_var'): self.attack_teammates_var.set(settings["AttackOnTeammates"])
        if hasattr(self, 'active_weapon_type'):
            self.active_weapon_type.set(settings.get('active_weapon_type', 'Rifles'))
            self.update_weapon_settings_display()

    def _update_overlay_settings_ui_from_config(self):
        """Update Overlay settings UI from the configuration."""
        settings = self.overlay.config["Overlay"]
        if hasattr(self, 'enable_box_var'): self.enable_box_var.set(settings["enable_box"])
        if hasattr(self, 'enable_skeleton_var'): self.enable_skeleton_var.set(settings["enable_skeleton"])
        if hasattr(self, 'box_line_thickness_slider'):
            self.box_line_thickness_slider.set(settings["box_line_thickness"])
            if hasattr(self, 'box_line_thickness_value_label'): self.box_line_thickness_value_label.configure(text=f"{settings['box_line_thickness']:.1f}")
        if hasattr(self, 'box_color_hex_combo'): self.box_color_hex_combo.set(Utility.get_color_name_from_hex(settings["box_color_hex"]))
        if hasattr(self, 'draw_snaplines_var'): self.draw_snaplines_var.set(settings["draw_snaplines"])
        if hasattr(self, 'snaplines_color_hex_combo'): self.snaplines_color_hex_combo.set(Utility.get_color_name_from_hex(settings["snaplines_color_hex"]))
        if hasattr(self, 'text_color_hex_combo'): self.text_color_hex_combo.set(Utility.get_color_name_from_hex(settings["text_color_hex"]))
        if hasattr(self, 'draw_health_numbers_var'): self.draw_health_numbers_var.set(settings["draw_health_numbers"])
        if hasattr(self, 'draw_nicknames_var'): self.draw_nicknames_var.set(settings["draw_nicknames"])
        if hasattr(self, 'use_transliteration_var'): self.use_transliteration_var.set(settings["use_transliteration"])
        if hasattr(self, 'draw_teammates_var'): self.draw_teammates_var.set(settings["draw_teammates"])
        if hasattr(self, 'teammate_color_hex_combo'): self.teammate_color_hex_combo.set(Utility.get_color_name_from_hex(settings["teammate_color_hex"]))
        if hasattr(self, 'target_fps_slider'):
            self.target_fps_slider.set(settings["target_fps"])
            if hasattr(self, 'target_fps_value_label'): self.target_fps_value_label.configure(text=f"{settings['target_fps']:.0f}")

    def _update_additional_settings_ui_from_config(self):
        """Update Additional (Bunnyhop, NoFlash) settings UI from the configuration."""
        bunnyhop_settings = self.bunnyhop.config.get("Bunnyhop", {})
        if hasattr(self, 'jump_key_entry'):
            self.jump_key_entry.delete(0, "end")
            self.jump_key_entry.insert(0, bunnyhop_settings.get("JumpKey", "space"))
        if hasattr(self, 'jump_delay_entry'):
            self.jump_delay_entry.delete(0, "end")
            self.jump_delay_entry.insert(0, str(bunnyhop_settings.get("JumpDelay", 0.01)))

        noflash_settings = self.noflash.config.get("NoFlash", {})
        if hasattr(self, 'FlashSuppressionStrength_slider'):
            self.FlashSuppressionStrength_slider.set(noflash_settings.get("FlashSuppressionStrength", 0.0))
            if hasattr(self, 'FlashSuppressionStrength_value_label'): self.FlashSuppressionStrength_value_label.configure(text=f"{noflash_settings.get('FlashSuppressionStrength', 0.0):.2f}")

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
        except Exception as e:
            logger.error("Failed to initialize config watcher: %s", e)

    def start_log_timer(self):
        """Start timer for updating logs in a separate thread."""
        def update_logs():
            logger = Logger.get_logger()
            while True:
                try:
                    # Update logs if the widget exists and log file is present
                    if hasattr(self, 'log_text') and os.path.exists(Logger.LOG_FILE):
                        file_size = os.path.getsize(Logger.LOG_FILE)
                        # Reset position if log file is truncated
                        if file_size < self.last_log_position:
                            self.last_log_position = 0
                        if self.last_log_position < file_size:
                            with open(Logger.LOG_FILE, 'r', encoding='utf-8') as log_file:
                                log_file.seek(self.last_log_position)
                                new_logs = log_file.read()
                                self.last_log_position = log_file.tell()
                                if new_logs:
                                    self.root.after(0, lambda logs=new_logs: self.update_log_display(logs))
                except Exception as e:
                    logger.error(f"Error in log update thread: {e}")
                time.sleep(0.1)

        # Start log update thread
        self.log_timer = threading.Thread(target=update_logs, daemon=True)
        self.log_timer.start()

    def update_log_display(self, new_logs):
        """Update the log display with new logs, limiting lines for performance."""
        logger = Logger.get_logger()
        try:
            # Ensure log widget exists and is valid
            if hasattr(self, 'log_text') and self.log_text.winfo_exists():
                self.log_text.configure(state="normal")
                self.log_text.insert("end", new_logs)
                self.log_text.see("end")
                
                # Limit log lines to 1000 for performance
                max_lines = 1000
                current_text = self.log_text.get("1.0", "end-1c")
                lines = current_text.splitlines()
                if len(lines) > max_lines:
                    excess_lines = len(lines) - max_lines
                    delete_to = f"{excess_lines + 1}.0"
                    self.log_text.delete("1.0", delete_to)
                
                self.log_text.configure(state="disabled")
        except Exception as e:
            logger.error(f"Error updating log display: {e}")

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
        except Exception as e:
            logger.error("Error during cleanup: %s", e)
