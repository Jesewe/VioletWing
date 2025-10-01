import customtkinter as ctk
from classes.config_manager import COLOR_CHOICES
from classes.utility import Utility

def populate_overlay_settings(main_window, frame):
    """
    Populates the Overlay Settings tab with UI elements for configuring overlay preferences.
    All changes are saved in real-time to the configuration.
    """
    # Create a scrollable container for settings
    settings = ctk.CTkScrollableFrame(
        frame,
        fg_color="transparent"
    )
    settings.pack(fill="both", expand=True, padx=40, pady=40)

    # Frame for page title and subtitle
    title_frame = ctk.CTkFrame(settings, fg_color="transparent")
    title_frame.pack(fill="x", pady=(0, 40))

    # Settings title with an icon
    title_label = ctk.CTkLabel(
        title_frame,
        text="🌍  Overlay Settings",
        font=("Chivo", 36, "bold"),
        text_color=("#1f2937", "#ffffff"),
        anchor="w"
    )
    title_label.pack(side="left")

    # Subtitle providing context
    subtitle_label = ctk.CTkLabel(
        title_frame,
        text="Configure your ESP overlay preferences",
        font=("Gambetta", 16),
        text_color=("#64748b", "#94a3b8"),
        anchor="w"
    )
    subtitle_label.pack(side="left", padx=(20, 0), pady=(10, 0))

    # Create sections for different overlay settings
    create_bounding_box_section(main_window, settings)
    create_snaplines_section(main_window, settings)
    create_text_section(main_window, settings)
    create_player_info_section(main_window, settings)
    create_team_section(main_window, settings)

def create_bounding_box_section(main_window, parent):
    """Create bounding box configuration section with related settings."""
    # Section frame with modern styling
    section = ctk.CTkFrame(
        parent,
        corner_radius=20,
        fg_color=("#ffffff", "#1a1b23"),
        border_width=2,
        border_color=("#e2e8f0", "#2d3748")
    )
    section.pack(fill="x", pady=(0, 30))

    # Header frame for section title and description
    header = ctk.CTkFrame(section, fg_color="transparent")
    header.pack(fill="x", padx=40, pady=(40, 30))

    # Section title with icon
    ctk.CTkLabel(
        header,
        text="📦  Bounding Box Configuration",
        font=("Chivo", 24, "bold"),
        text_color=("#1f2937", "#ffffff"),
        anchor="w"
    ).pack(side="left")

    # Description of section purpose
    ctk.CTkLabel(
        header,
        text="Settings for enemy bounding boxes",
        font=("Gambetta", 14),
        text_color=("#64748b", "#94a3b8"),
        anchor="e"
    ).pack(side="right")

    # List of settings for bounding box configuration
    settings_list = [
        ("Enable Bounding Box", "checkbox", "enable_box", "Toggle visibility of enemy bounding boxes"),
        ("Enable Skeleton ESP", "checkbox", "enable_skeleton", "Toggle visibility of player skeletons"),
        ("Line Thickness", "slider", "box_line_thickness", "Adjust thickness of bounding box lines (0.5-5.0)"),
        ("Box Color", "combo", "box_color_hex", "Select color for bounding boxes"),
        ("Target FPS", "slider", "target_fps", "Adjust target FPS for overlay rendering (60-420)")
    ]

    # Create each setting item
    for i, (label_text, widget_type, key, description) in enumerate(settings_list):
        create_setting_item(
            section,
            label_text,
            description,
            widget_type,
            key,
            main_window,
            is_last=(i == len(settings_list) - 1)
        )

def create_snaplines_section(main_window, parent):
    """Create snaplines configuration section with related settings."""
    # Section frame with modern styling
    section = ctk.CTkFrame(
        parent,
        corner_radius=20,
        fg_color=("#ffffff", "#1a1b23"),
        border_width=2,
        border_color=("#e2e8f0", "#2d3748")
    )
    section.pack(fill="x", pady=(0, 30))

    # Header frame for section title and description
    header = ctk.CTkFrame(section, fg_color="transparent")
    header.pack(fill="x", padx=40, pady=(40, 30))

    # Section title with icon
    ctk.CTkLabel(
        header,
        text="📍  Snaplines Configuration",
        font=("Chivo", 24, "bold"),
        text_color=("#1f2937", "#ffffff"),
        anchor="w"
    ).pack(side="left")

    # Description of section purpose
    ctk.CTkLabel(
        header,
        text="Settings for snaplines to enemies",
        font=("Gambetta", 14),
        text_color=("#64748b", "#94a3b8"),
        anchor="e"
    ).pack(side="right")

    # List of settings for snaplines configuration
    settings_list = [
        ("Draw Snaplines", "checkbox", "draw_snaplines", "Toggle drawing of snaplines to enemies"),
        ("Snaplines Color", "combo", "snaplines_color_hex", "Select color for snaplines")
    ]

    # Create each setting item
    for i, (label_text, widget_type, key, description) in enumerate(settings_list):
        create_setting_item(
            section,
            label_text,
            description,
            widget_type,
            key,
            main_window,
            is_last=(i == len(settings_list) - 1)
        )

def create_text_section(main_window, parent):
    """Create text configuration section with related settings."""
    # Section frame with modern styling
    section = ctk.CTkFrame(
        parent,
        corner_radius=20,
        fg_color=("#ffffff", "#1a1b23"),
        border_width=2,
        border_color=("#e2e8f0", "#2d3748")
    )
    section.pack(fill="x", pady=(0, 30))

    # Header frame for section title and description
    header = ctk.CTkFrame(section, fg_color="transparent")
    header.pack(fill="x", padx=40, pady=(40, 30))

    # Section title with icon
    ctk.CTkLabel(
        header,
        text="📝  Text Configuration",
        font=("Chivo", 24, "bold"),
        text_color=("#1f2937", "#ffffff"),
        anchor="w"
    ).pack(side="left")

    # Description of section purpose
    ctk.CTkLabel(
        header,
        text="Settings for text display",
        font=("Gambetta", 14),
        text_color=("#64748b", "#94a3b8"),
        anchor="e"
    ).pack(side="right")

    # List of settings for text configuration
    settings_list = [
        ("Text Color", "combo", "text_color_hex", "Select color for text")
    ]

    # Create each setting item
    for i, (label_text, widget_type, key, description) in enumerate(settings_list):
        create_setting_item(
            section,
            label_text,
            description,
            widget_type,
            key,
            main_window,
            is_last=(i == len(settings_list) - 1)
        )

def create_player_info_section(main_window, parent):
    """Create player information configuration section with related settings."""
    # Section frame with modern styling
    section = ctk.CTkFrame(
        parent,
        corner_radius=20,
        fg_color=("#ffffff", "#1a1b23"),
        border_width=2,
        border_color=("#e2e8f0", "#2d3748")
    )
    section.pack(fill="x", pady=(0, 30))

    # Header frame for section title and description
    header = ctk.CTkFrame(section, fg_color="transparent")
    header.pack(fill="x", padx=40, pady=(40, 30))

    # Section title with icon
    ctk.CTkLabel(
        header,
        text="👤  Player Information",
        font=("Chivo", 24, "bold"),
        text_color=("#1f2937", "#ffffff"),
        anchor="w"
    ).pack(side="left")

    # Description of section purpose
    ctk.CTkLabel(
        header,
        text="Settings for displaying player details",
        font=("Gambetta", 14),
        text_color=("#64748b", "#94a3b8"),
        anchor="e"
    ).pack(side="right")

    # List of settings for player information configuration
    settings_list = [
        ("Draw Health Numbers", "checkbox", "draw_health_numbers", "Show health numbers above players"),
        ("Draw Nicknames", "checkbox", "draw_nicknames", "Display player nicknames"),
        ("Use Transliteration", "checkbox", "use_transliteration", "Transliterate non-Latin characters")
    ]

    # Create each setting item
    for i, (label_text, widget_type, key, description) in enumerate(settings_list):
        create_setting_item(
            section,
            label_text,
            description,
            widget_type,
            key,
            main_window,
            is_last=(i == len(settings_list) - 1)
        )

def create_team_section(main_window, parent):
    """Create team configuration section with related settings."""
    # Section frame with modern styling
    section = ctk.CTkFrame(
        parent,
        corner_radius=20,
        fg_color=("#ffffff", "#1a1b23"),
        border_width=2,
        border_color=("#e2e8f0", "#2d3748")
    )
    section.pack(fill="x", pady=(0, 30))

    # Header frame for section title and description
    header = ctk.CTkFrame(section, fg_color="transparent")
    header.pack(fill="x", padx=40, pady=(40, 30))

    # Section title with icon
    ctk.CTkLabel(
        header,
        text="👥  Team Configuration",
        font=("Chivo", 24, "bold"),
        text_color=("#1f2937", "#ffffff"),
        anchor="w"
    ).pack(side="left")

    # Description of section purpose
    ctk.CTkLabel(
        header,
        text="Settings for teammate display",
        font=("Gambetta", 14),
        text_color=("#64748b", "#94a3b8"),
        anchor="e"
    ).pack(side="right")

    # List of settings for team configuration
    settings_list = [
        ("Draw Teammates", "checkbox", "draw_teammates", "Show teammates on the overlay"),
        ("Teammate Color", "combo", "teammate_color_hex", "Select color for teammates")
    ]

    # Create each setting item
    for i, (label_text, widget_type, key, description) in enumerate(settings_list):
        create_setting_item(
            section,
            label_text,
            description,
            widget_type,
            key,
            main_window,
            is_last=(i == len(settings_list) - 1)
        )

def create_setting_item(parent, label_text, description, widget_type, key, main_window, is_last=False):
    item_frame = ctk.CTkFrame(parent, fg_color="transparent")
    item_frame.pack(fill="x", padx=40, pady=(0, 30 if not is_last else 40))

    container = ctk.CTkFrame(
        item_frame,
        corner_radius=12,
        fg_color=("#f8fafc", "#252830"),
        border_width=1,
        border_color=("#e2e8f0", "#374151")
    )
    container.pack(fill="x", pady=(0, 0))

    content_frame = ctk.CTkFrame(container, fg_color="transparent")
    content_frame.pack(fill="x", padx=25, pady=25)

    label_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    label_frame.pack(side="left", fill="x", expand=True)

    ctk.CTkLabel(
        label_frame,
        text=label_text,
        font=("Chivo", 16, "bold"),
        text_color=("#1f2937", "#ffffff"),
        anchor="w"
    ).pack(fill="x", pady=(0, 4))

    ctk.CTkLabel(
        label_frame,
        text=description,
        font=("Gambetta", 13),
        text_color=("#64748b", "#94a3b8"),
        anchor="w",
        wraplength=400
    ).pack(fill="x")

    widget_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
    widget_frame.pack(side="right", padx=(30, 0))

    if widget_type == "checkbox":
        var = ctk.BooleanVar(value=main_window.overlay.config["Overlay"][key])
        widget = ctk.CTkCheckBox(
            widget_frame,
            text="",
            variable=var,
            width=30,
            height=30,
            corner_radius=8,
            border_width=2,
            fg_color=("#D5006D", "#E91E63"),
            hover_color=("#B8004A", "#C2185B"),
            checkmark_color="#ffffff",
            command=lambda: main_window.save_settings(show_message=False)
        )
        widget.pack()
        main_window.__setattr__(f"{key}_var", var)

    elif widget_type == "entry":
        widget = ctk.CTkEntry(
            widget_frame,
            width=220,
            height=45,
            corner_radius=12,
            border_width=2,
            border_color=("#d1d5db", "#374151"),
            fg_color=("#ffffff", "#1f2937"),
            text_color=("#1f2937", "#ffffff"),
            font=("Chivo", 14),
            justify="center"
        )
        widget.insert(0, str(main_window.overlay.config["Overlay"][key]))
        widget.bind("<FocusOut>", lambda e: main_window.save_settings(show_message=False))
        widget.bind("<Return>", lambda e: main_window.save_settings(show_message=False))
        widget.pack()
        main_window.__setattr__(f"{key}_entry", widget)

    elif widget_type == "slider":
        # Create a container for the slider and value display
        slider_container = ctk.CTkFrame(
            widget_frame,
            fg_color="transparent"
        )
        slider_container.pack()
        
        # Create a frame for the value label with background
        value_frame = ctk.CTkFrame(
            slider_container,
            corner_radius=8,
            fg_color=("#e2e8f0", "#374151"),
            width=60,
            height=35
        )
        value_frame.pack(side="right", padx=(15, 0))
        value_frame.pack_propagate(False)
        
        # Value label with improved styling
        value_label = ctk.CTkLabel(
            value_frame,
            text=f"{main_window.overlay.config['Overlay'][key]:.0f}" if key == "target_fps" else f"{main_window.overlay.config['Overlay'][key]:.1f}",
            font=("Chivo", 14, "bold"),
            text_color=("#1f2937", "#ffffff")
        )
        value_label.pack(expand=True)
        
        # Enhanced slider with custom styling
        widget = ctk.CTkSlider(
            slider_container,
            from_=0.5 if key == "box_line_thickness" else 60,
            to=5.0 if key == "box_line_thickness" else 420,
            number_of_steps=9 if key == "box_line_thickness" else 3,
            width=200,
            height=20,
            corner_radius=10,
            button_corner_radius=10,
            border_width=0,
            fg_color=("#e2e8f0", "#374151"),
            progress_color=("#D5006D", "#E91E63"),
            button_color=("#ffffff", "#ffffff"),
            button_hover_color=("#f8fafc", "#f8fafc"),
            command=lambda e: update_slider_value(e, key, main_window)
        )
        widget.set(main_window.overlay.config["Overlay"][key])
        widget.pack(side="left")
        
        # Store references for later use
        widget.value_label = value_label
        main_window.__setattr__(f"{key}_slider", widget)
        main_window.__setattr__(f"{key}_value_label", value_label)

    elif widget_type == "combo":
        # Enhanced ComboBox with improved styling
        widget = ctk.CTkComboBox(
            widget_frame,
            values=list(COLOR_CHOICES.keys()),
            width=180,
            height=45,
            corner_radius=12,
            border_width=2,
            border_color=("#d1d5db", "#374151"),
            fg_color=("#ffffff", "#1f2937"),
            text_color=("#1f2937", "#ffffff"),
            font=("Chivo", 14),
            dropdown_font=("Chivo", 13),
            button_color=("#D5006D", "#E91E63"),
            button_hover_color=("#B8004A", "#C2185B"),
            dropdown_fg_color=("#ffffff", "#1a1b23"),
            dropdown_hover_color=("#f8fafc", "#2d3748"),
            dropdown_text_color=("#1f2937", "#ffffff"),
            state="readonly",
            justify="center",
            command=lambda e: main_window.save_settings(show_message=False)
        )
        widget.set(Utility.get_color_name_from_hex(main_window.overlay.config["Overlay"][key]))
        widget.bind("<FocusOut>", lambda e: main_window.save_settings(show_message=False))
        widget.bind("<Return>", lambda e: main_window.save_settings(show_message=False))
        widget.pack()
        main_window.__setattr__(f"{key}_combo", widget)

    return item_frame

def update_slider_value(event, key, main_window):
    """Update the slider value label and save settings."""
    value = main_window.__getattribute__(f"{key}_slider").get()
    main_window.__getattribute__(f"{key}_slider").value_label.configure(text=f"{value:.0f}" if key == "target_fps" else f"{value:.1f}")
    main_window.save_settings(show_message=False)
