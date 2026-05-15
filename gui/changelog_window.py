import re
import webbrowser
import tkinter as tk
from tkinter import font as tkfont

import customtkinter as ctk

from classes.logger import Logger
import classes.error_codes as EC
from classes.utility import Utility
from gui.icon_loader import ASSETS_DIR
from gui.theme import (
    FONT_FAMILY_BOLD,
    FONT_SIZE_P,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_BACKGROUND,
    COLOR_VIOLET,
    COLOR_VIOLET_HOVER,
    COLOR_VIOLET_SUBTLE,
    COLOR_WIDGET_BACKGROUND,
    COLOR_WIDGET_BORDER,
    COLOR_BORDER,
    COLOR_HEADER_BG,
)

logger = Logger.get_logger(__name__)

# regex helpers

# Any line that is exclusively badge markup or a bare URL
_BADGE_LINE_RE = re.compile(
    r"^\s*"
    r"("
    r"(\[!\[.*?\]\(.*?\)\]\(.*?\))"   # [![alt](img)](link)  — linked badge
    r"|(\[!\[.*?\]\(.*?\)\])"         # [![alt](img)]        — unlinked badge
    r"|(!\\[.*?\\]\\(.*?\\))"         # ![alt](url)          — bare image/badge
    r"|(https?://\\S+)"               # bare URL
    r")"
    r"\s*$"
)

# The auto-generated "Full Changelog: url" footer
_FULL_CHANGELOG_RE = re.compile(
    r"^\*\*Full Changelog\*\*\s*:.*$", re.IGNORECASE
)

# Bare GitHub PR/issue URL → #NNN; lookbehind avoids matching inside Markdown link syntax
_GITHUB_PR_RE = re.compile(
    r"(?<!\()https://github\.com/[^/\s]+/[^/\s]+/(?:pull|issues)/(\d+)"
)

# Inline: bare URLs inside text (not already wrapped in Markdown link syntax)
_BARE_URL_RE = re.compile(r"(?<!\()(https?://\S+)")

# public entry point
def show_changelog_if_new(root: ctk.CTk, updater) -> None:
    """
    Show the changelog window only when the user hasn't seen this release yet.
    Safe to call before mainloop has started.
    """
    if not updater.changelog or updater.changelog_already_seen():
        return
    ChangelogWindow(root, updater)

# window
class ChangelogWindow(ctk.CTkToplevel):
    _WIDTH  = 720
    _HEIGHT = 580

    def __init__(self, parent: ctk.CTk, updater) -> None:
        super().__init__(parent)
        self._updater = updater
        self._ver = updater._latest_version or "Latest Release"

        self.title(f"What's new in {self._ver}")
        self.resizable(False, False)
        self._set_icon()
        self._center(parent)

        self.lift()
        self.attributes("-topmost", True)
        self.after(300, lambda: self.attributes("-topmost", False))
        self.after(100, self.grab_set)

        self._build_ui(updater.html_url or "")
        self._render_markdown(updater.changelog or "")

    # icon
    def _set_icon(self) -> None:
        try:
            path = Utility.resource_path(f"{ASSETS_DIR}/icon.ico")
            self.after(200, lambda: self.iconbitmap(path))
        except Exception as exc:
            Logger.error_code(EC.E0001, "changelog icon: %s", exc)

    # positioning
    def _center(self, parent: ctk.CTk) -> None:
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  - self._WIDTH)  // 2
        y = parent.winfo_y() + (parent.winfo_height() - self._HEIGHT) // 2
        self.geometry(f"{self._WIDTH}x{self._HEIGHT}+{x}+{y}")

    # layout
    # Row map: 0=header, 1=header separator, 2=body (weight=1), 3=footer separator, 4=footer
    def _build_ui(self, html_url: str) -> None:
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_body()
        self._build_footer(html_url)

    def _build_header(self) -> None:
        hdr = ctk.CTkFrame(
            self, corner_radius=0,
            fg_color=self._tc(COLOR_HEADER_BG),
            height=84,
        )
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(1, weight=1)
        hdr.grid_rowconfigure(0, weight=1)

        # Violet left accent bar gives the header a clear visual anchor
        ctk.CTkFrame(
            hdr,
            width=4,
            corner_radius=0,
            fg_color="#7c3aed",
        ).grid(row=0, column=0, sticky="ns")

        # Title + version stacked vertically
        content = ctk.CTkFrame(hdr, fg_color="transparent")
        content.grid(row=0, column=1, sticky="w", padx=(18, 20))

        ctk.CTkLabel(
            content,
            text="What's new",
            font=(FONT_FAMILY_BOLD[0], 22, "bold"),
            text_color=self._tc(COLOR_TEXT_PRIMARY),
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            content,
            text=self._ver,
            font=(FONT_FAMILY_BOLD[0], 13),
            text_color="#7c6fa0",
            anchor="w",
        ).pack(anchor="w")

        # Separator between header and body
        ctk.CTkFrame(
            self, height=1, corner_radius=0,
            fg_color=self._tc(COLOR_BORDER),
        ).grid(row=1, column=0, sticky="ew")

    def _build_body(self) -> None:
        outer = ctk.CTkFrame(self, fg_color=self._tc(COLOR_BACKGROUND), corner_radius=0)
        outer.grid(row=2, column=0, sticky="nsew")
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_columnconfigure(0, weight=1)

        bg = self._tc(COLOR_BACKGROUND)
        fg = self._tc(COLOR_TEXT_PRIMARY)

        self._text = tk.Text(
            outer,
            wrap="word",
            state="disabled",
            relief="flat",
            bd=0,
            padx=28,
            pady=18,
            cursor="arrow",
            highlightthickness=0,
        )
        self._text.grid(row=0, column=0, sticky="nsew")

        sb = ctk.CTkScrollbar(outer, command=self._text.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self._text.configure(yscrollcommand=sb.set)

        self._configure_tags(bg, fg)

    def _build_footer(self, html_url: str) -> None:
        ctk.CTkFrame(
            self, fg_color=self._tc(COLOR_BORDER), height=1, corner_radius=0
        ).grid(row=3, column=0, sticky="ew")

        footer = ctk.CTkFrame(
            self,
            fg_color=self._tc(COLOR_WIDGET_BACKGROUND),
            corner_radius=0,
            height=68,
        )
        footer.grid(row=4, column=0, sticky="ew")
        footer.grid_propagate(False)
        footer.grid_columnconfigure(0, weight=1)

        btn_row = ctk.CTkFrame(footer, fg_color="transparent")
        btn_row.grid(row=0, column=0, sticky="e", padx=20, pady=14)

        ctk.CTkButton(
            btn_row,
            text="View Release",
            width=136,
            height=40,
            corner_radius=10,
            fg_color=self._tc(COLOR_VIOLET),
            hover_color=self._tc(COLOR_VIOLET_HOVER),
            text_color="#ffffff",
            font=(FONT_FAMILY_BOLD[0], FONT_SIZE_P, "bold"),
            command=lambda: self._on_view(html_url),
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_row,
            text="Close",
            width=88,
            height=40,
            corner_radius=10,
            fg_color="transparent",
            hover_color=self._tc(COLOR_VIOLET_SUBTLE),
            border_width=1,
            border_color=self._tc(COLOR_WIDGET_BORDER),
            text_color=self._tc(COLOR_TEXT_PRIMARY),
            font=(FONT_FAMILY_BOLD[0], FONT_SIZE_P, "bold"),
            command=self._on_close,
        ).pack(side="left")

    # text tags
    def _configure_tags(self, bg: str, fg: str) -> None:
        subtle = self._tc(COLOR_VIOLET_SUBTLE)
        muted  = self._tc(COLOR_TEXT_SECONDARY)

        mono = "JetBrainsMono" if "JetBrainsMono" in tkfont.families() else "Courier"
        ui   = FONT_FAMILY_BOLD[0]
        # Outfit is a proportional sans-serif — much more readable for prose than JetBrainsMono
        body = FONT_FAMILY_BOLD[0]

        self._text.configure(bg=bg, fg=fg, insertbackground=fg, font=(body, 14))

        # Headings
        self._text.tag_configure("h1", font=(ui, 20, "bold"), foreground=fg,  spacing1=16, spacing3=6)
        self._text.tag_configure("h2", font=(ui, 17, "bold"), foreground=fg,  spacing1=12, spacing3=5)
        self._text.tag_configure("h3", font=(ui, 15, "bold"), foreground=fg,  spacing1=10, spacing3=4)

        # Body
        self._text.tag_configure("body", font=(body, 14), foreground=fg, spacing1=3)
        self._text.tag_configure("bold", font=(ui, 14, "bold"))
        self._text.tag_configure("code", font=(mono, 13), background=subtle, foreground=fg)

        # Inline PR/issue number — muted violet, no underline
        self._text.tag_configure("pr_num", font=(ui, 14, "bold"), foreground="#7c6fa0")

        # Divider
        self._text.tag_configure("hr", foreground=muted)

        # Bullet lead character
        self._text.tag_configure("bullet_dot", foreground="#7c3aed", font=(ui, 14, "bold"))

    # markdown rendering
    def _render_markdown(self, raw: str) -> None:
        lines = self._filter_lines(raw.splitlines())

        self._text.configure(state="normal")
        self._text.delete("1.0", "end")

        prev_blank = True
        for line in lines:
            stripped = line.strip()

            # Headings
            if stripped.startswith("### "):
                self._gap(prev_blank)
                self._insert_inline(stripped[4:], ("h3",))
                self._text.insert("end", "\n")
                prev_blank = False
                continue
            if stripped.startswith("## "):
                self._gap(prev_blank)
                self._insert_inline(stripped[3:], ("h2",))
                self._text.insert("end", "\n")
                prev_blank = False
                continue
            if stripped.startswith("# "):
                self._gap(prev_blank)
                self._insert_inline(stripped[2:], ("h1",))
                self._text.insert("end", "\n")
                prev_blank = False
                continue

            # Horizontal rule
            if re.fullmatch(r"[-*_]{3,}", stripped):
                self._text.insert("end", "─" * 58 + "\n", ("hr",))
                prev_blank = False
                continue

            # Bullet list item
            m_bullet = re.match(r"^(\s{0,4})[-*+] (.+)$", line)
            if m_bullet:
                indent = "  " * (len(m_bullet.group(1)) // 2)
                self._text.insert("end", indent)
                self._text.insert("end", "•  ", ("bullet_dot",))
                content = self._strip_inline_noise(m_bullet.group(2))
                self._insert_inline(content, ("body",))
                self._text.insert("end", "\n")
                prev_blank = False
                continue

            # Numbered list item
            m_num = re.match(r"^(\s{0,4})\d+\. (.+)$", line)
            if m_num:
                indent = "  " * (len(m_num.group(1)) // 2)
                self._text.insert("end", indent)
                content = self._strip_inline_noise(m_num.group(2))
                self._insert_inline(content, ("body",))
                self._text.insert("end", "\n")
                prev_blank = False
                continue

            # Blank line
            if not stripped:
                self._text.insert("end", "\n")
                prev_blank = True
                continue

            # Paragraph
            self._gap(prev_blank)
            self._insert_inline(self._strip_inline_noise(line), ("body",))
            self._text.insert("end", "\n")
            prev_blank = False

        self._text.configure(state="disabled")

    # filtering
    @staticmethod
    def _filter_lines(lines: list[str]) -> list[str]:
        """
        Drop lines that are exclusively badges, bare URLs, or the auto-generated
        Full Changelog footer - leaving everything else untouched.
        """
        out = []
        for ln in lines:
            if _BADGE_LINE_RE.match(ln):
                continue
            if _FULL_CHANGELOG_RE.match(ln.strip()):
                continue
            out.append(ln)

        # Trim leading/trailing blank lines that may have been left by filtering
        while out and not out[0].strip():
            out.pop(0)
        while out and not out[-1].strip():
            out.pop()

        return out

    @staticmethod
    def _strip_inline_noise(text: str) -> str:
        """Convert GitHub PR/issue bare URLs to #NNN and strip any remaining bare URLs."""
        # Convert bare GitHub PR/issue URLs to their short form before stripping everything else
        converted = _GITHUB_PR_RE.sub(lambda m: f"#{m.group(1)}", text)
        cleaned   = _BARE_URL_RE.sub("", converted)
        return re.sub(r"\s{2,}", " ", cleaned).strip()

    # inline spans
    _INLINE_RE = re.compile(r"(\*\*(.+?)\*\*|`(.+?)`|\[(.+?)\]\((.+?)\)|#\d+)")

    def _insert_inline(self, text: str, base: tuple) -> None:
        cursor = 0
        for m in self._INLINE_RE.finditer(text):
            if m.start() > cursor:
                self._text.insert("end", text[cursor:m.start()], base)
            raw = m.group(0)
            if raw.startswith("**"):
                self._text.insert("end", m.group(2), base + ("bold",))
            elif raw.startswith("`"):
                self._text.insert("end", m.group(3), ("code",))
            elif raw.startswith("#") and raw[1:].isdigit():
                # PR/issue short form produced by _strip_inline_noise
                self._text.insert("end", raw, ("pr_num",))
            else:
                # Markdown link — render display text only, URL discarded
                self._text.insert("end", m.group(4), base)
            cursor = m.end()
        if cursor < len(text):
            self._text.insert("end", text[cursor:], base)

    # helpers
    def _gap(self, prev_blank: bool) -> None:
        """Insert a small spacing line before a block element if not already spaced."""
        if not prev_blank:
            self._text.insert("end", "\n")

    @staticmethod
    def _tc(value) -> str:
        """Return the dark-mode value from a (light, dark) theme tuple."""
        if isinstance(value, (list, tuple)):
            return value[1]
        return value

    # button actions
    def _on_view(self, url: str) -> None:
        if url:
            webbrowser.open(url)
        self._dismiss()

    def _on_close(self) -> None:
        self._dismiss()

    def _dismiss(self) -> None:
        self._updater.mark_changelog_seen()
        self.grab_release()
        self.destroy()