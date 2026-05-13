import ctypes
import time

from classes.base_feature import BaseFeature
from classes.config_manager import ConfigManager
from classes.game_process import is_game_active
from classes.logger import Logger
import classes.error_codes as EC
from classes.memory_manager import MemoryManager
from constants.vk_codes import get_vk_code

logger = Logger.get_logger(__name__)

MAIN_LOOP_SLEEP = 0.001
FORCE_JUMP_ACTIVE = 65537
FORCE_JUMP_INACTIVE = 256

class CS2Bunnyhop(BaseFeature):
    def __init__(self, memory_manager: MemoryManager) -> None:
        super().__init__(memory_manager)
        self.config = ConfigManager.load_config()
        self.force_jump_address: int | None = None
        self.load_configuration()

    def load_configuration(self) -> None:
        self.jump_key = self.config.get("Bunnyhop", {}).get("JumpKey", "space").lower()
        self.jump_delay = self.config.get("Bunnyhop", {}).get("JumpDelay", 0.01)

    def update_config(self, config: dict) -> None:
        self.config = config
        self.load_configuration()
        logger.debug("Bunnyhop configuration updated.")

    def start(self) -> None:
        if not self._init_address():
            Logger.error_code(EC.E3001)
            return

        self.is_running = True
        # Clear here so stop() can always set it reliably.
        self.stop_event.clear()

        sleep = time.sleep

        last_action = 0.0
        jump_active = False

        while not self.stop_event.is_set():
            try:
                if not is_game_active():
                    sleep(MAIN_LOOP_SLEEP)
                    continue

                now = time.time()
                jump_delay = ConfigManager.get_value("Bunnyhop", "JumpDelay", default=0.01)
                vk = get_vk_code(ConfigManager.get_value("Bunnyhop", "JumpKey", default="space"))
                key_down = bool(ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000)

                if key_down:
                    if now - last_action >= jump_delay:
                        if not jump_active:
                            self._write_jump(FORCE_JUMP_ACTIVE)
                            jump_active = True
                        else:
                            self._write_jump(FORCE_JUMP_INACTIVE)
                            jump_active = False
                        last_action = now
                elif jump_active:
                    self._write_jump(FORCE_JUMP_INACTIVE)
                    jump_active = False

                sleep(MAIN_LOOP_SLEEP)

            except Exception:
                Logger.error_code(EC.E3002, exc_info=True)
                sleep(MAIN_LOOP_SLEEP)

    def stop(self) -> None:
        self.is_running = False
        self.stop_event.set()
        if self.force_jump_address:
            try:
                self.memory_manager.write_int(self.force_jump_address, FORCE_JUMP_INACTIVE)
            except Exception as exc:
                logger.error("Error deactivating jump during stop: %s", exc)
        logger.debug("Bunnyhop stopped.")

    def _init_address(self) -> bool:
        if self.memory_manager.dwForceJump is None:
            Logger.error_code(EC.E3001)
            return False
        try:
            self.force_jump_address = self.memory_manager.client_base + self.memory_manager.dwForceJump
            return True
        except Exception as exc:
            logger.error("Error setting force-jump address: %s", exc)
            return False

    def _write_jump(self, value: int) -> None:
        try:
            self.memory_manager.write_int(self.force_jump_address, value)
        except Exception as exc:
            logger.error("Error writing jump value %d: %s", value, exc)
