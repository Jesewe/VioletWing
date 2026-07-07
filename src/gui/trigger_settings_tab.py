import customtkinter as ctk
from src.gui.icon_loader import icon_label
from src.gui.components import create_section_frame, create_section_header, build_item_scaffold
from src.gui.keybind_recorder import KeybindRecorder
from src.gui.theme import (
    COLOR_BACKGROUND,
    FONT_TITLE, FONT_SUBTITLE, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    CHECKBOX_STYLE, ENTRY_STYLE, COMBOBOX_STYLE, SETTING_ITEM_STYLE
)

WEAPON_TYPES = ["Pistols", "Rifles", "Snipers", "SMGs", "Heavy"]

def populate_trigger_settings(main_window, frame):
    """Populate the settings frame with configuration options."""
    main_window.trigger_settings_frame = frame
    
    settings = ctk.CTkScrollableFrame(
        frame, fg_color=COLOR_BACKGROUND,
        scrollbar_button_color=COLOR_BACKGROUND,
        scrollbar_button_hover_color=COLOR_BACKGROUND,
        scrollbar_fg_color=COLOR_BACKGROUND
    )
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

    wf = build_item_scaffold(section, "Behavior", "Trigger key and behavior toggles", is_last=True)
    
    # Keybind on the left
    initial = main_window.triggerbot.config["Trigger"].get("TriggerKey", "")
    key_var = ctk.StringVar(value=initial)
    recorder = KeybindRecorder(wf, var=key_var, on_capture=main_window.save_settings)
    recorder.pack(side="left", padx=(0, 20))
    main_window.ui_bridge.register("TriggerKey", var=key_var)

    # Checkboxes to the right
    toggle_var = ctk.BooleanVar(value=main_window.triggerbot.config["Trigger"].get("ToggleMode", False))
    ctk.CTkCheckBox(wf, text="Toggle Mode", variable=toggle_var, command=main_window.save_settings, **CHECKBOX_STYLE).pack(side="left", padx=(0, 20))
    main_window.ui_bridge.register("ToggleMode", var=toggle_var)

    team_var = ctk.BooleanVar(value=main_window.triggerbot.config["Trigger"].get("AttackOnTeammates", False))
    ctk.CTkCheckBox(wf, text="Attack Teammates", variable=team_var, command=main_window.save_settings, **CHECKBOX_STYLE).pack(side="left")
    main_window.ui_bridge.register("AttackOnTeammates", var=team_var)

def create_timing_settings_section(main_window, parent):
    section = create_section_frame(parent)
    create_section_header(section, "Timing Settings",
                          "Fine-tune shooting delays per weapon type",
                          icon_file="stopwatch_icon.png")

    item_frame = ctk.CTkFrame(section, fg_color="transparent")
    item_frame.pack(fill="x", padx=40, pady=(0, 40))

    container = ctk.CTkFrame(item_frame, **SETTING_ITEM_STYLE)
    container.pack(fill="x")

    content = ctk.CTkFrame(container, fg_color="transparent")
    content.pack(pady=30)

    active_weapon_var = ctk.StringVar(
        value=main_window.triggerbot.config["Trigger"].get("active_weapon_type", "Rifles")
    )
    main_window.ui_bridge.register("active_weapon_type", var=active_weapon_var)
    
    combo_col = ctk.CTkFrame(content, fg_color="transparent")
    combo_col.pack(side="left", padx=(0, 40))
    
    ctk.CTkLabel(combo_col, text="Weapon Type", text_color=COLOR_TEXT_PRIMARY).pack(pady=(0, 4))
    ctk.CTkOptionMenu(
        combo_col,
        variable=active_weapon_var,
        values=WEAPON_TYPES,
        command=lambda e: main_window.update_weapon_settings_display(),
        **COMBOBOX_STYLE,
    ).pack()

    def _make_delay_column(parent, title, key, default_val):
        col = ctk.CTkFrame(parent, fg_color="transparent")
        ctk.CTkLabel(col, text=title, text_color=COLOR_TEXT_PRIMARY).pack(pady=(0, 4))
        
        widget = ctk.CTkEntry(col, justify="center", **{**ENTRY_STYLE, "width": 70})
        widget.bind("<FocusOut>", lambda e: main_window.save_settings())
        widget.bind("<Return>",   lambda e: main_window.save_settings())
        widget.insert(0, str(default_val))
        widget.pack()
        
        main_window.ui_bridge.register(key, widget=widget)
        return col

    _make_delay_column(content, "Min Delay", "ShotDelayMin", 0.01).pack(side="left", padx=(0, 15))
    _make_delay_column(content, "Max Delay", "ShotDelayMax", 0.03).pack(side="left", padx=(0, 15))
    _make_delay_column(content, "Post Delay", "PostShotDelay", 0.1).pack(side="left")

    main_window.update_weapon_settings_display()