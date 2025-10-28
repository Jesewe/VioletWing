import customtkinter as ctk
import os
from classes.logger import Logger
from gui.theme import (FONT_TITLE, FONT_SUBTITLE, FONT_SECTION_TITLE, FONT_WIDGET,
                         COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, SECTION_STYLE)

def populate_logs(main_window, frame):
    """Populate the logs frame with a text widget to display logs."""
    # Clear existing widgets to prevent duplication
    for widget in frame.winfo_children():
        widget.destroy()

    # Container for all logs UI elements with padding
    logs_container = ctk.CTkFrame(
        frame,
        fg_color="transparent"
    )
    logs_container.pack(fill="both", expand=True, padx=40, pady=40)

    create_title_section(logs_container)

    # Main card for logs display
    logs_card = ctk.CTkFrame(
        logs_container,
        **{**SECTION_STYLE, "border_width": 0}
    )
    logs_card.pack(fill="both", expand=True)

    # Header bar within the logs card
    logs_header = ctk.CTkFrame(
        logs_card,
        height=70,
        corner_radius=22,
        fg_color=("#f1f5f9", "#262626"),
    )
    logs_header.pack(fill="x", padx=3, pady=(3, 0))
    logs_header.pack_propagate(False)

    # Content frame for header elements
    header_content = ctk.CTkFrame(logs_header, fg_color="transparent")
    header_content.pack(fill="both", expand=True, padx=30, pady=20)

    # Logs section title
    logs_title = ctk.CTkLabel(
        header_content,
        text="System Logs",
        font=FONT_SECTION_TITLE,
        text_color=COLOR_TEXT_PRIMARY
    )
    logs_title.pack(side="left")

    # Status indicator frame
    status_frame = ctk.CTkFrame(
        header_content, 
        corner_radius=20,
        fg_color=("#dcfce7", "#14532d")
    )
    status_frame.pack(side="right")

    # Status content container
    status_content = ctk.CTkFrame(status_frame, fg_color="transparent")
    status_content.pack(padx=15, pady=8)

    # Status dot indicator
    status_dot = ctk.CTkLabel(
        status_content,
        text="●",
        font=FONT_WIDGET,
        text_color=("#059669", "#10b981")
    )
    status_dot.pack(side="left", padx=(0, 10))

    # Status text "Live"
    status_text = ctk.CTkLabel(
        status_content,
        text="Live",
        font=FONT_WIDGET,
        text_color=("#059669", "#10b981")
    )
    status_text.pack(side="left")

    # Content area for log text
    logs_content = ctk.CTkFrame(
        logs_card,
        corner_radius=0,
        fg_color="transparent"
    )
    logs_content.pack(fill="both", expand=True, padx=3, pady=(0, 3))

    # Text widget to display logs
    main_window.log_text = ctk.CTkTextbox(
        logs_content,
        corner_radius=22,
        border_width=0,
        font=FONT_WIDGET,
        fg_color=("#fcfcfd", "#0f0f11"),
        text_color=COLOR_TEXT_PRIMARY,
        state="disabled",
        wrap="word"
    )
    main_window.log_text.pack(fill="both", expand=True, padx=25, pady=25)

    # Load existing logs and set initial position
    _load_logs_safely(main_window)
    if os.path.exists(Logger.LOG_FILE):
        main_window.last_log_position = os.path.getsize(Logger.LOG_FILE)
    else:
        main_window.last_log_position = 0

def create_title_section(parent):
    """Create the title and subtitle for the settings page."""
    header_frame = ctk.CTkFrame(
        parent,
        fg_color="transparent",
        height=100
    )
    header_frame.pack(fill="x", pady=(0, 35))
    header_frame.pack_propagate(False)

    title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
    title_container.pack(side="left", fill="y")

    ctk.CTkLabel(
        title_container,
        text="📋 Application Logs",
        font=FONT_TITLE,
        text_color=COLOR_TEXT_PRIMARY
    ).pack(anchor="w", pady=(10, 0))

    ctk.CTkLabel(
        title_container,
        text="Real-time application logs and system events",
        font=FONT_SUBTITLE,
        text_color=COLOR_TEXT_SECONDARY
    ).pack(anchor="w", pady=(8, 0))

def _load_logs_safely(main_window):
    """Safely load logs with duplicate prevention and proper error handling."""
    logger = Logger.get_logger(__name__)
    try:
        # Display welcome message if log file doesn't exist
        if not os.path.exists(Logger.LOG_FILE):
            welcome_msg = (
                "=== Application Logs ===\n"
                "Welcome to the logs viewer!\n"
                "Logs will appear here as the application runs.\n\n"
                "[INFO] Logger initialized successfully\n"
                "[INFO] Logs tab loaded\n"
            )
            _replace_content(main_window, welcome_msg)
            return

        # Read all log lines from the file
        with open(Logger.LOG_FILE, 'r', encoding='utf-8') as log_file:
            raw_lines = log_file.read().splitlines()

        # Get currently displayed lines to avoid duplicates
        displayed = main_window.log_text.get("1.0", "end-1c").splitlines()
        # Filter out duplicates
        new_lines = [line for line in raw_lines if line not in displayed]

        if new_lines:
            main_window.log_text.configure(state="normal")
            if not displayed:
                # Initial load: replace all content
                main_window.log_text.delete("1.0", "end")
                main_window.log_text.insert("1.0", "\n".join(new_lines) + "\n")
            else:
                # Append new lines only
                main_window.log_text.insert("end", "\n".join(new_lines) + "\n")
            main_window.log_text.see("end")
            main_window.log_text.configure(state="disabled")
        elif not displayed:
            # Display message if log file is empty
            empty_msg = (
                "=== Application Logs ===\n"
                "Log file exists but is empty.\n"
                "New logs will appear here as they are generated.\n\n"
                "[INFO] Empty log file detected\n"
            )
            _replace_content(main_window, empty_msg)

    except FileNotFoundError:
        logger.warning(f"Log file {Logger.LOG_FILE} not found")
        _show_error_message(main_window, "Log file not found")
    except PermissionError:
        logger.error(f"Permission denied reading log file {Logger.LOG_FILE}")
        _show_error_message(main_window, "Permission denied accessing log file")
    except UnicodeDecodeError:
        logger.error(f"Encoding error reading log file {Logger.LOG_FILE}")
        _show_error_message(main_window, "Log file encoding error")
    except Exception as e:
        logger.error(f"Unexpected error loading logs: {e}")
        _show_error_message(main_window, f"Error loading logs: {str(e)}")

def _replace_content(main_window, text):
    """Helper to replace the entire content of the log widget."""
    # Enable widget, clear content, insert new text, and disable again
    main_window.log_text.configure(state="normal")
    main_window.log_text.delete("1.0", "end")
    main_window.log_text.insert("1.0", text)
    main_window.log_text.configure(state="disabled")

def _show_error_message(main_window, error_msg):
    """Display error message in the logs text area."""
    # Format error message with guidance
    error_display = (
        "=== Application Logs ===\n"
        "❌ Error Loading Logs\n\n"
        f"{error_msg}\n\n"
        "Please check the application logs directory and permissions.\n"
        "Try refreshing the logs tab or restarting the application.\n\n"
        f"[ERROR] {error_msg}\n"
    )
    main_window.log_text.configure(state="normal")
    main_window.log_text.delete("1.0", "end")
    main_window.log_text.insert("1.0", error_display)
    main_window.log_text.configure(state="disabled")