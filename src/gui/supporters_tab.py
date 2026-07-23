import io
import threading
import requests
import orjson
from PIL import Image, ImageDraw
import customtkinter as ctk

from src.utils.logger import Logger
from src.utils.utility import Utility
from src.gui.icon_loader import icon_label, load_icon
from src.gui.components import create_scrollable_frame
from src.gui.theme import (
    FONT_TITLE, FONT_SUBTITLE, FONT_SECTION_TITLE, FONT_ITEM_LABEL, FONT_ITEM_DESCRIPTION,
    FONT_FAMILY_BOLD,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_BACKGROUND, COLOR_BORDER,
    COLOR_WIDGET_BACKGROUND, COLOR_ACCENT_FG, SECTION_STYLE,
)

logger = Logger.get_logger(__name__)

# Global memory cache for loaded Vercel server avatar images
_AVATAR_CACHE: dict[str, ctk.CTkImage] = {}


def _load_user_avatar(username: str, main_window, callback) -> None:
    """Asynchronously fetch avatar image from VioletWing Vercel server."""
    if username in _AVATAR_CACHE:
        callback(_AVATAR_CACHE[username])
        return

    def _fetch():
        session = Utility.get_http_session()
        urls = [
            f"https://violetwing.vercel.app/avatars/{username}.png",
            f"https://violetwing.vercel.app/data/avatars/{username}.png",
            f"https://violetwing.vercel.app/avatars/{username.lower()}.png",
        ]
        for url in urls:
            try:
                resp = session.get(url, timeout=4)
                if resp.status_code == 200 and resp.content:
                    raw_img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
                    ctk_img = ctk.CTkImage(light_image=raw_img, dark_image=raw_img, size=(36, 36))
                    _AVATAR_CACHE[username] = ctk_img

                    def _safe_cb():
                        try:
                            if main_window.root.winfo_exists():
                                callback(ctk_img)
                        except Exception:
                            pass

                    main_window.root.after(0, _safe_cb)
                    return
            except Exception as e:
                logger.debug(f"Failed fetching avatar for {username} from {url}: {e}")

    threading.Thread(target=_fetch, daemon=True).start()


def populate_supporters(main_window, frame) -> None:
    """Populate Supporters tab matching Notifications alignment and padding 1:1."""
    for widget in frame.winfo_children():
        widget.destroy()

    supporters_container = create_scrollable_frame(frame, main_window)

    # Top Header section matching Notifications tab 1:1 (no extra inner padding)
    header_frame = ctk.CTkFrame(
        supporters_container,
        fg_color="transparent",
        height=100
    )
    header_frame.pack(fill="x", pady=(0, 35))
    header_frame.pack_propagate(False)

    title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
    title_container.pack(side="left", fill="y")

    _icon_row = ctk.CTkFrame(title_container, fg_color="transparent")
    _icon_row.pack(anchor="w", pady=(10, 0))
    icon_label(_icon_row, "handshake_icon.png", size=(32, 32), padx=(0, 14))
    title_label = ctk.CTkLabel(
        _icon_row,
        text="Project Supporters",
        font=FONT_TITLE,
        text_color=COLOR_TEXT_PRIMARY
    )
    title_label.pack(side="left")

    subtitle_label = ctk.CTkLabel(
        title_container,
        text="Celebrating our incredible community members and contributors who fuel VioletWing's growth.",
        font=FONT_SUBTITLE,
        text_color=COLOR_TEXT_SECONDARY
    )
    subtitle_label.pack(anchor="w", pady=(8, 0))

    # Horizontal Stat Chips Bar
    stats_bar = ctk.CTkFrame(supporters_container, fg_color="transparent")
    stats_bar.pack(fill="x", pady=(0, 28))

    # Main content frame
    content_frame = ctk.CTkFrame(supporters_container, fg_color="transparent")
    content_frame.pack(fill="x")

    # Loading state card
    loading_container = ctk.CTkFrame(content_frame, **SECTION_STYLE)
    loading_container.pack(fill="x", pady=(0, 24))

    loading_content = ctk.CTkFrame(loading_container, fg_color="transparent")
    loading_content.pack(padx=40, pady=28)

    indicator = ctk.CTkFrame(
        loading_content,
        width=48,
        height=48,
        corner_radius=24,
        fg_color=COLOR_ACCENT_FG
    )
    indicator.pack()

    _spin_icon = load_icon("rotate_icon.png", size=(24, 24))
    ctk.CTkLabel(
        indicator,
        text="" if _spin_icon else "...",
        image=_spin_icon,
        text_color="#ffffff"
    ).place(relx=0.5, rely=0.5, anchor="center")

    ctk.CTkLabel(
        loading_content,
        text="Loading community supporters...",
        font=FONT_ITEM_LABEL,
        text_color=COLOR_TEXT_SECONDARY
    ).pack(pady=(16, 0))

    def fetch_supporters():
        def safe_after(func):
            try:
                if main_window.root.winfo_exists():
                    main_window.root.after(0, func)
            except Exception:
                pass

        try:
            session = Utility.get_http_session()
            response = session.get('https://violetwing.vercel.app/data/supporters.json', timeout=10)
            response.raise_for_status()
            data = orjson.loads(response.content)
            safe_after(lambda: update_supporters_ui(data, loading_container, stats_bar))
        except requests.exceptions.RequestException as e:
            safe_after(lambda: show_error(loading_container, f"Failed to fetch data: {str(e)}"))
            logger.error(f"Failed to fetch supporters data: {e}")
        except orjson.JSONDecodeError as e:
            safe_after(lambda: show_error(loading_container, "Invalid JSON data received"))
            logger.error(f"Invalid JSON data: {e}")
        except Exception as e:
            safe_after(lambda: show_error(loading_container, f"Unexpected error: {str(e)}"))
            logger.error(f"Unexpected error: {e}")

    def update_supporters_ui(data, loading_card, stats_bar_frame):
        if loading_card.winfo_exists():
            loading_card.destroy()

        general_data = data.get('general', {}) if isinstance(data, dict) else {}
        developers = general_data.get('developers', [])
        supporters = general_data.get('supporter', [])

        render_stat_chips(stats_bar_frame, len(developers) + len(supporters), len(developers), len(supporters))

        if developers:
            render_participant_section(
                content_frame,
                title="Core Developers",
                subtitle="Core engineering team maintaining the codebase and offsets",
                icon_file="rocket_icon.png",
                role_label="Developer",
                role_color="#10b981",  # Emerald Green
                items=developers
            )

        if supporters:
            render_participant_section(
                content_frame,
                title="Community Supporters",
                subtitle="Valued community members supporting project operations and testing",
                icon_file="heart_icon.png",
                role_label="Supporter",
                role_color="#f59e0b",  # Amber / Gold
                items=supporters
            )

        if not developers and not supporters:
            show_no_supporters(content_frame)

    def render_stat_chips(parent_frame, total_count, dev_count, sup_count):
        for w in parent_frame.winfo_children():
            w.destroy()

        chip_data = [
            ("Total Contributors", total_count, "#7c3aed"),
            ("Developers", dev_count, "#10b981"),
            ("Supporters", sup_count, "#f59e0b"),
        ]

        for label, count, color in chip_data:
            chip = ctk.CTkFrame(
                parent_frame,
                fg_color=COLOR_WIDGET_BACKGROUND,
                border_width=1,
                border_color=COLOR_BORDER,
                corner_radius=10,
                height=34
            )
            chip.pack(side="left", padx=(0, 10))

            dot = ctk.CTkFrame(chip, width=8, height=8, corner_radius=4, fg_color=color)
            dot.pack(side="left", padx=(10, 6), pady=13)

            ctk.CTkLabel(
                chip,
                text=f"{label}:",
                font=FONT_ITEM_DESCRIPTION,
                text_color=COLOR_TEXT_SECONDARY
            ).pack(side="left", padx=(0, 4))

            ctk.CTkLabel(
                chip,
                text=str(count),
                font=(FONT_FAMILY_BOLD[0], 11, "bold"),
                text_color=COLOR_TEXT_PRIMARY
            ).pack(side="left", padx=(0, 10))

    def render_participant_section(container, title, subtitle, icon_file, role_label, role_color, items):
        section_wrapper = ctk.CTkFrame(container, fg_color="transparent")
        section_wrapper.pack(fill="x", pady=(0, 32))

        # Section Header Row - aligned at x=0 vertically matching top Project Supporters header icon
        _head_title_row = ctk.CTkFrame(section_wrapper, fg_color="transparent")
        _head_title_row.pack(anchor="w")
        icon_label(_head_title_row, icon_file, size=(24, 24), padx=(0, 12))

        ctk.CTkLabel(
            _head_title_row,
            text=title,
            font=FONT_SECTION_TITLE,
            text_color=COLOR_TEXT_PRIMARY
        ).pack(side="left")

        ctk.CTkLabel(
            section_wrapper,
            text=subtitle,
            font=FONT_ITEM_DESCRIPTION,
            text_color=COLOR_TEXT_SECONDARY
        ).pack(anchor="w", pady=(4, 16))

        # Card Grid Container (Left-aligned, 3 columns max, expanded 260x64 cards)
        grid_frame = ctk.CTkFrame(section_wrapper, fg_color="transparent")
        grid_frame.pack(anchor="w", pady=(0, 12))

        max_columns = 3

        for i, item in enumerate(items):
            username = item.get("username", str(item)) if isinstance(item, dict) else str(item)
            item_role = item.get("role", role_label) if isinstance(item, dict) else role_label

            create_participant_card(
                grid_frame,
                username=username,
                role_text=item_role,
                accent_color=role_color,
                row=i // max_columns,
                col=i % max_columns
            )

    def create_participant_card(parent_grid, username, role_text, accent_color, row, col):
        # Expanded fixed dimensions: width=260, height=64
        card = ctk.CTkFrame(
            parent_grid,
            fg_color=COLOR_WIDGET_BACKGROUND,
            border_width=1,
            border_color=COLOR_BORDER,
            corner_radius=12,
            width=260,
            height=64
        )
        card.grid(row=row, column=col, padx=(0, 16), pady=(0, 14), sticky="w")
        card.grid_propagate(False)
        card.pack_propagate(False)

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=12)

        # Avatar Frame on Left (circular 50% border radius)
        avatar_frame = ctk.CTkFrame(
            body,
            width=36,
            height=36,
            corner_radius=18,
            fg_color=accent_color
        )
        avatar_frame.pack(side="left", padx=(0, 10))
        avatar_frame.pack_propagate(False)

        initial = username[0].upper() if username else "?"
        avatar_lbl = ctk.CTkLabel(
            avatar_frame,
            text=initial,
            font=(FONT_FAMILY_BOLD[0], 13, "bold"),
            text_color="#ffffff"
        )
        avatar_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Async fetch avatar image from Vercel server and crop 50% circular mask
        def _apply_avatar_image(ctk_img):
            if avatar_lbl.winfo_exists():
                avatar_lbl.configure(text="", image=ctk_img)

        _load_user_avatar(username, main_window, _apply_avatar_image)

        # Nickname in center/left
        name_label = ctk.CTkLabel(
            body,
            text=username,
            font=FONT_ITEM_LABEL,
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w"
        )
        name_label.pack(side="left", fill="x", expand=True)

        # Role Pill Badge on Right
        role_pill = ctk.CTkFrame(body, fg_color=COLOR_BACKGROUND, corner_radius=6)
        role_pill.pack(side="right")

        ctk.CTkLabel(
            role_pill,
            text=role_text,
            font=(FONT_FAMILY_BOLD[0], 9, "bold"),
            text_color=accent_color
        ).pack(padx=6, pady=2)

        # Smooth hover effect
        def _on_enter(e):
            card.configure(
                border_color="#7c3aed",
                fg_color=("#e5e7eb", "#1f1838")
            )

        def _on_leave(e):
            card.configure(
                border_color=COLOR_BORDER,
                fg_color=COLOR_WIDGET_BACKGROUND
            )

        card.bind("<Enter>", _on_enter)
        card.bind("<Leave>", _on_leave)
        body.bind("<Enter>", _on_enter)
        body.bind("<Leave>", _on_leave)

    def show_no_supporters(container):
        card = ctk.CTkFrame(container, **SECTION_STYLE)
        card.pack(fill="x", pady=20)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(padx=40, pady=32)

        icon_frame = ctk.CTkFrame(
            content, width=56, height=56, corner_radius=28, fg_color=COLOR_BORDER
        )
        icon_frame.pack()
        _users_icon = load_icon("users_icon.png", size=(26, 26))
        ctk.CTkLabel(
            icon_frame,
            text="" if _users_icon else "...",
            image=_users_icon,
            text_color=COLOR_TEXT_SECONDARY
        ).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            content,
            text="No Supporters Found",
            font=FONT_SECTION_TITLE,
            text_color=COLOR_TEXT_SECONDARY
        ).pack(pady=(16, 6))

        ctk.CTkLabel(
            content,
            text="Be the first to join and support the VioletWing community!",
            font=FONT_SUBTITLE,
            text_color=COLOR_TEXT_SECONDARY
        ).pack()

    def show_error(loading_card, error_msg):
        if loading_card.winfo_exists():
            loading_card.destroy()

        err_card = ctk.CTkFrame(content_frame, **SECTION_STYLE)
        err_card.pack(fill="x", pady=20)

        content = ctk.CTkFrame(err_card, fg_color="transparent")
        content.pack(padx=40, pady=32)

        ctk.CTkLabel(
            content,
            text="Failed to Load Supporters",
            font=FONT_SECTION_TITLE,
            text_color="#ef4444"
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            content,
            text=error_msg,
            font=FONT_ITEM_DESCRIPTION,
            text_color=COLOR_TEXT_SECONDARY
        ).pack()

    threading.Thread(target=fetch_supporters, daemon=True).start()