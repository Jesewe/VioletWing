from __future__ import annotations
from typing import Any, Optional
from contextlib import contextmanager

class UIConfigBridge:
    def __init__(self) -> None:
        # key → {"widget": w, "var": v, "value_label": lbl, "fmt": fmt_str}
        self._registry: dict[str, dict] = {}
        self._batching: bool = False
        self._batch_queue: dict[str, tuple] = {}

    def register(
        self,
        key: str,
        *,
        widget=None,
        var=None,
        value_label=None,
        fmt: Optional[str] = None,
        refresh_cb=None,
    ) -> None:
        """Register a widget under a config key.

        Args:
            key:         Config key, e.g. "TriggerKey", "enable_box".
            widget:      A CTkEntry, CTkSlider, CTkComboBox, or CTkCheckBox instance.
            var:         A tkinter variable (BooleanVar, StringVar, etc.).
            value_label: An optional CTkLabel that mirrors the widget's numeric value.
            fmt:         Optional format string for value_label updates (e.g. ".1f").
            refresh_cb:  Optional callable(value) invoked by set_value() after updating
                         the var/widget, so composite widgets (e.g. color picker with
                         swatch + entry + combo) can stay in sync.
        """
        self._registry[key] = {
            "widget": widget,
            "var": var,
            "value_label": value_label,
            "fmt": fmt,
            "refresh_cb": refresh_cb,
        }

    def get_value(self, key: str) -> Any:
        """Read the current UI value for a config key.

        Prefers var.get() over widget.get() when both are present (checkbox pattern).
        Returns None for unregistered keys so callers can skip gracefully.
        """
        entry = self._registry.get(key)
        if entry is None:
            return None
        if entry["var"] is not None:
            return entry["var"].get()
        if entry["widget"] is not None:
            return entry["widget"].get()
        return None

    def set_value(self, key: str, value: Any) -> None:
        """Push a config value into the UI widget for the given key.

        Silently ignores unregistered keys so partial tab population works.
        """
        entry = self._registry.get(key)
        if entry is None:
            return

        var = entry["var"]
        widget = entry["widget"]
        label = entry["value_label"]
        fmt = entry["fmt"]
        refresh_cb = entry.get("refresh_cb")

        if var is not None:
            var.set(value)

        if widget is not None and var is None:
            # Entry widgets need delete+insert; sliders and combos use .set()
            if hasattr(widget, "delete"):
                widget.delete(0, "end")
                widget.insert(0, str(value))
            else:
                widget.set(value)

        if label is not None and fmt is not None:
            label.configure(text=f"{value:{fmt}}")

        if refresh_cb is not None:
            if self._batching:
                self._batch_queue[key] = (refresh_cb, value)
            else:
                refresh_cb(value)

    def _flush_batch(self) -> None:
        """Execute all queued callbacks from a batch operation."""
        # Make a copy of values in case callbacks modify the queue
        callbacks = list(self._batch_queue.values())
        self._batch_queue.clear()
        for cb, val in callbacks:
            try:
                cb(val)
            except Exception:
                # Catch exceptions so one bad callback doesn't break others in the idle queue
                import logging
                logging.getLogger(__name__).exception("Error in deferred UIConfigBridge callback")

    @contextmanager
    def batch_updates(self, widget):
        """Context manager to defer refresh_cb calls until after the block completes.
        
        Callbacks are deduped by key and scheduled via widget.after_idle() so they 
        run when Tkinter has finished processing the current event queue, preventing
        UI stutters during bulk loads.
        """
        self._batching = True
        try:
            yield
        finally:
            self._batching = False
            if self._batch_queue:
                widget.after_idle(self._flush_batch)

    def registered(self, key: str) -> bool:
        """Return True if a key has been registered."""
        return key in self._registry

    def set_error(self, key: str, error_message: str) -> None:
        """Set an inline validation error on a widget."""
        entry = self._registry.get(key)
        if entry is None:
            return
        widget = entry.get("widget")
        if widget is not None and hasattr(widget, "configure"):
            try:
                # Save original border color if not already saved
                if not hasattr(widget, "_orig_border_color"):
                    widget._orig_border_color = widget.cget("border_color")
                
                from src.gui.theme import COLOR_WIDGET_ERROR_BORDER, COLOR_TEXT_ERROR, FONT_ITEM_DESCRIPTION
                import customtkinter as ctk
                
                widget.configure(border_color=COLOR_WIDGET_ERROR_BORDER)
                
                # Display error label below the widget
                if not hasattr(widget, "_error_label"):
                    lbl = ctk.CTkLabel(widget.master, text=error_message, text_color=COLOR_TEXT_ERROR, font=FONT_ITEM_DESCRIPTION)
                    lbl.pack(pady=(5, 0))
                    widget._error_label = lbl
                else:
                    widget._error_label.configure(text=error_message)
                    widget._error_label.pack(pady=(5, 0))
            except Exception:
                pass

    def clear_errors(self) -> None:
        """Clear all validation errors from the UI."""
        for entry in self._registry.values():
            widget = entry.get("widget")
            if widget is not None:
                try:
                    if hasattr(widget, "_orig_border_color"):
                        widget.configure(border_color=widget._orig_border_color)
                    if hasattr(widget, "_error_label"):
                        widget._error_label.pack_forget()
                except Exception:
                    pass
