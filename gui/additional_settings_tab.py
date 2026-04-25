import customtkinter as ctk
from gui.theme import (
    FONT_TITLE, FONT_SUBTITLE, FONT_SECTION_TITLE, FONT_SECTION_DESCRIPTION,
    FONT_ITEM_LABEL, FONT_ITEM_DESCRIPTION,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    SECTION_STYLE, SETTING_ITEM_STYLE, ENTRY_STYLE, SLIDER_STYLE
)

def populate_additional_settings(main_window, frame):
    """Populate the additional settings frame with configuration options for Bunnyhop and NoFlash."""
    # Create a scrollable container for settings
    settings = ctk.CTkScrollableFrame(
        frame,
        fg_color="transparent"
    )
    settings.pack(fill="both", expand=True, padx=40, pady=40)
    
    # Configure faster scroll speed by modifying canvas
    settings._parent_canvas.configure(yscrollincrement=5)
    
    # Frame for page title and subtitle
    title_frame = ctk.CTkFrame(settings, fg_color="transparent")
    title_frame.pack(fill="x", pady=(0, 40))
    
    # Settings title with an icon
    title_label = ctk.CTkLabel(
        title_frame,
        text="⚡  Additional Settings",
        font=FONT_TITLE,
        text_color=COLOR_TEXT_PRIMARY,
        anchor="w"
    )
    title_label.pack(side="left")
    
    # Subtitle providing context
    subtitle_label = ctk.CTkLabel(
        title_frame,
        text="Configure Bunnyhop and NoFlash preferences",
        font=FONT_SUBTITLE,
        text_color=COLOR_TEXT_SECONDARY,
        anchor="w"
    )
    subtitle_label.pack(side="left", padx=(20, 0), pady=(10, 0))
    
    # Create sections for Bunnyhop and NoFlash settings
    create_bunnyhop_config_section(main_window, settings)
    create_noflash_config_section(main_window, settings)

def create_bunnyhop_config_section(main_window, parent):
    """Create Bunnyhop configuration section with related settings."""
    # Section frame with modern styling
    section = ctk.CTkFrame(parent, **SECTION_STYLE)
    section.pack(fill="x", pady=(0, 30))
    
    # Header frame for section title and description
    header = ctk.CTkFrame(section, fg_color="transparent")
    header.pack(fill="x", padx=40, pady=(40, 30))
    
    # Section title with icon
    ctk.CTkLabel(
        header,
        text="🐰  Bunnyhop Configuration",
        font=FONT_SECTION_TITLE,
        text_color=COLOR_TEXT_PRIMARY,
        anchor="w"
    ).pack(side="left")
    
    # Description of section purpose
    ctk.CTkLabel(
        header,
        text="Control Bunnyhop behavior",
        font=FONT_SECTION_DESCRIPTION,
        text_color=COLOR_TEXT_SECONDARY,
        anchor="e"
    ).pack(side="right")
    
    # List of settings for Bunnyhop configuration
    settings_list = [
        ("Jump Key", "entry", "JumpKey", "Key to activate Bunnyhop (e.g., 'space' or 'mouse4')"),
        ("Jump Delay", "entry", "JumpDelay", "Delay between jumps in seconds (0.01-0.5)")
    ]
    
    # Create each setting item
    for i, (label_text, widget_type, key, description) in enumerate(settings_list):
        item_frame = create_setting_item(
            section, 
            label_text, 
            description, 
            widget_type, 
            key, 
            main_window,
            is_last=(i == len(settings_list) - 1)
        )

def create_noflash_config_section(main_window, parent):
    """Create NoFlash configuration section with related settings."""
    # Section frame with modern styling
    section = ctk.CTkFrame(parent, **SECTION_STYLE)
    section.pack(fill="x", pady=(0, 30))
    
    # Header frame for section title and description
    header = ctk.CTkFrame(section, fg_color="transparent")
    header.pack(fill="x", padx=40, pady=(40, 30))
    
    # Section title with icon
    ctk.CTkLabel(
        header,
        text="🌞  NoFlash Configuration",
        font=FONT_SECTION_TITLE,
        text_color=COLOR_TEXT_PRIMARY,
        anchor="w"
    ).pack(side="left")
    
    # Description of section purpose
    ctk.CTkLabel(
        header,
        text="Control flash suppression behavior",
        font=FONT_SECTION_DESCRIPTION,
        text_color=COLOR_TEXT_SECONDARY,
        anchor="e"
    ).pack(side="right")
    
    # List of settings for NoFlash configuration
    settings_list = [
        ("Flash Suppression Strength", "slider", "FlashSuppressionStrength", "Strength of flash suppression (0.0-100.0)")
    ]
    
    # Create each setting item
    for i, (label_text, widget_type, key, description) in enumerate(settings_list):
        item_frame = create_setting_item(
            section, 
            label_text, 
            description, 
            widget_type, 
            key, 
            main_window,
            is_last=(i == len(settings_list) - 1)
        )

def create_setting_item(parent, label_text, description, widget_type, key, main_window, is_last=False):
    """Create a standardized setting item with improved styling."""
    # Frame for the setting item
    item_frame = ctk.CTkFrame(parent, fg_color="transparent")
    item_frame.pack(fill="x", padx=40, pady=(0, 30 if not is_last else 40))
    
    # Container with hover effect
    container = ctk.CTkFrame(item_frame, **SETTING_ITEM_STYLE)
    container.pack(fill="x", pady=(0, 0))
    
    # Content frame within the container
    content_frame = ctk.CTkFrame(container, fg_color="transparent")
    content_frame.pack(fill="x", padx=25, pady=25)
    
    # Frame for label and description
    label_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    label_frame.pack(side="left", fill="x", expand=True)
    
    # Setting name label
    ctk.CTkLabel(
        label_frame,
        text=label_text,
        font=FONT_ITEM_LABEL,
        text_color=COLOR_TEXT_PRIMARY,
        anchor="w"
    ).pack(fill="x", pady=(0, 4))
    
    # Description of the setting
    ctk.CTkLabel(
        label_frame,
        text=description,
        font=FONT_ITEM_DESCRIPTION,
        text_color=COLOR_TEXT_SECONDARY,
        anchor="w",
        wraplength=400
    ).pack(fill="x")
    
    # Frame for the input widget
    widget_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    widget_frame.pack(side="right", padx=(30, 0))
    
    if widget_type == "entry":
        widget = ctk.CTkEntry(widget_frame, justify="center", **ENTRY_STYLE)
        if key == "JumpKey":
            widget.insert(0, main_window.bunnyhop.config.get('Bunnyhop', {}).get('JumpKey', 'space'))
        elif key == "JumpDelay":
            widget.insert(0, str(main_window.bunnyhop.config.get('Bunnyhop', {}).get('JumpDelay', 0.01)))
        widget.bind("<FocusOut>", lambda e: main_window.save_settings())
        widget.bind("<Return>", lambda e: main_window.save_settings())
        main_window.ui_bridge.register(key, widget=widget)
        widget.pack()

    elif widget_type == "slider":
        slider_container = ctk.CTkFrame(widget_frame, fg_color="transparent")
        slider_container.pack()

        value_frame = ctk.CTkFrame(
            slider_container, corner_radius=8,
            fg_color=("#e2e8f0", "#374151"), width=60, height=35
        )
        value_frame.pack(side="right", padx=(15, 0))
        value_frame.pack_propagate(False)

        initial_val = main_window.noflash.config['NoFlash'].get(key, 0.0)
        value_label = ctk.CTkLabel(
            value_frame,
            text=f"{initial_val:.1f}",
            font=FONT_ITEM_LABEL,
            text_color=COLOR_TEXT_PRIMARY
        )
        value_label.pack(expand=True)

        widget = ctk.CTkSlider(
            slider_container,
            from_=0.0, to=100.0, number_of_steps=1000,
            command=lambda val: (
                value_label.configure(text=f"{val:.1f}"),
                main_window.save_settings(show_message=False)
            ),
            **SLIDER_STYLE
        )
        widget.set(initial_val)
        widget.pack(side="left")
        main_window.ui_bridge.register(key, widget=widget, value_label=value_label, fmt=".1f")

    return item_frame