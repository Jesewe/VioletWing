"""
Shared icon loading utility for tab UI components.
Wraps Utility.resource_path + PIL so tabs don't repeat try/except.
Returns None on missing file — callers skip rendering, nothing crashes.
"""
from PIL import Image
import customtkinter as ctk
from classes.utility import Utility

def load_icon(filename, size=(18, 18)):
    """Load a PNG from src/img/ and return a CTkImage, or None if not found."""
    try:
        img = Image.open(Utility.resource_path(f'src/img/{filename}'))
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    except FileNotFoundError:
        return None

def icon_label(parent, filename, size=(18, 18), padx=(0, 10), side="left"):
    """
    Create a CTkLabel bearing the icon and pack it.
    No-ops silently if the file is missing.
    Returns the label or None.
    """
    img = load_icon(filename, size)
    if img is None:
        return None
    lbl = ctk.CTkLabel(parent, text="", image=img, width=size[0])
    lbl.image = img  # keep reference alive
    lbl.pack(side=side, padx=padx)
    return lbl
