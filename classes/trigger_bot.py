import ctypes
import queue
import random
import threading
import time
import winsound
from typing import Any, Dict, Optional

from pynput.mouse import Button, Controller, Listener as MouseListener

from classes.base_feature import BaseFeature
from classes.config_manager import ConfigManager
from classes.game_process import is_game_active
from classes.logger import Logger
from classes.memory_manager import MemoryManager
from constants.vk_codes import get_vk_code

mouse = Controller()
logger = Logger.get_logger(__name__)

MAIN_LOOP_SLEEP = 0.001

class CS2TriggerBot(BaseFeature):
    def __init__(self, memory_manager: MemoryManager) -> None:
        super().__init__(memory_manager)
        self.config = ConfigManager.load_config()
        self.toggle_state = False
        self.trigger_active = False
        self.current_weapon_settings: Optional[Dict[str, Any]] = None
        self.last_weapon_type: Optional[str] = None

        self._audio_queue: queue.Queue = queue.Queue(maxsize=1)
        self._audio_worker = threading.Thread(target=self._run_audio_worker, daemon=True)
        self._audio_worker.start()

        self._mouse_listener: Optional[MouseListener] = None

        self.load_configuration()

    def load_configuration(self) -> None:
        settings = self.config["Trigger"]
        self.trigger_key = settings["TriggerKey"]
        self.toggle_mode = settings["ToggleMode"]
        self.attack_on_teammates = settings["AttackOnTeammates"]
        self.weapon_settings_cache = settings["WeaponSettings"]

        # Reset weapon cache so the next shot recalculates for the new config.
        self.current_weapon_settings = None
        self.last_weapon_type = None

        self.mouse_button_map = {
            "mouse3": Button.middle,
            "mouse4": Button.x1,
            "mouse5": Button.x2,
        }
        self.is_mouse_trigger = self.trigger_key in self.mouse_button_map

        if not self.is_mouse_trigger:
            self._trigger_vk_code = get_vk_code(self.trigger_key)

    def update_config(self, config: dict) -> None:
        self.config = config
        self.load_configuration()
        logger.debug("TriggerBot configuration updated.")

    def start(self) -> None:
        self.is_running = True
        # Clear here — the only correct place — so stop() can always set it.
        self.stop_event.clear()

        if self._mouse_listener is None or not self._mouse_listener.running:
            self._mouse_listener = MouseListener(on_click=self._on_mouse_click)
            self._mouse_listener.start()

        sleep = time.sleep
        get_fire_logic_data = self.memory_manager.get_fire_logic_data

        last_shot_time = 0.0
        min_shot_interval = 0.01
        _prev_key_pressed = False

        while not self.stop_event.is_set():
            try:
                if not is_game_active():
                    sleep(MAIN_LOOP_SLEEP)
                    continue

                if self.is_mouse_trigger:
                    trigger_ready = self.toggle_state if self.toggle_mode else self.trigger_active
                else:
                    key_down = self._is_key_pressed()
                    if self.toggle_mode:
                        if key_down and not _prev_key_pressed:
                            self.toggle_state = not self.toggle_state
                            self._enqueue_toggle_sound(self.toggle_state)
                        _prev_key_pressed = key_down
                        trigger_ready = self.toggle_state
                    else:
                        trigger_ready = key_down

                if not trigger_ready:
                    sleep(MAIN_LOOP_SLEEP)
                    continue

                data = get_fire_logic_data()
                if not data:
                    sleep(MAIN_LOOP_SLEEP)
                    continue

                if not self._should_fire(data["entity_team"], data["player_team"], data["entity_health"]):
                    sleep(MAIN_LOOP_SLEEP)
                    continue

                now = time.time()
                if now - last_shot_time < min_shot_interval:
                    sleep(MAIN_LOOP_SLEEP)
                    continue

                weapon_type = data.get("weapon_type", "Rifles")
                ws = self._weapon_settings(weapon_type)
                delay_min = ws.get("ShotDelayMin", 0.0)
                delay_max = ws.get("ShotDelayMax", 0.0)
                post_delay = ws.get("PostShotDelay", 0.0)

                if delay_max > delay_min:
                    sleep(random.uniform(delay_min, delay_max))

                mouse.click(Button.left)
                last_shot_time = time.time()

                if post_delay > 0:
                    sleep(post_delay)

            except Exception:
                logger.error("Unexpected error in TriggerBot loop.", exc_info=True)
                sleep(MAIN_LOOP_SLEEP)

    def stop(self) -> None:
        self.is_running = False
        self.stop_event.set()
        time.sleep(0.1)

        if self._mouse_listener is not None:
            try:
                if self._mouse_listener.running:
                    self._mouse_listener.stop()
            except Exception as exc:
                logger.error("Error stopping mouse listener: %s", exc)
            finally:
                self._mouse_listener = None

        logger.debug("TriggerBot stopped.")

    def _run_audio_worker(self) -> None:
        while True:
            freq, duration = self._audio_queue.get()
            try:
                winsound.Beep(freq, duration)
            except Exception as exc:
                logger.debug("Audio worker beep failed: %s", exc)
            finally:
                self._audio_queue.task_done()

    def _enqueue_toggle_sound(self, state: bool) -> None:
        tone = (1000, 200) if state else (500, 200)
        try:
            self._audio_queue.put_nowait(tone)
        except queue.Full:
            pass

    def _on_mouse_click(self, x, y, button, pressed) -> None:
        if not self.is_mouse_trigger:
            return
        expected = self.mouse_button_map.get(self.trigger_key)
        if button == expected:
            if self.toggle_mode and pressed:
                self.toggle_state = not self.toggle_state
                self._enqueue_toggle_sound(self.toggle_state)
            else:
                self.trigger_active = pressed

    def _is_key_pressed(self) -> bool:
        if self.is_mouse_trigger:
            return self.trigger_active
        return bool(ctypes.windll.user32.GetAsyncKeyState(self._trigger_vk_code) & 0x8000)

    def _should_fire(self, entity_team: int, player_team: int, entity_health: int) -> bool:
        return (self.attack_on_teammates or entity_team != player_team) and entity_health > 0

    def _weapon_settings(self, weapon_type: str) -> Dict[str, Any]:
        if weapon_type != self.last_weapon_type:
            self.current_weapon_settings = dict(
                self.weapon_settings_cache.get(
                    weapon_type,
                    self.weapon_settings_cache.get("Rifles", {}),
                )
            )
            self.last_weapon_type = weapon_type
        return self.current_weapon_settings

    def play_toggle_sound(self, state: bool) -> None:
        self._enqueue_toggle_sound(state)

    def on_mouse_click(self, x, y, button, pressed) -> None:
        self._on_mouse_click(x, y, button, pressed)

    def is_trigger_key_pressed(self) -> bool:
        return self._is_key_pressed()

    def should_trigger(self, entity_team, player_team, entity_health) -> bool:
        return self._should_fire(entity_team, player_team, entity_health)

    def get_weapon_settings(self, weapon_type: str) -> Dict[str, Any]:
        return self._weapon_settings(weapon_type)
