import threading
from tkinter import messagebox

from classes.game_process import is_game_running
from classes.logger import Logger
from classes.config_manager import ConfigManager

logger = Logger.get_logger(__name__)

class ClientManager:
    def __init__(self, main_window) -> None:
        self.main_window = main_window
        self.memory_manager = main_window.memory_manager
        self.features = main_window.features

    def _start_feature(self, feature_name: str, feature_obj, config: dict) -> bool:
        if getattr(feature_obj, "is_running", False):
            return False
        try:
            feature_obj.update_config(config)
            feature_obj.is_running = True
            thread = threading.Thread(target=feature_obj.start, daemon=True)
            thread.start()
            setattr(self.main_window, f"{feature_name.lower()}_thread", thread)
            logger.info("%s started.", feature_name)
            return True
        except Exception:
            feature_obj.is_running = False
            logger.exception("Failed to start feature: %s", feature_name)
            messagebox.showerror(
                f"{feature_name} Error",
                f"Failed to start {feature_name}. Check logs for details.",
            )
            return False

    def _stop_feature(self, feature_name: str, feature_obj) -> bool:
        if not (feature_obj and getattr(feature_obj, "is_running", False)):
            return False
        try:
            feature_obj.stop()
            thread = getattr(self.main_window, f"{feature_name.lower()}_thread", None)
            if thread and thread.is_alive():
                thread.join(timeout=2.0)
                if thread.is_alive():
                    logger.warning("%s thread did not terminate cleanly.", feature_name)
                else:
                    logger.info("%s thread terminated.", feature_name)
            setattr(self.main_window, f"{feature_name.lower()}_thread", None)
            feature_obj.is_running = False
            logger.debug("%s stopped.", feature_name)
            return True
        except Exception:
            logger.exception("Failed to stop feature: %s", feature_name)
            feature_obj.is_running = False
            return False

    def start_client(self) -> None:
        if not self.main_window.offsets:
            if self.main_window._offsets_fetching:
                self.main_window.update_client_status("Fetching offsets…", "#f59e0b")
                return
            self.main_window.update_client_status("Fetching offsets…", "#f59e0b")
            self.main_window.fetch_offsets_async(on_success=self.start_client)
            return

        if not is_game_running():
            messagebox.showerror(
                "Game Not Running",
                "Could not find cs2.exe. Make sure the game is running.",
            )
            return

        # Only initialize if we don't already have a valid memory handle.
        # Re-initializing while features are running replaces the shared pymem
        # handle underneath active threads.
        if not self.memory_manager.is_initialized:
            if not self.memory_manager.initialize():
                messagebox.showerror(
                    "Initialisation Error",
                    "Failed to initialise memory manager. Check logs for details.",
                )
                return

        config = ConfigManager.load_config()
        any_started = False

        for config_key, feature_data in self.features.items():
            if not config["General"].get(config_key, False):
                continue
            name = feature_data["name"]
            obj = feature_data["instance"]
            if getattr(obj, "is_running", False):
                logger.info("%s is already running.", name)
                any_started = True
            elif self._start_feature(name, obj, config):
                any_started = True

        if any_started:
            self.main_window.update_client_status("Active", "#22c55e")
        else:
            logger.warning("No features enabled in General settings.")
            messagebox.showwarning(
                "No Features Enabled",
                "Enable at least one feature in General Settings.",
            )

    def stop_client(self) -> None:
        stopped_any = False
        for feature_data in self.features.values():
            if self._stop_feature(feature_data["name"], feature_data["instance"]):
                stopped_any = True

        # Reset the memory handle so the next start_client gets a fresh attach.
        self.memory_manager.reset()

        if stopped_any:
            self.main_window.update_client_status("Inactive", "#ef4444")
        else:
            logger.debug("No features were running.")

    def apply_feature_state_changes(self, old_config: dict, new_config: dict) -> None:
        """Stop features whose enabled flag was turned off.

        Intentionally does NOT start features — that is exclusively the job of
        start_client(). Toggling a checkbox in General Settings is a config
        change, not a start command.
        """
        for key, feature_data in self.features.items():
            old_on = old_config["General"].get(key, False)
            new_on = new_config["General"].get(key, False)
            running = getattr(feature_data["instance"], "is_running", False)

            if old_on == new_on:
                continue

            # Only act on features that were turned OFF while running.
            if not new_on and running:
                self._stop_feature(feature_data["name"], feature_data["instance"])

    def update_running_feature_configs(self, new_config: dict) -> None:
        """Push a fresh config to every running feature and refresh the status indicator.

        Skips non-running features: they will pick up the latest config when
        next started, and calling update_config on them triggers load_configuration()
        which has the side effect of clearing stop_event.
        """
        any_running = False
        for feature_data in self.features.values():
            instance = feature_data["instance"]
            if getattr(instance, "is_running", False):
                instance.update_config(new_config)
                logger.debug("Config updated for %s.", feature_data["name"])
                any_running = True

        status, color = ("Active", "#22c55e") if any_running else ("Inactive", "#ef4444")
        self.main_window.update_client_status(status, color)