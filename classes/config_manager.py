import os
import orjson
import copy
from pathlib import Path
from typing import Dict, Any, Optional
import threading

from classes.logger import Logger

# Initialize the logger for consistent logging
logger = Logger.get_logger(__name__)

class ConfigManager:
    """
    Thread-safe configuration manager for the application.
    
    Provides methods to load and save configuration settings with:
    - Automatic caching for performance
    - Thread-safe operations
    - Automatic migration of missing keys
    - Validation and error recovery
    """
    
    # Application version
    VERSION = "v1.2.9.1"
    
    # Directory paths
    UPDATE_DIRECTORY = os.path.expanduser(r'~\AppData\Local\Requests\ItsJesewe\Update')
    OFFSETS_DIRECTORY = os.path.expanduser(r'~\AppData\Local\Requests\ItsJesewe\Offsets')
    CONFIG_DIRECTORY = os.path.expanduser(r'~\AppData\Local\Requests\ItsJesewe')
    CONFIG_FILE = Path(CONFIG_DIRECTORY) / 'config.json'
    
    # Default configuration settings
    DEFAULT_CONFIG = {
        "user_id": None,
        "General": {
            "Trigger": False,
            "Overlay": False,
            "Bunnyhop": False,
            "Noflash": False,
            "OffsetSource": "a2x",
            "OffsetsFile": str(Path(OFFSETS_DIRECTORY) / "offsets.json"),
            "ClientDLLFile": str(Path(OFFSETS_DIRECTORY) / "client_dll.json"),
            "ButtonsFile": str(Path(OFFSETS_DIRECTORY) / "buttons.json")
        },
        "Trigger": {
            "TriggerKey": "x",
            "ToggleMode": False,
            "AttackOnTeammates": False,
            "active_weapon_type": "Rifles",
            "WeaponSettings": {
                "Pistols": {"ShotDelayMin": 0.02, "ShotDelayMax": 0.04, "PostShotDelay": 0.02},
                "Rifles": {"ShotDelayMin": 0.01, "ShotDelayMax": 0.03, "PostShotDelay": 0.02},
                "Snipers": {"ShotDelayMin": 0.05, "ShotDelayMax": 0.1, "PostShotDelay": 0.5},
                "SMGs": {"ShotDelayMin": 0.01, "ShotDelayMax": 0.02, "PostShotDelay": 0.05},
                "Heavy": {"ShotDelayMin": 0.03, "ShotDelayMax": 0.05, "PostShotDelay": 0.2}
            }
        },
        "Overlay": {
            "target_fps": 60,
            "enable_box": True,
            "enable_skeleton": False,
            "draw_snaplines": True,
            "snaplines_color_hex": "#FFFFFF",
            "box_line_thickness": 1.0,
            "box_color_hex": "#FFA500",
            "text_color_hex": "#FFFFFF",
            "draw_health_numbers": True,
            "use_transliteration": False,
            "draw_nicknames": True,
            "draw_teammates": False,
            "teammate_color_hex": "#00FFFF"
        },
        "Bunnyhop": {
            "JumpKey": "space",
            "JumpDelay": 0.01
        },
        "NoFlash": {
            "FlashSuppressionStrength": 0.0
        },
        "GitHub": {
            "AccessToken": None
        }
    }
    
    # Cache and thread safety
    _config_cache: Optional[Dict[str, Any]] = None
    _lock: threading.Lock = threading.Lock()
    
    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """
        Load the configuration from the configuration file (thread-safe).
        
        - Creates the configuration directory and file with default settings if they don't exist
        - Caches the configuration to avoid redundant file reads
        - Automatically migrates missing keys from DEFAULT_CONFIG
        - Returns a deep copy to prevent accidental cache mutation
        
        Returns:
            Dictionary containing the configuration
        """
        # Fast path: return cached config if available (no lock needed for read)
        if cls._config_cache is not None:
            return copy.deepcopy(cls._config_cache)
        
        # Slow path: load from file (needs lock)
        with cls._lock:
            # Double-check pattern: another thread might have loaded it
            if cls._config_cache is not None:
                return copy.deepcopy(cls._config_cache)
            
            # Ensure directories exist
            cls._ensure_directories()
            
            # Load or create config
            if not cls.CONFIG_FILE.exists():
                cls._create_default_config()
            else:
                cls._load_existing_config()
            
            return copy.deepcopy(cls._config_cache)
    
    @classmethod
    def _ensure_directories(cls) -> None:
        """Ensure all required directories exist."""
        try:
            Path(cls.CONFIG_DIRECTORY).mkdir(parents=True, exist_ok=True)
            Path(cls.OFFSETS_DIRECTORY).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create directories: {e}")
    
    @classmethod
    def _create_default_config(cls) -> None:
        """Create a new configuration file with default settings."""
        logger.info(f"config.json not found at {cls.CONFIG_FILE}, creating default configuration.")
        default_copy = copy.deepcopy(cls.DEFAULT_CONFIG)
        cls._config_cache = default_copy
        cls._save_to_file(default_copy, log_info=False)
    
    @classmethod
    def _load_existing_config(cls) -> None:
        """Load configuration from existing file."""
        try:
            file_bytes = cls.CONFIG_FILE.read_bytes()
            loaded_config = orjson.loads(file_bytes)
            
            # Validate that loaded config is a dictionary
            if not isinstance(loaded_config, dict):
                raise ValueError("Configuration file does not contain a valid dictionary")
            
            cls._config_cache = loaded_config
            logger.info("Loaded configuration.")
            
            # Migrate missing keys from default config
            if cls._update_config(cls.DEFAULT_CONFIG, cls._config_cache):
                logger.info("Configuration updated with missing keys.")
                cls._save_to_file(cls._config_cache, log_info=False)
                
        except (orjson.JSONDecodeError, IOError, ValueError) as e:
            logger.error(f"Failed to load configuration: {e}. Using default configuration.")
            default_copy = copy.deepcopy(cls.DEFAULT_CONFIG)
            cls._config_cache = default_copy
            cls._save_to_file(default_copy, log_info=False)
    
    @classmethod
    def _update_config(cls, default: Dict[str, Any], current: Dict[str, Any]) -> bool:
        """
        Recursively update current config with missing keys from default.
        
        Args:
            default: Default configuration dictionary
            current: Current configuration dictionary to update
            
        Returns:
            True if any keys were added, False otherwise
        """
        updated = False
        for key, value in default.items():
            if key not in current:
                current[key] = copy.deepcopy(value)
                updated = True
                logger.debug(f"Added missing config key: {key}")
            elif isinstance(value, dict) and isinstance(current.get(key), dict):
                if cls._update_config(value, current[key]):
                    updated = True
        return updated
    
    @classmethod
    def save_config(cls, config: Dict[str, Any], log_info: bool = True) -> bool:
        """
        Save the configuration to the configuration file (thread-safe).
        
        Args:
            config: Configuration dictionary to save
            log_info: Whether to log the save operation
            
        Returns:
            True if save was successful, False otherwise
        """
        with cls._lock:
            # Update cache
            cls._config_cache = copy.deepcopy(config)
            # Save to file
            return cls._save_to_file(config, log_info)
    
    @classmethod
    def _save_to_file(cls, config: Dict[str, Any], log_info: bool = True) -> bool:
        """
        Internal method to save configuration to file.
        
        Args:
            config: Configuration dictionary to save
            log_info: Whether to log the save operation
            
        Returns:
            True if save was successful, False otherwise
        """
        try:
            # Ensure directory exists
            Path(cls.CONFIG_DIRECTORY).mkdir(parents=True, exist_ok=True)
            
            # Serialize and write configuration
            config_bytes = orjson.dumps(config, option=orjson.OPT_INDENT_2)
            cls.CONFIG_FILE.write_bytes(config_bytes)
            
            if log_info:
                logger.info(f"Saved configuration to {cls.CONFIG_FILE}.")
            return True
            
        except (OSError, IOError) as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    @classmethod
    def reset_to_default(cls) -> Dict[str, Any]:
        """
        Reset configuration to default values.
        
        Returns:
            The default configuration dictionary
        """
        with cls._lock:
            default_copy = copy.deepcopy(cls.DEFAULT_CONFIG)
            cls._config_cache = default_copy
            cls._save_to_file(default_copy, log_info=True)
            logger.info("Configuration reset to default values.")
            return copy.deepcopy(default_copy)
    
    @classmethod
    def invalidate_cache(cls) -> None:
        """Invalidate the configuration cache, forcing a reload on next access."""
        with cls._lock:
            cls._config_cache = None
            logger.debug("Configuration cache invalidated.")
    
    @classmethod
    def get_value(cls, *keys: str, default: Any = None) -> Any:
        """
        Get a configuration value using a key path.
        
        Args:
            *keys: Key path (e.g., "General", "Trigger")
            default: Default value if key path doesn't exist
            
        Returns:
            The configuration value or default
        """
        config = cls.load_config()
        current = config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    @classmethod
    def set_value(cls, *keys: str, value: Any) -> bool:
        """
        Set a configuration value using a key path.
        
        Args:
            *keys: Key path (e.g., "General", "Trigger")
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        if not keys:
            logger.error("No keys provided to set_value")
            return False
        
        config = cls.load_config()
        current = config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the value
        current[keys[-1]] = value
        
        # Save the configuration
        return cls.save_config(config, log_info=False)

# Color choices for Overlay
COLOR_CHOICES = {
    "Orange": "#FFA500",
    "Red": "#FF0000",
    "Green": "#00FF00",
    "Blue": "#0000FF",
    "White": "#FFFFFF",
    "Black": "#000000",
    "Cyan": "#00FFFF",
    "Yellow": "#FFFF00"
}

# Import pyMeow colors
try:
    from pyMeow import get_color, fade_color
    
    class Colors:
        """Pre-defined colors for overlay rendering using pyMeow."""
        orange = get_color("orange")
        black = get_color("black")
        cyan = get_color("cyan")
        white = get_color("white")
        grey = fade_color(get_color("#242625"), 0.7)
        red = get_color("red")
        green = get_color("green")
        blue = get_color("blue")
        yellow = get_color("yellow")
        
except ImportError:
    logger.warning("pyMeow not available, Colors class will not be initialized")
    Colors = None
