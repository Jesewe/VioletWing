import threading
import time
from typing import Optional

from classes.config_manager import ConfigManager
from classes.memory_manager import MemoryManager
from classes.logger import Logger
from classes.utility import Utility

# Initialize the logger for consistent logging
logger = Logger.get_logger(__name__)
# Define the main loop sleep time for NoFlash
NOFLASH_LOOP_SLEEP = 0.01

class CS2NoFlash:
    """Manages the NoFlash functionality for Counter-Strike 2."""
    def __init__(self, memory_manager: MemoryManager) -> None:
        """
        Initialize the NoFlash with a shared MemoryManager instance.
        """
        # Load the configuration settings
        self.config = ConfigManager.load_config()
        self.memory_manager = memory_manager
        self.is_running = False
        self.stop_event = threading.Event()
        self.local_player_address: Optional[int] = None
        self.flash_duration_address: Optional[int] = None
        
        # Cache offset
        self.flash_duration_offset: Optional[int] = None
        
        self.load_configuration()

    def load_configuration(self):
        """Load and apply configuration settings."""
        self.flash_suppression_strength = self.config.get("NoFlash", {}).get("FlashSuppressionStrength", 0.0)

    def update_config(self, config):
        """Update the configuration settings."""
        self.config = config
        self.load_configuration()
        logger.debug("NoFlash configuration updated.")

    def initialize_local_player(self) -> bool:
        """Initialize the local player address."""
        if self.memory_manager.dwLocalPlayerPawn is None or self.memory_manager.m_flFlashDuration is None:
            logger.error("dwLocalPlayerPawn or m_flFlashDuration offset not initialized.")
            return False
        try:
            self.local_player_address = self.memory_manager.client_base + self.memory_manager.dwLocalPlayerPawn
            # Cache the offset
            self.flash_duration_offset = self.memory_manager.m_flFlashDuration
            return True
        except Exception as e:
            logger.error(f"Error setting local player address: {e}")
            return False

    def disable_flash(self, player_position: int) -> bool:
        """Set the flash duration based on suppression strength."""
        try:
            self.memory_manager.write_float(
                player_position + self.flash_duration_offset, 
                self.flash_suppression_strength
            )
            return True
        except Exception as e:
            logger.error(f"Error disabling flash: {e}")
            return False

    def start(self) -> None:
        """Start the NoFlash."""
        if not self.initialize_local_player():
            logger.error("Failed to initialize local player address.")
            return

        self.is_running = True

        # Cache frequently
        is_game_active = Utility.is_game_active
        sleep = time.sleep
        read_longlong = self.memory_manager.read_longlong
        
        # Cache local variables
        local_player_addr = self.local_player_address
        flash_offset = self.flash_duration_offset
        suppression_value = self.flash_suppression_strength
        
        # Performance tracking
        last_player_position = 0
        failed_reads = 0
        max_failed_reads = 10  # Reinitialize after too many failures
        
        while not self.stop_event.is_set():
            try:
                if not is_game_active():
                    sleep(NOFLASH_LOOP_SLEEP)
                    continue

                # Read player position
                player_position = read_longlong(local_player_addr)
                
                if player_position and player_position > 0:
                    # Reset failure counter on successful read
                    if failed_reads > 0:
                        failed_reads = 0
                    
                    # Only write if player position changed or first time
                    if player_position != last_player_position:
                        last_player_position = player_position
                    
                    # Write flash duration
                    try:
                        self.memory_manager.write_float(
                            player_position + flash_offset, 
                            suppression_value
                        )
                    except Exception as e:
                        logger.error(f"Error writing flash duration: {e}")
                        failed_reads += 1
                else:
                    # Invalid player position
                    failed_reads += 1
                    
                    # Reinitialize if too many failures
                    if failed_reads >= max_failed_reads:
                        logger.warning("Too many failed reads, reinitializing local player address...")
                        if self.initialize_local_player():
                            local_player_addr = self.local_player_address
                            flash_offset = self.flash_duration_offset
                            failed_reads = 0
                        else:
                            sleep(NOFLASH_LOOP_SLEEP * 10)  # Wait longer on failure
                
                sleep(NOFLASH_LOOP_SLEEP)
                
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
                failed_reads += 1
                sleep(NOFLASH_LOOP_SLEEP)

    def stop(self) -> None:
        """Stop the NoFlash and clean up resources."""
        self.is_running = False
        self.stop_event.set()
        logger.debug("NoFlash stopped.")