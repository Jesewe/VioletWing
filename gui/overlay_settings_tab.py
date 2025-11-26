import customtkinter as ctk
from classes.config_manager import COLOR_CHOICES
from classes.utility import Utility
from gui.theme import (CHECKBOX_STYLE, COMBOBOX_STYLE, ENTRY_STYLE, SLIDER_STYLE,
                        SECTION_STYLE, SETTING_ITEM_STYLE, FONT_TITLE, FONT_SUBTITLE, 
                        FONT_SECTION_TITLE, FONT_SECTION_DESCRIPTION, FONT_ITEM_LABEL, 
                        FONT_ITEM_DESCRIPTION, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_BORDER)

def populate_overlay_settings(main_window, frame):
    """
    Populates the Overlay Settings tab with UI elements for configuring overlay preferences.
    All changes are saved in real-time to the configuration.
    """
    # Create a scrollable container for settings
    main_window.overlay_widgets = {}
    settings = ctk.CTkScrollableFrame(frame, fg_color="transparent")
    settings.pack(fill="both", expand=True, padx=40, pady=40)
    
    # Configure faster scroll speed by modifying canvas
    settings._parent_canvas.configure(yscrollincrement=20)
    
    create_title_section(settings)
    
    # Define all settings in a structured dictionary
    settings_data = {
        "Bounding Box": {
            "icon": "📦",
            "title": "Bounding Box Configuration",
            "description": "Settings for enemy bounding boxes",
            "settings": [
                ("Enable Bounding Box", "checkbox", "enable_box", "Toggle visibility of enemy bounding boxes"),
                ("Enable Skeleton ESP", "checkbox", "enable_skeleton", "Toggle visibility of player skeletons"),
                ("Line Thickness", "slider", "box_line_thickness", "Adjust thickness of bounding box lines (0.5-5.0)"),
                ("Box Color", "combo", "box_color_hex", "Select color for bounding boxes"),
                ("Target FPS", "slider", "target_fps", "Adjust target FPS for overlay rendering (60-420)"),
            ],
        },
        "Snaplines": {
            "icon": "📍",
            "title": "Snaplines Configuration",
            "description": "Settings for snaplines to enemies",
            "settings": [
                ("Draw Snaplines", "checkbox", "draw_snaplines", "Toggle drawing of snaplines to enemies"),
                ("Snaplines Color", "combo", "snaplines_color_hex", "Select color for snaplines"),
            ],
        },
        "Text": {
            "icon": "📝",
            "title": "Text Configuration",
            "description": "Settings for text display",
            "settings": [
                ("Text Color", "combo", "text_color_hex", "Select color for text"),
            ],
        },
        "Player Info": {
            "icon": "👤",
            "title": "Player Information",
            "description": "Settings for displaying player details",
            "settings": [
                ("Draw Health Numbers", "checkbox", "draw_health_numbers", "Show health numbers above players"),
                ("Draw Nicknames", "checkbox", "draw_nicknames", "Display player nicknames"),
                ("Use Transliteration", "checkbox", "use_transliteration", "Transliterate non-Latin characters"),
            ],
        },
        "Team": {
            "icon": "👥",
            "title": "Team Configuration",
            "description": "Settings for teammate display",
            "settings": [
                ("Draw Teammates", "checkbox", "draw_teammates", "Show teammates on the overlay"),
                ("Teammate Color", "combo", "teammate_color_hex", "Select color for teammates"),
            ],
        },
    }

    # Create sections for different overlay settings
    for section_name, section_data in settings_data.items():
        create_settings_section(
            main_window,
            settings,
            f"{section_data['icon']}  {section_data['title']}",
            section_data["description"],
            section_data["settings"],
        )

def create_title_section(parent):
    """Create the title and subtitle for the settings page."""

    title_frame = ctk.CTkFrame(parent, fg_color="transparent")
    title_frame.pack(fill="x", pady=(0, 40))
    
    ctk.CTkLabel(
        title_frame,
        text="🌍  Overlay Settings",
        font=FONT_TITLE,
        text_color=COLOR_TEXT_PRIMARY,
        anchor="w",
    ).pack(side="left")
    
    ctk.CTkLabel(
        title_frame,
        text="Configure your ESP overlay preferences",
        font=FONT_SUBTITLE,
        text_color=COLOR_TEXT_SECONDARY,
        anchor="w",
    ).pack(side="left", padx=(20, 0), pady=(10, 0))


def create_settings_section(main_window, parent, title, description, settings_list):
    """Creates a settings section with a title, description, and a list of settings."""
    section = ctk.CTkFrame(parent, **SECTION_STYLE)
    section.pack(fill="x", pady=(0, 30))

    header = ctk.CTkFrame(section, fg_color="transparent")
    header.pack(fill="x", padx=40, pady=(40, 30))

    ctk.CTkLabel(
        header,
        text=title,
        font=FONT_SECTION_TITLE,
        text_color=COLOR_TEXT_PRIMARY,
        anchor="w",
    ).pack(side="left")

    ctk.CTkLabel(
        header,
        text=description,
        font=FONT_SECTION_DESCRIPTION,
        text_color=COLOR_TEXT_SECONDARY,
        anchor="e",
    ).pack(side="right")

    for i, (label_text, widget_type, key, desc) in enumerate(settings_list):
        create_setting_item(
            section,
            label_text,
            desc,
            widget_type,
            key,
            main_window,
            is_last=(i == len(settings_list) - 1),
        )

def create_setting_item(parent, label_text, description, widget_type, key, main_window, is_last=False):
    """Creates a single setting item with a label, description, and the appropriate widget."""
    item_frame = ctk.CTkFrame(parent, fg_color="transparent")
    item_frame.pack(fill="x", padx=40, pady=(0, 30 if not is_last else 40))

    container = ctk.CTkFrame(item_frame, **SETTING_ITEM_STYLE)
    container.pack(fill="x")

    content_frame = ctk.CTkFrame(container, fg_color="transparent")
    content_frame.pack(fill="x", padx=25, pady=25)

    label_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    label_frame.pack(side="left", fill="x", expand=True)

    ctk.CTkLabel(
        label_frame,
        text=label_text,
        font=FONT_ITEM_LABEL,
        text_color=COLOR_TEXT_PRIMARY,
        anchor="w",
    ).pack(fill="x", pady=(0, 4))

    ctk.CTkLabel(
        label_frame,
        text=description,
        font=FONT_ITEM_DESCRIPTION,
        text_color=COLOR_TEXT_SECONDARY,
        anchor="w",
        wraplength=400,
    ).pack(fill="x")

    widget_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    widget_frame.pack(side="right", padx=(30, 0))

    widget_creators = {
        "checkbox": _create_checkbox,
        "entry": _create_entry,
        "slider": _create_slider,
        "combo": _create_combobox,
    }

    if widget_type in widget_creators:
        widget_info = widget_creators[widget_type](widget_frame, key, main_window)
        main_window.overlay_widgets[key] = widget_info


def _create_checkbox(parent, key, main_window):
    """Creates a checkbox widget and its associated variable."""
    var = ctk.BooleanVar(value=main_window.overlay.config["Overlay"][key])
    widget = ctk.CTkCheckBox(
        parent,
        text="",
        variable=var,
        command=lambda: main_window.save_settings(show_message=False),
        **CHECKBOX_STYLE,
    )
    widget.pack()
    return {"widget": widget, "variable": var}


def _create_entry(parent, key, main_window):
    """Creates an entry widget."""
    widget = ctk.CTkEntry(parent, justify="center", **ENTRY_STYLE)
    widget.insert(0, str(main_window.overlay.config["Overlay"][key]))
    widget.bind("<FocusOut>", lambda e: main_window.save_settings(show_message=False))
    widget.bind("<Return>", lambda e: main_window.save_settings(show_message=False))
    widget.pack()
    return {"widget": widget}


def _create_slider(parent, key, main_window):
    """Creates a slider widget with a value display."""
    slider_container = ctk.CTkFrame(parent, fg_color="transparent")
    slider_container.pack()

    value_frame = ctk.CTkFrame(
        slider_container,
        corner_radius=8,
        fg_color=COLOR_BORDER,
        width=60,
        height=35,
    )
    value_frame.pack(side="right", padx=(15, 0))
    value_frame.pack_propagate(False)

    value_label = ctk.CTkLabel(
        value_frame,
        text=f"{main_window.overlay.config['Overlay'][key]:.0f}"
        if key == "target_fps"
        else f"{main_window.overlay.config['Overlay'][key]:.1f}",
        font=ENTRY_STYLE["font"],
        text_color=COLOR_TEXT_PRIMARY,
    )
    value_label.pack(expand=True)

    widget = ctk.CTkSlider(
        slider_container,
        from_=0.5 if key == "box_line_thickness" else 60,
        to=5.0 if key == "box_line_thickness" else 420,
        number_of_steps=9 if key == "box_line_thickness" else 3,
        command=lambda e, k=key: update_slider_value(e, k, main_window),
        **SLIDER_STYLE,
    )
    widget.set(main_window.overlay.config["Overlay"][key])
    widget.pack(side="left")

    return {"widget": widget, "value_label": value_label}


def _create_combobox(parent, key, main_window):
    """Creates a combobox widget."""
    widget = ctk.CTkComboBox(
        parent,
        values=list(COLOR_CHOICES.keys()),
        state="readonly",
        justify="center",
        command=lambda e: main_window.save_settings(show_message=False),
        **COMBOBOX_STYLE,
    )
    widget.set(Utility.get_color_name_from_hex(main_window.overlay.config["Overlay"][key]))
    widget.bind("<FocusOut>", lambda e: main_window.save_settings(show_message=False))
    widget.bind("<Return>", lambda e: main_window.save_settings(show_message=False))
    widget.pack()
    return {"widget": widget}


def update_slider_value(event, key, main_window):
    """Update the slider value label and save settings."""
    slider_info = main_window.overlay_widgets.get(key, {})
    if "widget" in slider_info and "value_label" in slider_info:
        value = event
        format_spec = ".0f" if key == "target_fps" else ".1f"
        slider_info["value_label"].configure(text=f"{value:{format_spec}}")
        
        # Manually update the config for the slider before saving
        if main_window.overlay.config["Overlay"][key] != value:
            main_window.overlay.config["Overlay"][key] = value
            main_window.save_settings(show_message=False)