import threading
from tkinter import messagebox

from classes.utility import Utility
from classes.logger import Logger
from classes.config_manager import ConfigManager

logger = Logger.get_logger(__name__)

class ClientManager:
    def __init__(self, main_window):
        self.main_window = main_window
        self.memory_manager = main_window.memory_manager
        self.features = main_window.features

    def _start_feature(self, feature_name, feature_obj, config):
        """Helper method to start a single feature."""
        if not getattr(feature_obj, 'is_running', False):
            try:
                feature_obj.config = config
                feature_obj.is_running = True
                thread = threading.Thread(target=feature_obj.start, daemon=True)
                thread.start()
                setattr(self.main_window, f'{feature_name.lower()}_thread', thread)
                logger.info(f"{feature_name} started.")
                return True
            except Exception:
                feature_obj.is_running = False
                logger.exception(f"Failed to start feature: {feature_name}")
                messagebox.showerror(f"{feature_name} Error", f"Failed to start {feature_name}. Check logs for details.")
        return False

    def _stop_feature(self, feature_name, feature_obj):
        """Helper method to stop a single feature."""
        if feature_obj and getattr(feature_obj, 'is_running', False):
            try:
                feature_obj.stop()
                thread = getattr(self.main_window, f'{feature_name.lower()}_thread', None)
                if thread and thread.is_alive():
                    thread.join(timeout=2.0)
                    if thread.is_alive():
                        logger.warning(f"{feature_name} thread did not terminate cleanly.")
                    else:
                        logger.info(f"{feature_name} thread terminated successfully.")
                setattr(self.main_window, f'{feature_name.lower()}_thread', None)
                feature_obj.is_running = False
                logger.debug(f"{feature_name} stopped.")
                return True
            except Exception:
                logger.exception(f"Failed to stop feature: {feature_name}")
                feature_obj.is_running = False
        return False

    def start_client(self):
        """Start selected features based on General settings, ensuring no duplicates."""
        if not Utility.is_game_running():
            messagebox.showerror("Game Not Running", "Could not find cs2.exe process. Make sure the game is running.")
            return

        if not self.memory_manager.initialize():
            messagebox.showerror("Initialization Error", "Failed to initialize memory manager. Please check the logs for details.")
            return

        config = ConfigManager.load_config()
        any_feature_started = False

        for config_key, feature_data in self.features.items():
            if config["General"][config_key]:
                feature_name = feature_data["name"]
                feature_obj = feature_data["instance"]
                if not getattr(feature_obj, 'is_running', False):
                    if self._start_feature(feature_name, feature_obj, config):
                        any_feature_started = True
                else:
                    logger.info(f"{feature_name} is already running.")
                    any_feature_started = True

        if any_feature_started:
            self.main_window.update_client_status("Active", "#22c55e")
        else:
            logger.warning("No features enabled in General settings.")
            messagebox.showwarning("No Features Enabled", "Please enable at least one feature in General Settings.")

    def stop_client(self):
        """Stop all running features and ensure threads are terminated."""
        features_stopped = False

        for feature_data in self.features.values():
            if self._stop_feature(feature_data["name"], feature_data["instance"]):
                features_stopped = True

        if features_stopped:
            self.main_window.update_client_status("Inactive", "#ef4444")
        else:
            logger.debug("No features were running to stop.")

    def apply_feature_state_changes(self, old_config, new_config):
        """Start or stop features based on configuration changes."""
        game_running = Utility.is_game_running()

        for key, feature_data in self.features.items():
            old_enabled = old_config["General"].get(key, False)
            new_enabled = new_config["General"].get(key, False)
            is_running = getattr(feature_data["instance"], 'is_running', False)

            if old_enabled == new_enabled:
                continue

            if new_enabled and not is_running:
                if game_running:
                    if self.memory_manager.initialize():
                        self._start_feature(feature_data["name"], feature_data["instance"], new_config)
                    else:
                        logger.error(f"Failed to initialize memory manager for {feature_data['name']}")
                else:
                    logger.warning(f"Cannot start {feature_data['name']}: Game is not running")
            elif not new_enabled and is_running:
                self._stop_feature(feature_data["name"], feature_data["instance"])

    def update_running_feature_configs(self, new_config):
        """Update the configuration for all currently running features and update UI status."""
        any_feature_running = False
        for feature_data in self.features.values():
            instance = feature_data["instance"]
            if getattr(instance, 'is_running', False):
                instance.update_config(new_config)
                logger.debug(f"Configuration updated for {feature_data['name']}.")
                any_feature_running = True
        
        status = "Active" if any_feature_running else "Inactive"
        color = "#22c55e" if any_feature_running else "#ef4444"
        self.main_window.update_client_status(status, color)
