import threading
import time
import ctypes
from typing import Optional

from classes.config_manager import ConfigManager
from classes.memory_manager import MemoryManager
from classes.logger import Logger
from classes.utility import Utility

# Initialize the logger for consistent logging
logger = Logger.get_logger(__name__)
# Define the main loop sleep time for reduced CPU usage
MAIN_LOOP_SLEEP = 0.001  # Reduced for better timing precision
# Constants for bunnyhop
FORCE_JUMP_ACTIVE = 65537
FORCE_JUMP_INACTIVE = 256

class CS2Bunnyhop:
    """Manages the Bunnyhop functionality for Counter-Strike 2."""
    def __init__(self, memory_manager: MemoryManager) -> None:
        """
        Initialize the Bunnyhop with a shared MemoryManager instance.
        """
        # Load the configuration settings
        self.config = ConfigManager.load_config()
        self.memory_manager = memory_manager
        self.is_running = False
        self.stop_event = threading.Event()
        self.force_jump_address: Optional[int] = None
        self.load_configuration()

    def load_configuration(self):
        """Load and apply configuration settings."""
        self.bunnyhop_enabled = self.config.get("General", {}).get("Bunnyhop", False)
        self.jump_key = self.config.get("Bunnyhop", {}).get("JumpKey", "space").lower()
        self.jump_delay = self.config.get("Bunnyhop", {}).get("JumpDelay", 0.01)

    def update_config(self, config):
        """Update the configuration settings."""
        self.config = config
        self.load_configuration()
        logger.debug("Bunnyhop configuration updated.")

    def initialize_force_jump(self) -> bool:
        """Initialize the force jump address."""
        if self.memory_manager.dwForceJump is None:
            logger.error("dwForceJump offset not initialized.")
            return False
        try:
            self.force_jump_address = self.memory_manager.client_base + self.memory_manager.dwForceJump
            return True
        except Exception as e:
            logger.error(f"Error setting force jump address: {e}")
            return False

    def start(self) -> None:
        """Start the Bunnyhop."""
        if not self.initialize_force_jump():
            logger.error("Failed to initialize force jump address.")
            return

        self.is_running = True

        is_game_active = Utility.is_game_active
        sleep = time.sleep
        
        # Simple timing variables
        last_action_time = 0
        jump_active = False
        
        while not self.stop_event.is_set():
            try:
                if not is_game_active():
                    sleep(MAIN_LOOP_SLEEP)
                    continue

                current_time = time.time()
                key_pressed = ctypes.windll.user32.GetAsyncKeyState(Utility.get_vk_code(self.jump_key)) & 0x8000

                if key_pressed:
                    # Key is pressed - handle jump timing
                    if current_time - last_action_time >= self.jump_delay:
                        if not jump_active:
                            # Activate jump
                            try:
                                self.memory_manager.write_int(self.force_jump_address, FORCE_JUMP_ACTIVE)
                                jump_active = True
                                last_action_time = current_time
                            except Exception as e:
                                logger.error(f"Error activating jump: {e}")
                        else:
                            # Deactivate jump
                            try:
                                self.memory_manager.write_int(self.force_jump_address, FORCE_JUMP_INACTIVE)
                                jump_active = False
                                last_action_time = current_time
                            except Exception as e:
                                logger.error(f"Error deactivating jump: {e}")
                else:
                    # Key not pressed - ensure jump is inactive
                    if jump_active:
                        try:
                            self.memory_manager.write_int(self.force_jump_address, FORCE_JUMP_INACTIVE)
                            jump_active = False
                        except Exception as e:
                            logger.error(f"Error deactivating jump: {e}")

                sleep(MAIN_LOOP_SLEEP)
                
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
                sleep(MAIN_LOOP_SLEEP)

    def stop(self) -> None:
        """Stop the Bunnyhop and clean up resources."""
        self.is_running = False
        self.stop_event.set()
        
        # Ensure jump is deactivated when stopping
        if self.force_jump_address:
            try:
                self.memory_manager.write_int(self.force_jump_address, FORCE_JUMP_INACTIVE)
            except Exception as e:
                logger.error(f"Error deactivating jump during stop: {e}")
        
        logger.debug("Bunnyhop stopped.")