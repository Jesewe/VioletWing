import re
import customtkinter as ctk
from gui.icon_loader import icon_label
from classes.config_manager import COLOR_CHOICES
from classes.utility import Utility
from gui.theme import (CHECKBOX_STYLE, COMBOBOX_STYLE, ENTRY_STYLE, SLIDER_STYLE,
                        SECTION_STYLE, SETTING_ITEM_STYLE, FONT_TITLE, FONT_SUBTITLE,
                        FONT_SECTION_TITLE, FONT_SECTION_DESCRIPTION, FONT_ITEM_LABEL,
                        FONT_ITEM_DESCRIPTION, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
                        COLOR_BORDER, COLOR_WIDGET_BORDER)

# Validates a complete #RRGGBB hex string.
_HEX_RE = re.compile(r'^#[0-9A-Fa-f]{6}$')
# Named presets + sentinel shown when the active color is not in the preset list.
_COMBO_VALUES = list(COLOR_CHOICES.keys()) + ["Custom"]

def populate_overlay_settings(main_window, frame):
    """Populate the Overlay Settings tab."""
    settings = ctk.CTkScrollableFrame(frame, fg_color="transparent")
    settings.pack(fill="both", expand=True, padx=40, pady=40)
    settings._parent_canvas.configure(yscrollincrement=5)

    create_title_section(settings)

    sections = {
        "Bounding Box": {
            "icon": "vector_square_icon.png",
            "title": "Bounding Box Configuration",
            "description": "Settings for enemy bounding boxes",
            "settings": [
                ("Enable Bounding Box", "checkbox", "enable_box",          "Toggle visibility of enemy bounding boxes"),
                ("Enable Skeleton ESP", "checkbox", "enable_skeleton",     "Toggle visibility of player skeletons"),
                ("Line Thickness",      "slider",   "box_line_thickness",  "Adjust thickness of bounding box lines (0.5-5.0)"),
                ("Box Color",           "color",    "box_color_hex",       "Select color for bounding boxes"),
                ("Target FPS",          "slider",   "target_fps",          "Adjust target FPS for overlay rendering (60-420)"),
            ],
        },
        "Snaplines": {
            "icon": "crosshairs_icon.png",
            "title": "Snaplines Configuration",
            "description": "Settings for snaplines to enemies",
            "settings": [
                ("Draw Snaplines",  "checkbox", "draw_snaplines",      "Toggle drawing of snaplines to enemies"),
                ("Snaplines Color", "color",    "snaplines_color_hex", "Select color for snaplines"),
            ],
        },
        "Text": {
            "icon": "font_icon.png",
            "title": "Text Configuration",
            "description": "Settings for text display",
            "settings": [
                ("Text Color", "color", "text_color_hex", "Select color for text"),
            ],
        },
        "Player Info": {
            "icon": "user_icon.png",
            "title": "Player Information",
            "description": "Settings for displaying player details",
            "settings": [
                ("Draw Health Numbers", "checkbox", "draw_health_numbers",  "Show health numbers above players"),
                ("Draw Nicknames",      "checkbox", "draw_nicknames",       "Display player nicknames"),
                ("Use Transliteration", "checkbox", "use_transliteration",  "Transliterate non-Latin characters"),
            ],
        },
        "Team": {
            "icon": "users_icon.png",
            "title": "Team Configuration",
            "description": "Settings for teammate display",
            "settings": [
                ("Draw Teammates", "checkbox", "draw_teammates",     "Show teammates on the overlay"),
                ("Teammate Color", "color",    "teammate_color_hex", "Select color for teammates"),
            ],
        },
    }

    for data in sections.values():
        _create_section(main_window, settings, data["title"], data["description"],
                        data["settings"], data.get("icon"))

def create_title_section(parent):
    title_frame = ctk.CTkFrame(parent, fg_color="transparent")
    title_frame.pack(fill="x", pady=(0, 40))
    icon_label(title_frame, "layer_group_icon.png", size=(38, 38), padx=(0, 16))
    ctk.CTkLabel(title_frame, text="Overlay Settings", font=FONT_TITLE,
                 text_color=COLOR_TEXT_PRIMARY, anchor="w").pack(side="left")
    ctk.CTkLabel(title_frame, text="Configure your ESP overlay preferences",
                 font=FONT_SUBTITLE, text_color=COLOR_TEXT_SECONDARY,
                 anchor="w").pack(side="left", padx=(20, 0), pady=(10, 0))

def _create_section(main_window, parent, title, description, settings_list, icon_file=None):
    section = ctk.CTkFrame(parent, **SECTION_STYLE)
    section.pack(fill="x", pady=(0, 30))

    header = ctk.CTkFrame(section, fg_color="transparent")
    header.pack(fill="x", padx=40, pady=(40, 30))
    icon_label(header, icon_file, size=(22, 22), padx=(0, 10))
    ctk.CTkLabel(header, text=title, font=FONT_SECTION_TITLE,
                 text_color=COLOR_TEXT_PRIMARY, anchor="w").pack(side="left")
    ctk.CTkLabel(header, text=description, font=FONT_SECTION_DESCRIPTION,
                 text_color=COLOR_TEXT_SECONDARY, anchor="e").pack(side="right")

    for i, (label, widget_type, key, desc) in enumerate(settings_list):
        _create_setting_item(
            section, label, desc, widget_type, key, main_window,
            is_last=(i == len(settings_list) - 1),
        )

def _create_setting_item(parent, label_text, description, widget_type, key, main_window, is_last=False):
    item_frame = ctk.CTkFrame(parent, fg_color="transparent")
    item_frame.pack(fill="x", padx=40, pady=(0, 30 if not is_last else 40))

    container = ctk.CTkFrame(item_frame, **SETTING_ITEM_STYLE)
    container.pack(fill="x")

    content = ctk.CTkFrame(container, fg_color="transparent")
    content.pack(fill="x", padx=25, pady=25)

    lf = ctk.CTkFrame(content, fg_color="transparent")
    lf.pack(side="left", fill="x", expand=True)
    ctk.CTkLabel(lf, text=label_text, font=FONT_ITEM_LABEL,
                 text_color=COLOR_TEXT_PRIMARY, anchor="w").pack(fill="x", pady=(0, 4))
    ctk.CTkLabel(lf, text=description, font=FONT_ITEM_DESCRIPTION,
                 text_color=COLOR_TEXT_SECONDARY, anchor="w", wraplength=400).pack(fill="x")

    wf = ctk.CTkFrame(content, fg_color="transparent")
    wf.pack(side="right", padx=(30, 0))

    creators = {
        "checkbox": _make_checkbox,
        "slider":   _make_slider,
        "color":    _make_color_picker,
    }
    if widget_type in creators:
        creators[widget_type](wf, key, main_window)

def _make_checkbox(parent, key, main_window):
    var = ctk.BooleanVar(value=main_window.overlay.config["Overlay"].get(key, False))
    ctk.CTkCheckBox(
        parent, text="", variable=var,
        command=lambda: main_window.save_settings(show_message=False),
        **CHECKBOX_STYLE,
    ).pack()
    main_window.ui_bridge.register(key, var=var)

def _make_slider(parent, key, main_window):
    container = ctk.CTkFrame(parent, fg_color="transparent")
    container.pack()

    value_frame = ctk.CTkFrame(container, corner_radius=8, fg_color=COLOR_BORDER,
                                width=60, height=35)
    value_frame.pack(side="right", padx=(15, 0))
    value_frame.pack_propagate(False)

    initial = main_window.overlay.config["Overlay"].get(key, 60 if key == "target_fps" else 1.0)
    fmt = ".0f" if key == "target_fps" else ".1f"
    value_label = ctk.CTkLabel(value_frame, text=f"{initial:{fmt}}",
                                font=ENTRY_STYLE["font"], text_color=COLOR_TEXT_PRIMARY)
    value_label.pack(expand=True)

    from_v = 60.0    if key == "target_fps" else 0.5
    to_v   = 420.0   if key == "target_fps" else 5.0
    steps  = 3       if key == "target_fps" else 9

    def _on_change(val):
        value_label.configure(text=f"{val:{fmt}}")
        main_window.save_settings(show_message=False)

    widget = ctk.CTkSlider(container, from_=from_v, to=to_v, number_of_steps=steps,
                            command=_on_change, **SLIDER_STYLE)
    widget.set(initial)
    widget.pack(side="left")

    # Register with UIConfigBridge so save_settings / update_ui_from_config work uniformly.
    main_window.ui_bridge.register(key, widget=widget, value_label=value_label, fmt=fmt)

def _hex_to_combo_name(hex_val: str) -> str:
    """Return the named preset label for a hex value, or 'Custom' if not in the list."""
    normalized = hex_val.upper()
    for name, code in COLOR_CHOICES.items():
        if code.upper() == normalized:
            return name
    return "Custom"

def _make_color_picker(parent, key, main_window):
    """Composite color picker: live swatch + named-preset combo + free hex entry.

    The UIConfigBridge var stores the hex string directly (e.g. '#FFA500').
    _save_overlay reads this hex and writes it straight to config, eliminating
    the name-to-hex lookup that existed before.
    """
    current_hex = main_window.overlay.config["Overlay"].get(key, "#FFFFFF").upper()
    var = ctk.StringVar(value=current_hex)

    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack()

    # Swatch — live colored preview square
    swatch = ctk.CTkFrame(
        row, width=28, height=28, corner_radius=6,
        fg_color=current_hex, border_width=1, border_color=COLOR_WIDGET_BORDER,
    )
    swatch.pack(side="left", padx=(0, 8))
    swatch.pack_propagate(False)

    # Named-preset combo (read-only; "Custom" sentinel for unknown hex)
    combo_var = ctk.StringVar(value=_hex_to_combo_name(current_hex))
    combo = ctk.CTkComboBox(
        row, values=_COMBO_VALUES, state="readonly",
        justify="center", variable=combo_var,
        width=150, height=45, corner_radius=10,
        fg_color=COMBOBOX_STYLE["fg_color"],
        text_color=COMBOBOX_STYLE["text_color"],
        font=COMBOBOX_STYLE["font"],
        dropdown_font=COMBOBOX_STYLE["dropdown_font"],
        button_color=COMBOBOX_STYLE["button_color"],
        button_hover_color=COMBOBOX_STYLE["button_hover_color"],
        dropdown_fg_color=COMBOBOX_STYLE["dropdown_fg_color"],
        dropdown_hover_color=COMBOBOX_STYLE["dropdown_hover_color"],
        dropdown_text_color=COMBOBOX_STYLE["dropdown_text_color"],
    )
    combo.pack(side="left", padx=(0, 8))

    # Hex entry — free-form input, validated on commit
    entry = ctk.CTkEntry(
        row, width=100, height=45, justify="center",
        corner_radius=ENTRY_STYLE["corner_radius"],
        border_width=ENTRY_STYLE["border_width"],
        border_color=ENTRY_STYLE["border_color"],
        fg_color=ENTRY_STYLE["fg_color"],
        text_color=ENTRY_STYLE["text_color"],
        font=ENTRY_STYLE["font"],
        placeholder_text="#RRGGBB",
    )
    entry.insert(0, current_hex)
    entry.pack(side="left")

    def _apply_hex(hex_val: str, save: bool = True) -> None:
        """Normalize and push a valid hex value to all three sub-widgets."""
        hex_val = hex_val.upper()
        var.set(hex_val)
        swatch.configure(fg_color=hex_val)
        entry.delete(0, "end")
        entry.insert(0, hex_val)
        combo_var.set(_hex_to_combo_name(hex_val))
        if save:
            main_window.save_settings(show_message=False)

    def _on_combo_select(_event=None) -> None:
        name = combo_var.get()
        # "Custom" is display-only; selecting it again does nothing.
        if name in COLOR_CHOICES:
            _apply_hex(COLOR_CHOICES[name])

    def _on_entry_commit(_event=None) -> None:
        raw = entry.get().strip()
        if raw and not raw.startswith("#"):
            raw = "#" + raw
        if _HEX_RE.match(raw):
            _apply_hex(raw)
        else:
            # Revert to the last accepted value and flash the border red.
            entry.delete(0, "end")
            entry.insert(0, var.get())
            entry.configure(border_color="#ef4444")
            parent.after(900, lambda: entry.configure(border_color=ENTRY_STYLE["border_color"]))

    combo.configure(command=_on_combo_select)
    entry.bind("<FocusOut>", _on_entry_commit)
    entry.bind("<Return>",   _on_entry_commit)

    # refresh_cb lets update_ui_from_config() keep the swatch/combo/entry in sync
    # when set_value() is called externally (e.g. config reload or reset to default).
    main_window.ui_bridge.register(key, var=var, refresh_cb=lambda v: _apply_hex(v, save=False))