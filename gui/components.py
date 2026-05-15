import customtkinter as ctk
from gui.icon_loader import icon_label
from gui.theme import (
    FONT_SECTION_TITLE, FONT_SECTION_DESCRIPTION,
    FONT_ITEM_LABEL, FONT_ITEM_DESCRIPTION,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    SECTION_STYLE, SETTING_ITEM_STYLE,
)

def create_section_frame(parent) -> ctk.CTkFrame:
    """Create and pack a standard section card. Returns the frame."""
    section = ctk.CTkFrame(parent, **SECTION_STYLE)
    section.pack(fill="x", pady=(0, 30))
    return section

def create_section_header(parent, title, subtitle, icon_file=None) -> ctk.CTkFrame:
    """Create and pack a section header with optional icon.

    Returns the header frame so callers can attach additional widgets
    (e.g. an OptionMenu for offset source or weapon type).
    """
    header = ctk.CTkFrame(parent, fg_color="transparent")
    header.pack(fill="x", padx=40, pady=(40, 30))

    title_row = ctk.CTkFrame(header, fg_color="transparent")
    title_row.pack(side="left", fill="y")

    if icon_file:
        icon_label(title_row, icon_file, size=(22, 22), padx=(0, 10))

    ctk.CTkLabel(
        title_row, text=title, font=FONT_SECTION_TITLE,
        text_color=COLOR_TEXT_PRIMARY, anchor="w",
    ).pack(side="left")

    ctk.CTkLabel(
        header, text=subtitle, font=FONT_SECTION_DESCRIPTION,
        text_color=COLOR_TEXT_SECONDARY, anchor="e",
    ).pack(side="right")

    return header

def build_item_scaffold(parent, label_text, description, is_last=False) -> ctk.CTkFrame:
    """Build the standard setting-item card (label on left, widget slot on right).

    Bottom padding is 40 px for the last item in a section, 30 px otherwise —
    matching the visual rhythm used across all settings tabs.

    Returns the right-side widget frame for the caller to populate.
    """
    item_frame = ctk.CTkFrame(parent, fg_color="transparent")
    item_frame.pack(fill="x", padx=40, pady=(0, 40 if is_last else 30))

    container = ctk.CTkFrame(item_frame, **SETTING_ITEM_STYLE)
    container.pack(fill="x")

    content = ctk.CTkFrame(container, fg_color="transparent")
    content.pack(fill="x", padx=25, pady=25)

    lf = ctk.CTkFrame(content, fg_color="transparent")
    lf.pack(side="left", fill="x", expand=True)
    ctk.CTkLabel(
        lf, text=label_text, font=FONT_ITEM_LABEL,
        text_color=COLOR_TEXT_PRIMARY, anchor="w",
    ).pack(fill="x", pady=(0, 4))
    ctk.CTkLabel(
        lf, text=description, font=FONT_ITEM_DESCRIPTION,
        text_color=COLOR_TEXT_SECONDARY, anchor="w", wraplength=400,
    ).pack(fill="x")

    wf = ctk.CTkFrame(content, fg_color="transparent")
    wf.pack(side="right", padx=(30, 0))
    return wf