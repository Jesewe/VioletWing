import customtkinter as ctk
from gui.icon_loader import icon_label
from classes.config_manager import COLOR_CHOICES
from classes.utility import Utility
from gui.theme import (CHECKBOX_STYLE, COMBOBOX_STYLE, ENTRY_STYLE, SLIDER_STYLE,
                        SECTION_STYLE, SETTING_ITEM_STYLE, FONT_TITLE, FONT_SUBTITLE,
                        FONT_SECTION_TITLE, FONT_SECTION_DESCRIPTION, FONT_ITEM_LABEL,
                        FONT_ITEM_DESCRIPTION, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_BORDER)

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
                ("Box Color",           "combo",    "box_color_hex",       "Select color for bounding boxes"),
                ("Target FPS",          "slider",   "target_fps",          "Adjust target FPS for overlay rendering (60-420)"),
            ],
        },
        "Snaplines": {
            "icon": "crosshairs_icon.png",
            "title": "Snaplines Configuration",
            "description": "Settings for snaplines to enemies",
            "settings": [
                ("Draw Snaplines",  "checkbox", "draw_snaplines",      "Toggle drawing of snaplines to enemies"),
                ("Snaplines Color", "combo",    "snaplines_color_hex", "Select color for snaplines"),
            ],
        },
        "Text": {
            "icon": "font_icon.png",
            "title": "Text Configuration",
            "description": "Settings for text display",
            "settings": [
                ("Text Color", "combo", "text_color_hex", "Select color for text"),
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
                ("Draw Teammates", "checkbox", "draw_teammates",    "Show teammates on the overlay"),
                ("Teammate Color", "combo",    "teammate_color_hex", "Select color for teammates"),
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
        "combo":    _make_combobox,
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

def _make_combobox(parent, key, main_window):
    current_hex = main_window.overlay.config["Overlay"].get(key, "#FFFFFF")
    var = ctk.StringVar(value=Utility.get_color_name_from_hex(current_hex))

    ctk.CTkComboBox(
        parent, values=list(COLOR_CHOICES.keys()), state="readonly",
        justify="center", variable=var,
        command=lambda _: main_window.save_settings(show_message=False),
        **COMBOBOX_STYLE,
    ).pack()

    main_window.ui_bridge.register(key, var=var)