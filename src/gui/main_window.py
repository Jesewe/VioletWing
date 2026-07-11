import copy
import os
import platform
import queue
import re
import threading
import time
import webbrowser

import customtkinter as ctk
from PIL import Image
from tkinter import messagebox
from watchdog.observers import Observer

from src.utils.updater import Updater
from src.utils.utility import Utility
from src.features.trigger_bot import CS2TriggerBot
from src.features.esp import CS2Overlay
from src.features.bunnyhop import CS2Bunnyhop
from src.features.noflash import CS2NoFlash
from src.utils.config_manager import ConfigManager
import src.utils.profile_manager as ProfileManager
from src.utils.file_watcher import ConfigFileChangeHandler
from src.utils.logger import Logger
from src.core.memory_manager import MemoryManager
from src.core.client_manager import ClientManager
from src.core.offset_fetcher import fetch_offsets
from src.features import ghost_manager as _gm

from src.gui.changelog_window import show_changelog_if_new
from src.gui.modal import AppModal
from src.gui.icon_loader import load_icon, ASSETS_DIR
from src.gui.ui_config_bridge import UIConfigBridge
from src.gui.home_tab import populate_dashboard
from src.gui.general_settings_tab import populate_general_settings
from src.gui.trigger_settings_tab import populate_trigger_settings
from src.gui.overlay_settings_tab import populate_overlay_settings
from src.gui.additional_settings_tab import populate_additional_settings
from src.gui.logs_tab import populate_logs, _LEVEL_LINE_RE
from src.gui.faq_tab import populate_faq
from src.gui.notifications_tab import populate_notifications
from src.gui.supporters_tab import populate_supporters
from src.gui.theme import (
    FONT_FAMILY_BOLD, FONT_FAMILY_REGULAR, FONT_SIZE_H2, FONT_SIZE_H4, FONT_SIZE_P,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_BACKGROUND,
    COLOR_ACCENT_FG, COLOR_HEADER_BG, COLOR_SIDEBAR_BG, COLOR_SIDEBAR_ACTIVE_BG,
    COLOR_SIDEBAR_INDICATOR, COLOR_VIOLET_SUBTLE,
    BUTTON_STYLE_PRIMARY, BUTTON_STYLE_DANGER,
)

logger = Logger.get_logger(__name__)

class MainWindow:
    def __init__(self) -> None:
        self.repo_url = "github.com/Jesewe/VioletWing"

        # Thread handles
        self.trigger_thread = None
        self.overlay_thread = None
        self.bunnyhop_thread = None
        self.noflash_thread = None
        self.observer = None
        self._suppress_watcher = False
        self.ui_queue: queue.SimpleQueue = queue.SimpleQueue()
        self.log_timer = None
        self._log_file_pos = 0
        self._active_log_file: str = Logger.LOG_FILE()

        # Log buffer: each element is one logical entry (may span multiple lines).
        # The widget is a read-only view of this buffer filtered by level + search.
        self._log_lines: list[str] = []
        self._log_filter_level: str = "ALL"
        self._log_search_term: str = ""
        self._log_filter_chips: dict = {}
        self._search_debounce: str | None = None

        # Stop events for dashboard network threads - set in cleanup()
        self._fetch_update_stop: threading.Event | None = None
        self._fetch_patch_stop: threading.Event | None = None
        self._process_monitor_timer: str | None = None

        # Tracks the last successfully loaded profile name; cleared on manual save.
        self.active_profile_name: str | None = None

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.root = ctk.CTk()

        self.offsets, self.client_data, self.buttons_data = {}, {}, {}
        self._offsets_fetching: bool = False
        self.memory_manager = MemoryManager(self.offsets, self.client_data, self.buttons_data)
        self.initialize_features()

        # The setup_disguise function will handle executable cloning if enabled
        self.ghost = _gm.setup_disguise()

        # Single unified widget registry - overlay tab migrated to use this too.
        self.ui_bridge = UIConfigBridge()

        # Set title dynamically based on active ghost
        title = self.ghost["name"] if self.ghost else "VioletWing"
        self.root.title(title)
        self.root.resizable(True, True)
        self.root.minsize(1400, 800)
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 700
        y = (self.root.winfo_screenheight() // 2) - 400
        self.root.geometry(f"1400x800+{x}+{y}")

        # Set taskbar/titlebar icon
        icon_path = Utility.resource_path(f"{ASSETS_DIR}/icon.ico")
        if self.ghost and "icon" in self.ghost:
            ghost_icon = Utility.resource_path(self.ghost["icon"])
            if os.path.exists(ghost_icon):
                icon_path = ghost_icon
            else:
                logger.warning("Ghost icon not found at %s. Falling back to default.", ghost_icon)

        try:
            self.root.iconbitmap(icon_path)
        except Exception as exc:
            logger.warning("Failed to set window icon: %s", exc)

        if platform.system() == "Windows":
            import ctypes
            
            # Detach the taskbar icon from the executable's embedded icon
            app_id = f'VioletWing.Ghost.{self.ghost["id"]}' if self.ghost else 'VioletWing.App.Main'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            
            gdi32 = ctypes.WinDLL("gdi32")
            for font in [
                "assets/fonts/Outfit-Regular.ttf", "assets/fonts/Outfit-Bold.ttf",
                "assets/fonts/JetBrainsMono-Regular.ttf", "assets/fonts/JetBrainsMono-Bold.ttf",
            ]:
                path = Utility.resource_path(font)
                if os.path.exists(path):
                    gdi32.AddFontResourceW(path)
                else:
                    logger.warning("Font not found: %s", path)

        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        self.updater = Updater(self)
        self.setup_ui()
        self.init_config_watcher()
        self.start_log_timer()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.client_manager = ClientManager(self)

        # Kick off GitHub release fetch after mainloop is running so the
        # UI is fully visible before the modal changelog window appears.
        self.root.after(0, self._start_release_fetch)

    def initialize_features(self) -> None:
        try:
            self.triggerbot = CS2TriggerBot(self.memory_manager)
            self.overlay    = CS2Overlay(self.memory_manager)
            self.bunnyhop   = CS2Bunnyhop(self.memory_manager)
            self.noflash    = CS2NoFlash(self.memory_manager)
            self.features = {
                "Trigger":  {"name": "TriggerBot", "instance": self.triggerbot, "class": CS2TriggerBot},
                "Overlay":  {"name": "Overlay",    "instance": self.overlay,    "class": CS2Overlay},
                "Bunnyhop": {"name": "Bunnyhop",   "instance": self.bunnyhop,   "class": CS2Bunnyhop},
                "Noflash":  {"name": "Noflash",    "instance": self.noflash,    "class": CS2NoFlash},
            }
            logger.info("All features initialised.")
        except Exception:
            logger.exception("Failed to initialise features.")
            AppModal.error(self.root, "Initialisation Error",
                           "Failed to initialise features. Check logs.")

    def setup_ui(self) -> None:
        self.create_modern_header()
        self.create_main_content()
        self.create_toast_notification()

    def create_modern_header(self) -> None:
        hc = ctk.CTkFrame(self.root, height=80, corner_radius=0, fg_color=COLOR_HEADER_BG)
        hc.grid(row=0, column=0, sticky="ew")
        hc.grid_propagate(False)
        hc.grid_columnconfigure(1, weight=1)
        self.create_header_left(hc)
        self.create_header_right(hc)

    def create_header_left(self, parent) -> None:
        lf = ctk.CTkFrame(parent, fg_color="transparent")
        lf.grid(row=0, column=0, sticky="w", padx=30, pady=15)
        tf = ctk.CTkFrame(lf, fg_color="transparent")
        tf.pack(side="left")
        
        # Display the disguised name in the header, or default to VioletWing.
        header_text = self.ghost["name"] if self.ghost else "VioletWing"
        ctk.CTkLabel(tf, text=header_text, font=(FONT_FAMILY_BOLD[0], FONT_SIZE_H2, "bold"),
                     text_color="#f0ebff").pack(side="left")
        badge = ctk.CTkFrame(lf, fg_color=COLOR_VIOLET_SUBTLE, corner_radius=8, height=26)
        badge.pack(side="left", padx=(15, 0))
        ctk.CTkLabel(badge, text=ConfigManager.VERSION,
                     font=(FONT_FAMILY_BOLD[0], 12, "bold"),
                     text_color="#a78bfa", padx=10, pady=3).pack()

    def create_header_right(self, parent) -> None:
        rf = ctk.CTkFrame(parent, fg_color="transparent")
        rf.grid(row=0, column=2, sticky="e", padx=30, pady=15)
        self.create_status_indicator(rf)
        sf = self.create_social_buttons(rf)
        # Store so _on_release_fetched can attach the update button later.
        self._header_buttons_frame = sf

    def create_status_indicator(self, parent) -> None:
        self.status_frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.status_frame.pack(side="right", padx=(20, 0))
        self.status_dot = ctk.CTkFrame(self.status_frame, width=12, height=12,
                                       corner_radius=6, fg_color="#ef4444")
        self.status_dot.pack(side="left", pady=(0, 2))
        self.status_label = ctk.CTkLabel(
            self.status_frame, text="Inactive",
            font=(FONT_FAMILY_BOLD[0], FONT_SIZE_H4, "bold"),
            text_color=BUTTON_STYLE_DANGER["fg_color"][0])
        self.status_label.pack(side="left", padx=(8, 0))
        # The toast notification has been moved to a floating frame via create_toast_notification()
        self._saved_toast_timer = None

    def create_social_buttons(self, parent) -> ctk.CTkFrame:
        sf = ctk.CTkFrame(parent, fg_color="transparent")
        sf.pack(side="right")
        socials = [
            ("GitHub",   "github_icon.png",    "https://github.com/Jesewe/VioletWing"),
            ("Telegram", "telegram_icon.png",  "https://t.me/cs2_jesewe"),
            ("Website",  "book_open_icon.png", "https://violetwing.vercel.app/"),
        ]
        for i, (text, icon_file, url) in enumerate(socials):
            ci = load_icon(icon_file)
            ctk.CTkButton(
                sf, text=text, image=ci, compound="left",
                command=lambda u=url: webbrowser.open(u),
                height=36, corner_radius=10, fg_color="transparent",
                hover_color=COLOR_SIDEBAR_ACTIVE_BG,
                border_width=1, border_color=("#c4b5fd", "#3d2a6e"),
                text_color=("#7c3aed", "#a78bfa"),
                font=(FONT_FAMILY_BOLD[0], FONT_SIZE_P, "bold"),
            ).pack(side="left", padx=(0, 8) if i < len(socials) - 1 else (0, 0))
        return sf

    def create_toast_notification(self) -> None:
        """Create the floating bottom-right toast notification frame."""
        self._toast_frame = ctk.CTkFrame(
            self.root,
            corner_radius=12,
            bg_color=COLOR_BACKGROUND,
            fg_color=("#f5f3ff", "#1c1433"),
            border_width=1,
            border_color=("#c4b5fd", "#3d2a6e")
        )
        # Content container
        content = ctk.CTkFrame(self._toast_frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=15)
        
        self._toast_icon_label = ctk.CTkLabel(content, text="", width=18)
        self._toast_icon_label.pack(side="left", padx=(0, 10))
            
        self._toast_text_label = ctk.CTkLabel(
            content,
            text="Settings Saved",
            font=(FONT_FAMILY_BOLD[0], FONT_SIZE_P, "bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        self._toast_text_label.pack(side="left")
        self._toast_animation_timer = None

    def show_saved_toast(self, message: str = "Settings Saved", is_error: bool = False) -> None:
        """Slide the floating toast into view."""
        if self._saved_toast_timer is not None:
            self.root.after_cancel(self._saved_toast_timer)
        if hasattr(self, "_toast_animation_timer") and self._toast_animation_timer is not None:
            self.root.after_cancel(self._toast_animation_timer)
            
        # Update styling based on state
        from src.gui.theme import COLOR_WIDGET_ERROR_BORDER, COLOR_TEXT_ERROR
        icon_file = "xmark_icon.png" if is_error else "check_icon.png"
        icon = load_icon(icon_file, size=(18, 18))
        if icon:
            self._toast_icon_label.configure(image=icon)
            self._toast_icon_label.image = icon
            
        self._toast_text_label.configure(
            text=message, 
            text_color=COLOR_TEXT_ERROR if is_error else COLOR_TEXT_PRIMARY
        )
        
        self._toast_frame.configure(
            border_color=COLOR_WIDGET_ERROR_BORDER if is_error else ("#c4b5fd", "#3d2a6e")
        )
        
        # Start animation from right side (off-screen)
        start_x = 400
        end_x = -40
        self._toast_frame.place(relx=1.0, rely=1.0, anchor="se", x=start_x, y=-40)
        
        def animate_in(current_x):
            if current_x > end_x:
                new_x = max(end_x, current_x - max(1, int((current_x - end_x) * 0.2)))
                self._toast_frame.place(relx=1.0, rely=1.0, anchor="se", x=new_x, y=-40)
                self._toast_animation_timer = self.root.after(16, animate_in, new_x)
            else:
                self._saved_toast_timer = self.root.after(3500 if is_error else 2500, animate_out_start)

        def animate_out_start():
            animate_out(end_x)

        def animate_out(current_x):
            if current_x < start_x:
                new_x = current_x + max(1, int((start_x - current_x) * 0.2))
                self._toast_frame.place(relx=1.0, rely=1.0, anchor="se", x=new_x, y=-40)
                self._toast_animation_timer = self.root.after(16, animate_out, new_x)
            else:
                self._toast_frame.place_forget()
                
        animate_in(start_x)

    def create_update_button(self, parent, is_prerelease: bool) -> None:
        """Attach the update button to parent. Called from _on_release_fetched on the UI thread."""
        ci = load_icon("update_icon.png")
        ctk.CTkButton(
            parent,
            text="Pre-release Available!" if is_prerelease else "Update Available!",
            image=ci, compound="left",
            command=self.updater.handle_update,
            height=36, corner_radius=10,
            fg_color="#f59e0b" if is_prerelease else "#ef4444",
            hover_color="#d97706" if is_prerelease else "#dc2626",
            border_width=0, text_color="#ffffff",
            font=(FONT_FAMILY_BOLD[0], FONT_SIZE_P, "bold"),
        ).pack(side="left", padx=(8, 0))

    def _start_release_fetch(self) -> None:
        self._start_ui_queue_drain()
        self.updater.fetch_in_background(self._on_release_fetched)

    def _start_ui_queue_drain(self) -> None:
        def _drain():
            try:
                while True:
                    fn = self.ui_queue.get_nowait()
                    try:
                        fn()
                    except Exception:
                        logger.exception("ui_queue callback raised")
            except queue.Empty:
                pass
            self.root.after(10, _drain)
        self.root.after(10, _drain)

    def ui_queue_put(self, fn) -> None:
        """Submit a zero-argument callable to run on the main thread. Thread-safe."""
        self.ui_queue.put(fn)

    def _on_release_fetched(self, has_update: bool, release: "dict | None") -> None:
        if has_update:
            self.create_update_button(self._header_buttons_frame, self.updater.is_prerelease)
        show_changelog_if_new(self.root, self.updater)

    def create_main_content(self) -> None:
        mc = ctk.CTkFrame(self.root, fg_color="transparent")
        mc.grid(row=1, column=0, sticky="nsew")
        mc.grid_columnconfigure(1, weight=1)
        mc.grid_rowconfigure(0, weight=1)

        self.create_sidebar(mc)

        self.content_frame = ctk.CTkFrame(mc, corner_radius=0, fg_color=COLOR_BACKGROUND)
        self.content_frame.grid(row=0, column=1, sticky="nsew")

        self.tab_views = {
            "dashboard":           self.populate_dashboard,
            "general_settings":    self.populate_general_settings,
            "trigger_settings":    self.populate_trigger_settings,
            "overlay_settings":    self.populate_overlay_settings,
            "additional_settings": self.populate_additional_settings,
            "logs":                self.populate_logs,
            "faq":                 self.populate_faq,
            "notifications":       self.populate_notifications,
            "supporters":          self.populate_supporters,
        }
        self.tab_frames: dict[str, ctk.CTkFrame] = {}
        for key, fn in self.tab_views.items():
            frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
            self.tab_frames[key] = frame
            fn(frame)

        self.current_view = None
        self.switch_view("dashboard")

    def create_sidebar(self, parent) -> None:
        sidebar = ctk.CTkFrame(parent, width=280, corner_radius=0, fg_color=COLOR_SIDEBAR_BG)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # section_label=None → no header for that group (Dashboard stands alone)
        nav_items = [
            (None,       "Dashboard",           "dashboard",           "charts_icon.png"),
            ("SETTINGS", "General Settings",    "general_settings",    "gear_icon.png"),
            (None,       "Trigger Settings",    "trigger_settings",    "crosshairs_icon.png"),
            (None,       "Overlay Settings",    "overlay_settings",    "layer_group_icon.png"),
            (None,       "Additional Settings", "additional_settings", "bolt_icon.png"),
            ("TOOLS",    "Logs",                "logs",                "clipboard_list_icon.png"),
            ("INFO",     "FAQ",                 "faq",                 "circle_question_icon.png"),
            (None,       "Notifications",       "notifications",       "bell_icon.png"),
            (None,       "Supporters",          "supporters",          "handshake_icon.png"),
        ]

        ctk.CTkFrame(sidebar, height=1, fg_color=("#c4b5fd", "#2a1d4e")).pack(fill="x")
        ctk.CTkFrame(sidebar, height=20, fg_color="transparent").pack(fill="x")

        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self.nav_indicators: dict[str, ctk.CTkFrame] = {}
        self._nav_images: dict = {}

        for section_label, name, key, icon_file in nav_items:
            if section_label is not None:
                ctk.CTkFrame(sidebar, height=1, fg_color=("#c4b5fd", "#2a1d4e")).pack(
                    fill="x", padx=16, pady=(10, 0)
                )
                ctk.CTkLabel(
                    sidebar,
                    text=section_label,
                    font=(FONT_FAMILY_BOLD[0], 10, "bold"),
                    text_color=COLOR_TEXT_SECONDARY,
                    anchor="w",
                ).pack(fill="x", padx=24, pady=(6, 2))
            ci = load_icon(icon_file)
            self._nav_images[key] = ci

            row = ctk.CTkFrame(sidebar, fg_color="transparent", height=50)
            row.pack(fill="x", padx=0, pady=(0, 4))
            row.pack_propagate(False)

            indicator = ctk.CTkFrame(row, width=3, corner_radius=2, fg_color="transparent")
            indicator.pack(side="left", fill="y", padx=(8, 0))

            btn = ctk.CTkButton(
                row, text=name, image=ci, compound="left",
                command=lambda k=key: self.switch_view(k),
                height=46, corner_radius=10, fg_color="transparent",
                hover_color=COLOR_SIDEBAR_ACTIVE_BG,
                text_color=COLOR_TEXT_SECONDARY,
                font=(FONT_FAMILY_BOLD[0], FONT_SIZE_H4),
                anchor="w",
            )
            btn.pack(side="left", fill="x", expand=True, padx=(6, 12))
            self.nav_buttons[key] = btn
            self.nav_indicators[key] = indicator

        self.set_active_nav("dashboard")

    def set_active_nav(self, active_key: str) -> None:
        for key, btn in self.nav_buttons.items():
            ind = self.nav_indicators[key]
            if key == active_key:
                btn.configure(fg_color=COLOR_SIDEBAR_ACTIVE_BG, text_color=COLOR_TEXT_PRIMARY)
                ind.configure(fg_color=COLOR_SIDEBAR_INDICATOR)
            else:
                btn.configure(fg_color="transparent", text_color=COLOR_TEXT_SECONDARY,
                              hover_color=COLOR_SIDEBAR_ACTIVE_BG)
                ind.configure(fg_color="transparent")

    def switch_view(self, view_key: str) -> None:
        if self.current_view == view_key:
            return
        if self.current_view and self.current_view in self.tab_frames:
            self.tab_frames[self.current_view].pack_forget()
            # Force Tkinter to redraw the exposed area immediately to prevent artifacts
            self.root.update_idletasks()
        self.current_view = view_key
        self.set_active_nav(view_key)
        if view_key in self.tab_frames:
            self.tab_frames[view_key].pack(fill="both", expand=True)

    def populate_dashboard(self, frame):           populate_dashboard(self, frame)
    def populate_general_settings(self, frame):    populate_general_settings(self, frame)
    def populate_trigger_settings(self, frame):    populate_trigger_settings(self, frame)
    def populate_overlay_settings(self, frame):    populate_overlay_settings(self, frame)
    def populate_additional_settings(self, frame): populate_additional_settings(self, frame)
    def populate_logs(self, frame):                populate_logs(self, frame)
    def populate_faq(self, frame):                 populate_faq(self, frame)
    def populate_notifications(self, frame):       populate_notifications(self, frame)
    def populate_supporters(self, frame):          populate_supporters(self, frame)

    def fetch_offsets_async(self, on_success: callable = None) -> None:
        self._offsets_fetching = True

        def _worker():
            try:
                offsets, client, buttons = fetch_offsets()
                if None in (offsets, client, buttons):
                    raise ValueError("fetch_offsets() returned None.")
                self.root.after(0, lambda: self._on_offsets_ready(offsets, client, buttons, on_success))
            except Exception:
                logger.exception("Failed to fetch offsets.")
                self._offsets_fetching = False
                self.root.after(0, self._on_offsets_failed)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_offsets_ready(self, offsets, client_data, buttons_data, on_success: callable = None) -> None:
        self.offsets = self.memory_manager.offsets = offsets
        self.client_data = self.memory_manager.client_data = client_data
        self.buttons_data = self.memory_manager.buttons_data = buttons_data
        self._offsets_fetching = False
        if hasattr(self.memory_manager, "_apply_offsets"):
            self.memory_manager._apply_offsets()
        if hasattr(self, "loading_label"):
            self.loading_label.destroy()
            del self.loading_label
        if on_success is not None:
            on_success()

    def _on_offsets_failed(self) -> None:
        self.update_client_status("Inactive", "#ef4444")
        AppModal.error(self.root, "Offset Error", "Failed to fetch offsets. Check logs.")
        if hasattr(self, "loading_label"):
            self.loading_label.configure(text="Failed to load offsets.", text_color="#ef4444")

    def update_client_status(self, status: str, color: str) -> None:
        self.status_label.configure(text=status, text_color=color)
        self.status_dot.configure(fg_color=color)
        if hasattr(self, "bot_status_label"):
            self.bot_status_label.configure(text=status, text_color=color)

    def start_client(self):
        self.client_manager.start_client()

    def stop_client(self) -> None:
        self.client_manager.stop_client()

    def update_weapon_settings_display(self) -> None:
        weapon_type = self.ui_bridge.get_value("active_weapon_type")
        if weapon_type is None:
            return
        config = ConfigManager.load_config()
        ws = config["Trigger"]["WeaponSettings"].get(weapon_type, {})
        
        for key, default in [("ShotDelayMin", 0.01), ("ShotDelayMax", 0.03), ("PostShotDelay", 0.1)]:
            self.ui_bridge.set_value(key, str(ws.get(key, default)))
            self._flash_widget(key)

    def _flash_widget(self, key: str) -> None:
        if not self.ui_bridge.registered(key):
            return
        entry = self.ui_bridge._registry.get(key)
        if entry is None:
            return
        widget = entry.get("widget")
        if not widget or not hasattr(widget, "configure"):
            return
            
        if not hasattr(widget, "_orig_fg_color"):
            widget._orig_fg_color = widget.cget("fg_color")
            
        widget.configure(fg_color=COLOR_VIOLET_SUBTLE)
        
        if hasattr(widget, "_flash_timer") and widget._flash_timer:
            self.root.after_cancel(widget._flash_timer)
            
        widget._flash_timer = self.root.after(
            400, lambda: widget.configure(fg_color=widget._orig_fg_color)
        )

    def save_settings(self, show_message: bool = False) -> None:
        try:
            self.ui_bridge.clear_errors()
            errors = self._validate_inputs()
            if errors:
                for key, msg in errors.items():
                    self.ui_bridge.set_error(key, msg)
                self.show_saved_toast("Error saving settings", is_error=True)
                return

            config = ConfigManager.load_config()
            old_config = copy.deepcopy(config)
            self._update_config_from_ui(config)
            self._suppress_watcher = True
            try:
                ConfigManager.save_config(config, log_info=False)
            finally:
                self._suppress_watcher = False
            self.client_manager.apply_feature_state_changes(old_config, config)
            self.client_manager.update_running_feature_configs(config)
            self.active_profile_name = None
            self.update_active_profile_label()
            
            if show_message:
                self.show_saved_toast("Configuration saved successfully.")
            else:
                self.show_saved_toast("Settings Saved")
        except Exception:
            logger.exception("Unexpected error while saving settings.")
            self.show_saved_toast("An unexpected error occurred.", is_error=True)

    def _update_config_from_ui(self, config: dict) -> None:
        self._save_general(config)
        self._save_trigger(config)
        self._save_overlay(config)
        self._save_additional(config)

    def _save_general(self, config: dict) -> None:
        s = config["General"]
        for key in ("Trigger", "Overlay", "Bunnyhop", "Noflash", "Disguise", "DetailedLogs"):
            val = self.ui_bridge.get_value(key)
            if val is not None:
                s[key] = val

    def _save_trigger(self, config: dict) -> None:
        s = config["Trigger"]
        for key in ("TriggerKey", "ToggleMode", "AttackOnTeammates"):
            val = self.ui_bridge.get_value(key)
            if val is not None:
                s[key] = val.strip() if key == "TriggerKey" else val
        if self.ui_bridge.registered("active_weapon_type"):
            wt = self.ui_bridge.get_value("active_weapon_type")
            s["active_weapon_type"] = wt
            ws = s["WeaponSettings"].setdefault(wt, {})
            for dk in ("ShotDelayMin", "ShotDelayMax", "PostShotDelay"):
                raw = self.ui_bridge.get_value(dk)
                if raw is not None:
                    try:
                        ws[dk] = float(raw)
                    except ValueError:
                        pass

    def _save_overlay(self, config: dict) -> None:
        s = config["Overlay"]
        checkboxes = (
            "enable_box", "enable_skeleton", "draw_snaplines", "draw_bomb_timer",
            "draw_health_numbers", "draw_armor", "draw_nicknames", "draw_weapon_names", "draw_teammates",
            "draw_scoped", "draw_reloading", "draw_flashed", "draw_defusing",
        )
        for key in checkboxes:
            val = self.ui_bridge.get_value(key)
            if val is not None:
                s[key] = val

        val = self.ui_bridge.get_value("box_line_thickness")
        if val is not None:
            s["box_line_thickness"] = val

        val = self.ui_bridge.get_value("target_fps")
        if val is not None:
            try:
                s["target_fps"] = int(float(val))
            except (ValueError, TypeError):
                pass

        color_defaults = {
            "box_color_hex":       "#FFA500",
            "snaplines_color_hex": "#FFFFFF",
            "text_color_hex":      "#FFFFFF",
            "weapon_color_hex":    "#FFFFFF",
            "teammate_color_hex":  "#00FFFF",
        }
        for key, default in color_defaults.items():
            val = self.ui_bridge.get_value(key)
            if val is not None:
                s[key] = val.upper() if re.match(r'^#[0-9A-Fa-f]{6}$', val) else default
                
        pos = self.ui_bridge.get_value("bomb_timer_position")
        if pos is not None:
            s["bomb_timer_position"] = pos

    def _save_additional(self, config: dict) -> None:
        bh = config.setdefault("Bunnyhop", {})
        jk = self.ui_bridge.get_value("JumpKey")
        if jk is not None:
            bh["JumpKey"] = jk.strip()
        jd = self.ui_bridge.get_value("JumpDelay")
        if jd is not None:
            try:
                bh["JumpDelay"] = float(jd)
            except ValueError:
                pass

        nf = config.setdefault("NoFlash", {})

    def update_ui_from_config(self) -> None:
        config = ConfigManager.load_config()
        with self.ui_bridge.batch_updates(self.root):
            self._load_general(config)
            self._load_trigger(config)
            self._load_overlay(config)
            self._load_additional(config)

    def _load_general(self, config: dict) -> None:
        s = config["General"]
        for key in ("Trigger", "Overlay", "Bunnyhop", "Noflash", "Disguise", "DetailedLogs"):
            self.ui_bridge.set_value(key, s.get(key, False))

    def _load_trigger(self, config: dict) -> None:
        s = config["Trigger"]
        self.ui_bridge.set_value("TriggerKey",         s.get("TriggerKey", "x"))
        self.ui_bridge.set_value("ToggleMode",         s.get("ToggleMode", False))
        self.ui_bridge.set_value("AttackOnTeammates",  s.get("AttackOnTeammates", False))
        if self.ui_bridge.registered("active_weapon_type"):
            self.ui_bridge.set_value("active_weapon_type", s.get("active_weapon_type", "Rifles"))
            self.update_weapon_settings_display()

    def _load_overlay(self, config: dict) -> None:
        s = config["Overlay"]
        checkboxes = (
            "enable_box", "enable_skeleton", "draw_snaplines", "draw_bomb_timer",
            "draw_health_numbers", "draw_armor", "draw_nicknames", "draw_weapon_names", "draw_teammates",
            "draw_scoped", "draw_reloading", "draw_flashed", "draw_defusing",
        )
        for key in checkboxes:
            self.ui_bridge.set_value(key, s.get(key, False))

        for key, fmt in (("box_line_thickness", ".1f"), ("target_fps", ".0f")):
            self.ui_bridge.set_value(key, s.get(key, 0))

        for key in ("box_color_hex", "snaplines_color_hex", "text_color_hex", "weapon_color_hex", "teammate_color_hex"):
            self.ui_bridge.set_value(key, s.get(key, "#FFFFFF").upper())
            
        self.ui_bridge.set_value("bomb_timer_position", s.get("bomb_timer_position", "Center-Left"))

    def _load_additional(self, config: dict) -> None:
        bh = config.get("Bunnyhop", {})
        self.ui_bridge.set_value("JumpKey",   bh.get("JumpKey", "space"))
        self.ui_bridge.set_value("JumpDelay", str(bh.get("JumpDelay", 0.01)))


    def _validate_inputs(self) -> dict[str, str]:
        errors = {}
        tk = self.ui_bridge.get_value("TriggerKey")
        if tk is not None and not tk.strip():
            errors["TriggerKey"] = "Trigger key cannot be empty."

        min_delay = None
        raw_min = self.ui_bridge.get_value("ShotDelayMin")
        if raw_min is not None:
            try:
                min_delay = float(raw_min)
                if min_delay < 0:
                    errors["ShotDelayMin"] = "Must be non-negative."
            except ValueError:
                errors["ShotDelayMin"] = "Must be a valid number."

        raw_max = self.ui_bridge.get_value("ShotDelayMax")
        if raw_max is not None:
            try:
                max_delay = float(raw_max)
                if max_delay < 0:
                    errors["ShotDelayMax"] = "Must be non-negative."
                elif min_delay is not None and min_delay > max_delay:
                    errors["ShotDelayMax"] = "Cannot be less than minimum delay."
            except ValueError:
                errors["ShotDelayMax"] = "Must be a valid number."

        raw_post = self.ui_bridge.get_value("PostShotDelay")
        if raw_post is not None:
            try:
                post = float(raw_post)
                if post < 0:
                    errors["PostShotDelay"] = "Must be non-negative."
            except ValueError:
                errors["PostShotDelay"] = "Must be a valid number."

        fps_val = self.ui_bridge.get_value("target_fps")
        if fps_val is not None:
            try:
                fps = float(fps_val)
                if not (60 <= fps <= 420):
                    errors["target_fps"] = "Must be between 60 and 420."
            except (ValueError, TypeError):
                errors["target_fps"] = "Must be a valid number."

        jk = self.ui_bridge.get_value("JumpKey")
        if jk is not None and not jk.strip():
            errors["JumpKey"] = "Jump key cannot be empty."

        trigger_enabled = self.ui_bridge.get_value("Trigger")
        bunnyhop_enabled = self.ui_bridge.get_value("Bunnyhop")
        if (
            trigger_enabled
            and bunnyhop_enabled
            and tk is not None
            and jk is not None
            and tk.strip().lower() == jk.strip().lower()
        ):
            errors["JumpKey"] = "Cannot match Trigger Key."
            errors["TriggerKey"] = "Cannot match Jump Key."

        raw_jd = self.ui_bridge.get_value("JumpDelay")
        if raw_jd is not None:
            try:
                jd = float(raw_jd)
                if not (0.01 <= jd <= 0.5):
                    errors["JumpDelay"] = "Must be between 0.01 and 0.5."
            except ValueError:
                errors["JumpDelay"] = "Must be a valid number."



        return errors

    def reset_to_default_settings(self) -> None:
        if not AppModal.confirm(self.root,
            "Reset Settings",
            "Reset all settings to defaults? This will stop all active features.",
        ):
            return
        try:
            self.stop_client()
            new_config = ConfigManager.reset_to_default()
            for fd in self.features.values():
                fd["instance"].update_config(new_config)
            self.update_ui_from_config()
            AppModal.info(self.root, "Settings Reset", "All settings reset to defaults.")
        except Exception:
            logger.exception("Failed to reset settings.")
            AppModal.error(self.root, "Error", "Failed to reset settings. Check logs.")

    def save_current_as_profile(self, name: str) -> bool:
        """Flush current UI to disk, then snapshot it into a named profile."""
        self.save_settings(show_message=False)
        config = ConfigManager.load_config()
        return ProfileManager.save_profile(name, config)

    def load_profile(self, name: str) -> None:
        """Apply a named profile: merge into live config, update UI, apply feature changes."""
        merged = ProfileManager.load_profile(name)
        if merged is None:
            AppModal.error(self.root, "Profile Error",
                           f"Could not load profile '{name}'. Check logs.")
            return
        try:
            old_config = ConfigManager.load_config()
            self._suppress_watcher = True
            try:
                ConfigManager.save_config(merged, log_info=False)
            finally:
                self._suppress_watcher = False
            for fd in self.features.values():
                fd["instance"].update_config(merged)
            self.update_ui_from_config()
            self.client_manager.apply_feature_state_changes(old_config, merged)
            self.client_manager.update_running_feature_configs(merged)
            self.active_profile_name = name
            self.update_active_profile_label()
            logger.info("Loaded profile '%s'.", name)
        except Exception:
            logger.exception("Failed to apply profile '%s'.", name)
            AppModal.error(self.root, "Profile Error",
                           f"Failed to apply profile '{name}'. Check logs.")

    def delete_profile(self, name: str) -> bool:
        """Delete a named profile file."""
        return ProfileManager.delete_profile(name)

    def refresh_profile_dropdown(self) -> None:
        """Rebuild the profile OptionMenu values from disk. Called after save/delete."""
        if not hasattr(self, "_profile_dropdown"):
            return
        profiles = ProfileManager.list_profiles()
        display = profiles if profiles else ["No profiles"]
        self._profile_dropdown.configure(values=display)
        # Reset selection to the first entry so the widget always shows a valid state.
        self._profile_var.set(display[0])

    def update_active_profile_label(self) -> None:
        """Sync the active-profile label in the General tab with current state."""
        if not hasattr(self, "_active_profile_label"):
            return
        if self.active_profile_name:
            self._active_profile_label.configure(text=f"Active: {self.active_profile_name}")
        else:
            self._active_profile_label.configure(text="")

    def open_config_directory(self) -> None:
        if platform.system() == "Windows":
            os.startfile(ConfigManager.CONFIG_DIRECTORY)

    def init_config_watcher(self) -> None:
        try:
            handler = ConfigFileChangeHandler(self)
            self.observer = Observer()
            self.observer.schedule(handler, path=ConfigManager.CONFIG_DIRECTORY, recursive=False)
            self.observer.start()
            logger.info("Config file watcher started.")
        except Exception:
            logger.exception("Failed to start config file watcher.")

    def start_log_timer(self) -> None:
        def _poll():
            try:
                if self.current_view == "logs":
                    use_detailed = ConfigManager.get_value("General", "DetailedLogs", default=False)
                    target = Logger.DETAILED_LOG_FILE() if use_detailed else Logger.LOG_FILE()

                    if target != self._active_log_file:
                        self._active_log_file = target
                        self._log_file_pos = 0
                        self.root.after(0, self._reload_log_display)
                    elif hasattr(self, "log_text") and os.path.exists(target):
                        with open(target, "r", encoding="utf-8") as fh:
                            fh.seek(self._log_file_pos)
                            new_bytes = fh.read()
                            self._log_file_pos = fh.tell()
                        if new_bytes:
                            self.root.after(0, self.append_log_display, new_bytes)
            except Exception:
                logger.exception("Error reading log file for GUI display.")
            self.log_timer = self.root.after(2000, _poll)

        _poll()

    def _reload_log_display(self) -> None:
        """Flush the log widget and reload from the current active log file."""
        from src.gui.logs_tab import _initial_load
        _initial_load(self)

    def update_log_display(self, content: str) -> None:
        """Replace the entire log buffer and re-render. Kept for external callers."""
        self._reset_log_buffer(content)

    def append_log_display(self, content: str) -> None:
        """Append new log text to the buffer and re-render."""
        self._append_to_log_buffer(content)

    def _parse_log_entries(self, text: str) -> list[str]:
        """Split raw log text into logical entries.

        Continuation lines (tracebacks, etc.) that don't start with a level
        tag are attached to their parent entry so filtering keeps them together.
        """
        entries: list[str] = []
        current: list[str] = []
        for line in text.splitlines(keepends=True):
            if _LEVEL_LINE_RE.match(line):
                if current:
                    entries.append("".join(current))
                current = [line]
            else:
                if current:
                    current.append(line)
                else:
                    # Header/placeholder text that has no level tag
                    entries.append(line)
        if current:
            entries.append("".join(current))
        return entries

    def _reset_log_buffer(self, text: str) -> None:
        """Replace the entire buffer and re-render the widget."""
        self._log_lines = self._parse_log_entries(text)
        self._apply_log_filter()

    def _append_to_log_buffer(self, text: str) -> None:
        """Append new entries to the buffer (capped at 10 000) and re-render."""
        self._log_lines.extend(self._parse_log_entries(text))
        if len(self._log_lines) > 10_000:
            self._log_lines = self._log_lines[-10_000:]
        self._apply_log_filter()

    # Maps [LEVEL] token -> tag name registered in _create_log_body
    _LEVEL_TAG: dict[str, str] = {
        "DEBUG":    "log_debug",
        "INFO":     "log_info",
        "WARNING":  "log_warning",
        "ERROR":    "log_error",
        "CRITICAL": "log_critical",
    }

    def _apply_log_filter(self) -> None:
        """Render the log widget from the buffer with active level and search filters."""
        if not hasattr(self, "log_text") or not self.log_text.winfo_exists():
            return
        level = self._log_filter_level
        term  = self._log_search_term.lower().strip()

        visible = [
            e for e in self._log_lines
            if (level == "ALL" or f"[{level}]" in e)
            and (not term or term in e.lower())
        ]
        content = "".join(visible)

        try:
            self.log_text.configure(state="normal")
            self.log_text.delete("1.0", "end")
            if content:
                self.log_text.insert("1.0", content)
                self._apply_level_tags(visible)
            if term:
                self._apply_search_tags(term)
            self.log_text.see("end")
            self.log_text.configure(state="disabled")
        except Exception:
            logger.exception("Failed to render log view.")

    def _apply_level_tags(self, entries: list[str]) -> None:
        """Color the [LEVEL] token in each entry after a bulk insert.

        Walks the entry list tracking the running character offset so we can
        derive exact tk.Text line/column positions without a second file scan.
        Each entry may span multiple lines (e.g. tracebacks); only the first
        line carries the level tag.
        """
        widget = self.log_text._textbox
        # Remove stale level tags from the previous render in one pass each
        for tag in self._LEVEL_TAG.values():
            widget.tag_remove(tag, "1.0", "end")

        line_num = 1
        for entry in entries:
            # Only the opening line of each entry has a [LEVEL] token
            first_line = entry.split("\n", 1)[0]
            m = _LEVEL_LINE_RE.search(first_line)
            if m:
                tag = self._LEVEL_TAG.get(m.group(1))
                if tag:
                    # m.start()/end() are byte offsets into first_line - use as col indices
                    start = f"{line_num}.{m.start()}"
                    end   = f"{line_num}.{m.end()}"
                    widget.tag_add(tag, start, end)
            line_num += entry.count("\n")

    def _apply_search_tags(self, term: str) -> None:
        """Highlight all occurrences of term with amber background in the widget."""
        widget = self.log_text._textbox
        widget.tag_remove("search_hl", "1.0", "end")
        start = "1.0"
        while True:
            pos = widget.search(term, start, nocase=True, stopindex="end")
            if not pos:
                break
            end = f"{pos}+{len(term)}c"
            widget.tag_add("search_hl", pos, end)
            start = end

    def set_log_filter(self, level: str) -> None:
        """Set the active level filter and re-render."""
        self._log_filter_level = level
        self._refresh_log_chips()
        self._apply_log_filter()

    def set_log_search(self, term: str) -> None:
        """Debounced search: waits 200 ms of inactivity before re-rendering."""
        if self._search_debounce:
            self.root.after_cancel(self._search_debounce)
        self._search_debounce = self.root.after(200, self._commit_log_search, term)

    def _commit_log_search(self, term: str) -> None:
        self._log_search_term = term
        self._apply_log_filter()

    def _refresh_log_chips(self) -> None:
        """Update filter chip visuals to reflect the currently active level."""
        from src.gui.logs_tab import _CHIP_COLORS, _CHIP_INACTIVE_FG, _CHIP_INACTIVE_HOVER, _CHIP_INACTIVE_BORDER, _CHIP_INACTIVE_TEXT
        for level, btn in self._log_filter_chips.items():
            if level == self._log_filter_level:
                fg, hover = _CHIP_COLORS[level]
                btn.configure(
                    fg_color=fg, hover_color=hover,
                    border_width=0, text_color="#ffffff",
                )
            else:
                btn.configure(
                    fg_color=_CHIP_INACTIVE_FG, hover_color=_CHIP_INACTIVE_HOVER,
                    border_width=1, border_color=_CHIP_INACTIVE_BORDER,
                    text_color=_CHIP_INACTIVE_TEXT,
                )

    def clear_log_display(self) -> None:
        """Clear the display buffer and advance the file pointer to EOF.

        Only the in-memory view is cleared; the log file on disk is untouched.
        """
        self._log_lines = []
        try:
            if os.path.exists(self._active_log_file):
                with open(self._active_log_file, "rb") as fh:
                    fh.seek(0, 2)
                    self._log_file_pos = fh.tell()
        except Exception:
            logger.exception("Failed to advance log file position on clear.")
        self._apply_log_filter()

    def export_log_to_clipboard(self) -> None:
        """Copy the currently visible (filtered) log content to the clipboard."""
        try:
            if not hasattr(self, "log_text") or not self.log_text.winfo_exists():
                return
            content = self.log_text.get("1.0", "end-1c")
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            logger.info("Log exported to clipboard (%d chars).", len(content))
        except Exception:
            logger.exception("Failed to export log to clipboard.")

    def run(self) -> None:
        self.root.mainloop()

    def on_closing(self) -> None:
        self.cleanup()
        self.root.destroy()

    def cleanup(self) -> None:
        try:
            # Signal dashboard network threads to stop before destroying the root.
            if self._fetch_update_stop:
                self._fetch_update_stop.set()
            if self._fetch_patch_stop:
                self._fetch_patch_stop.set()

            self.stop_client()

            if self.observer:
                self.observer.stop()
                self.observer.join()

            if self.log_timer:
                self.root.after_cancel(self.log_timer)
            if self._process_monitor_timer:
                self.root.after_cancel(self._process_monitor_timer)
        except Exception:
            logger.exception("Error during application cleanup.")