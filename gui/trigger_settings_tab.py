import customtkinter as ctk
from gui.icon_loader import icon_label
from gui.components import create_section_frame, create_section_header, build_item_scaffold
from gui.theme import (
    FONT_TITLE, FONT_SUBTITLE, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    CHECKBOX_STYLE, ENTRY_STYLE, COMBOBOX_STYLE,
)

WEAPON_TYPES = ["Pistols", "Rifles", "Snipers", "SMGs", "Heavy"]

def populate_trigger_settings(main_window, frame):
    """Populate the settings frame with configuration options."""
    main_window.trigger_settings_frame = frame
    
    settings = ctk.CTkScrollableFrame(frame, fg_color="transparent")
    settings.pack(fill="both", expand=True, padx=40, pady=40)
    
    # Configure faster scroll speed by modifying canvas
    settings._parent_canvas.configure(yscrollincrement=5)
    
    create_title_section(settings)
    create_trigger_config_section(main_window, settings)
    create_timing_settings_section(main_window, settings)

def create_title_section(parent):
    """Create the title and subtitle for the settings page."""
    title_frame = ctk.CTkFrame(parent, fg_color="transparent")
    title_frame.pack(fill="x", pady=(0, 40))
    
    icon_label(title_frame, "crosshairs_icon.png", size=(38, 38), padx=(0, 16))
    ctk.CTkLabel(
        title_frame,
        text="Trigger Settings",
        font=FONT_TITLE,
        text_color=COLOR_TEXT_PRIMARY,
        anchor="w"
    ).pack(side="left")
    
    ctk.CTkLabel(
        title_frame,
        text="Configure your trigger bot preferences",
        font=FONT_SUBTITLE,
        text_color=COLOR_TEXT_SECONDARY,
        anchor="w"
    ).pack(side="left", padx=(20, 0), pady=(10, 0))

def create_trigger_config_section(main_window, parent):
    section = create_section_frame(parent)
    create_section_header(section, "Configuration", "Control how the trigger responds",
                          icon_file="bullseye_icon.png")

    settings_list = [
        ("Trigger Key",       "entry",    "TriggerKey",        "Key to activate trigger (e.g., 'x', 'mouse4')"),
        ("Toggle Mode",       "checkbox", "ToggleMode",        "Enable toggle mode instead of hold mode"),
        ("Attack Teammates",  "checkbox", "AttackOnTeammates", "Allow triggering on teammates"),
    ]
    for i, (label, widget_type, key, desc) in enumerate(settings_list):
        create_setting_item(section, main_window, label, desc, widget_type, key,
                            is_last=(i == len(settings_list) - 1))

def create_timing_settings_section(main_window, parent):
    section = create_section_frame(parent)
    header_frame = create_section_header(section, "Timing Settings",
                                         "Fine-tune shooting delays per weapon type",
                                         icon_file="stopwatch_icon.png")

    active_weapon_var = ctk.StringVar(
        value=main_window.triggerbot.config["Trigger"].get("active_weapon_type", "Rifles")
    )
    main_window.ui_bridge.register("active_weapon_type", var=active_weapon_var)
    ctk.CTkOptionMenu(
        header_frame,
        variable=active_weapon_var,
        values=WEAPON_TYPES,
        command=lambda e: main_window.update_weapon_settings_display(),
        **COMBOBOX_STYLE,
    ).pack(side="right", padx=(0, 10))

    settings_list = [
        ("Min Shot Delay",  "entry", "ShotDelayMin",  "Minimum delay before shooting (seconds)"),
        ("Max Shot Delay",  "entry", "ShotDelayMax",  "Maximum delay before shooting (seconds)"),
        ("Post Shot Delay", "entry", "PostShotDelay", "Delay after shooting (seconds)"),
    ]
    for i, (label, widget_type, key, desc) in enumerate(settings_list):
        create_setting_item(section, main_window, label, desc, widget_type, key,
                            is_last=(i == len(settings_list) - 1), is_weapon_specific=True)
    main_window.update_weapon_settings_display()

def create_setting_item(parent, main_window, label_text, description, widget_type, key,
                        is_last=False, is_weapon_specific=False):
    wf = build_item_scaffold(parent, label_text, description, is_last)
    _populate_widget(wf, main_window, widget_type, key, is_weapon_specific)


def _populate_widget(wf, main_window, widget_type, key, is_weapon_specific):
    """Create the input widget directly inside the pre-built widget frame."""
    if widget_type == "entry":
        widget = ctk.CTkEntry(wf, justify="center", **ENTRY_STYLE)
        widget.bind("<FocusOut>", lambda e: main_window.save_settings())
        widget.bind("<Return>",   lambda e: main_window.save_settings())
        if is_weapon_specific:
            defaults = {"ShotDelayMin": 0.01, "ShotDelayMax": 0.03, "PostShotDelay": 0.1}
            widget.insert(0, str(defaults.get(key, "")))
        elif key == "TriggerKey":
            widget.insert(0, main_window.triggerbot.config["Trigger"].get("TriggerKey", ""))
        main_window.ui_bridge.register(key, widget=widget)
        widget.pack()
    elif widget_type == "checkbox":
        var = ctk.BooleanVar(value=main_window.triggerbot.config["Trigger"].get(key, False))
        ctk.CTkCheckBox(wf, text="", variable=var,
                        command=main_window.save_settings, **CHECKBOX_STYLE).pack()
        main_window.ui_bridge.register(key, var=var)