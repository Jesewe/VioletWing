import time
from typing import Optional

from classes.base_feature import BaseFeature
from classes.config_manager import ConfigManager
from classes.game_process import is_game_active
from classes.logger import Logger
from classes.memory_manager import MemoryManager
import classes.error_codes as EC

logger = Logger.get_logger(__name__)

MAIN_LOOP_SLEEP = 0.01

class CS2NoFlash(BaseFeature):
    def __init__(self, memory_manager: MemoryManager) -> None:
        super().__init__(memory_manager)
        self.config = ConfigManager.load_config()
        self.local_player_address: Optional[int] = None
        self.flash_duration_offset: Optional[int] = None
        self.load_configuration()

    def load_configuration(self) -> None:
        # No mutable state to reset here beyond what _init_player sets at start().
        pass

    def update_config(self, config: dict) -> None:
        self.config = config
        self.load_configuration()
        logger.debug("NoFlash configuration updated.")

    def start(self) -> None:
        if not self._init_player():
            Logger.error_code(EC.E3003)
            return

        self.is_running = True
        # Clear here so stop() can always set it reliably.
        self.stop_event.clear()

        sleep = time.sleep
        read_longlong = self.memory_manager.read_longlong

        local_player_addr = self.local_player_address
        flash_offset = self.flash_duration_offset

        last_player_position = 0
        failed_reads = 0
        max_failed_reads = 10
        reinit_backoff = 0.1
        max_reinit_backoff = 5.0
        logged_waiting = False

        while not self.stop_event.is_set():
            try:
                if not is_game_active():
                    sleep(MAIN_LOOP_SLEEP)
                    logged_waiting = False
                    continue

                suppression = ConfigManager.get_value(
                    "NoFlash", "FlashSuppressionStrength", default=0.0
                )

                player_position = read_longlong(local_player_addr)

                if player_position and player_position > 0:
                    if failed_reads > 0:
                        failed_reads = 0
                        reinit_backoff = 0.1
                        logged_waiting = False

                    last_player_position = player_position

                    try:
                        current = self.memory_manager.pm.read_float(player_position + flash_offset)
                        if abs(current - suppression) > 1e-6:
                            self.memory_manager.write_float(
                                player_position + flash_offset, suppression
                            )
                    except Exception as exc:
                        logger.debug("Error writing flash duration: %s", exc)
                        failed_reads += 1
                else:
                    failed_reads += 1
                    if failed_reads >= max_failed_reads:
                        if not logged_waiting:
                            logger.warning("Player not found - waiting for spawn…")
                            logged_waiting = True
                        if self._init_player():
                            local_player_addr = self.local_player_address
                            flash_offset = self.flash_duration_offset
                        failed_reads = 0
                        sleep(reinit_backoff)
                        reinit_backoff = min(reinit_backoff * 2, max_reinit_backoff)
                        continue

                sleep(MAIN_LOOP_SLEEP)

            except Exception:
                Logger.error_code(EC.E3004, exc_info=True)
                failed_reads += 1
                sleep(MAIN_LOOP_SLEEP)

    def stop(self) -> None:
        self.is_running = False
        self.stop_event.set()
        logger.debug("NoFlash stopped.")

    def _init_player(self) -> bool:
        if (
            self.memory_manager.dwLocalPlayerPawn is None
            or self.memory_manager.m_flFlashBangTime is None
        ):
            Logger.error_code(EC.E3003)
            return False
        try:
            self.local_player_address = (
                self.memory_manager.client_base + self.memory_manager.dwLocalPlayerPawn
            )
            self.flash_duration_offset = self.memory_manager.m_flFlashBangTime
            return True
        except Exception as exc:
            logger.error("Error setting local player address: %s", exc)
            return False