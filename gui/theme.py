"""
Centralized theme for the application's UI.
"""

# Font families
FONT_FAMILY_BOLD = ("Chivo", 0, "bold")
FONT_FAMILY_REGULAR = ("Gambetta", 0)

# Font sizes
FONT_SIZE_H1 = 36
FONT_SIZE_H2 = 24
FONT_SIZE_H3 = 16
FONT_SIZE_H4 = 14
FONT_SIZE_P = 13

# Colors (Light Mode, Dark Mode)
COLOR_TEXT_PRIMARY = ("#1f2937", "#ffffff")
COLOR_TEXT_SECONDARY = ("#64748b", "#94a3b8")
COLOR_BACKGROUND = ("#ffffff", "#1a1b23")
COLOR_BORDER = ("#e2e8f0", "#2d3748")
COLOR_WIDGET_BACKGROUND = ("#f8fafc", "#252830")

# Primary Button Colors
COLOR_BUTTON_PRIMARY_FG = ("#0d9488", "#14b8a6")
COLOR_BUTTON_PRIMARY_HOVER = ("#0f766e", "#0d9488")
COLOR_BUTTON_PRIMARY_BORDER = ("#a7f3d0", "#134e4a")
COLOR_BUTTON_PRIMARY_TEXT = "#ffffff"

# Danger Button Colors
COLOR_BUTTON_DANGER_FG = ("#dc2626", "#ef4444")
COLOR_BUTTON_DANGER_HOVER = ("#b91c1c", "#dc2626")
COLOR_BUTTON_DANGER_BORDER = ("#fecaca", "#7f1d1d")
COLOR_BUTTON_DANGER_TEXT = "#ffffff"

# Accent Colors (for checkboxes, option menus)
COLOR_ACCENT_FG = ("#8e44ad", "#8e44ad")
COLOR_ACCENT_HOVER = ("#9b59b6", "#9b59b6")
COLOR_ACCENT_BUTTON = ("#8e44ad", "#8e44ad")
COLOR_ACCENT_BUTTON_HOVER = ("#9b59b6", "#9b59b6")

# Widget-specific Colors
COLOR_WIDGET_BORDER = ("#d1d5db", "#374151")
COLOR_WIDGET_FG = ("#ffffff", "#1f2937")
COLOR_SLIDER_BUTTON = ("#ffffff", "#ffffff")
COLOR_SLIDER_BUTTON_HOVER = ("#f8fafc", "#f8fafc")
COLOR_DROPDOWN_HOVER = ("#f8fafc", "#2d3748")

# Font Styles
FONT_TITLE = (FONT_FAMILY_BOLD[0], FONT_SIZE_H1, FONT_FAMILY_BOLD[2])
FONT_SUBTITLE = (FONT_FAMILY_REGULAR[0], FONT_SIZE_H3)
FONT_SECTION_TITLE = (FONT_FAMILY_BOLD[0], FONT_SIZE_H2, FONT_FAMILY_BOLD[2])
FONT_SECTION_DESCRIPTION = (FONT_FAMILY_REGULAR[0], FONT_SIZE_H4)
FONT_ITEM_LABEL = (FONT_FAMILY_BOLD[0], FONT_SIZE_H3, FONT_FAMILY_BOLD[2])
FONT_ITEM_DESCRIPTION = (FONT_FAMILY_REGULAR[0], FONT_SIZE_P)
FONT_WIDGET = (FONT_FAMILY_BOLD[0], FONT_SIZE_H4, FONT_FAMILY_BOLD[2])
FONT_DROPDOWN = (FONT_FAMILY_REGULAR[0], FONT_SIZE_P)

# Component Styles
SECTION_STYLE = {
    "corner_radius": 20,
    "fg_color": COLOR_BACKGROUND,
    "border_width": 2,
    "border_color": COLOR_BORDER
}

SETTING_ITEM_STYLE = {
    "corner_radius": 12,
    "fg_color": COLOR_WIDGET_BACKGROUND,
    "border_width": 1,
    "border_color": COLOR_BORDER
}

CHECKBOX_STYLE = {
    "width": 30,
    "height": 30,
    "corner_radius": 8,
    "border_width": 2,
    "fg_color": COLOR_ACCENT_FG,
    "hover_color": COLOR_ACCENT_HOVER,
    "checkmark_color": "#ffffff",
}

ENTRY_STYLE = {
    "width": 220,
    "height": 45,
    "corner_radius": 12,
    "border_width": 2,
    "border_color": COLOR_WIDGET_BORDER,
    "fg_color": COLOR_WIDGET_FG,
    "text_color": COLOR_TEXT_PRIMARY,
    "font": FONT_WIDGET,
}

SLIDER_STYLE = {
    "width": 200,
    "height": 20,
    "corner_radius": 10,
    "button_corner_radius": 10,
    "border_width": 0,
    "fg_color": COLOR_BORDER,
    "progress_color": COLOR_ACCENT_FG,
    "button_color": COLOR_SLIDER_BUTTON,
    "button_hover_color": COLOR_SLIDER_BUTTON_HOVER,
}

COMBOBOX_STYLE = {
    "width": 180,
    "height": 45,
    "corner_radius": 12,
    "fg_color": COLOR_WIDGET_FG,
    "text_color": COLOR_TEXT_PRIMARY,
    "font": FONT_WIDGET,
    "dropdown_font": FONT_DROPDOWN,
    "button_color": COLOR_ACCENT_FG,
    "button_hover_color": COLOR_ACCENT_HOVER,
    "dropdown_fg_color": COLOR_BACKGROUND,
    "dropdown_hover_color": COLOR_DROPDOWN_HOVER,
    "dropdown_text_color": COLOR_TEXT_PRIMARY,
}

BUTTON_STYLE_PRIMARY = {
    "font": (FONT_FAMILY_BOLD[0], FONT_SIZE_H3, FONT_FAMILY_BOLD[2]),
    "corner_radius": 16,
    "fg_color": COLOR_BUTTON_PRIMARY_FG,
    "hover_color": COLOR_BUTTON_PRIMARY_HOVER,
    "border_width": 2,
    "border_color": COLOR_BUTTON_PRIMARY_BORDER,
    "text_color": COLOR_BUTTON_PRIMARY_TEXT,
    "height": 56
}

BUTTON_STYLE_DANGER = {
    "font": (FONT_FAMILY_BOLD[0], FONT_SIZE_H3, FONT_FAMILY_BOLD[2]),
    "corner_radius": 16,
    "fg_color": COLOR_BUTTON_DANGER_FG,
    "hover_color": COLOR_BUTTON_DANGER_HOVER,
    "border_width": 2,
    "border_color": COLOR_BUTTON_DANGER_BORDER,
    "text_color": COLOR_BUTTON_DANGER_TEXT,
    "height": 56
}