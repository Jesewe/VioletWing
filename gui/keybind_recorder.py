from __future__ import annotations
import customtkinter as ctk
from gui.theme import (
    COLOR_ACCENT_FG, COLOR_ACCENT_HOVER, COLOR_VIOLET_BORDER,
    COLOR_WIDGET_FG, COLOR_WIDGET_BORDER, COLOR_TEXT_PRIMARY,
    FONT_WIDGET,
)
from constants.vk_codes import VK_CODES

# Reverse map: Windows VK code (int) -> canonical name from VK_CODES.
# Built by iterating VK_CODES in definition order so the first entry wins on
# any collision (there are none in practice, but order is explicit).
# Mouse buttons are excluded here -- they're resolved from event.num instead.
_VK_TO_CANONICAL: dict[int, str] = {
    code: name
    for name, code in VK_CODES.items()
    if not name.startswith("mouse")
}

# tkinter event.num -> canonical name for mouse buttons.
# Scroll wheel on Windows also sends num=4/5 but with event.delta != 0;
# we guard against that in _on_mouse.
_MOUSE_NUM_TO_CANONICAL: dict[int, str] = {
    1: "mouse1",
    2: "mouse2",
    3: "mouse3",
    8: "mouse4",
    9: "mouse5",
}

_STATE_IDLE   = "idle"
_STATE_LISTEN = "listen"


class KeybindRecorder(ctk.CTkFrame):
    """A button that captures the next keypress or mouse button click as a keybind.

    Integrates with UIConfigBridge via a StringVar -- register with var=, not widget=.
    The var always holds the canonical key name (e.g. "mouse4", "x", "f5").

    IMPORTANT: do not attach a trace to the var that calls save_settings(). Instead,
    pass on_capture= to receive a callback only when the user actually records a key.
    This prevents a feedback loop with the file watcher's update_ui_from_config().
    """

    def __init__(self, parent, var: ctk.StringVar, on_capture=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        self._var = var
        self._on_capture = on_capture  # called after a successful capture, not on programmatic set
        self._state = _STATE_IDLE
        self._key_bid: str | None = None
        self._mouse_bid: str | None = None

        self._btn = ctk.CTkButton(
            self,
            text=self._display_text(var.get()),
            width=220,
            height=45,
            corner_radius=10,
            border_width=1,
            border_color=COLOR_WIDGET_BORDER,
            fg_color=COLOR_WIDGET_FG,
            hover_color=COLOR_ACCENT_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            font=FONT_WIDGET,
            command=self._start_listening,
        )
        self._btn.pack()

        # Sync display on programmatic updates (profile load, reset to default)
        var.trace_add("write", lambda *_: self._sync_display())

    def get(self) -> str:
        return self._var.get()

    def _display_text(self, key: str) -> str:
        return key.upper() if key else "-- unbound --"

    def _sync_display(self) -> None:
        self._btn.configure(text=self._display_text(self._var.get()))

    def _start_listening(self) -> None:
        if self._state == _STATE_LISTEN:
            self._stop_listening(commit=False)
            return

        self._state = _STATE_LISTEN
        self._btn.configure(
            text="Press a key...",
            fg_color=COLOR_ACCENT_FG,
            text_color="#ffffff",
            border_color=COLOR_VIOLET_BORDER,
        )

        # Defer by one tick so the click that opened listening doesn't self-capture
        self.after(1, self._attach_bindings)

    def _attach_bindings(self) -> None:
        if self._state != _STATE_LISTEN:
            return

        root = self.winfo_toplevel()

        self._key_bid = root.bind("<KeyPress>", self._on_key, add=True)

        # Single <ButtonPress> binding catches all mouse buttons via event.num,
        # including side buttons (num=8/9) without needing <Button-8/9> sequences
        # which are invalid Tcl on Tk 8.6.
        self._mouse_bid = root.bind("<ButtonPress>", self._on_mouse, add=True)

        self._btn.bind("<FocusOut>", lambda e: self._stop_listening(commit=False), add=True)
        root.focus_set()

    def _stop_listening(self, *, commit: bool) -> None:
        if self._state != _STATE_LISTEN:
            return

        self._state = _STATE_IDLE
        root = self.winfo_toplevel()

        if self._key_bid is not None:
            try:
                root.unbind("<KeyPress>", self._key_bid)
            except Exception:
                pass
            self._key_bid = None

        if self._mouse_bid is not None:
            try:
                root.unbind("<ButtonPress>", self._mouse_bid)
            except Exception:
                pass
            self._mouse_bid = None

        self._btn.configure(
            fg_color=COLOR_WIDGET_FG,
            text_color=COLOR_TEXT_PRIMARY,
            border_color=COLOR_WIDGET_BORDER,
        )
        self._sync_display()

    def _commit(self, canonical: str) -> None:
        """Set the var and fire on_capture. Kept separate so both handlers share the path."""
        self._var.set(canonical)
        self._stop_listening(commit=True)
        if self._on_capture is not None:
            self._on_capture()

    def _on_key(self, event) -> str:
        if event.keysym == "Escape":
            self._stop_listening(commit=False)
            return "break"

        # Use event.keycode (Windows VK code) so the result is layout-independent.
        # Russian/any other layout pressing physical 'A' still yields keycode=0x41 -> 'a'.
        canonical = _VK_TO_CANONICAL.get(event.keycode)
        if canonical is None:
            # Key not in VK_CODES -- ignore silently
            return "break"

        self._commit(canonical)
        return "break"

    def _on_mouse(self, event) -> str:
        # Scroll wheel fires ButtonPress with num=4/5 and event.delta != 0.
        # Side buttons also use num=4/5 on some drivers but with delta=0.
        # Reject scroll events to avoid accidentally binding wheel movement.
        if event.num in (4, 5) and getattr(event, "delta", 0) != 0:
            return "break"

        canonical = _MOUSE_NUM_TO_CANONICAL.get(event.num)
        if canonical is None:
            return "break"

        self._commit(canonical)
        return "break"