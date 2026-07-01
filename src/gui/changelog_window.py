import re
import webbrowser
import tkinter as tk
from tkinter import font as tkfont

import customtkinter as ctk

from src.utils.logger import Logger
import src.utils.error_codes as EC
from src.utils.utility import Utility
from src.gui.icon_loader import ASSETS_DIR
from src.gui.theme import (
    FONT_FAMILY_BOLD,
    FONT_FAMILY_REGULAR,
    FONT_SIZE_P,
    FONT_SIZE_H3,
    FONT_SIZE_H4,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_BACKGROUND,
    COLOR_VIOLET,
    COLOR_VIOLET_HOVER,
    COLOR_VIOLET_SUBTLE,
    COLOR_VIOLET_BORDER,
    COLOR_WIDGET_BACKGROUND,
    COLOR_WIDGET_BORDER,
    COLOR_BORDER,
    COLOR_HEADER_BG,
)

logger = Logger.get_logger(__name__)\

# Any line that is exclusively badge markup or a bare URL
_BADGE_LINE_RE = re.compile(
    r"^\s*"
    r"("
    r"(\[!\[.*?\]\(.*?\)\]\(.*?\))"   # [![alt](img)](link)  - linked badge
    r"|(\[!\[.*?\]\(.*?\)\])"         # [![alt](img)]        - unlinked badge
    r"|(!\\[.*?\\]\\(.*?\\))"         # ![alt](url)          - bare image/badge
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


def show_changelog_if_new(root: ctk.CTk, updater) -> None:
    """
    Show the changelog window only when the user hasn't seen this release yet.
    Safe to call before mainloop has started.
    """
    if not updater.changelog or updater.changelog_already_seen():
        return
    ChangelogWindow(root, updater)


class ChangelogWindow(ctk.CTkToplevel):
    _WIDTH  = 700
    _HEIGHT = 600

    # Palette used throughout — derived from theme tokens resolved to dark-mode values at init
    _ACCENT       = "#7c3aed"
    _ACCENT_DIM   = "#3b1f7a"
    _SURFACE      = "#150f2a"   # widget background — slightly lighter than body
    _SEL_BG       = "#3b2a6e"
    _SEL_BG_INACT = "#2d2050"

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

    def _set_icon(self) -> None:
        try:
            path = Utility.resource_path(f"{ASSETS_DIR}/icon.ico")
            self.after(200, lambda: self.iconbitmap(path))
        except Exception as exc:
            Logger.error_code(EC.E0001, "changelog icon: %s", exc)

    def _center(self, parent: ctk.CTk) -> None:
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width()  - self._WIDTH)  // 2
        y = parent.winfo_y() + (parent.winfo_height() - self._HEIGHT) // 2
        self.geometry(f"{self._WIDTH}x{self._HEIGHT}+{x}+{y}")

    # Row layout: 0=hero banner, 1=body (weight=1), 2=footer
    def _build_ui(self, html_url: str) -> None:
        self.configure(fg_color=self._tc(COLOR_BACKGROUND))
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_hero()
        self._build_body()
        self._build_footer(html_url)

    def _build_hero(self) -> None:
        """
        Full-width gradient-style hero block. Uses two layered frames to create
        a subtle two-tone depth effect without a hard border line.
        """
        hero = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=self._tc(COLOR_HEADER_BG),
            height=100,
        )
        hero.grid(row=0, column=0, sticky="ew")
        hero.grid_propagate(False)
        hero.grid_columnconfigure(0, weight=1)
        hero.grid_rowconfigure(0, weight=1)

        inner = ctk.CTkFrame(hero, fg_color="transparent")
        inner.grid(row=0, column=0, sticky="w", padx=32, pady=0)

        # "sparkle" pill badge above the title
        badge = ctk.CTkFrame(
            inner,
            fg_color=self._ACCENT_DIM,
            corner_radius=100,
            height=22,
        )
        badge.pack(anchor="w", pady=(0, 6))
        badge.pack_propagate(False)

        badge_inner = ctk.CTkFrame(badge, fg_color="transparent")
        badge_inner.pack(side="left", padx=10, pady=2)

        ctk.CTkLabel(
            badge_inner,
            text="✦  NEW RELEASE",
            font=(FONT_FAMILY_BOLD[0], 10, "bold"),
            text_color=self._ACCENT,
        ).pack(side="left")

        title_row = ctk.CTkFrame(inner, fg_color="transparent")
        title_row.pack(anchor="w")

        ctk.CTkLabel(
            title_row,
            text="What's new",
            font=(FONT_FAMILY_BOLD[0], 22, "bold"),
            text_color=self._tc(COLOR_TEXT_PRIMARY),
        ).pack(side="left")

        ctk.CTkLabel(
            title_row,
            text=f"  ·  {self._ver}",
            font=(FONT_FAMILY_BOLD[0], FONT_SIZE_H3),
            text_color=self._tc(COLOR_TEXT_SECONDARY),
        ).pack(side="left", pady=(3, 0))

        # Thin accent line at the very bottom of the hero — separates without a border
        ctk.CTkFrame(
            self,
            height=2,
            corner_radius=0,
            fg_color=self._ACCENT_DIM,
        ).grid(row=0, column=0, sticky="sew")

    def _build_body(self) -> None:
        outer = ctk.CTkFrame(
            self,
            fg_color=self._tc(COLOR_BACKGROUND),
            corner_radius=0,
        )
        outer.grid(row=1, column=0, sticky="nsew")
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
            padx=32,
            pady=22,
            cursor="arrow",
            highlightthickness=0,
            selectbackground=self._SEL_BG,
            selectforeground=fg,
            inactiveselectbackground=self._SEL_BG_INACT,
        )
        self._text.grid(row=0, column=0, sticky="nsew")

        sb = ctk.CTkScrollbar(outer, command=self._text.yview, width=8)
        sb.grid(row=0, column=1, sticky="ns", padx=(0, 6))
        self._text.configure(yscrollcommand=sb.set)

        self._configure_tags(bg, fg)

    def _build_footer(self, html_url: str) -> None:
        footer = ctk.CTkFrame(
            self,
            fg_color=self._tc(COLOR_WIDGET_BACKGROUND),
            corner_radius=0,
            height=64,
        )
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_propagate(False)
        footer.grid_columnconfigure(0, weight=1)

        # Thin top rule — matches the accent underline on the hero for visual bookending
        ctk.CTkFrame(
            footer,
            height=1,
            corner_radius=0,
            fg_color=self._tc(COLOR_BORDER),
        ).pack(fill="x", side="top")

        btn_row = ctk.CTkFrame(footer, fg_color="transparent")
        btn_row.pack(side="right", padx=24, pady=0, fill="y")

        # Primary action — full violet fill
        ctk.CTkButton(
            btn_row,
            text="View on GitHub",
            width=144,
            height=36,
            corner_radius=8,
            fg_color=self._ACCENT,
            hover_color=self._tc(COLOR_VIOLET_HOVER),
            border_width=1,
            border_color=self._ACCENT_DIM,
            text_color="#ffffff",
            font=(FONT_FAMILY_BOLD[0], FONT_SIZE_P, "bold"),
            command=lambda: self._on_view(html_url),
        ).pack(side="left", padx=(0, 8), pady=14)

        # Secondary action — ghost button, visually recessed
        ctk.CTkButton(
            btn_row,
            text="Close",
            width=80,
            height=36,
            corner_radius=8,
            fg_color="transparent",
            hover_color=self._tc(COLOR_VIOLET_SUBTLE),
            border_width=1,
            border_color=self._tc(COLOR_WIDGET_BORDER),
            text_color=self._tc(COLOR_TEXT_SECONDARY),
            font=(FONT_FAMILY_BOLD[0], FONT_SIZE_P),
            command=self._on_close,
        ).pack(side="left", pady=14)

    def _configure_tags(self, bg: str, fg: str) -> None:
        muted  = self._tc(COLOR_TEXT_SECONDARY)
        subtle = self._tc(COLOR_VIOLET_SUBTLE)

        mono = FONT_FAMILY_REGULAR[0] if FONT_FAMILY_REGULAR[0] in tkfont.families() else "Courier"
        ui   = FONT_FAMILY_BOLD[0]
        body = FONT_FAMILY_BOLD[0]

        self._text.configure(bg=bg, fg=fg, insertbackground=fg, font=(body, FONT_SIZE_P))

        # Headings — each level drops 2pt from the previous
        self._text.tag_configure("h1", font=(ui, 18, "bold"), foreground=fg,  spacing1=18, spacing3=6)
        self._text.tag_configure("h2", font=(ui, 16, "bold"), foreground=fg,  spacing1=14, spacing3=5)
        self._text.tag_configure("h3", font=(ui, FONT_SIZE_H4, "bold"), foreground=fg,  spacing1=10, spacing3=4)

        # Body text sized to match the app's FONT_SIZE_P so changelog reads like the rest of the UI
        self._text.tag_configure("body",    font=(body, FONT_SIZE_P),           foreground=fg,    spacing1=3)
        self._text.tag_configure("bold",    font=(ui,   FONT_SIZE_P, "bold"),   foreground=fg)
        self._text.tag_configure("code",    font=(mono, FONT_SIZE_P - 1),       background=subtle, foreground=self._ACCENT)
        self._text.tag_configure("muted",   font=(body, FONT_SIZE_P),           foreground=muted)

        # Muted violet for PR/issue refs — distinct without competing with headings
        self._text.tag_configure("pr_num",  font=(ui, FONT_SIZE_P, "bold"),     foreground=self._tc(COLOR_TEXT_SECONDARY))

        # Divider
        self._text.tag_configure("hr",      foreground=self._tc(COLOR_BORDER))

        # Violet bullet dot anchors list items to the accent palette
        self._text.tag_configure("bullet_dot", foreground=self._ACCENT, font=(ui, FONT_SIZE_P + 1, "bold"))

    # markdown rendering (logic unchanged — only spacing tweaks)
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
                self._text.insert("end", "▸  ", ("bullet_dot",))
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
                # Markdown link - render display text only, URL discarded
                self._text.insert("end", m.group(4), base)
            cursor = m.end()
        if cursor < len(text):
            self._text.insert("end", text[cursor:], base)

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