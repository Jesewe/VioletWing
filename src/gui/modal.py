import customtkinter as ctk

from src.utils.utility import Utility
from src.gui.icon_loader import ASSETS_DIR
from src.gui.theme import (
    FONT_FAMILY_BOLD, FONT_FAMILY_REGULAR,
    FONT_SIZE_H4, FONT_SIZE_P,
    COLOR_BACKGROUND, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_BORDER,
    COLOR_ACCENT_FG, COLOR_ACCENT_HOVER,
)

_KIND_PALETTE = {
    "error":   ("#ef4444", "#dc2626", "\u26a0"),
    "warning": ("#f59e0b", "#d97706", "\u26a0"),
    "info":    (COLOR_ACCENT_FG[1], COLOR_ACCENT_HOVER[1], "\u2139"),
    "confirm": (COLOR_ACCENT_FG[1], COLOR_ACCENT_HOVER[1], "\u2753"),
}

class _AppModalDialog:
    _WIDTH = 420

    def __init__(
        self,
        root: ctk.CTk,
        kind: str,
        title: str,
        message: str,
        *,
        confirm: bool = False,
    ) -> None:
        self._result = False
        accent, _, glyph = _KIND_PALETTE[kind]

        self._win = ctk.CTkToplevel(root)
        self._win.title(title)
        self._win.resizable(False, False)
        self._win.protocol("WM_DELETE_WINDOW", self._on_cancel)

        self._win.update_idletasks()
        height = 190 if not confirm else 210
        x = root.winfo_x() + (root.winfo_width()  // 2) - (self._WIDTH // 2)
        y = root.winfo_y() + (root.winfo_height() // 2) - (height       // 2)
        self._win.geometry(f"{self._WIDTH}x{height}+{x}+{y}")

        # CTkToplevel on Windows drops iconbitmap set before the first draw.
        # 200 ms matches the pattern used in changelog_window.py.
        self._win.after(200, self._apply_icon)

        self._build(glyph, accent, title, message, confirm)
        self._win.grab_set()
        self._win.lift()
        self._win.focus_force()
        root.wait_window(self._win)

    def _apply_icon(self) -> None:
        try:
            self._win.iconbitmap(Utility.resource_path(f"{ASSETS_DIR}/icon.ico"))
        except Exception:
            pass

    def _build(self, glyph: str, accent: str, title: str, message: str, confirm: bool) -> None:
        outer = ctk.CTkFrame(self._win, fg_color=COLOR_BACKGROUND, corner_radius=0)
        outer.pack(fill="both", expand=True)

        header = ctk.CTkFrame(outer, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 0))

        ctk.CTkLabel(
            header,
            text=glyph,
            font=(FONT_FAMILY_BOLD[0], 22, "bold"),
            text_color=accent,
        ).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            header,
            text=title,
            font=(FONT_FAMILY_BOLD[0], FONT_SIZE_H4, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        ).pack(side="left", fill="x", expand=True)

        ctk.CTkFrame(outer, height=1, fg_color=COLOR_BORDER).pack(
            fill="x", padx=24, pady=(12, 0)
        )

        ctk.CTkLabel(
            outer,
            text=message,
            font=(FONT_FAMILY_REGULAR[0], FONT_SIZE_P),
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
            justify="left",
            wraplength=self._WIDTH - 48,
        ).pack(fill="x", padx=24, pady=(12, 0))

        btn_row = ctk.CTkFrame(outer, fg_color="transparent")
        btn_row.pack(fill="x", padx=24, pady=(16, 20))

        if confirm:
            ctk.CTkButton(
                btn_row,
                text="Cancel",
                width=120, height=36, corner_radius=10,
                fg_color="transparent",
                hover_color=COLOR_BACKGROUND,
                border_width=1, border_color=COLOR_BORDER,
                text_color=COLOR_TEXT_SECONDARY,
                font=(FONT_FAMILY_BOLD[0], FONT_SIZE_P, "bold"),
                command=self._on_cancel,
            ).pack(side="right", padx=(8, 0))

            ctk.CTkButton(
                btn_row,
                text="Confirm",
                width=120, height=36, corner_radius=10,
                fg_color=COLOR_ACCENT_FG,
                hover_color=COLOR_ACCENT_HOVER,
                text_color="#ffffff",
                font=(FONT_FAMILY_BOLD[0], FONT_SIZE_P, "bold"),
                command=self._on_confirm,
            ).pack(side="right")
        else:
            ctk.CTkButton(
                btn_row,
                text="OK",
                width=120, height=36, corner_radius=10,
                fg_color=COLOR_ACCENT_FG,
                hover_color=COLOR_ACCENT_HOVER,
                text_color="#ffffff",
                font=(FONT_FAMILY_BOLD[0], FONT_SIZE_P, "bold"),
                command=self._on_confirm,
            ).pack(side="right")

    def _on_confirm(self) -> None:
        self._result = True
        self._win.grab_release()
        self._win.destroy()

    def _on_cancel(self) -> None:
        self._result = False
        self._win.grab_release()
        self._win.destroy()

class AppModal:
    @staticmethod
    def error(root: ctk.CTk, title: str, message: str) -> None:
        _AppModalDialog(root, "error", title, message)

    @staticmethod
    def warning(root: ctk.CTk, title: str, message: str) -> None:
        _AppModalDialog(root, "warning", title, message)

    @staticmethod
    def info(root: ctk.CTk, title: str, message: str) -> None:
        _AppModalDialog(root, "info", title, message)

    @staticmethod
    def confirm(root: ctk.CTk, title: str, message: str) -> bool:
        dlg = _AppModalDialog(root, "confirm", title, message, confirm=True)
        return dlg._result