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
        
        # Initialize UI components like header and content
        self.setup_ui()
        
        # Set up configuration file watcher and log update timer
        self.init_config_watcher()
        self.start_log_timer()
        
        # Bind window close event to cleanup resources
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def initialize_features(self):
        """Initialize all feature instances with the shared MemoryManager."""
        try:
            self.triggerbot = CS2TriggerBot(self.memory_manager)
            self.overlay = CS2Overlay(self.memory_manager)
            self.bunnyhop = CS2Bunnyhop(self.memory_manager)
            self.noflash = CS2NoFlash(self.memory_manager)
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
        # Main header container with fixed height and dark background
        header_container = ctk.CTkFrame(
            self.root, 
            height=80,
            corner_radius=0,
            fg_color=("#1a1a1a", "#0d1117")
        )
        header_container.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_container.grid_propagate(False)
        header_container.grid_columnconfigure(1, weight=1)
        
        # Left side frame for logo and title
        left_frame = ctk.CTkFrame(header_container, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="w", padx=30, pady=15)
        
        # Frame for title components
        title_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        title_frame.pack(side="left")
        
        # Main title "Violet" with accent color
        main_title = ctk.CTkLabel(
            title_frame,
            text="Violet",
            font=("Chivo", 28, "bold"),
            text_color="#D5006D"
        )
        main_title.pack(side="left")
        
        # Subtitle "Wing" in white
        sub_title = ctk.CTkLabel(
            title_frame,
            text="Wing",
            font=("Chivo", 28, "bold"),
            text_color="#E0E0E0"
        )
        sub_title.pack(side="left", padx=(5, 0))
        
        # Version label with smaller font and gray color
        version_label = ctk.CTkLabel(
            title_frame,
            text=f"{ConfigManager.VERSION}",
            font=("Gambetta", 12),
            text_color="#6b7280"
        )
        version_label.pack(side="left", padx=(10, 0), pady=(8, 0))
        
        # Right side frame for status and action buttons
        right_frame = ctk.CTkFrame(header_container, fg_color="transparent")
        right_frame.grid(row=0, column=2, sticky="e", padx=30, pady=15)
        
        # Status indicator frame
        self.status_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        self.status_frame.pack(side="right", padx=(20, 0))
        
        # Status dot indicating client activity
        status_dot = ctk.CTkFrame(
            self.status_frame,
            width=12,
            height=12,
            corner_radius=6,
            fg_color="#ef4444"
        )
        status_dot.pack(side="left", pady=(0, 2))
        
        # Status label showing "Inactive" or "Active"
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Inactive",
            font=("Chivo", 14, "bold"),
            text_color="#ef4444"
        )
        self.status_label.pack(side="left", padx=(8, 0))
        
        # Frame for social media buttons
        social_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        social_frame.pack(side="right")
        
        # Load social media icons using CTkImage
        icons = ['github', 'telegram', 'violetwing']
        for icon in icons:
            try:
                image = Image.open(Utility.resource_path(f'src/img/{icon}_icon.png'))
                setattr(self, f'{icon}_ctk_image', ctk.CTkImage(light_image=image, dark_image=image, size=(24, 24)))
            except FileNotFoundError:
                setattr(self, f'{icon}_ctk_image', None)
        
        social_buttons = [
            ("GitHub", "github", "https://github.com/Jesewe/VioletWing", "#21262d", "#30363d", "#30363d"),
            ("Telegram", "telegram", "https://t.me/cs2_jesewe", "#0088cc", "#006bb3", None),
            ("Help Center", "violetwing", "https://violetwing.featurebase.app/en/help", "#d5006d", "#97004e", None)
        ]

        for i, (text, icon, url, fg_color, hover_color, border_color) in enumerate(social_buttons):
            btn = ctk.CTkButton(
                social_frame,
                text=text,
                image=getattr(self, f'{icon}_ctk_image'),
                compound="left",
                command=lambda u=url: webbrowser.open(u),
                height=32,
                corner_radius=16,
                fg_color=fg_color,
                hover_color=hover_color,
                border_width=1 if border_color else 0,
                border_color=border_color,
                font=("Chivo", 14)
            )
            btn.pack(side="left", padx=(0, 8) if i < len(social_buttons) - 1 else (0, 0))

        # Check for updates if running as an executable
        if getattr(sys, 'frozen', False):
            logger.info("Running from executable. Checking for updates...")
            download_url, is_prerelease = Utility.check_for_updates(ConfigManager.VERSION)
            if download_url:
                self.download_url = download_url
                self.is_prerelease = is_prerelease
                # Update button shown when a new version is available
                update_btn = ctk.CTkButton(
                    social_frame,
                    text="Pre-release Available!" if is_prerelease else "Update Available!",
                    command=self.handle_update,
                    width=120,
                    height=32,
                    corner_radius=16,
                    fg_color="#ef4444" if not is_prerelease else "#f59e0b",
                    hover_color="#dc2626" if not is_prerelease else "#d97706",
                    font=("Chivo", 14)
                )
                update_btn.pack(side="left", padx=(8, 0))
        else:
            logger.info("Running from source code. Auto-update disabled.")

    def handle_update(self):
        """Handle the update process with user confirmation."""
        # Check if download URL exists
        if not hasattr(self, 'download_url'):
            messagebox.showerror("Error", "No update available.")
            return

        # Prompt user to confirm update
        update_type = "pre-release" if getattr(self, 'is_prerelease', False) else "stable release"
        response = messagebox.askyesno("Update Available", f"A new {update_type} is available. Are you ready to update?")
        if response:
            messagebox.showinfo("Updating", "Downloading update in background. You will be notified when the update is complete.")
            # Start update in a separate thread
            threading.Thread(target=self.download_and_update, args=(self.download_url,)).start()

    def download_and_update(self, download_url):
        """Download the new executable, create a .bat file to update and notify."""
        try:
            logger.info(f"Downloading update from {download_url}")
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            # Define paths for current and temporary executables
            current_exe = sys.executable
            exe_name = os.path.basename(current_exe)
            temp_exe = os.path.join(ConfigManager.UPDATE_DIRECTORY, "new_VioletWing.exe")
            bat_file = os.path.join(ConfigManager.UPDATE_DIRECTORY, "update.bat")
            
            # Download the new executable
            with open(temp_exe, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info("Update downloaded successfully")
            
            # Create a batch file to handle the update process
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
            
            # Execute the batch file and close the application
            subprocess.Popen(bat_file, shell=True)
            self.root.quit()
        except Exception as e:
            logger.error(f"Failed to update: {e}")
            messagebox.showerror("Update Error", f"Failed to update: {str(e)}")

    def create_main_content(self):
        """Create the main content area with modern layout."""
        # Main container for content and sidebar
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        main_container.grid_columnconfigure(1, weight=1)
        main_container.grid_rowconfigure(0, weight=1)
        
        # Create sidebar navigation
        self.create_sidebar(main_container)
        
        # Content area frame
        self.content_frame = ctk.CTkFrame(
            main_container,
            corner_radius=0,
            fg_color=("#f8fafc", "#161b22")
        )
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        
        # Frames for each tab
        self.dashboard_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.general_settings_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.trigger_settings_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.overlay_settings_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.additional_settings_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.logs_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.faq_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.notifications_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        self.supporters_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")

        # Populate tab frames once during initialization
        self.populate_dashboard()
        self.populate_general_settings()
        self.populate_trigger_settings()
        self.populate_overlay_settings()
        self.populate_additional_settings()
        self.populate_logs()
        self.populate_faq()
        self.populate_notifications()
        self.populate_supporters()
        
        # Show dashboard as the default view
        self.dashboard_frame.pack(fill="both", expand=True)
        self.current_view = "dashboard"

    def create_sidebar(self, parent):
        """Create modern sidebar navigation."""
        # Sidebar frame with fixed width
        sidebar = ctk.CTkFrame(
            parent,
            width=280,
            corner_radius=0,
            fg_color=("#ffffff", "#0d1117")
        )
        sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        sidebar.grid_propagate(False)
        
        # Navigation items with icons and labels
        nav_items = [
            ("Dashboard", "dashboard", "🏠"),
            ("General Settings", "general_settings", "⚙️"),
            ("Trigger Settings", "trigger_settings", "🔫"),
            ("Overlay Settings", "overlay_settings", "🌍"),
            ("Additional Settings", "additional_settings", "⚡"),
            ("Logs", "logs", "📋"),
            ("FAQ", "faq", "❓"),
            ("Notifications", "notifications", "🔔"),
            ("Supporters", "supporters", "🤝")
        ]
        
        # Dictionary to store navigation buttons
        self.nav_buttons = {}
        
        # Add padding at the top of the sidebar
        ctk.CTkFrame(sidebar, height=30, fg_color="transparent").pack(fill="x")
        
        # Create navigation buttons
        for name, key, icon in nav_items:
            btn = ctk.CTkButton(
                sidebar,
                text=f"{icon}  {name}",
                command=lambda k=key: self.switch_view(k),
                width=240,
                height=50,
                corner_radius=12,
                fg_color="transparent",
                hover_color=("#e5e7eb", "#21262d"),
                text_color=("#374151", "#d1d5db"),
                font=("Chivo", 16),
                anchor="w"
            )
            btn.pack(pady=(0, 8), padx=20, fill="x")
            self.nav_buttons[key] = btn
        
        # Set the dashboard button as active by default
        self.set_active_nav("dashboard")

    def set_active_nav(self, active_key):
        """Set the active navigation button with visual feedback."""
        for key, btn in self.nav_buttons.items():
            if key == active_key:
                # Highlight the active button
                btn.configure(
                    fg_color=("#D5006D", "#D5006D"),
                    text_color="#ffffff"
                )
            else:
                # Reset inactive buttons to default style
                btn.configure(
                    fg_color="transparent",
                    text_color=("#374151", "#d1d5db")
                )

    def switch_view(self, view_key):
        """Switch between different views by showing the appropriate frame."""
        # Avoid redundant switches
        if self.current_view == view_key:
            return
        self.current_view = view_key
        self.set_active_nav(view_key)
        
        # Hide all frames
        self.dashboard_frame.pack_forget()
        self.general_settings_frame.pack_forget()
        self.trigger_settings_frame.pack_forget()
        self.overlay_settings_frame.pack_forget()
        self.additional_settings_frame.pack_forget()
        self.logs_frame.pack_forget()
        self.faq_frame.pack_forget()
        self.notifications_frame.pack_forget()
        self.supporters_frame.pack_forget()
        
        # Show the selected frame and update if necessary
        if view_key == "dashboard":
            self.dashboard_frame.pack(fill="both", expand=True)
        elif view_key == "general_settings":
            self.general_settings_frame.pack(fill="both", expand=True)
        elif view_key == "trigger_settings":
            self.trigger_settings_frame.pack(fill="both", expand=True)
        elif view_key == "overlay_settings":
            self.overlay_settings_frame.pack(fill="both", expand=True)
        elif view_key == "additional_settings":
            self.additional_settings_frame.pack(fill="both", expand=True)
        elif view_key == "logs":
            self.logs_frame.pack(fill="both", expand=True)
        elif view_key == "faq":
            self.faq_frame.pack(fill="both", expand=True)
        elif view_key == "notifications":
            self.notifications_frame.pack(fill="both", expand=True)
        elif view_key == "supporters":
            self.supporters_frame.pack(fill="both", expand=True)

    def populate_dashboard(self):
        """Populate the dashboard frame with controls and stats."""
        populate_dashboard(self, self.dashboard_frame)

    def populate_general_settings(self):
        """Populate the general settings frame with configuration options."""
        populate_general_settings(self, self.general_settings_frame)

    def populate_trigger_settings(self):
        """Populate the trigger settings frame with configuration options."""
        populate_trigger_settings(self, self.trigger_settings_frame)

    def populate_overlay_settings(self):
        """Populate the overlay settings frame with configuration options."""
        populate_overlay_settings(self, self.overlay_settings_frame)

    def populate_additional_settings(self):
        """Populate the additional settings frame with configuration options for Bunnyhop and NoFlash."""
        populate_additional_settings(self, self.additional_settings_frame)

    def populate_logs(self):
        """Populate the logs frame with log display."""
        populate_logs(self, self.logs_frame)

    def populate_faq(self):
        """Populate the FAQ frame with questions and answers."""
        populate_faq(self, self.faq_frame)
    
    def populate_notifications(self):
        """Populate the notifications frame with notification settings."""
        populate_notifications(self, self.notifications_frame)

    def populate_supporters(self):
        """Populate the supporters frame with supporter data."""
        populate_supporters(self, self.supporters_frame)

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

        # Define features to start
        features = [
            ("TriggerBot", "Trigger", self.triggerbot),
            ("Overlay", "Overlay", self.overlay),
            ("Bunnyhop", "Bunnyhop", self.bunnyhop),
            ("NoFlash", "Noflash", self.noflash)
        ]

        # Start features based on General settings
        for feature_name, config_key, feature_obj in features:
            if config["General"][config_key]:
                # Check if feature is not already running
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

        # Define features to stop
        features = [
            ("TriggerBot", self.triggerbot),
            ("Overlay", self.overlay),
            ("Bunnyhop", self.bunnyhop),
            ("NoFlash", self.noflash)
        ]

        # Stop all features
        for feature_name, feature_obj in features:
            if self._stop_feature(feature_name, feature_obj):
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
            old_config = ConfigManager.load_config().copy()
            self.update_config_from_ui()
            new_config = self.triggerbot.config
            ConfigManager.save_config(new_config, log_info=False)

            # Define features and their threads
            features = {
                "Trigger": (self.triggerbot, "TriggerBot"),
                "Overlay": (self.overlay, "Overlay"),
                "Bunnyhop": (self.bunnyhop, "Bunnyhop"),
                "Noflash": (self.noflash, "NoFlash")
            }

            any_feature_running = False

            # Handle enabling/disabling and config updates
            for feature_key, (feature_obj, feature_name) in features.items():
                old_enabled = old_config["General"].get(feature_key, False)
                new_enabled = new_config["General"].get(feature_key, False)
                is_running = getattr(feature_obj, 'is_running', False)

                # Handle state changes only if game is running
                if old_enabled != new_enabled:
                    if new_enabled and not is_running:
                        # Only try to start if game is running
                        if Utility.is_game_running():
                            # Initialize memory manager if not already done
                            if not self.memory_manager.initialize():
                                logger.error(f"Failed to initialize memory manager for {feature_name}")
                                continue
                            self._start_feature(feature_name, feature_obj, new_config)
                        else:
                            logger.warning(f"Cannot start {feature_name}: Game is not running")
                    elif not new_enabled and is_running:
                        self._stop_feature(feature_name, feature_obj)
                
                # Update config for running features
                if is_running:
                    feature_obj.update_config(new_config)
                    logger.debug(f"Configuration updated for {feature_name}.")
                    any_feature_running = True

            # Update UI status
            self.update_client_status("Active" if any_feature_running else "Inactive", 
                                    "#22c55e" if any_feature_running else "#ef4444")

            if show_message:
                messagebox.showinfo("Settings Saved", "Configuration has been saved successfully.")
        except ValueError as e:
            logger.error(f"Invalid input: {e}")
            messagebox.showerror("Invalid Input", str(e))
        except Exception as e:
            logger.error(f"Unexpected error during save_settings: {e}")
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")

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

        # Helper to check if config section has changed
        def config_changed(section):
            return old_config.get(section, {}) != new_config.get(section, {})

        # Define features with their classes and config sections
        features = [
            ("TriggerBot", self.triggerbot, "CS2TriggerBot", "Trigger"),
            ("Overlay", self.overlay, "CS2Overlay", "Overlay"), 
            ("Bunnyhop", self.bunnyhop, "CS2Bunnyhop", "Bunnyhop"),
            ("NoFlash", self.noflash, "CS2NoFlash", "Noflash")
        ]

        # Restart features if their config changed and they're running
        for feature_name, feature_obj, class_name, config_section in features:
            if (hasattr(feature_obj, 'is_running') and feature_obj.is_running and 
                (config_changed(config_section) or config_changed("General"))):
                
                # Get the actual class from globals or import it
                feature_class = globals().get(class_name)
                if feature_class and self._restart_feature(feature_name, feature_obj, feature_class, config_section, new_config):
                    any_feature_running = True

        # Update UI status
        if any_feature_running:
            self.update_client_status("Active", "#22c55e")
        else:
            self.update_client_status("Inactive", "#ef4444")

    def update_config_from_ui(self):
        """Update the configuration from the UI elements."""
        # Update General settings
        general_settings = self.triggerbot.config["General"]
        if hasattr(self, 'trigger_var'):
            general_settings["Trigger"] = self.trigger_var.get()
        if hasattr(self, 'overlay_var'):
            general_settings["Overlay"] = self.overlay_var.get()
        if hasattr(self, 'bunnyhop_var'):
            general_settings["Bunnyhop"] = self.bunnyhop_var.get()
        if hasattr(self, 'noflash_var'):
            general_settings["Noflash"] = self.noflash_var.get()

        # Update Trigger settings
        trigger_settings = self.triggerbot.config["Trigger"]
        if hasattr(self, 'trigger_key_entry'):
            trigger_settings["TriggerKey"] = self.trigger_key_entry.get().strip()
        if hasattr(self, 'toggle_mode_var'):
            trigger_settings["ToggleMode"] = self.toggle_mode_var.get()
        if hasattr(self, 'attack_teammates_var'):
            trigger_settings["AttackOnTeammates"] = self.attack_teammates_var.get()
        if hasattr(self, 'min_delay_entry'):
            try:
                trigger_settings["ShotDelayMin"] = float(self.min_delay_entry.get())
            except ValueError:
                pass
        if hasattr(self, 'max_delay_entry'):
            try:
                trigger_settings["ShotDelayMax"] = float(self.max_delay_entry.get())
            except ValueError:
                pass
        if hasattr(self, 'post_shot_delay_entry'):
            try:
                trigger_settings["PostShotDelay"] = float(self.post_shot_delay_entry.get())
            except ValueError:
                pass
        
        if hasattr(self, 'active_weapon_type'):
            weapon_type = self.active_weapon_type.get()
            trigger_settings['active_weapon_type'] = weapon_type
            weapon_settings = trigger_settings['WeaponSettings'].get(weapon_type, {})
            
            if hasattr(self, 'min_delay_entry'): weapon_settings['ShotDelayMin'] = float(self.min_delay_entry.get())
            if hasattr(self, 'max_delay_entry'): weapon_settings['ShotDelayMax'] = float(self.max_delay_entry.get())
            if hasattr(self, 'post_shot_delay_entry'): weapon_settings['PostShotDelay'] = float(self.post_shot_delay_entry.get())
            
            trigger_settings['WeaponSettings'][weapon_type] = weapon_settings

        # Update Overlay settings
        overlay_settings = self.overlay.config["Overlay"]
        if hasattr(self, 'enable_box_var'):
            overlay_settings["enable_box"] = self.enable_box_var.get()
        if hasattr(self, 'enable_skeleton_var'):
            overlay_settings["enable_skeleton"] = self.enable_skeleton_var.get()
        if hasattr(self, 'box_line_thickness_slider'):
            overlay_settings["box_line_thickness"] = self.box_line_thickness_slider.get()
        if hasattr(self, 'box_color_hex_combo'):
            overlay_settings["box_color_hex"] = COLOR_CHOICES.get(self.box_color_hex_combo.get(), "#FFA500")
        if hasattr(self, 'draw_snaplines_var'):
            overlay_settings["draw_snaplines"] = self.draw_snaplines_var.get()
        if hasattr(self, 'snaplines_color_hex_combo'):
            overlay_settings["snaplines_color_hex"] = COLOR_CHOICES.get(self.snaplines_color_hex_combo.get(), "#FFFFFF")
        if hasattr(self, 'text_color_hex_combo'):
            overlay_settings["text_color_hex"] = COLOR_CHOICES.get(self.text_color_hex_combo.get(), "#FFFFFF")
        if hasattr(self, 'draw_health_numbers_var'):
            overlay_settings["draw_health_numbers"] = self.draw_health_numbers_var.get()
        if hasattr(self, 'draw_nicknames_var'):
            overlay_settings["draw_nicknames"] = self.draw_nicknames_var.get()
        if hasattr(self, 'use_transliteration_var'):
            overlay_settings["use_transliteration"] = self.use_transliteration_var.get()
        if hasattr(self, 'draw_teammates_var'):
            overlay_settings["draw_teammates"] = self.draw_teammates_var.get()
        if hasattr(self, 'teammate_color_hex_combo'):
            overlay_settings["teammate_color_hex"] = COLOR_CHOICES.get(self.teammate_color_hex_combo.get(), "#00FFFF")
        if hasattr(self, 'target_fps_slider'):
            overlay_settings["target_fps"] = self.target_fps_slider.get()

        # Update Bunnyhop settings
        bunnyhop_settings = self.bunnyhop.config.get("Bunnyhop", {})
        if hasattr(self, 'jump_key_entry'):
            bunnyhop_settings["JumpKey"] = self.jump_key_entry.get().strip()
        if hasattr(self, 'jump_delay_entry'):
            try:
                bunnyhop_settings["JumpDelay"] = float(self.jump_delay_entry.get())
            except ValueError:
                pass

        # Update NoFlash settings
        noflash_settings = self.noflash.config.get("NoFlash", {})
        if hasattr(self, 'FlashSuppressionStrength_slider'):
            noflash_settings["FlashSuppressionStrength"] = self.FlashSuppressionStrength_slider.get()

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
        """Update the UI elements from the configuration."""
        # Update General settings UI
        general_settings = self.triggerbot.config["General"]
        if hasattr(self, 'trigger_var'):
            self.trigger_var.set(general_settings["Trigger"])
        if hasattr(self, 'overlay_var'):
            self.overlay_var.set(general_settings["Overlay"])
        if hasattr(self, 'bunnyhop_var'):
            self.bunnyhop_var.set(general_settings["Bunnyhop"])
        if hasattr(self, 'noflash_var'):
            self.noflash_var.set(general_settings["Noflash"])

        # Update Trigger settings UI
        trigger_settings = self.triggerbot.config["Trigger"]
        if hasattr(self, 'trigger_key_entry'):
            self.trigger_key_entry.delete(0, "end")
            self.trigger_key_entry.insert(0, trigger_settings["TriggerKey"])
        if hasattr(self, 'toggle_mode_var'):
            self.toggle_mode_var.set(trigger_settings["ToggleMode"])
        if hasattr(self, 'attack_teammates_var'):
            self.attack_teammates_var.set(trigger_settings["AttackOnTeammates"])

        if hasattr(self, 'active_weapon_type'):
            self.active_weapon_type.set(trigger_settings.get('active_weapon_type', 'Rifles'))
            self.update_weapon_settings_display()

        # Update Overlay settings UI
        overlay_settings = self.overlay.config["Overlay"]
        if hasattr(self, 'enable_box_var'):
            self.enable_box_var.set(overlay_settings["enable_box"])
        if hasattr(self, 'enable_skeleton_var'):
            self.enable_skeleton_var.set(overlay_settings.get("enable_skeleton", True))
        if hasattr(self, 'box_line_thickness_slider'):
            self.box_line_thickness_slider.set(overlay_settings["box_line_thickness"])
            if hasattr(self, 'box_line_thickness_value_label'):
                self.box_line_thickness_value_label.configure(text=f"{overlay_settings['box_line_thickness']:.1f}")
        if hasattr(self, 'box_color_hex_combo'):
            self.box_color_hex_combo.set(Utility.get_color_name_from_hex(overlay_settings["box_color_hex"]))
        if hasattr(self, 'draw_snaplines_var'):
            self.draw_snaplines_var.set(overlay_settings["draw_snaplines"])
        if hasattr(self, 'snaplines_color_hex_combo'):
            self.snaplines_color_hex_combo.set(Utility.get_color_name_from_hex(overlay_settings["snaplines_color_hex"]))
        if hasattr(self, 'text_color_hex_combo'):
            self.text_color_hex_combo.set(Utility.get_color_name_from_hex(overlay_settings["text_color_hex"]))
        if hasattr(self, 'draw_health_numbers_var'):
            self.draw_health_numbers_var.set(overlay_settings["draw_health_numbers"])
        if hasattr(self, 'draw_nicknames_var'):
            self.draw_nicknames_var.set(overlay_settings["draw_nicknames"])
        if hasattr(self, 'use_transliteration_var'):
            self.use_transliteration_var.set(overlay_settings["use_transliteration"])
        if hasattr(self, 'draw_teammates_var'):
            self.draw_teammates_var.set(overlay_settings["draw_teammates"])
        if hasattr(self, 'teammate_color_hex_combo'):
            self.teammate_color_hex_combo.set(Utility.get_color_name_from_hex(overlay_settings["teammate_color_hex"]))
        if hasattr(self, 'target_fps_slider'):
            self.target_fps_slider.set(overlay_settings["target_fps"])
            if hasattr(self, 'target_fps_value_label'):
                self.target_fps_value_label.configure(text=f"{overlay_settings['target_fps']:.0f}")

        # Update Bunnyhop settings UI
        bunnyhop_settings = self.bunnyhop.config.get("Bunnyhop", {})
        if hasattr(self, 'jump_key_entry'):
            self.jump_key_entry.delete(0, "end")
            self.jump_key_entry.insert(0, bunnyhop_settings.get("JumpKey", "space"))
        if hasattr(self, 'jump_delay_entry'):
            self.jump_delay_entry.delete(0, "end")
            self.jump_delay_entry.insert(0, str(bunnyhop_settings.get("JumpDelay", 0.01)))

        # Update NoFlash settings UI
        noflash_settings = self.noflash.config.get("NoFlash", {})
        if hasattr(self, 'FlashSuppressionStrength_slider'):
            self.FlashSuppressionStrength_slider.set(noflash_settings.get("FlashSuppressionStrength", 0.0))
            if hasattr(self, 'FlashSuppressionStrength_value_label'):
                self.FlashSuppressionStrength_value_label.configure(text=f"{noflash_settings.get('FlashSuppressionStrength', 0.0):.2f}")

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