import customtkinter as ctk
from gui.icon_loader import icon_label
import os
from classes.logger import Logger
from gui.theme import (FONT_TITLE, FONT_SUBTITLE, FONT_SECTION_TITLE, FONT_WIDGET, FONT_LOG,
                         COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, SECTION_STYLE)

def populate_logs(main_window, frame):
    """Populate the logs frame with a text widget to display logs."""
    for widget in frame.winfo_children():
        widget.destroy()

    logs_container = ctk.CTkFrame(frame, fg_color="transparent")
    logs_container.pack(fill="both", expand=True, padx=40, pady=40)

    create_title_section(logs_container)

    logs_card = ctk.CTkFrame(logs_container, **{**SECTION_STYLE, "border_width": 0})
    logs_card.pack(fill="both", expand=True)

    logs_header = ctk.CTkFrame(
        logs_card, height=70, corner_radius=22,
        fg_color=("#f1f5f9", "#262626"),
    )
    logs_header.pack(fill="x", padx=3, pady=(3, 0))
    logs_header.pack_propagate(False)

    header_content = ctk.CTkFrame(logs_header, fg_color="transparent")
    header_content.pack(fill="both", expand=True, padx=30, pady=20)

    ctk.CTkLabel(
        header_content, text="System Logs",
        font=FONT_SECTION_TITLE, text_color=COLOR_TEXT_PRIMARY,
    ).pack(side="left")

    status_frame = ctk.CTkFrame(header_content, corner_radius=20, fg_color=("#dcfce7", "#14532d"))
    status_frame.pack(side="right")
    status_content = ctk.CTkFrame(status_frame, fg_color="transparent")
    status_content.pack(padx=15, pady=8)
    ctk.CTkLabel(
        status_content, text="●", font=FONT_WIDGET,
        text_color=("#059669", "#10b981"),
    ).pack(side="left", padx=(0, 10))
    ctk.CTkLabel(
        status_content, text="Live", font=FONT_WIDGET,
        text_color=("#059669", "#10b981"),
    ).pack(side="left")

    logs_content = ctk.CTkFrame(logs_card, corner_radius=0, fg_color="transparent")
    logs_content.pack(fill="both", expand=True, padx=3, pady=(0, 3))

    main_window.log_text = ctk.CTkTextbox(
        logs_content, corner_radius=22, border_width=0,
        font=FONT_LOG, fg_color=("#fcfcfd", "#0f0f11"),
        text_color=COLOR_TEXT_PRIMARY, state="disabled", wrap="word",
    )
    main_window.log_text.pack(fill="both", expand=True, padx=25, pady=25)

    # Do an initial bulk load from disk, then set the file-position tracker so
    # the polling timer only picks up lines written after this point.
    _initial_load(main_window)

def create_title_section(parent):
    header_frame = ctk.CTkFrame(parent, fg_color="transparent", height=100)
    header_frame.pack(fill="x", pady=(0, 35))
    header_frame.pack_propagate(False)

    title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
    title_container.pack(side="left", fill="y")

    _icon_row = ctk.CTkFrame(title_container, fg_color="transparent")
    _icon_row.pack(anchor="w", pady=(10, 0))
    icon_label(_icon_row, "clipboard_list_icon.png", size=(32, 32), padx=(0, 14))
    ctk.CTkLabel(
        _icon_row, text="Application Logs",
        font=FONT_TITLE, text_color=COLOR_TEXT_PRIMARY,
    ).pack(side="left")

    ctk.CTkLabel(
        title_container,
        text="Real-time application logs and system events",
        font=FONT_SUBTITLE, text_color=COLOR_TEXT_SECONDARY,
    ).pack(anchor="w", pady=(8, 0))

def _initial_load(main_window) -> None:
    """Read the entire log file once on tab open and advance the position tracker."""
    logger = Logger.get_logger(__name__)
    log_path = getattr(main_window, "_active_log_file", Logger.LOG_FILE())

    if not os.path.exists(log_path):
        _write_to_widget(main_window, (
            "=== Application Logs ===\n"
            "Welcome to the logs viewer!\n"
            "Logs will appear here as the application runs.\n\n"
            "[INFO] Logger initialized successfully\n"
            "[INFO] Logs tab loaded\n"
        ))
        main_window._log_file_pos = 0
        return

    try:
        with open(log_path, "r", encoding="utf-8") as fh:
            content = fh.read()
            eof = fh.tell()

        if content:
            _write_to_widget(main_window, content)
        else:
            _write_to_widget(main_window, (
                "=== Application Logs ===\n"
                "Log file exists but is empty.\n"
                "New logs will appear here as they are generated.\n\n"
                "[INFO] Empty log file detected\n"
            ))

        # Single source of truth for where the polling timer should resume.
        main_window._log_file_pos = eof

    except PermissionError:
        logger.error("Permission denied reading log file %s", log_path)
        _write_to_widget(main_window, "[ERROR] Permission denied accessing log file\n")
        main_window._log_file_pos = 0
    except UnicodeDecodeError:
        logger.error("Encoding error reading log file %s", log_path)
        _write_to_widget(main_window, "[ERROR] Log file encoding error\n")
        main_window._log_file_pos = 0
    except Exception as exc:
        logger.error("Unexpected error loading logs: %s", exc)
        _write_to_widget(main_window, f"[ERROR] Error loading logs: {exc}\n")
        main_window._log_file_pos = 0

def _write_to_widget(main_window, text: str) -> None:
    """Replace the entire log widget content."""
    main_window.log_text.configure(state="normal")
    main_window.log_text.delete("1.0", "end")
    main_window.log_text.insert("1.0", text)
    main_window.log_text.see("end")
    main_window.log_text.configure(state="disabled")