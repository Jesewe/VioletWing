import customtkinter as ctk
from src.gui.icon_loader import icon_label, load_icon
from src.utils.config_manager import ConfigManager
import src.utils.profile_manager as ProfileManager
from src.gui.components import create_section_frame, create_section_header, build_item_scaffold, create_scrollable_frame
from src.gui.modal import AppModal
from src.gui.theme import (
    COLOR_BACKGROUND,
    FONT_TITLE, FONT_SUBTITLE, FONT_ITEM_LABEL, FONT_ITEM_DESCRIPTION, FONT_WIDGET,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    CHECKBOX_STYLE, COMBOBOX_STYLE,
    BUTTON_STYLE_PRIMARY, BUTTON_STYLE_DANGER,
)

def populate_general_settings(main_window, frame):
    settings = create_scrollable_frame(frame, main_window)

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
    
    wf = build_item_scaffold(section, "Enable Features", "", is_last=True)
    
    _create_checkbox_item(wf, "Trigger", "Trigger", main_window)
    _create_checkbox_item(wf, "Overlay", "Overlay", main_window)
    _create_checkbox_item(wf, "Bunnyhop", "Bunnyhop", main_window)
    _create_checkbox_item(wf, "Noflash", "Noflash", main_window)

def _create_program_section(main_window, parent):
    section = create_section_frame(parent)
    create_section_header(section, "Program Settings",
                          "Configure core program behaviour and disguise",
                          icon_file="user_secret_icon.png")
    
    wf_prog = build_item_scaffold(section, "Program Behaviour", "", is_last=False)
    _create_checkbox_item(wf_prog, "Detailed Logs", "DetailedLogs", main_window)
    _create_checkbox_item(wf_prog, "Disguise", "Disguise", main_window)

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

    wf_util = build_item_scaffold(section, "System Config", "Directly manage underlying configuration files", is_last=False)
    
    util_col = ctk.CTkFrame(wf_util, fg_color="transparent")
    util_col.pack(side="right")

    _folder = load_icon("folder_open_icon.png", size=(16, 16))
    ctk.CTkButton(util_col, text="Open Config Directory", image=_folder,
                  compound="left", width=220,
                  command=main_window.open_config_directory,
                  **BUTTON_STYLE_PRIMARY).pack(pady=(0, 10), fill="x")

    def _do_reinstall():
        import threading
        from src.core.offset_fetcher import force_reinstall_dumper
        
        def _run():
            success = force_reinstall_dumper()
            def _finish():
                if success:
                    AppModal.info(main_window.root, "Success", "cs2-dumper.exe reinstalled successfully.")
                else:
                    AppModal.error(main_window.root, "Failed", "Could not reinstall cs2-dumper.exe. Check logs.")
            main_window.ui_queue_put(_finish)
        
        threading.Thread(target=_run, daemon=True).start()

    _reinstall = load_icon("rotate_icon.png", size=(16, 16))
    ctk.CTkButton(util_col, text="Reinstall cs2-dumper", image=_reinstall,
                  compound="left", width=220, command=_do_reinstall,
                  **BUTTON_STYLE_PRIMARY).pack(pady=(0, 10), fill="x")

    _reset = load_icon("rotate_left_icon.png", size=(16, 16))
    ctk.CTkButton(util_col, text="Reset All Settings", image=_reset,
                  compound="left", width=220,
                  command=main_window.reset_to_default_settings,
                  **BUTTON_STYLE_DANGER).pack(fill="x")

    wf_prof = build_item_scaffold(section, "Profiles", "Save, load, and manage custom setting profiles", is_last=True)
    _create_profile_row(main_window, wf_prof)

def _create_profile_row(main_window, parent):
    col = ctk.CTkFrame(parent, fg_color="transparent")
    col.pack(side="right")

    active_label = ctk.CTkLabel(
        col, text="", font=FONT_ITEM_DESCRIPTION,
        text_color=COLOR_TEXT_PRIMARY, fg_color="transparent", anchor="e",
    )
    active_label.pack(fill="x", pady=(0, 8))
    main_window._active_profile_label = active_label

    row1 = ctk.CTkFrame(col, fg_color="transparent")
    row1.pack(fill="x", pady=(0, 10))

    row2 = ctk.CTkFrame(col, fg_color="transparent")
    row2.pack(fill="x")

    input_frame = ctk.CTkFrame(col, fg_color="transparent")

    # -- ROW 1: Dropdown, Load, Delete --
    profiles = ProfileManager.list_profiles()
    display  = profiles if profiles else ["No profiles"]
    profile_var = ctk.StringVar(value=display[0])
    
    dropdown = ctk.CTkOptionMenu(
        row1, variable=profile_var, values=display, width=160,
        **{k: v for k, v in COMBOBOX_STYLE.items() if k != "width"},
    )
    dropdown.pack(side="left", padx=(0, 10))
    main_window._profile_var = profile_var
    main_window._profile_dropdown = dropdown

    _load_icon = load_icon("rotate_icon.png", size=(16, 16))
    ctk.CTkButton(row1, text="Load", image=_load_icon, compound="left", width=100,
                  command=lambda: _load_selected_profile(main_window),
                  **BUTTON_STYLE_PRIMARY).pack(side="left", padx=(0, 10))

    _del_icon = load_icon("circle_xmark_icon.png", size=(16, 16))
    ctk.CTkButton(row1, text="Delete", image=_del_icon, compound="left", width=100,
                  command=lambda: _delete_selected_profile(main_window),
                  **BUTTON_STYLE_DANGER).pack(side="left")

    # -- ROW 2: Save As button --
    _save_icon = load_icon("box_archive_icon.png", size=(16, 16))
    
    from src.gui.theme import ENTRY_STYLE
    name_entry = ctk.CTkEntry(input_frame, placeholder_text="Profile name…", **{**ENTRY_STYLE, "width": 200})
    name_entry.pack(side="left", padx=(0, 10))

    def _toggle_save_input():
        if input_frame.winfo_ismapped():
            input_frame.pack_forget()
        else:
            input_frame.pack(fill="x", pady=(10, 0))
            name_entry.delete(0, "end")
            name_entry.focus_set()

    ctk.CTkButton(row2, text="Save As New Profile", image=_save_icon,
                  compound="left", width=380, command=_toggle_save_input,
                  **BUTTON_STYLE_PRIMARY).pack(side="left")

    def _confirm_save(event=None):
        name = name_entry.get().strip()
        err = ProfileManager.validate_name(name)
        if err:
            AppModal.error(main_window.root, "Invalid Name", err)
            return
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
                  width=90, command=_confirm_save, **BUTTON_STYLE_PRIMARY).pack(side="left", padx=(0, 10))

    _cancel_icon = load_icon("xmark_icon.png", size=(16, 16))
    ctk.CTkButton(input_frame, text="Cancel", image=_cancel_icon, compound="left",
                  width=80, command=lambda: input_frame.pack_forget(),
                  **BUTTON_STYLE_DANGER).pack(side="left")
    
    # Initialize profile state
    main_window.update_active_profile_label()

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

def _create_checkbox_item(parent, label_text, key, main_window):
    var = ctk.BooleanVar(value=main_window.triggerbot.config["General"].get(key, False))
    cb = ctk.CTkCheckBox(parent, text=label_text, variable=var,
                         command=lambda: main_window.save_settings(show_message=False),
                         **CHECKBOX_STYLE)
    cb.pack(side="left", padx=(0, 20))
    main_window.ui_bridge.register(key, var=var)