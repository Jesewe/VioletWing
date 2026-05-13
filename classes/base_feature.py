import threading
from abc import ABC, abstractmethod

from classes.logger import Logger

logger = Logger.get_logger(__name__)

class BaseFeature(ABC):
    """
    Abstract base class for all game features (TriggerBot, Overlay, Bunnyhop, NoFlash).

    Enforces a consistent lifecycle:
        __init__ → load_configuration (via update_config) → start (daemon thread) → stop
    """
    def __init__(self, memory_manager) -> None:
        self.memory_manager = memory_manager
        self.is_running: bool = False
        self.stop_event: threading.Event = threading.Event()

    @abstractmethod
    def load_configuration(self) -> None:
        """
        Read from self.config and populate instance attributes.
        Called by update_config - never call externally.
        """

    @abstractmethod
    def update_config(self, config: dict) -> None:
        """
        Accept a fresh config dict, store it as self.config,
        and delegate to load_configuration().
        """

    @abstractmethod
    def start(self) -> None:
        """
        Main blocking loop - intended to run inside a daemon thread.
        Must respect self.stop_event and exit when it is set.
        """

    @abstractmethod
    def stop(self) -> None:
        """
        Signal the main loop to exit and release any external resources
        (listeners, overlays, memory handles, etc.).
        """