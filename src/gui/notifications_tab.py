import re
import threading
import webbrowser
import requests
import orjson
import customtkinter as ctk

from src.utils.logger import Logger
from src.utils.utility import Utility
from src.utils.config_manager import ConfigManager
from src.gui.icon_loader import icon_label, load_icon
from src.gui.theme import (
    FONT_TITLE, FONT_SUBTITLE, FONT_SECTION_TITLE, FONT_ITEM_LABEL, FONT_ITEM_DESCRIPTION,
    FONT_FAMILY_BOLD, FONT_SIZE_P,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_BACKGROUND, COLOR_BORDER,
    COLOR_WIDGET_BACKGROUND, COLOR_ACCENT_FG, COLOR_BUTTON_DANGER_FG, COLOR_BUTTON_DANGER_BORDER,
    SECTION_STYLE_DANGER,
)

logger = Logger.get_logger(__name__)

# Category mapping for notification types, icons, and left border accent colors
_TYPE_MAP = {
    "info": {
        "icon": "circle_question_icon.png",
        "color": "#3b82f6",  # Blue
        "label": "INFO",
    },
    "warning": {
        "icon": "circle_exclamation_icon.png",
        "color": "#f59e0b",  # Amber / Orange
        "label": "WARNING",
    },
    "success": {
        "icon": "check_icon.png",
        "color": "#10b981",  # Emerald Green
        "label": "SUCCESS",
    },
    "update": {
        "icon": "update_icon.png",
        "color": "#7c3aed",  # Violet Accent
        "label": "UPDATE",
    },
    "danger": {
        "icon": "circle_xmark_icon.png",
        "color": "#ef4444",  # Red
        "label": "ALERT",
    },
}

_URL_REGEX = re.compile(r"(https?://[^\s<]+|\[(.+?)\]\((https?://[^\s<]+)\))")


def _get_read_notification_ids() -> set:
    """Retrieve the set of read notification IDs from configuration."""
    config = ConfigManager.load_config()
    return set(config.get("read_notifications", []))


def _save_read_notification_ids(read_set: set) -> None:
    """Persist the set of read notification IDs to configuration."""
    config = ConfigManager.load_config()
    config["read_notifications"] = list(read_set)
    ConfigManager.save_config(config, log_info=False)


def _resolve_type(notification: dict) -> tuple[str, dict]:
    """Resolve notification type string and style metadata with JSON icon override support."""
    custom_icon = notification.get("icon") or notification.get("icon_file")
    if custom_icon:
        icon_name = custom_icon if custom_icon.endswith(".png") else f"{custom_icon}.png"
        color = "#7c3aed" if "github" in icon_name.lower() else "#3b82f6"
        return "custom", {
            "icon": icon_name,
            "color": color,
            "label": "INFO",
        }

    n_type = str(notification.get("type", notification.get("category", ""))).lower().strip()
    if n_type in _TYPE_MAP:
        return n_type, _TYPE_MAP[n_type]

    title_msg = (str(notification.get("title", "")) + " " + str(notification.get("message", ""))).lower()
    if "github" in title_msg:
        if "suspended" in title_msg or "warn" in title_msg or "error" in title_msg:
            return "warning", {
                "icon": "github_icon.png",
                "color": "#f59e0b",
                "label": "WARNING",
            }
        elif "restore" in title_msg or "success" in title_msg or "fixed" in title_msg:
            return "success", {
                "icon": "github_icon.png",
                "color": "#10b981",
                "label": "SUCCESS",
            }
        return "github", {
            "icon": "github_icon.png",
            "color": "#7c3aed",
            "label": "GITHUB",
        }

    if "warn" in title_msg or "important" in title_msg or "alert" in title_msg or "suspend" in title_msg:
        return "warning", _TYPE_MAP["warning"]
    if "success" in title_msg or "fixed" in title_msg or "resolved" in title_msg or "restore" in title_msg:
        return "success", _TYPE_MAP["success"]
    if "update" in title_msg or "release" in title_msg or "v1." in title_msg:
        return "update", _TYPE_MAP["update"]

    return "info", _TYPE_MAP["info"]


def populate_notifications(main_window, frame) -> None:
    """Populate the Notifications tab with news from a JSON file."""
    for widget in frame.winfo_children():
        widget.destroy()

    notifications_container = ctk.CTkScrollableFrame(
        frame,
        fg_color=COLOR_BACKGROUND,
        scrollbar_button_color=COLOR_BACKGROUND,
        scrollbar_button_hover_color=COLOR_BACKGROUND,
        scrollbar_fg_color=COLOR_BACKGROUND
    )
    notifications_container.pack(fill="both", expand=True, padx=40, pady=40)
    notifications_container._parent_canvas.configure(yscrollincrement=5)

    # Header section
    header_frame = ctk.CTkFrame(
        notifications_container,
        fg_color="transparent",
        height=100
    )
    header_frame.pack(fill="x", pady=(0, 35))
    header_frame.pack_propagate(False)

    title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
    title_container.pack(side="left", fill="y")

    _icon_row = ctk.CTkFrame(title_container, fg_color="transparent")
    _icon_row.pack(anchor="w", pady=(10, 0))
    icon_label(_icon_row, "bell_icon.png", size=(32, 32), padx=(0, 14))
    title_label = ctk.CTkLabel(
        _icon_row,
        text="Notifications",
        font=FONT_TITLE,
        text_color=COLOR_TEXT_PRIMARY
    )
    title_label.pack(side="left")

    subtitle_label = ctk.CTkLabel(
        title_container,
        text="Latest news and updates for VioletWing",
        font=FONT_SUBTITLE,
        text_color=COLOR_TEXT_SECONDARY
    )
    subtitle_label.pack(anchor="w", pady=(8, 0))

    header_right = ctk.CTkFrame(header_frame, fg_color="transparent")
    header_right.pack(side="right", fill="y")

    # Loading card
    loading_card = ctk.CTkFrame(notifications_container, fg_color=COLOR_WIDGET_BACKGROUND, corner_radius=12)
    loading_card.pack(fill="x", pady=(0, 40))

    loading_content = ctk.CTkFrame(loading_card, fg_color="transparent")
    loading_content.pack(padx=50, pady=40)

    loading_indicator = ctk.CTkFrame(
        loading_content,
        width=60,
        height=60,
        corner_radius=30,
        fg_color=COLOR_ACCENT_FG
    )
    loading_indicator.pack()

    _spin_icon = load_icon("rotate_icon.png", size=(28, 28))
    ctk.CTkLabel(
        loading_indicator,
        text="" if _spin_icon else "...",
        image=_spin_icon,
        text_color="#ffffff"
    ).place(relx=0.5, rely=0.5, anchor="center")

    ctk.CTkLabel(
        loading_content,
        text="Loading notifications data...",
        font=FONT_ITEM_LABEL,
        text_color=COLOR_TEXT_SECONDARY
    ).pack(pady=(24, 0))

    def fetch_notifications():
        def safe_after(func):
            try:
                if main_window.root.winfo_exists():
                    main_window.root.after(0, func)
            except Exception:
                pass

        try:
            session = Utility.get_http_session()
            response = session.get('https://violetwing.vercel.app/data/notifications.json', timeout=10)
            response.raise_for_status()
            data = orjson.loads(response.content)

            valid_notifications = [
                n for n in data
                if isinstance(n, dict) and ("number" in n or "id" in n) and "message" in n
            ]
            if not valid_notifications:
                safe_after(lambda: show_error(loading_card, "No valid notifications found"))
                logger.warning("No valid notifications found in JSON data")
                return
            safe_after(lambda: update_notifications_ui(valid_notifications, loading_card, notifications_container))
        except requests.exceptions.RequestException as e:
            safe_after(lambda: show_error(loading_card, f"Failed to fetch notifications: {str(e)}"))
            logger.error(f"Failed to fetch notifications data: {e}")
        except orjson.JSONDecodeError as e:
            safe_after(lambda: show_error(loading_card, "Invalid JSON data received"))
            logger.error(f"Invalid JSON data: {e}")
        except Exception as e:
            safe_after(lambda: show_error(loading_card, f"Unexpected error: {str(e)}"))
            logger.error(f"Unexpected error: {e}")

    def update_notifications_ui(data, loading_card, container):
        """Update the UI with fetched notifications data."""
        if loading_card.winfo_exists():
            loading_card.destroy()

        notifications = sorted(
            data,
            key=lambda x: x.get('number', x.get('id', 0)),
            reverse=True
        )
        read_set = _get_read_notification_ids()

        def sync_sidebar_badge():
            unread_count = len([
                n for n in notifications
                if (n.get('number') if n.get('number') is not None else n.get('id')) not in read_set
            ])
            if hasattr(main_window, "set_notification_badge"):
                main_window.set_notification_badge(unread_count)

        sync_sidebar_badge()

        def mark_all_read():
            for n in notifications:
                nid = n.get('number') if n.get('number') is not None else n.get('id')
                if nid is not None:
                    read_set.add(nid)
            _save_read_notification_ids(read_set)
            sync_sidebar_badge()
            # Re-render UI
            update_notifications_ui(data, ctk.CTkFrame(container), container)

        # "Mark all as read" button
        for child in header_right.winfo_children():
            child.destroy()

        ctk.CTkButton(
            header_right,
            text="Mark all as read",
            font=(FONT_FAMILY_BOLD[0], 12),
            fg_color="transparent",
            hover_color=("#e5e7eb", "#2a1d4e"),
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT_SECONDARY,
            height=32,
            corner_radius=8,
            command=mark_all_read,
        ).pack(side="right", pady=(10, 0))

        # Render cards
        for widget in list(container.winfo_children()):
            if widget != header_frame:
                widget.destroy()

        for i, notification in enumerate(notifications):
            create_notification_card(
                container,
                notification,
                read_set,
                sync_sidebar_badge,
                is_last=(i == len(notifications) - 1)
            )

    def create_notification_card(container, notification, read_set, sync_sidebar_badge, is_last=False):
        nid = notification.get('number') if notification.get('number') is not None else notification.get('id')
        is_read = nid in read_set
        _, type_meta = _resolve_type(notification)

        bg_color = ("#f3f4f6", "#120c24") if is_read else ("#ffffff", "#1e1438")
        border_color = COLOR_BORDER if is_read else ("#c4b5fd", "#4c3a7a")

        card = ctk.CTkFrame(
            container,
            fg_color=bg_color,
            border_width=1,
            border_color=border_color,
            corner_radius=12,
        )
        card.pack(fill="x", pady=(0, 20 if not is_last else 0))

        # Inset capsule status indicator
        accent_strip = ctk.CTkFrame(
            card,
            width=4,
            corner_radius=2,
            fg_color=type_meta["color"],
        )
        accent_strip.pack(side="left", fill="y", padx=(12, 0), pady=12)

        card_body = ctk.CTkFrame(card, fg_color="transparent")
        card_body.pack(side="left", fill="both", expand=True, padx=(10, 24), pady=20)

        # Header row inside card
        header_row = ctk.CTkFrame(card_body, fg_color="transparent")
        header_row.pack(fill="x", pady=(0, 10))

        # Category icon badge
        badge_bg = type_meta["color"] if not is_read else COLOR_BORDER
        badge_frame = ctk.CTkFrame(
            header_row,
            width=42,
            height=42,
            corner_radius=21,
            fg_color=badge_bg
        )
        badge_frame.pack(side="left", padx=(0, 14))
        badge_frame.pack_propagate(False)

        cat_icon = load_icon(type_meta["icon"], size=(22, 22))
        ctk.CTkLabel(
            badge_frame,
            text="" if cat_icon else type_meta["label"][0],
            image=cat_icon,
            text_color="#ffffff"
        ).place(relx=0.5, rely=0.5, anchor="center")

        # Title
        title = notification.get('title', 'Notification')
        url = notification.get('url', '')
        title_color = COLOR_TEXT_SECONDARY if is_read else COLOR_TEXT_PRIMARY

        title_label = ctk.CTkLabel(
            header_row,
            text=title,
            font=FONT_SECTION_TITLE,
            text_color=title_color if not url else COLOR_ACCENT_FG,
            anchor="w",
            cursor="hand2" if url else "arrow"
        )
        title_label.pack(side="left", fill="x", expand=True)
        if url:
            title_label.bind("<Button-1>", lambda e: webbrowser.open(url))

        # Meta container on right: timestamp + UNREAD badge
        meta_frame = ctk.CTkFrame(header_row, fg_color="transparent")
        meta_frame.pack(side="right")

        if not is_read:
            unread_pill = ctk.CTkFrame(
                meta_frame,
                corner_radius=10,
                fg_color="#7c3aed"
            )
            unread_pill.pack(side="left", padx=(0, 8))
            ctk.CTkLabel(
                unread_pill,
                text="UNREAD",
                font=(FONT_FAMILY_BOLD[0], 9, "bold"),
                text_color="#ffffff"
            ).pack(padx=8, pady=2)

        timestamp = notification.get('timestamp', '')
        if timestamp:
            ts_frame = ctk.CTkFrame(
                meta_frame,
                corner_radius=12,
                fg_color=COLOR_BACKGROUND,
                border_width=1,
                border_color=COLOR_BORDER
            )
            ts_frame.pack(side="left")
            ctk.CTkLabel(
                ts_frame,
                text=timestamp,
                font=FONT_ITEM_DESCRIPTION,
                text_color=COLOR_TEXT_SECONDARY
            ).pack(padx=10, pady=4)

        # Message body frame
        message_frame = ctk.CTkFrame(card_body, fg_color="transparent")
        message_frame.pack(fill="x", padx=(56, 0), pady=(4, 0))

        _render_message_with_links(message_frame, notification.get('message', ''))

        # Click handler to mark individual card as read
        def on_card_click(event=None):
            nonlocal is_read
            if not is_read and nid is not None:
                is_read = True
                read_set.add(nid)
                _save_read_notification_ids(read_set)
                sync_sidebar_badge()
                card.configure(fg_color=("#f3f4f6", "#120c24"), border_color=COLOR_BORDER)
                title_label.configure(text_color=COLOR_TEXT_SECONDARY if not url else COLOR_ACCENT_FG)
                badge_frame.configure(fg_color=COLOR_BORDER)
                if 'unread_pill' in locals():
                    unread_pill.pack_forget()

        card.bind("<Button-1>", on_card_click)
        card_body.bind("<Button-1>", on_card_click)

    def _render_message_with_links(parent, text: str):
        """Render message text, converting URLs and markdown links into interactive labels."""
        matches = list(_URL_REGEX.finditer(text))
        if not matches:
            ctk.CTkLabel(
                parent,
                text=text,
                font=FONT_ITEM_DESCRIPTION,
                text_color=COLOR_TEXT_SECONDARY,
                anchor="w",
                wraplength=740,
                justify="left"
            ).pack(fill="x")
            return

        cursor = 0
        for m in matches:
            if m.start() > cursor:
                part = text[cursor:m.start()]
                if part.strip():
                    ctk.CTkLabel(
                        parent,
                        text=part.strip(),
                        font=FONT_ITEM_DESCRIPTION,
                        text_color=COLOR_TEXT_SECONDARY,
                        anchor="w",
                        justify="left",
                        wraplength=740
                    ).pack(anchor="w", pady=(0, 2))

            raw_match = m.group(0)
            if raw_match.startswith("["):
                link_text = m.group(2)
                target_url = m.group(3)
            else:
                link_text = raw_match
                target_url = raw_match

            link_btn = ctk.CTkLabel(
                parent,
                text=link_text,
                font=(FONT_FAMILY_BOLD[0], FONT_SIZE_P, "bold"),
                text_color="#9d5cff",
                cursor="hand2",
                anchor="w"
            )
            link_btn.pack(anchor="w", pady=(2, 4))
            link_btn.bind("<Button-1>", lambda e, u=target_url: webbrowser.open(u))

            cursor = m.end()

        if cursor < len(text):
            rem = text[cursor:]
            if rem.strip():
                ctk.CTkLabel(
                    parent,
                    text=rem.strip(),
                    font=FONT_ITEM_DESCRIPTION,
                    text_color=COLOR_TEXT_SECONDARY,
                    anchor="w",
                    justify="left",
                    wraplength=740
                ).pack(anchor="w", pady=(2, 0))

    def show_error(loading_card, error_msg):
        if loading_card.winfo_exists():
            loading_card.destroy()

        if not notifications_container.winfo_exists():
            return

        error_card = ctk.CTkFrame(
            notifications_container,
            **SECTION_STYLE_DANGER
        )
        error_card.pack(fill="x", pady=(0, 40))

        content = ctk.CTkFrame(error_card, fg_color="transparent")
        content.pack(padx=50, pady=40)

        _xmark_icon = load_icon("circle_xmark_icon.png", size=(28, 28))
        icon = ctk.CTkFrame(
            content,
            width=70,
            height=70,
            corner_radius=35,
            fg_color=COLOR_BUTTON_DANGER_FG
        )
        icon.pack()
        ctk.CTkLabel(
            icon,
            text="" if _xmark_icon else "x",
            image=_xmark_icon,
            text_color="#ffffff"
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            content,
            text="Failed to Load Notifications",
            font=FONT_SECTION_TITLE,
            text_color=COLOR_BUTTON_DANGER_FG
        ).pack(pady=(24, 10))

        ctk.CTkLabel(
            content,
            text=error_msg,
            font=FONT_ITEM_DESCRIPTION,
            text_color=COLOR_BUTTON_DANGER_FG,
            wraplength=700
        ).pack()

        ctk.CTkLabel(
            content,
            text="Please check your internet connection or verify the notifications data.",
            font=FONT_ITEM_DESCRIPTION,
            text_color=COLOR_BUTTON_DANGER_BORDER
        ).pack(pady=(16, 0))

    threading.Thread(target=fetch_notifications, daemon=True).start()