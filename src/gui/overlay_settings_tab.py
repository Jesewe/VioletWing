import re
import customtkinter as ctk
from src.gui.icon_loader import icon_label
from src.utils.config_manager import COLOR_CHOICES
from src.utils.utility import Utility
from src.gui.components import create_section_frame, create_section_header, build_item_scaffold, create_scrollable_frame
from src.gui.theme import (
    COLOR_BACKGROUND,
    CHECKBOX_STYLE, COMBOBOX_STYLE, ENTRY_STYLE, SLIDER_STYLE,
    FONT_TITLE, FONT_SUBTITLE, FONT_TABULAR, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_BORDER, COLOR_WIDGET_BORDER,
)

# Validates a complete #RRGGBB hex string.
_HEX_RE = re.compile(r'^#[0-9A-Fa-f]{6}$')
# Named presets + sentinel shown when the active color is not in the preset list.
_COMBO_VALUES = list(COLOR_CHOICES.keys()) + ["Custom"]

def populate_overlay_settings(main_window, frame):
    """Populate the Overlay Settings tab."""
    settings = create_scrollable_frame(frame, main_window)

    create_title_section(settings)

    _create_bounding_box_section(main_window, settings)
    _create_snaplines_section(main_window, settings)
    _create_player_info_section(main_window, settings)
    _create_game_info_section(main_window, settings)
    _create_colors_and_team_section(main_window, settings)

def create_title_section(parent):
    title_frame = ctk.CTkFrame(parent, fg_color="transparent")
    title_frame.pack(fill="x", pady=(0, 40))
    icon_label(title_frame, "layer_group_icon.png", size=(38, 38), padx=(0, 16))
    ctk.CTkLabel(title_frame, text="Overlay Settings", font=FONT_TITLE,
                 text_color=COLOR_TEXT_PRIMARY, anchor="w").pack(side="left")
    ctk.CTkLabel(title_frame, text="Configure your ESP overlay preferences",
                 font=FONT_SUBTITLE, text_color=COLOR_TEXT_SECONDARY,
                 anchor="w").pack(side="left", padx=(20, 0), pady=(10, 0))

def _create_bounding_box_section(main_window, parent):
    section = create_section_frame(parent)
    create_section_header(section, "Bounding Box Configuration", "Settings for enemy bounding boxes", icon_file="vector_square_icon.png")

    wf = build_item_scaffold(section, "Visibility", "")
    _make_checkbox(wf, "enable_box", main_window, text="Bounding Box").pack(side="left", padx=(0, 15))
    _make_checkbox(wf, "enable_skeleton", main_window, text="Skeleton ESP").pack(side="left")

    wf_color = build_item_scaffold(section, "Box Color", "")
    _make_color_picker(wf_color, "box_color_hex", main_window).pack(side="left")

    wf2 = build_item_scaffold(section, "Line Thickness", "")
    _make_slider(wf2, "box_line_thickness", main_window).pack(side="right")

    wf3 = build_item_scaffold(section, "Target FPS", "", is_last=True)
    _make_fps_entry(wf3, "target_fps", main_window).pack(side="right")

def _create_snaplines_section(main_window, parent):
    section = create_section_frame(parent)
    create_section_header(section, "Snaplines Configuration", "Settings for snaplines to enemies", icon_file="crosshairs_icon.png")

    wf = build_item_scaffold(section, "Snaplines", "")
    _make_checkbox(wf, "draw_snaplines", main_window, text="Enabled").pack(side="left", padx=(0, 15))

    wf_color = build_item_scaffold(section, "Snaplines Color", "", is_last=True)
    _make_color_picker(wf_color, "snaplines_color_hex", main_window).pack(side="left")

def _create_player_info_section(main_window, parent):
    section = create_section_frame(parent)
    create_section_header(section, "Player Information", "Settings for displaying player details", icon_file="user_icon.png")

    wf = build_item_scaffold(section, "Details", "", is_last=True)
    grid = ctk.CTkFrame(wf, fg_color="transparent")
    grid.pack(side="left", padx=(15, 0))

    _make_checkbox(grid, "draw_nicknames",      main_window, text="Nicknames").grid(row=0, column=0, sticky="w", padx=(0, 20), pady=(0, 10))
    _make_checkbox(grid, "draw_weapon_names",   main_window, text="Weapons").grid(row=0, column=1, sticky="w", padx=(0, 20), pady=(0, 10))
    _make_checkbox(grid, "draw_health_numbers", main_window, text="Health").grid(row=0, column=2, sticky="w", padx=(0, 20), pady=(0, 10))
    _make_checkbox(grid, "draw_flashed",        main_window, text="Flashed").grid(row=0, column=3, sticky="w", padx=(0, 20), pady=(0, 10))
    _make_checkbox(grid, "draw_distance",       main_window, text="Distance").grid(row=0, column=4, sticky="w", pady=(0, 10))

    _make_checkbox(grid, "draw_armor",          main_window, text="Armor").grid(row=1, column=0, sticky="w", padx=(0, 20))
    _make_checkbox(grid, "draw_scoped",         main_window, text="Scoped").grid(row=1, column=1, sticky="w", padx=(0, 20))
    _make_checkbox(grid, "draw_reloading",      main_window, text="Reloading").grid(row=1, column=2, sticky="w", padx=(0, 20))
    _make_checkbox(grid, "draw_defusing",       main_window, text="Defusing").grid(row=1, column=3, sticky="w", padx=(0, 20))
    _make_checkbox(grid, "draw_money",          main_window, text="Money").grid(row=1, column=4, sticky="w")

def _create_game_info_section(main_window, parent):
    section = create_section_frame(parent)
    create_section_header(section, "Game Information", "Settings for global game information", icon_file="layer_group_icon.png")

    wf = build_item_scaffold(section, "Bomb Timer", "")
    _make_checkbox(wf, "draw_bomb_timer", main_window, text="Enabled").pack(side="left", padx=(0, 20))
    _make_combobox(wf, "bomb_timer_position", main_window).pack(side="left")

    wf2 = build_item_scaffold(section, "Sniper Crosshair", "")
    _make_checkbox(wf2, "draw_sniper_crosshair", main_window, text="Enabled").pack(side="left")

    wf3 = build_item_scaffold(section, "Spectator List", "", is_last=True)
    _make_checkbox(wf3, "draw_spectators", main_window, text="Enabled").pack(side="left", padx=(0, 20))
    _make_combobox(wf3, "spectators_position", main_window).pack(side="left", padx=(0, 20))
    _make_checkbox(wf3, "spectators_detailed", main_window, text="Detailed").pack(side="left", padx=(0, 20))
    _make_checkbox(wf3, "spectators_self_only", main_window, text="Self Only").pack(side="left")

def _create_colors_and_team_section(main_window, parent):
    section = create_section_frame(parent)
    create_section_header(section, "Colors & Team", "Configure text and teammate colors", icon_file="font_icon.png")

    wf = build_item_scaffold(section, "Main Text Color", "")
    _make_color_picker(wf, "text_color_hex", main_window).pack(side="left")
    
    wf_font = build_item_scaffold(section, "Overlay Font", "")
    _make_combobox(wf_font, "overlay_font", main_window,
                   override_values=["Inter", "JetBrainsMono", "Exo 2", "Rubik", "Roboto", "Open Sans", "Fira Code"],
                   default_val="Inter").pack(side="left")
    
    wf_wpn = build_item_scaffold(section, "Weapon Text Color", "")
    _make_color_picker(wf_wpn, "weapon_color_hex", main_window).pack(side="left")

    wf2 = build_item_scaffold(section, "Team ESP", "")
    _make_checkbox(wf2, "draw_teammates", main_window, text="Teammates").pack(side="left")

    wf3 = build_item_scaffold(section, "Teammate Color", "", is_last=True)
    _make_color_picker(wf3, "teammate_color_hex", main_window).pack(side="left")

def _make_checkbox(parent, key, main_window, text=""):
    var = ctk.BooleanVar(value=main_window.overlay.config["Overlay"].get(key, False))
    cb = ctk.CTkCheckBox(
        parent, text=text, variable=var,
        command=lambda: main_window.save_settings(show_message=False),
        **CHECKBOX_STYLE,
    )
    main_window.ui_bridge.register(key, var=var)
    return cb

def _make_combobox(parent, key, main_window, override_values=None, default_val=None):
    if override_values is not None:
        values = override_values
        default_val = main_window.overlay.config["Overlay"].get(key, default_val if default_val else values[0])
    elif key in ("bomb_timer_position", "spectators_position"):
        values = ["Center-Left", "Center-Right", "Center-Top", "Center-Bottom"]
        default_val = main_window.overlay.config["Overlay"].get(key, "Center-Right" if key == "spectators_position" else "Center-Left")
    else:
        values = ["Option 1", "Option 2"]
        default_val = values[0]
        
    initial = main_window.overlay.config["Overlay"].get(key, default_val)
    var = ctk.StringVar(value=initial)
    
    combo = ctk.CTkComboBox(
        parent, values=values, state="readonly", justify="center",
        variable=var, width=150, height=35, corner_radius=8,
        fg_color=COMBOBOX_STYLE["fg_color"],
        text_color=COMBOBOX_STYLE["text_color"],
        font=COMBOBOX_STYLE["font"],
        dropdown_font=COMBOBOX_STYLE["dropdown_font"],
        button_color=COMBOBOX_STYLE["button_color"],
        button_hover_color=COMBOBOX_STYLE["button_hover_color"],
        dropdown_fg_color=COMBOBOX_STYLE["dropdown_fg_color"],
        dropdown_hover_color=COMBOBOX_STYLE["dropdown_hover_color"],
        dropdown_text_color=COMBOBOX_STYLE["dropdown_text_color"],
        command=lambda _: main_window.save_settings(show_message=False)
    )
    combo.pack_configure = combo.pack
    main_window.ui_bridge.register(key, var=var)
    return combo

def _make_slider(parent, key, main_window):
    if key == "target_fps":
        _make_fps_entry(parent, key, main_window)
        return

    container = ctk.CTkFrame(parent, fg_color="transparent")

    value_frame = ctk.CTkFrame(container, corner_radius=8, fg_color=COLOR_BORDER,
                                width=60, height=35)
    value_frame.pack(side="right", padx=(15, 0))
    value_frame.pack_propagate(False)

    initial = main_window.overlay.config["Overlay"].get(key, 1.0)
    value_label = ctk.CTkLabel(
        value_frame, text=f"{initial:.1f}",
        font=FONT_TABULAR, text_color=COLOR_TEXT_PRIMARY,
    )
    value_label.pack(expand=True)

    def _on_change(val):
        value_label.configure(text=f"{val:.1f}")
        main_window.save_settings(show_message=False)

    widget = ctk.CTkSlider(container, from_=0.5, to=5.0, number_of_steps=9,
                            command=_on_change, **SLIDER_STYLE)
    widget.set(initial)
    widget.pack(side="left")

    container.pack_configure = container.pack
    main_window.ui_bridge.register(key, widget=widget, value_label=value_label, fmt=".1f")
    return container

def _make_fps_entry(parent, key, main_window):
    """Entry-based FPS input. Accepts any integer in [60, 420] and saves on commit.

    A slider is the wrong widget here: the value space is large, the meaningful
    values are specific (144, 165, 240 ...), and users know the number they want.
    """
    _FPS_MIN = 60
    _FPS_MAX = 420

    initial = int(main_window.overlay.config["Overlay"].get(key, _FPS_MIN))

    container = ctk.CTkFrame(parent, fg_color="transparent")

    entry = ctk.CTkEntry(
        container,
        width=80, height=45, justify="center",
        corner_radius=ENTRY_STYLE["corner_radius"],
        border_width=ENTRY_STYLE["border_width"],
        border_color=ENTRY_STYLE["border_color"],
        fg_color=ENTRY_STYLE["fg_color"],
        text_color=ENTRY_STYLE["text_color"],
        font=ENTRY_STYLE["font"],
        placeholder_text="144",
    )
    entry.insert(0, str(initial))
    entry.pack(side="left")

    ctk.CTkLabel(
        container, text=f"fps  ({_FPS_MIN}–{_FPS_MAX})",
        font=ENTRY_STYLE["font"], text_color=COLOR_TEXT_SECONDARY,
    ).pack(side="left", padx=(8, 0))

    def _commit(_event=None):
        raw = entry.get().strip()
        try:
            val = int(float(raw))
            if not (_FPS_MIN <= val <= _FPS_MAX):
                raise ValueError
        except (ValueError, TypeError):
            # Revert to the last accepted value and flash the border.
            entry.delete(0, "end")
            entry.insert(0, str(int(float(main_window.ui_bridge.get_value(key) or initial))))
            entry.configure(border_color="#ef4444")
            parent.after(900, lambda: entry.configure(border_color=ENTRY_STYLE["border_color"]))
            return
        entry.delete(0, "end")
        entry.insert(0, str(val))
        main_window.save_settings(show_message=False)

    entry.bind("<FocusOut>", _commit)
    entry.bind("<Return>",   _commit)

    container.pack_configure = container.pack
    # refresh_cb keeps the entry in sync when update_ui_from_config() pushes a new value.
    main_window.ui_bridge.register(
        key, widget=entry,
        refresh_cb=lambda v: (entry.delete(0, "end"), entry.insert(0, str(int(float(v))))),
    )
    return container

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

    # Swatch - live colored preview square
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

    # Hex entry - free-form input, validated on commit
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

    row.pack_configure = row.pack
    return row