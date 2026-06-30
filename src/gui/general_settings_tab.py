import customtkinter as ctk
from src.gui.icon_loader import icon_label, load_icon
from src.utils.config_manager import ConfigManager
import src.utils.profile_manager as ProfileManager
from src.gui.components import create_section_frame, create_section_header, build_item_scaffold
from src.gui.modal import AppModal
from src.gui.theme import (
    FONT_TITLE, FONT_SUBTITLE, FONT_ITEM_LABEL, FONT_ITEM_DESCRIPTION, FONT_WIDGET,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    CHECKBOX_STYLE, COMBOBOX_STYLE,
    BUTTON_STYLE_PRIMARY, BUTTON_STYLE_DANGER,
)

FEATURE_SETTINGS = [
    ("Enable Trigger",  "checkbox", "Trigger",      "Toggle the trigger bot feature"),
    ("Enable Overlay",  "checkbox", "Overlay",       "Toggle the ESP overlay feature"),
    ("Enable Bunnyhop", "checkbox", "Bunnyhop",      "Toggle the bunnyhop feature"),
    ("Enable Noflash",  "checkbox", "Noflash",       "Toggle the noflash feature"),
]

PROGRAM_SETTINGS = [
    ("Detailed Logs",   "checkbox", "DetailedLogs",  "Show verbose debug log instead of the standard log"),
    ("Enable Disguise", "checkbox", "Disguise",       "Disguise the program as another app on next startup"),
]

def populate_general_settings(main_window, frame):
    settings = ctk.CTkScrollableFrame(frame, fg_color="transparent")
    settings.pack(fill="both", expand=True, padx=40, pady=40)
    settings._parent_canvas.configure(yscrollincrement=5)

    title_frame = ctk.CTkFrame(settings, fg_color="transparent")
    title_frame.pack(fill="x", pady=(0, 40))
    icon_label(title_frame, "gear_icon.png", size=(38, 38), padx=(0, 16))
    ctk.CTkLabel(title_frame, text="General Settings", font=FONT_TITLE,
                 text_color=COLOR_TEXT_PRIMARY, anchor="w").pack(side="left")
    ctk.CTkLabel(title_frame, text="Configure main application features",
                 font=FONT_SUBTITLE, text_color=COLOR_TEXT_SECONDARY,
                 anchor="w").pack(side="left", padx=(20, 0), pady=(10, 0))

    _create_features_section(main_window, settings)
    _create_program_section(main_window, settings)
    _create_reset_section(main_window, settings)

def _create_features_section(main_window, parent):
    section = create_section_frame(parent)
    create_section_header(section, "Feature Configuration",
                          "Enable or disable main application features",
                          icon_file="sliders_icon.png")
    for i, (label, widget, key, desc) in enumerate(FEATURE_SETTINGS):
        _create_checkbox_item(section, label, desc, key, main_window,
                              is_last=(i == len(FEATURE_SETTINGS) - 1))

def _create_program_section(main_window, parent):
    section = create_section_frame(parent)
    create_section_header(section, "Program Settings",
                          "Configure core program behaviour and disguise",
                          icon_file="user_secret_icon.png")
    for i, (label, widget, key, desc) in enumerate(PROGRAM_SETTINGS):
        _create_checkbox_item(section, label, desc, key, main_window,
                              is_last=(i == len(PROGRAM_SETTINGS) - 1))

    wf = build_item_scaffold(section, "Active Profile",
                             "The program this instance is currently disguised as.",
                             is_last=True)
    disguise_name = main_window.ghost["name"] if getattr(main_window, "ghost", None) else "None"
    color = COLOR_TEXT_PRIMARY if main_window.ghost else COLOR_TEXT_SECONDARY
    ctk.CTkLabel(wf, text=disguise_name, font=FONT_WIDGET,
                 text_color=color, fg_color="transparent").pack()

def _create_reset_section(main_window, parent):
    section = create_section_frame(parent)
    create_section_header(section, "Configuration Management",
                          "Manage configuration files, settings, and profiles",
                          icon_file="screwdriver_wrench_icon.png")

    # Row 1: utility buttons
    btn_frame = ctk.CTkFrame(section, fg_color="transparent")
    btn_frame.pack(fill="x", padx=40, pady=(0, 20))

    _folder = load_icon("folder_open_icon.png", size=(16, 16))
    ctk.CTkButton(btn_frame, text="Open Config Directory", image=_folder,
                  compound="left", width=280,
                  command=main_window.open_config_directory,
                  **BUTTON_STYLE_PRIMARY).pack(side="left", padx=(0, 20))

    _reset = load_icon("rotate_left_icon.png", size=(16, 16))
    ctk.CTkButton(btn_frame, text="Reset All Settings", image=_reset,
                  compound="left", width=280,
                  command=main_window.reset_to_default_settings,
                  **BUTTON_STYLE_DANGER).pack(side="left")

    # Row 2: profile management
    _create_profile_row(main_window, section)

def _create_profile_row(main_window, section):
    """Build the Save As / Load / Delete profile controls.

    Layout:
      Row A (always visible): [Save As Profile] [dropdown] [Load Profile] [Delete Profile]
      Row B (toggles in):     [name entry] [Confirm] [Cancel]
    """
    outer = ctk.CTkFrame(section, fg_color="transparent")
    outer.pack(fill="x", padx=40, pady=(0, 40))

    # Row A
    profile_frame = ctk.CTkFrame(outer, fg_color="transparent")
    profile_frame.pack(fill="x")

    # Row B - inline name-entry, hidden until "Save As Profile" is clicked
    input_frame = ctk.CTkFrame(outer, fg_color="transparent")
    # not packed yet; revealed by _toggle_save_input

    from src.gui.theme import ENTRY_STYLE
    name_entry = ctk.CTkEntry(
        input_frame,
        placeholder_text="Profile name…",
        **{**ENTRY_STYLE, "width": 280},
    )
    name_entry.pack(side="left", padx=(0, 12))

    def _toggle_save_input():
        if input_frame.winfo_ismapped():
            input_frame.pack_forget()
        else:
            input_frame.pack(fill="x", pady=(10, 0))
            name_entry.delete(0, "end")
            name_entry.focus_set()

    def _confirm_save(event=None):
        name = name_entry.get()
        err = ProfileManager.validate_name(name)
        if err:
            AppModal.error(main_window.root, "Invalid Name", err)
            return
        name = name.strip()
        if name in ProfileManager.list_profiles():
            if not AppModal.confirm(
                main_window.root, "Overwrite Profile",
                f"A profile named '{name}' already exists. Overwrite it?",
            ):
                return
        ok = main_window.save_current_as_profile(name)
        if ok:
            input_frame.pack_forget()
            main_window.refresh_profile_dropdown()
        else:
            AppModal.error(main_window.root, "Save Failed",
                           f"Could not save profile '{name}'. Check logs.")

    name_entry.bind("<Return>", _confirm_save)
    name_entry.bind("<Escape>", lambda e: input_frame.pack_forget())

    _confirm_icon = load_icon("play_icon.png", size=(16, 16))
    ctk.CTkButton(input_frame, text="Confirm", image=_confirm_icon, compound="left",
                  width=130, command=_confirm_save, **BUTTON_STYLE_PRIMARY).pack(
        side="left", padx=(0, 8))

    _cancel_icon = load_icon("xmark_icon.png", size=(16, 16))
    ctk.CTkButton(input_frame, text="Cancel", image=_cancel_icon, compound="left",
                  width=110, command=lambda: input_frame.pack_forget(),
                  **BUTTON_STYLE_DANGER).pack(side="left")

    # Row A contents
    _save_icon = load_icon("box_archive_icon.png", size=(16, 16))
    ctk.CTkButton(profile_frame, text="Save As Profile", image=_save_icon,
                  compound="left", width=200, command=_toggle_save_input,
                  **BUTTON_STYLE_PRIMARY).pack(side="left", padx=(0, 16))

    # Profile selector dropdown
    profiles = ProfileManager.list_profiles()
    display  = profiles if profiles else ["No profiles"]
    profile_var = ctk.StringVar(value=display[0])
    dropdown = ctk.CTkOptionMenu(
        profile_frame, variable=profile_var, values=display, width=200,
        **{k: v for k, v in COMBOBOX_STYLE.items() if k != "width"},
    )
    dropdown.pack(side="left", padx=(0, 12))

    main_window._profile_var      = profile_var
    main_window._profile_dropdown = dropdown

    # Active profile indicator - updated by main_window.update_active_profile_label()
    active_label = ctk.CTkLabel(
        profile_frame, text="", font=FONT_ITEM_DESCRIPTION,
        text_color=COLOR_TEXT_SECONDARY, fg_color="transparent", anchor="w",
    )
    active_label.pack(side="left", padx=(0, 12))
    main_window._active_profile_label = active_label
    # Reflect any profile that was loaded before this tab was built
    main_window.update_active_profile_label()

    # Load Profile
    _load_icon = load_icon("rotate_icon.png", size=(16, 16))
    ctk.CTkButton(profile_frame, text="Load Profile", image=_load_icon,
                  compound="left", width=160,
                  command=lambda: _load_selected_profile(main_window),
                  **BUTTON_STYLE_PRIMARY).pack(side="left", padx=(0, 12))

    # Delete Profile
    _del_icon = load_icon("circle_xmark_icon.png", size=(16, 16))
    ctk.CTkButton(profile_frame, text="Delete Profile", image=_del_icon,
                  compound="left", width=160,
                  command=lambda: _delete_selected_profile(main_window),
                  **BUTTON_STYLE_DANGER).pack(side="left")

def _load_selected_profile(main_window) -> None:
    name = main_window._profile_var.get()
    if not name or name == "No profiles":
        AppModal.warning(main_window.root, "No Profile", "No profile selected.")
        return
    main_window.load_profile(name)

def _delete_selected_profile(main_window) -> None:
    name = main_window._profile_var.get()
    if not name or name == "No profiles":
        AppModal.warning(main_window.root, "No Profile", "No profile selected.")
        return
    if not AppModal.confirm(main_window.root, "Delete Profile",
                            f"Delete profile '{name}'? This cannot be undone."):
        return
    ok = main_window.delete_profile(name)
    if ok:
        main_window.refresh_profile_dropdown()
    else:
        AppModal.error(main_window.root, "Delete Failed",
                       f"Could not delete profile '{name}'. Check logs.")

def _create_checkbox_item(parent, label_text, description, key, main_window, is_last=False):
    wf = build_item_scaffold(parent, label_text, description, is_last)
    var = ctk.BooleanVar(value=main_window.triggerbot.config["General"].get(key, False))
    ctk.CTkCheckBox(wf, text="", variable=var,
                    command=lambda: main_window.save_settings(show_message=False),
                    **CHECKBOX_STYLE).pack()
    main_window.ui_bridge.register(key, var=var)