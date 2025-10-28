import os
import requests
import psutil
import sys
import subprocess
import pygetwindow as gw
import orjson
from packaging import version
from dateutil.parser import parse as parse_date
from pathlib import Path

from classes.config_manager import ConfigManager, COLOR_CHOICES
from classes.logger import Logger

# Initialize the logger for consistent logging
logger = Logger.get_logger(__name__)

class Utility:
    @staticmethod
    def load_offset_sources():
        """
        Loads available offset sources from src/offsets.json
        Returns a dictionary with source configurations
        """
        try:
            response = requests.get('https://raw.githubusercontent.com/Jesewe/VioletWing/refs/heads/main/src/offsets.json', timeout=10)
            response.raise_for_status()
            sources_data = orjson.loads(response.content)
            
            # Validate structure
            for source_id, source_config in sources_data.items():
                required_keys = ["name", "author", "repository", "offsets_url", "client_dll_url", "buttons_url"]
                missing_keys = [key for key in required_keys if key not in source_config]
                if missing_keys:
                    logger.error(f"Source '{source_id}' missing keys: {missing_keys}")
                    continue
            
            logger.debug(f"Loaded {len(sources_data)} offsets sources from remote offsets.json")
            return sources_data
            
        except Exception as e:
            logger.warning(f"Failed to load remote offsets sources: {e}, using default sources")
            return {
                "a2x": {
                    "name": "A2X Source",
                    "author": "a2x",
                    "repository": "a2x/cs2-dumper",
                    "offsets_url": "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json",
                    "client_dll_url": "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json",
                    "buttons_url": "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/buttons.json"
                },
                "jesewe": {
                    "name": "Jesewe Source", 
                    "author": "Jesewe",
                    "repository": "Jesewe/cs2-dumper",
                    "offsets_url": "https://raw.githubusercontent.com/Jesewe/cs2-dumper/main/output/offsets.json",
                    "client_dll_url": "https://raw.githubusercontent.com/Jesewe/cs2-dumper/main/output/client_dll.json",
                    "buttons_url": "https://raw.githubusercontent.com/Jesewe/cs2-dumper/main/output/buttons.json"
                }
            }

    @staticmethod
    def fetch_offsets():
        """
        Fetches JSON data from remote URLs or local files based on configuration.
        - Supports dynamic offset sources loaded from src/offsets.json
        - Retrieves data from 'offsets.json', 'client_dll.json', and 'buttons.json'
        - Logs an error if either request fails or the server returns a non-200 status code.
        - Handles exceptions gracefully, ensuring no unhandled errors crash the application.
        - Supports loading from local files if configured.
        """
        config = ConfigManager.load_config()
        source = config["General"].get("OffsetSource", "a2x")
        
        if source == "local":
            config_dir = Path(ConfigManager.CONFIG_DIRECTORY)
            offsets_file = config.get("General", {}).get("OffsetsFile", config_dir / "offsets.json")
            client_file = config.get("General", {}).get("ClientDLLFile", config_dir / "client_dll.json")
            buttons_file = config.get("General", {}).get("ButtonsFile", config_dir / "buttons.json")
            
            try:
                if not all(f.exists() for f in [Path(offsets_file), Path(client_file), Path(buttons_file)]):
                    missing = [f.name for f in [Path(offsets_file), Path(client_file), Path(buttons_file)] if not f.exists()]
                    logger.error(f"Local offset files missing: {', '.join(missing)}. Falling back to a2x.")
                    config["General"]["OffsetSource"] = "a2x"
                    ConfigManager.save_config(config)
                    return Utility.fetch_offsets()  # Recursive fallback to a2x
                
                offset_bytes = Path(offsets_file).read_bytes()
                client_bytes = Path(client_file).read_bytes()
                buttons_bytes = Path(buttons_file).read_bytes()
                
                offset = orjson.loads(offset_bytes)
                client = orjson.loads(client_bytes)
                buttons = orjson.loads(buttons_bytes)
                
                # Validate by attempting to extract offsets
                extracted = Utility.extract_offsets(offset, client, buttons)
                if extracted is None:
                    logger.error("Local offset files invalid: Missing required offsets. Falling back to a2x.")
                    config["General"]["OffsetSource"] = "a2x"
                    ConfigManager.save_config(config)
                    return Utility.fetch_offsets()  # Recursive fallback to a2x
                
                logger.info("Loaded and validated local offsets.")
                return offset, client, buttons
                
            except (orjson.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load local offset files: {e}. Falling back to a2x.")
                config["General"]["OffsetSource"] = "a2x"
                ConfigManager.save_config(config)
                return Utility.fetch_offsets()  # Recursive fallback to a2x
            except Exception as e:
                logger.exception(f"Unexpected error loading local offsets: {e}. Falling back to a2x.")
                config["General"]["OffsetSource"] = "a2x"
                ConfigManager.save_config(config)
                return Utility.fetch_offsets()  # Recursive fallback to a2x
        
        # Server-based offset fetching (dynamic sources)
        try:
            # Load available sources
            available_sources = Utility.load_offset_sources()
            
            if source not in available_sources:
                logger.error(f"Unknown offset source '{source}'. Falling back to a2x.")
                source = "a2x"
                config["General"]["OffsetSource"] = source
                ConfigManager.save_config(config)
                
                if source not in available_sources:
                    logger.error("No valid offset sources available.")
                    return None, None, None
            
            source_config = available_sources[source]
            
            # Get URLs from source configuration (with environment variable override support)
            offsets_url = os.getenv('OFFSETS_URL', source_config["offsets_url"])
            client_dll_url = os.getenv('CLIENT_DLL_URL', source_config["client_dll_url"])
            buttons_url = os.getenv('BUTTONS_URL', source_config["buttons_url"])
            
            server_name = source_config["name"]
            author = source_config["author"]
            repository = source_config["repository"]
            
            logger.debug(f"Fetching offsets from {server_name} (Author: {author}, Repo: {repository})...")
            
            response_offset = requests.get(offsets_url)
            response_client = requests.get(client_dll_url)
            response_buttons = requests.get(buttons_url)

            if response_offset.status_code != 200:
                logger.error(f"Failed to fetch offsets from {server_name}: offsets.json request failed (status: {response_offset.status_code}).")
                return None, None, None

            if response_client.status_code != 200:
                logger.error(f"Failed to fetch offsets from {server_name}: client_dll.json request failed (status: {response_client.status_code}).")
                return None, None, None
            
            if response_buttons.status_code != 200:
                logger.error(f"Failed to fetch buttons from {server_name}: buttons.json request failed (status: {response_buttons.status_code}).")
                return None, None, None

            try:
                offset = orjson.loads(response_offset.content)
                client = orjson.loads(response_client.content)
                buttons = orjson.loads(response_buttons.content)
                
                # Validate by attempting to extract offsets
                extracted = Utility.extract_offsets(offset, client, buttons)
                if extracted is None:
                    logger.error(f"Offset files from {server_name} invalid: Missing required offsets.")
                    return None, None, None
                
                logger.info(f"Successfully loaded and validated offsets from {server_name}.")
                return offset, client, buttons
            except orjson.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON response from {server_name}: {e}")
                return None, None, None

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {server_name}: {e}")
            return None, None, None
        except Exception as e:
            logger.exception(f"An unexpected error occurred while fetching from {server_name}: {e}")
            return None, None, None
        
    @staticmethod
    def get_available_offset_sources():
        """
        Returns list of available offset sources for UI dropdown
        """
        sources = Utility.load_offset_sources()
        source_list = []
        
        # Add dynamic sources
        for source_id, source_config in sources.items():
            source_list.append({
                "id": source_id,
                "name": source_config["name"],
                "author": source_config["author"],
                "display": f"{source_config['name']} ({source_config['author']})"
            })
        
        # Add local option
        source_list.append({
            "id": "local",
            "name": "Local Files",
            "author": "User",
            "display": "Local Files"
        })
        
        return source_list

    @staticmethod
    def check_for_updates(current_version):
        """Checks GitHub for the latest stable and pre-release versions and returns the download URL of 'VioletWing.exe' if an update is available."""
        try:
            # Fetch all releases to check both stable and pre-releases
            response = requests.get("https://api.github.com/repos/Jesewe/VioletWing/releases")
            response.raise_for_status()
            releases = orjson.loads(response.content)

            latest_stable = None
            latest_prerelease = None
            stable_download_url = None
            prerelease_download_url = None

            for release in releases:
                release_version = release.get("tag_name")
                if not release_version:
                    continue
                try:
                    parsed_version = version.parse(release_version)
                except version.InvalidVersion:
                    logger.warning(f"Invalid version format: {release_version}")
                    continue

                # Check if release is a pre-release
                is_prerelease = release.get("prerelease", False)
                for asset in release.get("assets", []):
                    if asset.get("name") == "VioletWing.exe":
                        download_url = asset.get("browser_download_url")
                        if download_url:
                            if is_prerelease:
                                if not latest_prerelease or parsed_version > version.parse(latest_prerelease):
                                    latest_prerelease = release_version
                                    prerelease_download_url = download_url
                            else:
                                if not latest_stable or parsed_version > version.parse(latest_stable):
                                    latest_stable = release_version
                                    stable_download_url = download_url

            current = version.parse(current_version)

            # Prioritize stable release if it's newer than current version
            if latest_stable and version.parse(latest_stable) > current:
                logger.info(f"New stable version available: {latest_stable}")
                return stable_download_url, False  # False indicates stable release
            # If no newer stable release, check pre-release
            elif latest_prerelease and version.parse(latest_prerelease) > current:
                logger.info(f"New pre-release version available: {latest_prerelease}")
                return prerelease_download_url, True  # True indicates pre-release
            else:
                logger.info("No new updates available.")
                return None, False

        except requests.exceptions.RequestException as e:
            logger.error(f"Update check failed: {e}")
            return None, False
        except Exception as e:
            logger.error(f"An unexpected error occurred during update check: {e}")
            return None, False

    @staticmethod
    def resource_path(relative_path):
        """Returns the path to a resource, supporting both normal startup and frozen .exe."""
        try:
            if hasattr(sys, '_MEIPASS'):
                return os.path.join(sys._MEIPASS, relative_path)
            return os.path.join(os.path.abspath("."), relative_path)
        except Exception as e:
            logger.error(f"Failed to get resource path: {e}")
            return None

    @staticmethod
    def is_game_active():
        """Check if the game window is active using pygetwindow."""
        windows = gw.getWindowsWithTitle('Counter-Strike 2')
        return any(window.isActive for window in windows)

    @staticmethod
    def is_game_running():
        """Check if the game process is running using psutil."""
        return any(proc.info['name'] == 'cs2.exe' for proc in psutil.process_iter(attrs=['name']))
    
    @staticmethod
    def extract_offsets(offsets: dict, client_data: dict, buttons_data: dict) -> dict | None:
        """Load memory offsets for game functionality."""
        try:
            client = offsets.get("client.dll", {})
            buttons = buttons_data.get("client.dll", {})
            classes = client_data.get("client.dll", {}).get("classes", {})

            def get_field(class_name, field_name):
                """Recursively search for a field in a class and its parents."""
                class_info = classes.get(class_name)
                if not class_info:
                    raise KeyError(f"Class '{class_name}' not found")

                field = class_info.get("fields", {}).get(field_name)
                if field is not None:
                    return field
                
                parent_class_name = class_info.get("parent")
                if parent_class_name:
                    return get_field(parent_class_name, field_name)
                    
                raise KeyError(f"'{field_name}' not found in '{class_name}' or its parents")

            extracted_offsets = {
                "dwEntityList": client.get("dwEntityList"),
                "dwLocalPlayerPawn": client.get("dwLocalPlayerPawn"),
                "dwLocalPlayerController": client.get("dwLocalPlayerController"),
                "dwViewMatrix": client.get("dwViewMatrix"),
                "dwForceJump": buttons.get("jump"),
                "m_iHealth": get_field("C_BaseEntity", "m_iHealth"),
                "m_iTeamNum": get_field("C_BaseEntity", "m_iTeamNum"),
                "m_pGameSceneNode": get_field("C_BaseEntity", "m_pGameSceneNode"),
                "m_vOldOrigin": get_field("C_BasePlayerPawn", "m_vOldOrigin"),
                "m_vecAbsOrigin": get_field("CGameSceneNode", "m_vecAbsOrigin"),
                "m_pWeaponServices": get_field("C_BasePlayerPawn", "m_pWeaponServices"),
                "m_iIDEntIndex": get_field("C_CSPlayerPawn", "m_iIDEntIndex"),
                "m_flFlashDuration": get_field("C_CSPlayerPawnBase", "m_flFlashDuration"),
                "m_pClippingWeapon": get_field("C_CSPlayerPawn", "m_pClippingWeapon"),
                "m_hPlayerPawn": get_field("CCSPlayerController", "m_hPlayerPawn"),
                "m_iszPlayerName": get_field("CBasePlayerController", "m_iszPlayerName"),
                "m_hActiveWeapon": get_field("CPlayer_WeaponServices", "m_hActiveWeapon"),
                "m_bDormant": get_field("CGameSceneNode", "m_bDormant"),
                "m_AttributeManager": get_field("C_EconEntity", "m_AttributeManager"),
                "m_Item": get_field("C_AttributeContainer", "m_Item"),
                "m_iItemDefinitionIndex": get_field("C_EconItemView", "m_iItemDefinitionIndex"),
                "m_pBoneArray": 528
            }

            missing_keys = [k for k, v in extracted_offsets.items() if v is None]
            if missing_keys:
                logger.error(f"Offset initialization error: Missing top-level keys {missing_keys}")
                return None

            return extracted_offsets

        except KeyError as e:
            logger.error(f"Offset initialization error: Missing key {e}")
            return None
        
    @staticmethod
    def get_color_name_from_hex(hex_color: str) -> str:
        """Get color name from hex value."""
        for name, hex_code in COLOR_CHOICES.items():
            if hex_code == hex_color:
                return name
        return "Black"
    
    @staticmethod
    def transliterate(text: str) -> str:
        """Converts Cyrillic characters in the given text to their Latin equivalents."""
        mapping = {
            'А': 'A',  'а': 'a',
            'Б': 'B',  'б': 'b',
            'В': 'V',  'в': 'v',
            'Г': 'G',  'г': 'g',
            'Д': 'D',  'д': 'd',
            'Е': 'E',  'е': 'e',
            'Ё': 'Yo', 'ё': 'yo',
            'Ж': 'Zh', 'ж': 'zh',
            'З': 'Z',  'з': 'z',
            'И': 'I',  'и': 'i',
            'Й': 'I',  'й': 'i',
            'К': 'K',  'к': 'k',
            'Л': 'L',  'л': 'l',
            'М': 'M',  'м': 'm',
            'Н': 'N',  'н': 'n',
            'О': 'O',  'о': 'o',
            'П': 'P',  'п': 'p',
            'Р': 'R',  'р': 'r',
            'С': 'S',  'с': 's',
            'Т': 'T',  'т': 't',
            'У': 'U',  'у': 'u',
            'Ф': 'F',  'ф': 'f',
            'Х': 'Kh', 'х': 'kh',
            'Ц': 'Ts', 'ц': 'ts',
            'Ч': 'Ch', 'ч': 'ch',
            'Ш': 'Sh', 'ш': 'sh',
            'Щ': 'Shch', 'щ': 'shch',
            'Ъ': '',   'ъ': '',
            'Ы': 'Y',  'ы': 'y',
            'Ь': '',   'ь': '',
            'Э': 'E',  'э': 'e',
            'Ю': 'Yu', 'ю': 'yu',
            'Я': 'Ya', 'я': 'ya'
        }
        return "".join(mapping.get(char, char) for char in text)

    @staticmethod
    def get_vk_code(key: str) -> int:
        """Convert a key string to its corresponding virtual key code."""
        key = key.lower()
        vk_codes = {
            # Mouse buttons
            "mouse1": 0x01,        # Left mouse button
            "mouse2": 0x02,        # Right mouse button
            "mouse3": 0x04,        # Middle mouse button
            "mouse4": 0x05,        # X1 mouse button
            "mouse5": 0x06,        # X2 mouse button
            # Common keyboard keys
            "space": 0x20,         # Spacebar
            "enter": 0x0D,         # Enter key
            "shift": 0x10,         # Shift key
            "ctrl": 0x11,          # Control key
            "alt": 0x12,           # Alt key
            "tab": 0x09,           # Tab key
            "backspace": 0x08,     # Backspace key
            "esc": 0x1B,           # Escape key
            # Alphabet keys
            "a": 0x41, "b": 0x42, "c": 0x43, "d": 0x44, "e": 0x45, "f": 0x46,
            "g": 0x47, "h": 0x48, "i": 0x49, "j": 0x4A, "k": 0x4B, "l": 0x4C,
            "m": 0x4D, "n": 0x4E, "o": 0x4F, "p": 0x50, "q": 0x51, "r": 0x52,
            "s": 0x53, "t": 0x54, "u": 0x55, "v": 0x56, "w": 0x57, "x": 0x58,
            "y": 0x59, "z": 0x5A,
            # Number keys
            "0": 0x30, "1": 0x31, "2": 0x32, "3": 0x33, "4": 0x34,
            "5": 0x35, "6": 0x36, "7": 0x37, "8": 0x38, "9": 0x39,
            # Function keys
            "f1": 0x70, "f2": 0x71, "f3": 0x72, "f4": 0x73, "f5": 0x74,
            "f6": 0x75, "f7": 0x76, "f8": 0x77, "f9": 0x78, "f10": 0x79,
            "f11": 0x7A, "f12": 0x7B
        }
        return vk_codes.get(key, 0x20)  # Default to space key