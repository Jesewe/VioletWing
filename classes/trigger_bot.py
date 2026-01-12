import threading, time, random, ctypes, winsound
from typing import Optional, Dict, Any

from pynput.mouse import Controller, Button, Listener as MouseListener
from pynput.keyboard import Listener as KeyboardListener

from classes.config_manager import ConfigManager
from classes.memory_manager import MemoryManager
from classes.logger import Logger
from classes.utility import Utility

# Initialize mouse controller and logger
mouse = Controller()
# Initialize the logger for consistent logging
logger = Logger.get_logger(__name__)
# Define the main loop sleep time for reduced CPU usage
MAIN_LOOP_SLEEP = 0.001  # Reduced for better responsiveness

class CS2TriggerBot:
    def __init__(self, memory_manager: MemoryManager) -> None:
        """
        Initialize the TriggerBot with a shared MemoryManager instance.
        """
        # Load the configuration settings
        self.config = ConfigManager.load_config()
        self.memory_manager = memory_manager
        self.is_running = False
        self.stop_event = threading.Event()
        self.trigger_active = False
        self.toggle_state = False
        
        # Cached weapon settings for current weapon
        self.current_weapon_settings: Optional[Dict[str, Any]] = None
        self.last_weapon_type: Optional[str] = None
        
        # Performance optimizations
        self._vk_code_cache = {}
        
        # Initialize configuration settings
        self.load_configuration()
        self.update_config(self.config)

        # Setup listeners
        self.keyboard_listener = KeyboardListener(on_press=self.on_key_press, on_release=self.on_key_release)
        self.mouse_listener = MouseListener(on_click=self.on_mouse_click)
        self.keyboard_listener.start()
        self.mouse_listener.start()

    def load_configuration(self) -> None:
        """Load and apply configuration settings."""
        settings = self.config['Trigger']
        self.trigger_key = settings['TriggerKey']
        self.toggle_mode = settings['ToggleMode']
        self.attack_on_teammates = settings['AttackOnTeammates']
        self.weapon_settings_cache = settings["WeaponSettings"]
        
        # Reset cached weapon settings to force fresh lookup
        self.current_weapon_settings = None
        self.last_weapon_type = None
        
        self.mouse_button_map = {
            "mouse3": Button.middle,
            "mouse4": Button.x1,
            "mouse5": Button.x2,
        }

        # Check if the trigger key is a mouse button
        self.is_mouse_trigger = self.trigger_key in self.mouse_button_map
        
        # Cache VK code for keyboard trigger
        if not self.is_mouse_trigger:
            self._trigger_vk_code = Utility.get_vk_code(self.trigger_key)

    def update_config(self, config):
        """Update the configuration settings."""
        self.config = config
        self.load_configuration()
        logger.debug("TriggerBot configuration updated.")

    def play_toggle_sound(self, state: bool) -> None:
        """Play a sound when the toggle key is pressed."""
        try:
            # Use threading to avoid blocking
            def play_sound():
                if state:
                    winsound.Beep(1000, 200)
                else:
                    winsound.Beep(500, 200)
            
            threading.Thread(target=play_sound, daemon=True).start()
        except Exception as e:
            logger.error(f"Error playing toggle sound: {e}")

    def on_key_press(self, key) -> None:
        """Handle key press events."""
        if not self.is_mouse_trigger:
            try:
                # Check if the key pressed is the trigger key
                if hasattr(key, 'char') and key.char == self.trigger_key:
                    if self.toggle_mode:
                        self.toggle_state = not self.toggle_state
                        self.play_toggle_sound(self.toggle_state)
                    else:
                        self.trigger_active = True
            except AttributeError:
                pass

    def on_key_release(self, key) -> None:
        """Handle key release events."""
        if not self.is_mouse_trigger and not self.toggle_mode:
            try:
                if hasattr(key, 'char') and key.char == self.trigger_key:
                    self.trigger_active = False
            except AttributeError:
                pass

    def on_mouse_click(self, x, y, button, pressed) -> None:
        """Handle mouse click events."""
        if not self.is_mouse_trigger:
            return

        expected_btn = self.mouse_button_map.get(self.trigger_key)
        if button == expected_btn:
            if self.toggle_mode and pressed:
                self.toggle_state = not self.toggle_state
                self.play_toggle_sound(self.toggle_state)
            else:
                self.trigger_active = pressed

    def should_trigger(self, entity_team: int, player_team: int, entity_health: int) -> bool:
        """Determine if the bot should fire."""
        return (self.attack_on_teammates or entity_team != player_team) and entity_health > 0

    def get_weapon_settings(self, weapon_type: str) -> Dict[str, Any]:
        """Get weapon settings with caching for performance. Always uses the actual in-game weapon type."""
        # Always update cache when weapon type changes to ensure correct settings
        if weapon_type != self.last_weapon_type:
            self.current_weapon_settings = self.weapon_settings_cache.get(
                weapon_type, self.weapon_settings_cache.get("Rifles", {})
            )
            self.last_weapon_type = weapon_type
            logger.debug(f"Weapon type changed to: {weapon_type}")
        
        return self.current_weapon_settings

    def is_trigger_key_pressed(self) -> bool:
        """Check if trigger key is pressed using optimized method."""
        if self.is_mouse_trigger:
            return self.trigger_active
        else:
            # Use direct Windows API call for better performance
            return bool(ctypes.windll.user32.GetAsyncKeyState(self._trigger_vk_code) & 0x8000)

    def start(self) -> None:
        """Start the TriggerBot."""
        self.is_running = True

        # Define local variables for utility functions
        is_game_active = Utility.is_game_active
        sleep = time.sleep
        get_fire_logic_data = self.memory_manager.get_fire_logic_data
        mouse_click = mouse.click
        
        # Pre-calculate random values to reduce computation in loop
        last_shot_time = 0
        min_shot_interval = 0.01  # Minimum time between shots to prevent spam
        
        while not self.stop_event.is_set():
            try:
                # Quick exit conditions
                if not is_game_active():
                    sleep(MAIN_LOOP_SLEEP)
                    continue

                # Check trigger activation
                trigger_ready = False
                if self.toggle_mode:
                    trigger_ready = self.toggle_state
                else:
                    trigger_ready = self.trigger_active or self.is_trigger_key_pressed()

                if not trigger_ready:
                    sleep(MAIN_LOOP_SLEEP)
                    continue

                # Get game data
                data = get_fire_logic_data()
                if not data:
                    sleep(MAIN_LOOP_SLEEP)
                    continue

                # Check if should trigger
                if not self.should_trigger(data["entity_team"], data["player_team"], data["entity_health"]):
                    sleep(MAIN_LOOP_SLEEP)
                    continue

                # Rate limiting to prevent excessive shooting
                current_time = time.time()
                if current_time - last_shot_time < min_shot_interval:
                    sleep(MAIN_LOOP_SLEEP)
                    continue

                # Get weapon settings - CRITICAL: Use the actual weapon type from game data
                weapon_type = data.get("weapon_type", "Rifles")
                weapon_settings = self.get_weapon_settings(weapon_type)
                
                # Ensure weapon_settings is valid
                if not weapon_settings:
                    logger.warning(f"No settings found for weapon type: {weapon_type}, using Rifles defaults")
                    weapon_settings = self.weapon_settings_cache.get("Rifles", {})
                
                shot_delay_min = weapon_settings.get('ShotDelayMin', 0.0)
                shot_delay_max = weapon_settings.get('ShotDelayMax', 0.0)
                post_shot_delay = weapon_settings.get('PostShotDelay', 0.0)

                # Pre-shot delay
                if shot_delay_max > shot_delay_min:
                    delay = random.uniform(shot_delay_min, shot_delay_max)
                    sleep(delay)

                # Fire the shot
                mouse_click(Button.left)
                last_shot_time = time.time()
                
                # Post-shot delay
                if post_shot_delay > 0:
                    sleep(post_shot_delay)

            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
                sleep(MAIN_LOOP_SLEEP)

    def stop(self) -> None:
        """Stops the TriggerBot and cleans up resources."""
        self.is_running = False
        self.stop_event.set()
        
        # Give threads time to cleanup
        sleep_time = 0.1
        time.sleep(sleep_time)
        
        try:
            if hasattr(self, 'keyboard_listener') and self.keyboard_listener.running:
                self.keyboard_listener.stop()
            if hasattr(self, 'mouse_listener') and self.mouse_listener.running:
                self.mouse_listener.stop()
            logger.debug("TriggerBot stopped.")
        except Exception as e:
            logger.error(f"Error stopping TriggerBot: {e}")