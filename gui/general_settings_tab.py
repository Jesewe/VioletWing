import customtkinter as ctk
import os
import requests
import orjson
from pathlib import Path
from tkinter import filedialog, messagebox
from classes.config_manager import ConfigManager
from gui.theme import (
    FONT_TITLE, FONT_SUBTITLE, FONT_SECTION_TITLE, FONT_SECTION_DESCRIPTION,
    FONT_ITEM_LABEL, FONT_ITEM_DESCRIPTION, FONT_WIDGET,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, COLOR_ACCENT_FG, COLOR_ACCENT_HOVER,
    COLOR_ACCENT_BUTTON, COLOR_ACCENT_BUTTON_HOVER,
    SECTION_STYLE, SETTING_ITEM_STYLE, CHECKBOX_STYLE, COMBOBOX_STYLE,
    BUTTON_STYLE_PRIMARY, BUTTON_STYLE_DANGER
)

# --- Constants ---
FEATURE_SETTINGS = [
    ("Enable Trigger", "checkbox", "Trigger", "Toggle the trigger bot feature"),
    ("Enable Overlay", "checkbox", "Overlay", "Toggle the ESP overlay feature"),
    ("Enable Bunnyhop", "checkbox", "Bunnyhop", "Toggle the bunnyhop feature"),
    ("Enable Noflash", "checkbox", "Noflash", "Toggle the noflash feature")
]

OFFSET_FILES = [
    ("Offsets File", "offsets.json", "Select offsets.json file", "OffsetsFile"),
    ("Client DLL File", "client.dll.json", "Select client.dll.json file", "ClientDLLFile"),
    ("Buttons File", "buttons.json", "Select buttons.json file", "ButtonsFile")
]

def create_section_header(parent, title, subtitle):
    """Creates a standardized section header."""
    header = ctk.CTkFrame(parent, fg_color="transparent")
    header.pack(fill="x", padx=40, pady=(40, 30))

    ctk.CTkLabel(
        header,
        text=title,
        font=FONT_SECTION_TITLE,
        text_color=COLOR_TEXT_PRIMARY,
        anchor="w"
    ).pack(side="left")

    ctk.CTkLabel(
        header,
        text=subtitle,
        font=FONT_SECTION_DESCRIPTION,
        text_color=COLOR_TEXT_SECONDARY,
        anchor="e"
    ).pack(side="right")
    
    return header

def populate_general_settings(main_window, frame):
    """
    Populates the General Settings tab with UI elements for configuring main application features.
    """
    settings = ctk.CTkScrollableFrame(frame, fg_color="transparent")
    settings.pack(fill="both", expand=True, padx=40, pady=40)
    
    # Configure faster scroll speed by modifying canvas
    settings._parent_canvas.configure(yscrollincrement=20)

    title_frame = ctk.CTkFrame(settings, fg_color="transparent")
    title_frame.pack(fill="x", pady=(0, 40))

    ctk.CTkLabel(
        title_frame,
        text="⚙️  General Settings",
        font=FONT_TITLE,
        text_color=COLOR_TEXT_PRIMARY,
        anchor="w"
    ).pack(side="left")

    ctk.CTkLabel(
        title_frame,
        text="Configure main application features",
        font=FONT_SUBTITLE,
        text_color=COLOR_TEXT_SECONDARY,
        anchor="w"
    ).pack(side="left", padx=(20, 0), pady=(10, 0))

    create_features_section(main_window, settings)
    create_offsets_section(main_window, settings)
    create_reset_section(main_window, settings)

def create_reset_section(main_window, parent):
    """Create section for resetting all settings to default."""
    section = ctk.CTkFrame(parent, **SECTION_STYLE)
    section.pack(fill="x", pady=(0, 30))

    create_section_header(section, "⚙️  Configuration Management", "Manage configuration files and settings")

    button_frame = ctk.CTkFrame(section, fg_color="transparent")
    button_frame.pack(fill="x", padx=40, pady=(0, 40))

    ctk.CTkButton(
        button_frame,
        text="📁  Open Config Directory",
        width=280,
        command=main_window.open_config_directory,
        **BUTTON_STYLE_PRIMARY
    ).pack(side="left", padx=(0, 20))

    ctk.CTkButton(
        button_frame,
        text="🔄  Reset All Settings",
        width=280,
        command=main_window.reset_to_default_settings,
        **BUTTON_STYLE_DANGER
    ).pack(side="left")

def create_features_section(main_window, parent):
    """Create section for configuring main application features."""
    section = ctk.CTkFrame(parent, **SECTION_STYLE)
    section.pack(fill="x", pady=(0, 30))

    create_section_header(section, "🔧  Feature Configuration", "Enable or disable main application features")

    for i, (label, widget, key, desc) in enumerate(FEATURE_SETTINGS):
        create_setting_item(
            parent=section,
            label_text=label,
            description=desc,
            widget_type=widget,
            key=key,
            main_window=main_window,
            is_last=(i == len(FEATURE_SETTINGS) - 1)
        )

def load_dynamic_offset_sources():
    """Load available offset sources from remote JSON file."""
    try:
        response = requests.get('https://raw.githubusercontent.com/Jesewe/VioletWing/refs/heads/main/src/offsets.json', timeout=10)
        response.raise_for_status()
        sources_data = orjson.loads(response.content)
        
        valid_sources = {
            sid: config for sid, config in sources_data.items()
            if all(k in config for k in ["name", "author", "repository", "offsets_url", "client_dll_url", "buttons_url"])
        }
        return valid_sources
    except (requests.RequestException, orjson.JSONDecodeError):
        return {
            "a2x": {"name": "a2x Source", "author": "a2x", "repository": "a2x/cs2-dumper"},
            "jesewe": {"name": "Jesewe Source", "author": "Jesewe", "repository": "Jesewe/cs2-dumper"}
        }

def create_offsets_section(main_window, parent):
    """Create section for configuring offset source and local file selection."""
    section = ctk.CTkFrame(parent, **SECTION_STYLE)
    section.pack(fill="x", pady=(0, 30))

    header = create_section_header(section, "📡  Offsets Configuration", "Configure offset source and local files")

    available_sources = load_dynamic_offset_sources()
    source_mapping = {f"{cfg['name']} ({cfg['author']})": sid for sid, cfg in available_sources.items()}
    source_mapping["Local Files"] = "local"
    
    dropdown_values = list(source_mapping.keys())

    current_source = main_window.triggerbot.config["General"].get("OffsetSource", "a2x")
    current_display = next((name for name, sid in source_mapping.items() if sid == current_source), "Local Files")

    main_window.offset_source_var = ctk.StringVar(value=current_display)
    ctk.CTkOptionMenu(
        header,
        variable=main_window.offset_source_var,
        values=dropdown_values,
        command=lambda dn: update_offset_source(main_window, source_mapping[dn]),
        **COMBOBOX_STYLE
    ).pack(side="right", padx=(0, 10))

    main_window.local_files_frame = ctk.CTkFrame(section, fg_color="transparent")
    if current_source == "local":
        main_window.local_files_frame.pack(fill="x", padx=40, pady=(0, 40))

    main_window.local_file_paths = {}
    for label, filename, desc, config_key in OFFSET_FILES:
        create_file_selector(main_window, main_window.local_files_frame, label, filename, desc, config_key)

def create_file_selector(main_window, parent, label_text, filename, description, config_key):
    """Create a file selector for a specific offset file."""
    item_frame = ctk.CTkFrame(parent, fg_color="transparent")
    item_frame.pack(fill="x", padx=0, pady=(0, 10))
    
    container = ctk.CTkFrame(item_frame, **SETTING_ITEM_STYLE)
    container.pack(fill="x")

    content_frame = ctk.CTkFrame(container, fg_color="transparent")
    content_frame.pack(fill="x", padx=25, pady=15)

    label_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    label_frame.pack(side="left", fill="x", expand=True)

    ctk.CTkLabel(
        label_frame,
        text=label_text,
        font=FONT_ITEM_LABEL,
        text_color=COLOR_TEXT_PRIMARY,
        anchor="w"
    ).pack(fill="x", pady=(0, 4))

    ctk.CTkLabel(
        label_frame,
        text=description,
        font=FONT_ITEM_DESCRIPTION,
        text_color=COLOR_TEXT_SECONDARY,
        anchor="w",
        wraplength=400
    ).pack(fill="x")

    button_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    button_frame.pack(side="right", padx=(30, 0))

    def select_file():
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")],
            initialdir=Path(ConfigManager.CONFIG_DIRECTORY)
        )
        if file_path:
            main_window.local_file_paths[filename] = file_path
            file_button.configure(text=f"Selected: {os.path.basename(file_path)}")
            main_window.triggerbot.config["General"][config_key] = file_path
            main_window.save_settings(show_message=False)

    current_file = main_window.triggerbot.config["General"].get(config_key, "")
    button_text = f"Selected: {os.path.basename(current_file)}" if current_file and os.path.exists(current_file) else f"Select {filename}"

    file_button = ctk.CTkButton(
        button_frame,
        text=button_text,
        font=FONT_WIDGET,
        corner_radius=10,
        fg_color=COLOR_ACCENT_FG,
        hover_color=COLOR_ACCENT_HOVER,
        command=select_file
    )
    file_button.pack()

def update_offset_source(main_window, selected_source_id):
    """Update offset source and show/hide file selection frame."""
    main_window.triggerbot.config["General"]["OffsetSource"] = selected_source_id
    main_window.save_settings(show_message=False)

    messagebox.showwarning(
        "Restart Required", 
        "Offset source has been changed. Please restart the application for the changes to take effect."
    )

    if selected_source_id == "local":
        main_window.local_files_frame.pack(fill="x", padx=40, pady=(0, 40))
    else:
        main_window.local_files_frame.pack_forget()

def create_setting_item(parent, label_text, description, widget_type, key, main_window, is_last=False):
    """Creates a generic setting item with a label, description, and a widget."""
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
        anchor="w"
    ).pack(fill="x", pady=(0, 4))
    
    ctk.CTkLabel(
        label_frame,
        text=description,
        font=FONT_ITEM_DESCRIPTION,
        text_color=COLOR_TEXT_SECONDARY,
        anchor="w",
        wraplength=400
    ).pack(fill="x")
    
    widget_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    widget_frame.pack(side="right", padx=(30, 0))
    
    if widget_type == "checkbox":
        var = ctk.BooleanVar(value=main_window.triggerbot.config["General"].get(key, False))
        
        ctk.CTkCheckBox(
            widget_frame,
            text="",
            variable=var,
            command=lambda: main_window.save_settings(show_message=False),
            **CHECKBOX_STYLE
        ).pack()
        
        setattr(main_window, f"{key.lower()}_var", var)
    else:
        raise ValueError(f"Unsupported widget type: {widget_type}")