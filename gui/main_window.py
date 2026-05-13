import copy
import os
import platform
import threading
import time
import webbrowser

import customtkinter as ctk
from PIL import Image
from tkinter import messagebox
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
from classes.offset_fetcher import fetch_offsets
from classes import ghost_manager as _gm

from gui.icon_loader import load_icon, ASSETS_DIR
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
from gui.theme import (
    FONT_FAMILY_BOLD, FONT_FAMILY_REGULAR, FONT_SIZE_H2, FONT_SIZE_H4, FONT_SIZE_P,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_BACKGROUND,
    COLOR_ACCENT_FG, COLOR_HEADER_BG, COLOR_SIDEBAR_BG, COLOR_SIDEBAR_ACTIVE_BG,
    COLOR_SIDEBAR_INDICATOR, COLOR_VIOLET_SUBTLE,
    BUTTON_STYLE_PRIMARY, BUTTON_STYLE_DANGER,
)

logger = Logger.get_logger(__name__)

class MainWindow:
    def __init__(self) -> None:
        self.repo_url = "violetwing.vercel.app"

        # Thread handles
        self.trigger_thread = None
        self.overlay_thread = None
        self.bunnyhop_thread = None
        self.noflash_thread = None
        self.observer = None
        self.log_timer = None
        self._log_file_pos = 0
        self._active_log_file: str = Logger.LOG_FILE()

        # Stop events for dashboard network threads - set in cleanup()
        self._fetch_update_stop: threading.Event | None = None
        self._fetch_patch_stop: threading.Event | None = None

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.root = ctk.CTk()

        self.offsets, self.client_data, self.buttons_data = {}, {}, {}
        self._offsets_fetching: bool = False
        self.memory_manager = MemoryManager(self.offsets, self.client_data, self.buttons_data)
        self.initialize_features()

        # Pick a ghost profile for dynamic disguise
        config = ConfigManager.load_config()
        if config["General"].get("Disguise", False):
            self.ghost = _gm.pick()
        else:
            self.ghost = None

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
            gdi32 = ctypes.WinDLL("gdi32")
            for font in [
                "src/fonts/Outfit-Regular.ttf", "src/fonts/Outfit-Bold.ttf",
                "src/fonts/JetBrainsMono-Regular.ttf", "src/fonts/JetBrainsMono-Bold.ttf",
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
            messagebox.showerror("Initialisation Error",
                                 "Failed to initialise features. Check logs.")

    def setup_ui(self) -> None:
        self.create_modern_header()
        self.create_main_content()

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
        self.create_update_button(sf)

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

    def create_social_buttons(self, parent) -> ctk.CTkFrame:
        sf = ctk.CTkFrame(parent, fg_color="transparent")
        sf.pack(side="right")
        socials = [
            ("Discord",  "discord_icon.png",   "https://discord.gg/Avb3yUeW98"),
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

    def create_update_button(self, parent) -> None:
        ci = load_icon("update_icon.png")
        if self.updater.check_for_updates():
            is_pre = self.updater.is_prerelease
            ctk.CTkButton(
                parent,
                text="Pre-release Available!" if is_pre else "Update Available!",
                image=ci, compound="left",
                command=self.updater.handle_update,
                height=36, corner_radius=10,
                fg_color="#f59e0b" if is_pre else "#ef4444",
                hover_color="#d97706" if is_pre else "#dc2626",
                border_width=0, text_color="#ffffff",
                font=(FONT_FAMILY_BOLD[0], FONT_SIZE_P, "bold"),
            ).pack(side="left", padx=(8, 0))

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

        nav_items = [
            ("Dashboard",           "dashboard",           "charts_icon.png"),
            ("General Settings",    "general_settings",    "gear_icon.png"),
            ("Trigger Settings",    "trigger_settings",    "crosshairs_icon.png"),
            ("Overlay Settings",    "overlay_settings",    "layer_group_icon.png"),
            ("Additional Settings", "additional_settings", "bolt_icon.png"),
            ("Logs",                "logs",                "clipboard_list_icon.png"),
            ("FAQ",                 "faq",                 "circle_question_icon.png"),
            ("Notifications",       "notifications",       "bell_icon.png"),
            ("Supporters",          "supporters",          "handshake_icon.png"),
        ]

        ctk.CTkFrame(sidebar, height=1, fg_color=("#c4b5fd", "#2a1d4e")).pack(fill="x")
        ctk.CTkFrame(sidebar, height=20, fg_color="transparent").pack(fill="x")

        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self.nav_indicators: dict[str, ctk.CTkFrame] = {}
        self._nav_images: dict = {}

        for name, key, icon_file in nav_items:
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
        messagebox.showerror("Offset Error", "Failed to fetch offsets. Check logs.")
        if hasattr(self, "loading_label"):
            self.loading_label.configure(text="Failed to load offsets.", text_color="#ef4444")

    def update_client_status(self, status: str, color: str) -> None:
        self.status_label.configure(text=status, text_color=color)
        self.status_dot.configure(fg_color=color)
        if hasattr(self, "bot_status_label"):
            self.bot_status_label.configure(text=status, text_color=color)

    def start_client(self):  self.client_manager.start_client()
    def stop_client(self):   self.client_manager.stop_client()

    def update_weapon_settings_display(self) -> None:
        weapon_type = self.ui_bridge.get_value("active_weapon_type")
        if weapon_type is None:
            return
        config = ConfigManager.load_config()
        ws = config["Trigger"]["WeaponSettings"].get(weapon_type, {})
        self.ui_bridge.set_value("ShotDelayMin",  str(ws.get("ShotDelayMin",  0.01)))
        self.ui_bridge.set_value("ShotDelayMax",  str(ws.get("ShotDelayMax",  0.03)))
        self.ui_bridge.set_value("PostShotDelay", str(ws.get("PostShotDelay", 0.1)))

    def save_settings(self, show_message: bool = False) -> None:
        try:
            self._validate_inputs()
            config = ConfigManager.load_config()
            old_config = copy.deepcopy(config)
            self._update_config_from_ui(config)
            ConfigManager.save_config(config, log_info=False)
            self.client_manager.apply_feature_state_changes(old_config, config)
            self.client_manager.update_running_feature_configs(config)
            if show_message:
                messagebox.showinfo("Settings Saved", "Configuration saved successfully.")
        except ValueError as exc:
            logger.warning("Invalid input during settings save: %s", exc)
            messagebox.showerror("Invalid Input", str(exc))
        except Exception:
            logger.exception("Unexpected error while saving settings.")
            messagebox.showerror("Error", "An unexpected error occurred. Check logs.")

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
        if self.ui_bridge.registered("OffsetSource"):
            display = self.ui_bridge.get_value("OffsetSource")
            s["OffsetSource"] = getattr(self, "offset_source_mapping", {}).get(display, "a2x")

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
            "enable_box", "enable_skeleton", "draw_snaplines",
            "draw_health_numbers", "draw_nicknames", "use_transliteration", "draw_teammates",
        )
        for key in checkboxes:
            val = self.ui_bridge.get_value(key)
            if val is not None:
                s[key] = val

        for key in ("box_line_thickness", "target_fps"):
            val = self.ui_bridge.get_value(key)
            if val is not None:
                s[key] = val

        color_defaults = {
            "box_color_hex":       "#FFA500",
            "snaplines_color_hex": "#FFFFFF",
            "text_color_hex":      "#FFFFFF",
            "teammate_color_hex":  "#00FFFF",
        }
        for key, default in color_defaults.items():
            val = self.ui_bridge.get_value(key)
            if val is not None:
                s[key] = COLOR_CHOICES.get(val, default)

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
        st = self.ui_bridge.get_value("FlashSuppressionStrength")
        if st is not None:
            nf["FlashSuppressionStrength"] = st

    def update_ui_from_config(self) -> None:
        config = ConfigManager.load_config()
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
            "enable_box", "enable_skeleton", "draw_snaplines",
            "draw_health_numbers", "draw_nicknames", "use_transliteration", "draw_teammates",
        )
        for key in checkboxes:
            self.ui_bridge.set_value(key, s.get(key, False))

        for key, fmt in (("box_line_thickness", ".1f"), ("target_fps", ".0f")):
            self.ui_bridge.set_value(key, s.get(key, 0))

        for key in ("box_color_hex", "snaplines_color_hex", "text_color_hex", "teammate_color_hex"):
            self.ui_bridge.set_value(key, Utility.get_color_name_from_hex(s.get(key, "#FFFFFF")))

    def _load_additional(self, config: dict) -> None:
        bh = config.get("Bunnyhop", {})
        self.ui_bridge.set_value("JumpKey",   bh.get("JumpKey", "space"))
        self.ui_bridge.set_value("JumpDelay", str(bh.get("JumpDelay", 0.01)))
        nf = config.get("NoFlash", {})
        self.ui_bridge.set_value("FlashSuppressionStrength",
                                 nf.get("FlashSuppressionStrength", 0.0))

    def _validate_inputs(self) -> None:
        tk = self.ui_bridge.get_value("TriggerKey")
        if tk is not None and not tk.strip():
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
                raise ValueError("Minimum delay cannot exceed maximum delay.")

        raw_post = self.ui_bridge.get_value("PostShotDelay")
        if raw_post is not None:
            try:
                post = float(raw_post)
            except ValueError:
                raise ValueError("Post-shot delay must be a valid number.")
            if post < 0:
                raise ValueError("Post-shot delay must be non-negative.")

        fps_val = self.ui_bridge.get_value("target_fps")
        if fps_val is not None:
            try:
                fps = float(fps_val)
                if not (60 <= fps <= 420):
                    raise ValueError("Target FPS must be between 60 and 420.")
            except (ValueError, TypeError) as exc:
                if "Target FPS" in str(exc):
                    raise
                raise ValueError("Target FPS must be a valid number.")

        jk = self.ui_bridge.get_value("JumpKey")
        if jk is not None and not jk.strip():
            raise ValueError("Jump key cannot be empty.")

        raw_jd = self.ui_bridge.get_value("JumpDelay")
        if raw_jd is not None:
            try:
                jd = float(raw_jd)
            except ValueError:
                raise ValueError("Jump delay must be a valid number.")
            if not (0.01 <= jd <= 0.5):
                raise ValueError("Jump delay must be between 0.01 and 0.5 seconds.")

        strength = self.ui_bridge.get_value("FlashSuppressionStrength")
        if strength is not None and not (0.0 <= strength <= 100.0):
            raise ValueError("Flash suppression strength must be between 0.0 and 100.0.")

    def reset_to_default_settings(self) -> None:
        if not messagebox.askyesno(
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
            messagebox.showinfo("Settings Reset", "All settings reset to defaults.")
        except Exception:
            logger.exception("Failed to reset settings.")
            messagebox.showerror("Error", "Failed to reset settings. Check logs.")

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
        from gui.logs_tab import _initial_load
        _initial_load(self)

    def update_log_display(self, content: str) -> None:
        try:
            if hasattr(self, "log_text") and self.log_text.winfo_exists():
                self.log_text.configure(state="normal")
                self.log_text.delete("1.0", "end")
                self.log_text.insert("1.0", content)
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except Exception:
            logger.exception("Failed to update log display.")

    def append_log_display(self, content: str) -> None:
        try:
            if hasattr(self, "log_text") and self.log_text.winfo_exists():
                self.log_text.configure(state="normal")
                self.log_text.insert("end", content)
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except Exception:
            logger.exception("Failed to append log display.")

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
        except Exception:
            logger.exception("Error during application cleanup.")