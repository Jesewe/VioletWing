import os
import threading
from watchdog.events import FileSystemEventHandler

from classes.config_manager import ConfigManager
from classes.logger import Logger

# Initialize the logger for consistent logging
logger = Logger.get_logger(__name__)

class ConfigFileChangeHandler(FileSystemEventHandler):
    """
    A file system event handler for monitoring changes to the configuration file.
    Automatically updates the configuration for all features when the config file is modified.
    """
    def __init__(self, main_window, debounce_interval=1.0):
        """
        Initializes the file change handler with a reference to the main window instance.
        Caches the configuration file path for efficiency.

        Args:
            main_window: Instance of MainWindow managing all features.
            debounce_interval: Time in seconds to debounce file change events.
        """
        self.main_window = main_window
        self.debounce_interval = debounce_interval
        self.debounce_timer = None
        self.config_path = ConfigManager.CONFIG_FILE

    def on_modified(self, event):
        """Called when a file or directory is modified."""
        if event.src_path and os.path.exists(self.config_path) and os.path.samefile(event.src_path, self.config_path):
            if self.debounce_timer is not None:
                self.debounce_timer.cancel()
            self.debounce_timer = threading.Timer(self.debounce_interval, self.reload_config)
            self.debounce_timer.start()

    def reload_config(self):
        """Reloads the configuration file and updates all feature configurations."""
        try:
            # Reload the updated configuration file
            new_config = ConfigManager.load_config()
            
            # Update configurations for all features
            self.main_window.triggerbot.config = new_config
            self.main_window.overlay.config = new_config
            self.main_window.bunnyhop.config = new_config
            self.main_window.noflash.config = new_config
            
            # Update UI in the main thread to reflect new configuration
            self.main_window.root.after(0, self.main_window.update_ui_from_config)
        except Exception as e:
            logger.exception("Failed to reload configuration from %s: %s", self.config_path, e)