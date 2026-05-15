import customtkinter as ctk
import re
from gui.icon_loader import icon_label
import os
from classes.logger import Logger
from gui.theme import (FONT_TITLE, FONT_SUBTITLE, FONT_WIDGET, FONT_LOG,
                       COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY, SECTION_STYLE)

# Detects the start of a level-tagged log line, e.g. [INFO] or [ERROR].
# Used to group multi-line entries (tracebacks) with their parent line.
_LEVEL_LINE_RE = re.compile(r'^\[(INFO|WARNING|ERROR|DEBUG|CRITICAL)\]')

# Per-level chip colors: (active_fg, active_hover)
_CHIP_COLORS = {
    "ALL":     (("#6d28d9", "#7c3aed"), ("#5b21b6", "#6d28d9")),
    "INFO":    (("#059669", "#10b981"), ("#047857", "#059669")),
    "WARNING": (("#d97706", "#f59e0b"), ("#b45309", "#d97706")),
    "ERROR":   (("#dc2626", "#ef4444"), ("#b91c1c", "#dc2626")),
}
_CHIP_INACTIVE_FG    = "transparent"
_CHIP_INACTIVE_HOVER = ("#ede9fe", "#1e0f4a")
_CHIP_INACTIVE_BORDER = ("#c4b5fd", "#3d2a6e")
_CHIP_INACTIVE_TEXT  = ("#64748b", "#7c6fa0")

def populate_logs(main_window, frame):
    """Populate the logs frame with toolbar and text widget."""
    for widget in frame.winfo_children():
        widget.destroy()

    # Reset chip references each time the tab is rebuilt
    main_window._log_filter_chips = {}

    logs_container = ctk.CTkFrame(frame, fg_color="transparent")
    logs_container.pack(fill="both", expand=True, padx=40, pady=40)

    create_title_section(logs_container)

    logs_card = ctk.CTkFrame(logs_container, **{**SECTION_STYLE, "border_width": 0})
    logs_card.pack(fill="both", expand=True)

    _create_toolbar(main_window, logs_card)
    _create_log_body(main_window, logs_card)

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

def _create_toolbar(main_window, parent):
    toolbar = ctk.CTkFrame(
        parent, height=64, corner_radius=16,
        fg_color=("#f1f5f9", "#1a1030"),
    )
    toolbar.pack(fill="x", padx=3, pady=(3, 0))
    toolbar.pack_propagate(False)

    inner = ctk.CTkFrame(toolbar, fg_color="transparent")
    inner.pack(fill="both", expand=True, padx=24, pady=0)

    # Left: live indicator + title
    left = ctk.CTkFrame(inner, fg_color="transparent")
    left.pack(side="left", fill="y")

    live_dot = ctk.CTkFrame(left, width=8, height=8, corner_radius=4, fg_color=("#059669", "#10b981"))
    live_dot.pack(side="left", pady=(0, 1))
    ctk.CTkLabel(
        left, text="Live",
        font=FONT_WIDGET, text_color=("#059669", "#10b981"),
    ).pack(side="left", padx=(6, 16))

    # Divider after title
    ctk.CTkFrame(inner, width=1, fg_color=("#c4b5fd", "#2a1d4e")).pack(
        side="left", fill="y", padx=(0, 16), pady=14,
    )

    # Filter chips
    chips_frame = ctk.CTkFrame(inner, fg_color="transparent")
    chips_frame.pack(side="left", fill="y")

    for label, level in (("All", "ALL"), ("INFO", "INFO"), ("WARN", "WARNING"), ("ERROR", "ERROR")):
        btn = ctk.CTkButton(
            chips_frame, text=label, width=64, height=32,
            corner_radius=8, font=FONT_WIDGET,
            command=lambda lv=level: main_window.set_log_filter(lv),
        )
        btn.pack(side="left", padx=(0, 6))
        main_window._log_filter_chips[level] = btn

    # Divider before search
    ctk.CTkFrame(inner, width=1, fg_color=("#c4b5fd", "#2a1d4e")).pack(
        side="left", fill="y", padx=(6, 12), pady=14,
    )

    # Search entry
    search_var = ctk.StringVar()
    search_var.trace_add("write", lambda *_: main_window.set_log_search(search_var.get()))
    ctk.CTkEntry(
        inner, textvariable=search_var, placeholder_text="Search logs...",
        width=200, height=34, corner_radius=8,
        border_width=1, border_color=("#c4b5fd", "#3d2a6e"),
        fg_color=("#ffffff", "#0f0a1e"), text_color=COLOR_TEXT_PRIMARY,
        font=FONT_LOG,
    ).pack(side="left")

    # Action buttons pinned to the right
    actions = ctk.CTkFrame(inner, fg_color="transparent")
    actions.pack(side="right", fill="y")

    ctk.CTkButton(
        actions, text="Export", width=80, height=34, corner_radius=8,
        font=FONT_WIDGET, fg_color=("#6d28d9", "#7c3aed"),
        hover_color=("#5b21b6", "#6d28d9"), text_color="#ffffff",
        command=main_window.export_log_to_clipboard,
    ).pack(side="right")

    ctk.CTkButton(
        actions, text="Clear", width=76, height=34, corner_radius=8,
        font=FONT_WIDGET, fg_color=("#dc2626", "#ef4444"),
        hover_color=("#b91c1c", "#dc2626"), text_color="#ffffff",
        command=main_window.clear_log_display,
    ).pack(side="right", padx=(0, 8))

    # Sync chip visuals to the current filter state
    main_window._refresh_log_chips()

def _create_log_body(main_window, parent):
    logs_content = ctk.CTkFrame(parent, corner_radius=0, fg_color="transparent")
    logs_content.pack(fill="both", expand=True, padx=3, pady=(0, 3))

    main_window.log_text = ctk.CTkTextbox(
        logs_content, corner_radius=22, border_width=0,
        font=FONT_LOG, fg_color=("#fcfcfd", "#0f0f11"),
        text_color=COLOR_TEXT_PRIMARY, state="disabled", wrap="word",
    )
    main_window.log_text.pack(fill="both", expand=True, padx=25, pady=25)

    # Amber highlight for search matches; configured on the underlying tk.Text widget
    main_window.log_text._textbox.tag_config(
        "search_hl", background="#f59e0b", foreground="#000000",
    )

def _initial_load(main_window) -> None:
    """Read the entire log file into the buffer, then render."""
    logger = Logger.get_logger(__name__)
    log_path = getattr(main_window, "_active_log_file", Logger.LOG_FILE())

    if not os.path.exists(log_path):
        main_window._reset_log_buffer(
            "=== Application Logs ===\n"
            "Welcome to the logs viewer!\n"
            "Logs will appear here as the application runs.\n\n"
            "[INFO] Logger initialized successfully\n"
            "[INFO] Logs tab loaded\n"
        )
        main_window._log_file_pos = 0
        return

    try:
        with open(log_path, "r", encoding="utf-8") as fh:
            content = fh.read()
            eof = fh.tell()

        if content:
            main_window._reset_log_buffer(content)
        else:
            main_window._reset_log_buffer(
                "=== Application Logs ===\n"
                "Log file exists but is empty.\n"
                "New logs will appear here as they are generated.\n\n"
                "[INFO] Empty log file detected\n"
            )

        main_window._log_file_pos = eof

    except PermissionError:
        logger.error("Permission denied reading log file %s", log_path)
        main_window._reset_log_buffer("[ERROR] Permission denied accessing log file\n")
        main_window._log_file_pos = 0
    except UnicodeDecodeError:
        logger.error("Encoding error reading log file %s", log_path)
        main_window._reset_log_buffer("[ERROR] Log file encoding error\n")
        main_window._log_file_pos = 0
    except Exception as exc:
        logger.error("Unexpected error loading logs: %s", exc)
        main_window._reset_log_buffer(f"[ERROR] Error loading logs: {exc}\n")
        main_window._log_file_pos = 0