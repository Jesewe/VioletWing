from PIL import Image
import customtkinter as ctk
from classes.utility import Utility
from classes.logger import Logger

logger = Logger.get_logger(__name__)

ASSETS_DIR = "src/assets"

def load_icon(filename, size=(18, 18)):
    """Load a PNG from ASSETS_DIR and return a CTkImage, or None if not found."""
    try:
        img = Image.open(Utility.resource_path(f"{ASSETS_DIR}/{filename}"))
        return ctk.CTkImage(light_image=img, dark_image=img, size=size)
    except FileNotFoundError:
        logger.debug("Icon file not found: %s", filename)
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