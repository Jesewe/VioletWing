from __future__ import annotations
from typing import Any, Optional

class UIConfigBridge:
    def __init__(self) -> None:
        # key → {"widget": w, "var": v, "value_label": lbl, "fmt": fmt_str}
        self._registry: dict[str, dict] = {}

    def register(
        self,
        key: str,
        *,
        widget=None,
        var=None,
        value_label=None,
        fmt: Optional[str] = None,
    ) -> None:
        """Register a widget under a config key.

        Args:
            key:         Config key, e.g. "TriggerKey", "enable_box".
            widget:      A CTkEntry, CTkSlider, CTkComboBox, or CTkCheckBox instance.
            var:         A tkinter variable (BooleanVar, StringVar, etc.).
            value_label: An optional CTkLabel that mirrors the widget's numeric value.
            fmt:         Optional format string for value_label updates (e.g. ".1f").
        """
        self._registry[key] = {
            "widget": widget,
            "var": var,
            "value_label": value_label,
            "fmt": fmt,
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

    def registered(self, key: str) -> bool:
        """Return True if a key has been registered."""
        return key in self._registry
