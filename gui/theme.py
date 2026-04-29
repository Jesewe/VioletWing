"""
Centralized theme for the application's UI.
"""

# Font families
FONT_FAMILY_BOLD = ("Outfit", 0, "bold")
FONT_FAMILY_REGULAR = ("JetBrainsMono", 0)

# Font sizes
FONT_SIZE_H1 = 36
FONT_SIZE_H2 = 24
FONT_SIZE_H3 = 16
FONT_SIZE_H4 = 14
FONT_SIZE_P = 13

# Core violet palette (single source for brand color)
COLOR_VIOLET =        ("#6d28d9", "#7c3aed")
COLOR_VIOLET_HOVER =  ("#5b21b6", "#6d28d9")
COLOR_VIOLET_BORDER = ("#ddd6fe", "#3b1f7a")
COLOR_VIOLET_SUBTLE = ("#ede9fe", "#1e0f4a")  # badge / tinted bg

# Colors (Light Mode, Dark Mode)
COLOR_TEXT_PRIMARY =      ("#1f2937", "#f0ebff")
COLOR_TEXT_SECONDARY =    ("#64748b", "#7c6fa0")
COLOR_BACKGROUND =        ("#f5f3ff", "#0d0a1a")
COLOR_BORDER =            ("#d8b4fe", "#2a1d4e")
COLOR_WIDGET_BACKGROUND = ("#ede9fe", "#150f2a")
COLOR_HEADER_BG =         ("#1a0b3b", "#08051a")

# Primary Button Colors  (violet, not teal)
COLOR_BUTTON_PRIMARY_FG =     COLOR_VIOLET
COLOR_BUTTON_PRIMARY_HOVER =  COLOR_VIOLET_HOVER
COLOR_BUTTON_PRIMARY_BORDER = COLOR_VIOLET_BORDER
COLOR_BUTTON_PRIMARY_TEXT =   "#ffffff"

# Danger Button Colors
COLOR_BUTTON_DANGER_FG =     ("#dc2626", "#ef4444")
COLOR_BUTTON_DANGER_HOVER =  ("#b91c1c", "#dc2626")
COLOR_BUTTON_DANGER_BORDER = ("#fecaca", "#7f1d1d")
COLOR_BUTTON_DANGER_TEXT =   "#ffffff"

# Accent Colors - alias to unified violet
COLOR_ACCENT_FG =           COLOR_VIOLET
COLOR_ACCENT_HOVER =        COLOR_VIOLET_HOVER
COLOR_ACCENT_BUTTON =       COLOR_VIOLET
COLOR_ACCENT_BUTTON_HOVER = COLOR_VIOLET_HOVER

# Widget-specific Colors
COLOR_WIDGET_BORDER =       ("#c4b5fd", "#3d2a6e")
COLOR_WIDGET_FG =           ("#ffffff", "#1a1030")
COLOR_SLIDER_BUTTON =       ("#ffffff", "#ffffff")
COLOR_SLIDER_BUTTON_HOVER = ("#f5f3ff", "#f5f3ff")
COLOR_DROPDOWN_HOVER =      ("#ede9fe", "#1e0f4a")

# Sidebar
COLOR_SIDEBAR_BG =         ("#f0ebff", "#0b0817")
COLOR_SIDEBAR_ACTIVE_BG =  ("#ede9fe", "#1a0f35")
COLOR_SIDEBAR_INDICATOR =  ("#7c3aed", "#7c3aed")

# Font Styles
FONT_TITLE =               (FONT_FAMILY_BOLD[0],    FONT_SIZE_H1, FONT_FAMILY_BOLD[2])
FONT_SUBTITLE =            (FONT_FAMILY_REGULAR[0], FONT_SIZE_H3)
FONT_SECTION_TITLE =       (FONT_FAMILY_BOLD[0],    FONT_SIZE_H2, FONT_FAMILY_BOLD[2])
FONT_SECTION_DESCRIPTION = (FONT_FAMILY_REGULAR[0], FONT_SIZE_H4)
FONT_ITEM_LABEL =          (FONT_FAMILY_BOLD[0],    FONT_SIZE_H3, FONT_FAMILY_BOLD[2])
FONT_ITEM_DESCRIPTION =    (FONT_FAMILY_REGULAR[0], FONT_SIZE_P)
FONT_WIDGET =              (FONT_FAMILY_BOLD[0],    FONT_SIZE_H4, FONT_FAMILY_BOLD[2])
FONT_DROPDOWN =            (FONT_FAMILY_REGULAR[0], FONT_SIZE_P)

# Component Styles
SECTION_STYLE = {
    "corner_radius": 16,
    "fg_color": COLOR_BACKGROUND,
    "border_width": 1,
    "border_color": COLOR_BORDER
}

SETTING_ITEM_STYLE = {
    "corner_radius": 10,
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
    "corner_radius": 10,
    "border_width": 1,
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
    "corner_radius": 10,
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
    "corner_radius": 12,
    "fg_color": COLOR_BUTTON_PRIMARY_FG,
    "hover_color": COLOR_BUTTON_PRIMARY_HOVER,
    "border_width": 1,
    "border_color": COLOR_BUTTON_PRIMARY_BORDER,
    "text_color": COLOR_BUTTON_PRIMARY_TEXT,
    "height": 48
}

BUTTON_STYLE_DANGER = {
    "font": (FONT_FAMILY_BOLD[0], FONT_SIZE_H3, FONT_FAMILY_BOLD[2]),
    "corner_radius": 12,
    "fg_color": COLOR_BUTTON_DANGER_FG,
    "hover_color": COLOR_BUTTON_DANGER_HOVER,
    "border_width": 1,
    "border_color": COLOR_BUTTON_DANGER_BORDER,
    "text_color": COLOR_BUTTON_DANGER_TEXT,
    "height": 48
}
