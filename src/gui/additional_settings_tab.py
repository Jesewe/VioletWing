import customtkinter as ctk
from src.gui.icon_loader import icon_label
from src.gui.components import create_section_frame, create_section_header, build_item_scaffold
from src.gui.keybind_recorder import KeybindRecorder
from src.gui.theme import (
    COLOR_BACKGROUND,
    FONT_TITLE, FONT_SUBTITLE, FONT_TABULAR,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    ENTRY_STYLE,
)

def populate_additional_settings(main_window, frame):
    """Populate the additional settings frame with configuration options for Bunnyhop."""
    # Create a scrollable container for settings
    settings = ctk.CTkScrollableFrame(
        frame,
        fg_color=COLOR_BACKGROUND
    )
    settings.pack(fill="both", expand=True, padx=40, pady=40)
    
    # Configure faster scroll speed by modifying canvas
    settings._parent_canvas.configure(yscrollincrement=5)
    
    # Frame for page title and subtitle
    title_frame = ctk.CTkFrame(settings, fg_color="transparent")
    title_frame.pack(fill="x", pady=(0, 40))
    
    icon_label(title_frame, "bolt_icon.png", size=(38, 38), padx=(0, 16))
    title_label = ctk.CTkLabel(
        title_frame,
        text="Additional Settings",
        font=FONT_TITLE,
        text_color=COLOR_TEXT_PRIMARY,
        anchor="w"
    )
    title_label.pack(side="left")
    
    # Subtitle providing context
    subtitle_label = ctk.CTkLabel(
        title_frame,
        text="Configure Bunnyhop preferences",
        font=FONT_SUBTITLE,
        text_color=COLOR_TEXT_SECONDARY,
        anchor="w"
    )
    subtitle_label.pack(side="left", padx=(20, 0), pady=(10, 0))
    
    # Create sections for Bunnyhop settings
    create_bunnyhop_config_section(main_window, settings)

def create_bunnyhop_config_section(main_window, parent):
    section = create_section_frame(parent)
    create_section_header(section, "Bunnyhop Configuration", "Control Bunnyhop behavior",
                          icon_file="paw_icon.png")

    wf = build_item_scaffold(section, "Jump Settings", "", is_last=True)

    # Jump Key
    initial_key = main_window.bunnyhop.config.get("Bunnyhop", {}).get("JumpKey", "space")
    key_var = ctk.StringVar(value=initial_key)
    recorder = KeybindRecorder(wf, var=key_var, on_capture=main_window.save_settings)
    recorder.pack(side="left", padx=(0, 20))
    main_window.ui_bridge.register("JumpKey", var=key_var)

    # Jump Delay
    delay_frame = ctk.CTkFrame(wf, fg_color="transparent")
    delay_frame.pack(side="left")
    ctk.CTkLabel(delay_frame, text="Delay:", text_color=COLOR_TEXT_SECONDARY).pack(side="left", padx=(0, 10))
    
    delay_entry = ctk.CTkEntry(delay_frame, justify="center", **{**ENTRY_STYLE, "width": 70})
    delay_entry.insert(0, str(main_window.bunnyhop.config.get("Bunnyhop", {}).get("JumpDelay", 0.01)))
    delay_entry.bind("<FocusOut>", lambda e: main_window.save_settings())
    delay_entry.bind("<Return>",   lambda e: main_window.save_settings())
    main_window.ui_bridge.register("JumpDelay", widget=delay_entry)
    delay_entry.pack(side="left")