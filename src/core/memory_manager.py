import pymem
import pymem.process
import struct

from src.utils.logger import Logger
from src.utils.utility import Utility
import src.utils.error_codes as EC

# Initialize the logger for consistent logging
logger = Logger.get_logger(__name__)

class MemoryManager:
    def __init__(self, offsets: dict, client_data: dict, buttons_data: dict) -> None:
        """Initialize MemoryManager with offsets and client data."""
        self.offsets = offsets
        self.client_data = client_data
        self.buttons_data = buttons_data
        self.pm = None
        self.client_base = None
        self.config = None
        self._initialized: bool = False
        # Offset attributes
        self.dwEntityList = None
        self.dwLocalPlayerPawn = None
        self.dwLocalPlayerController = None
        self.dwViewMatrix = None
        self.dwPlantedC4 = None
        self.dwGlobalVars = None
        self.m_iHealth = None
        self.m_ArmorValue = None
        self.m_iTeamNum = None
        self.m_iIDEntIndex = None
        self.m_iszPlayerName = None
        self.m_vOldOrigin = None
        self.m_pGameSceneNode = None
        self.m_bDormant = None
        self.m_hPlayerPawn = None
        self.m_flFlashDuration = None
        self.m_pBoneArray = None
        self.jump = None
        self.m_AttributeManager = None
        self.m_iItemDefinitionIndex = None
        self.m_Item = None
        self.m_pWeaponServices = None
        self.m_hActiveWeapon = None
        self.m_bBombTicking = None
        self.m_flC4Blow = None
        self.m_bBeingDefused = None
        self.m_flDefuseCountDown = None
        self.m_bHasExploded = None
        self.m_bBombDefused = None
        self.m_nBombSite = None
        self.m_bIsDefusing = None
        self.m_flFlashOverlayAlpha = None
        self.m_bIsScoped = None
        self.m_bInReload = None
        self.m_iPing = None
        self._cached_weapon_handle: int = 0
        self._cached_weapon_type: str = "Rifles"

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def initialize(self) -> bool:
        """Initialize memory access by attaching to the process and setting up necessary data."""
        # Check if pymem is initialized and the client module is retrieved
        if not self.initialize_pymem() or not self.get_client_module():
            return False
        self.load_offsets()
        if self.dwEntityList is None:
            return False
        self._initialized = True
        return True

    def reset(self) -> None:
        """Release the pymem handle and mark as uninitialized."""
        self._initialized = False
        if self.pm is not None:
            try:
                self.pm.close_process()
            except Exception as exc:
                logger.debug("Error closing pymem handle: %s", exc)
            self.pm = None
        self.client_base = None

    def _apply_offsets(self) -> None:
        """Re-derive offset attributes after an async offset fetch completes."""
        self.load_offsets()

    def initialize_pymem(self) -> bool:
        """Attach pymem to the game process."""
        try:
            self.pm = pymem.Pymem("cs2.exe")
            logger.debug("Successfully attached to cs2.exe process.")
            return True
        except pymem.exception.ProcessNotFound:
            Logger.error_code(EC.E2001)
            return False
        except Exception as e:
            Logger.error_code(EC.E2002, "%s", e)
            return False

    def get_client_module(self) -> bool:
        """Retrieve the client.dll module base address."""
        try:
            client_module = pymem.process.module_from_name(self.pm.process_handle, "client.dll")
            self.client_base = client_module.lpBaseOfDll
            logger.debug("client.dll module found and base address retrieved.")
            return True
        except pymem.exception.ModuleNotFoundError:
            Logger.error_code(EC.E2003)
            return False
        except Exception as e:
            Logger.error_code(EC.E2004, "%s", e)
            return False

    def load_offsets(self) -> None:
        """Load memory offsets from Utility.extract_offsets."""
        extracted = Utility.extract_offsets(self.offsets, self.client_data, self.buttons_data)
        if extracted:
            self.dwEntityList = extracted["dwEntityList"]
            self.dwLocalPlayerPawn = extracted["dwLocalPlayerPawn"]
            self.dwLocalPlayerController = extracted["dwLocalPlayerController"]
            self.dwViewMatrix = extracted["dwViewMatrix"]
            self.dwPlantedC4 = extracted["dwPlantedC4"]
            self.dwGameRules = extracted["dwGameRules"]
            self.dwGlobalVars = extracted["dwGlobalVars"]
            self.jump = extracted["jump"]
            self.m_iHealth = extracted["m_iHealth"]
            self.m_ArmorValue = extracted["m_ArmorValue"]
            self.m_iTeamNum = extracted["m_iTeamNum"]
            self.m_iIDEntIndex = extracted["m_iIDEntIndex"]
            self.m_iszPlayerName = extracted["m_iszPlayerName"]
            self.m_vOldOrigin = extracted["m_vOldOrigin"]
            self.m_pGameSceneNode = extracted["m_pGameSceneNode"]
            self.m_bDormant = extracted["m_bDormant"]
            self.m_hPlayerPawn = extracted["m_hPlayerPawn"]
            self.m_flFlashDuration = extracted["m_flFlashDuration"]
            self.m_pBoneArray = extracted["m_pBoneArray"]
            self.m_AttributeManager = extracted["m_AttributeManager"]
            self.m_iItemDefinitionIndex = extracted["m_iItemDefinitionIndex"]
            self.m_Item = extracted["m_Item"]
            self.m_pWeaponServices = extracted["m_pWeaponServices"]
            self.m_hActiveWeapon = extracted["m_hActiveWeapon"]
            self.m_bBombTicking = extracted["m_bBombTicking"]
            self.m_flC4Blow = extracted["m_flC4Blow"]
            self.m_bBeingDefused = extracted["m_bBeingDefused"]
            self.m_flDefuseCountDown = extracted["m_flDefuseCountDown"]
            self.m_bHasExploded = extracted["m_bHasExploded"]
            self.m_bBombDefused = extracted["m_bBombDefused"]
            self.m_nBombSite = extracted["m_nBombSite"]
            self.m_bBombPlanted = extracted["m_bBombPlanted"]
            self.m_bIsDefusing = extracted["m_bIsDefusing"]
            self.m_flFlashOverlayAlpha = extracted["m_flFlashOverlayAlpha"]
            self.m_bIsScoped = extracted["m_bIsScoped"]
            self.m_bInReload = extracted["m_bInReload"]
            self.m_iPing = extracted["m_iPing"]
            self.m_hPawn = extracted["m_hPawn"]
            self.m_hObserverPawn = extracted["m_hObserverPawn"]
            self.m_pObserverServices = extracted["m_pObserverServices"]
            self.m_iObserverMode = extracted["m_iObserverMode"]
            self.m_hObserverTarget = extracted["m_hObserverTarget"]
            self.m_fFlags = extracted["m_fFlags"]
        else:
            Logger.error_code(EC.E2005)

    def get_entity(self, index: int):
        """Retrieve an entity from the entity list."""
        try:
            ent_list = self.read_longlong(self.client_base + self.dwEntityList)
            list_offset = 0x8 * (index >> 9)
            ent_entry = self.read_longlong(ent_list + list_offset + 0x10)
            entity_offset = 112 * (index & 0x1FF)
            return self.read_longlong(ent_entry + entity_offset)
        except Exception as e:
            logger.debug(f"Error reading entity: {e}")
            return None

    def get_bomb_info(self) -> dict | None:
        """Retrieve information about the planted C4."""
        try:
            if not self.dwGlobalVars or not self.dwPlantedC4 or not self.dwGameRules:
                return None

            game_rules = self.read_longlong(self.client_base + self.dwGameRules)
            if not game_rules:
                return None
                
            # If the bomb isn't actively planted in the current round, ignore any stale C4 pointers
            is_bomb_planted = bool(self.pm.read_bytes(game_rules + self.m_bBombPlanted, 1)[0])
            if not is_bomb_planted:
                return None

            global_vars = self.read_longlong(self.client_base + self.dwGlobalVars)
            if not global_vars:
                return None
            
            # Extract current time (m_flCurrentTime is at offset 0x2C from GlobalVarsBase)
            try:
                data = self.pm.read_bytes(global_vars + 0x2C, 4)
                curtime = struct.unpack('f', data)[0]
            except Exception:
                curtime = 0.0

            planted_c4 = self.read_longlong(self.client_base + self.dwPlantedC4)
            if not planted_c4:
                return None

            try:
                ticking = bool(self.pm.read_bytes(planted_c4 + self.m_bBombTicking, 1)[0])
            except Exception:
                ticking = False

            if ticking:
                blow_time_data = self.pm.read_bytes(planted_c4 + self.m_flC4Blow, 4)
                defuse_time_data = self.pm.read_bytes(planted_c4 + self.m_flDefuseCountDown, 4)
                
                blow_time = struct.unpack('f', blow_time_data)[0]
                defuse_countdown = struct.unpack('f', defuse_time_data)[0]
                
                is_defusing = bool(self.pm.read_bytes(planted_c4 + self.m_bBeingDefused, 1)[0])
                has_exploded = bool(self.pm.read_bytes(planted_c4 + self.m_bHasExploded, 1)[0])
                is_defused = bool(self.pm.read_bytes(planted_c4 + self.m_bBombDefused, 1)[0])
                
                bomb_site_raw = self.read_int(planted_c4 + self.m_nBombSite)
                bomb_site = "B" if bomb_site_raw == 1 else "A" if bomb_site_raw == 0 else "?"

                # Dynamically find the correct curtime offset to ensure accurate timers across patches
                curtime_candidates = [0x28, 0x2C, 0x30, 0x34]
                actual_curtime = curtime
                for offset in curtime_candidates:
                    try:
                        data = self.pm.read_bytes(global_vars + offset, 4)
                        ct = struct.unpack('f', data)[0]
                        # Valid C4 timer should be between -5s and 60s from curtime
                        if -5.0 < (blow_time - ct) < 60.0:
                            actual_curtime = ct
                            break
                    except Exception:
                        pass

                return {
                    "is_planted": True,
                    "curtime": actual_curtime,
                    "blow_time": blow_time,
                    "is_defusing": is_defusing,
                    "defuse_countdown": defuse_countdown,
                    "has_exploded": has_exploded,
                    "is_defused": is_defused,
                    "bomb_site": bomb_site
                }
            return None
        except Exception as e:
            logger.debug(f"Error reading bomb info: {e}")
            return None

    def is_in_match(self) -> bool:
        """Check if the player is currently in a match (not in the lobby)."""
        try:
            if not self.dwGlobalVars:
                return False
            global_vars = self.read_longlong(self.client_base + self.dwGlobalVars)
            if not global_vars:
                return False
            # MaxClients is at offset 0x10
            max_clients = self.read_int(global_vars + 0x10)
            return max_clients > 1
        except Exception as e:
            logger.debug(f"Error checking is_in_match: {e}")
            return False

    def get_map_name(self) -> str:
        """Retrieve the current map name from GlobalVars."""
        try:
            if not self.dwGlobalVars:
                return ""
            global_vars = self.read_longlong(self.client_base + self.dwGlobalVars)
            if not global_vars:
                return ""
            map_name_addr = self.read_longlong(global_vars + 0x0188)
            if not map_name_addr:
                return ""
            map_name = self.read_string(map_name_addr, 64)
            return map_name.strip() if map_name else ""
        except Exception:
            return ""

    def get_fire_logic_data(self) -> dict | None:
        """Retrieve data necessary for firing logic."""
        try:
            player = self.read_longlong(self.client_base + self.dwLocalPlayerPawn)
            entity_id = self.read_int(player + self.m_iIDEntIndex)

            if entity_id > 0:
                entity = self.get_entity(entity_id)
                if entity:
                    entity_team = self.read_int(entity + self.m_iTeamNum)
                    player_team = self.read_int(player + self.m_iTeamNum)
                    entity_health = self.read_int(entity + self.m_iHealth)
                    weapon_type = self.get_weapon_type()
                    return {
                        "entity_team": entity_team,
                        "player_team": player_team,
                        "entity_health": entity_health,
                        "weapon_type": weapon_type
                    }
            return None
        except Exception as e:
            if "Could not read memory at" in str(e):
                Logger.error_code(EC.E2006)
            else:
                logger.error(f"Error in fire logic: {e}")
            return None

    def get_weapon_type(self) -> str:
        """Get the category of the currently equipped weapon via m_iItemDefinitionIndex."""
        try:
            player = self.read_longlong(self.client_base + self.dwLocalPlayerPawn)
            if not player:
                return "Rifles"

            weapon_services = self.read_longlong(player + self.m_pWeaponServices)
            if not weapon_services:
                return "Rifles"

            weapon_handle = self.read_longlong(weapon_services + self.m_hActiveWeapon)
            if not weapon_handle:
                return "Rifles"

            if weapon_handle == self._cached_weapon_handle:
                return self._cached_weapon_type

            weapon_index = weapon_handle & 0x7FFF
            ent_list = self.read_longlong(self.client_base + self.dwEntityList)
            list_entry = self.read_longlong(ent_list + 8 * (weapon_index >> 9) + 16)
            if not list_entry:
                return "Rifles"

            weapon_entity = self.read_longlong(list_entry + 112 * (weapon_index & 0x1FF))
            if not weapon_entity:
                return "Rifles"

            # All three are embedded struct offsets - add them, do NOT dereference as pointers.
            # m_iItemDefinitionIndex is uint16, mask the int read to 16 bits.
            item_id = self.read_int(
                weapon_entity + self.m_AttributeManager + self.m_Item + self.m_iItemDefinitionIndex
            ) & 0xFFFF

            weapon_map = {
                1: "Pistols", 2: "Pistols", 3: "Pistols", 4: "Pistols",
                30: "Pistols", 32: "Pistols", 36: "Pistols",
                61: "Pistols", 63: "Pistols", 64: "Pistols",
                7: "Rifles", 8: "Rifles", 10: "Rifles", 13: "Rifles",
                16: "Rifles", 39: "Rifles", 60: "Rifles",
                9: "Snipers", 11: "Snipers", 38: "Snipers", 40: "Snipers",
                17: "SMGs", 19: "SMGs", 23: "SMGs", 24: "SMGs",
                26: "SMGs", 33: "SMGs", 34: "SMGs",
                14: "Heavy", 25: "Heavy", 27: "Heavy", 28: "Heavy", 29: "Heavy", 35: "Heavy",
            }
            category = weapon_map.get(item_id, "Rifles")
            logger.debug(f"ItemDefinitionIndex={item_id} → {category}")

            self._cached_weapon_handle = weapon_handle
            self._cached_weapon_type = category

            return category

        except Exception as e:
            logger.debug(f"Failed to get weapon type: {e}")
            return "Rifles"

    def get_entity_weapon_ptr(self, pawn_ptr: int) -> int:
        """Get the weapon entity pointer for an arbitrary player pawn."""
        try:
            if not pawn_ptr:
                return 0

            weapon_services = self.read_longlong(pawn_ptr + self.m_pWeaponServices)
            if not weapon_services:
                return 0

            weapon_handle = self.read_longlong(weapon_services + self.m_hActiveWeapon)
            if not weapon_handle:
                return 0

            weapon_index = weapon_handle & 0x7FFF
            ent_list = self.read_longlong(self.client_base + self.dwEntityList)
            list_entry = self.read_longlong(ent_list + 8 * (weapon_index >> 9) + 16)
            if not list_entry:
                return 0

            weapon_entity = self.read_longlong(list_entry + 112 * (weapon_index & 0x1FF))
            return weapon_entity

        except Exception as e:
            logger.debug(f"Failed to get entity weapon ptr: {e}")
            return 0

    def get_entity_weapon_name(self, pawn_ptr: int) -> str:
        """Get the specific weapon name for an arbitrary player pawn."""
        try:
            weapon_entity = self.get_entity_weapon_ptr(pawn_ptr)
            if not weapon_entity:
                return ""

            item_id = self.read_int(
                weapon_entity + self.m_AttributeManager + self.m_Item + self.m_iItemDefinitionIndex
            ) & 0xFFFF

            if item_id >= 500 or item_id in (42, 59):
                return "Knife"
                
            weapon_names = {
                1: "Desert Eagle", 2: "Dual Berettas", 3: "Five-SeveN", 4: "Glock-18",
                7: "AK-47", 8: "AUG", 9: "AWP", 10: "FAMAS", 11: "G3SG1", 13: "Galil AR",
                14: "M249", 16: "M4A4", 17: "MAC-10", 19: "P90", 23: "MP5-SD", 24: "UMP-45",
                25: "XM1014", 26: "Bizon", 27: "MAG-7", 28: "Negev", 29: "Sawed-Off",
                30: "Tec-9", 31: "Zeus x27", 32: "P2000", 33: "MP7", 34: "MP9", 35: "Nova",
                36: "P250", 38: "SCAR-20", 39: "SG 553", 40: "SSG 08", 43: "Flashbang",
                44: "HE Grenade", 45: "Smoke Grenade", 46: "Molotov", 47: "Decoy",
                48: "Incendiary", 49: "C4 Explosive", 60: "M4A1-S", 61: "USP-S",
                63: "CZ75-Auto", 64: "R8 Revolver",
            }
            return weapon_names.get(item_id, "Unknown")

        except Exception as e:
            logger.debug(f"Failed to get entity weapon name: {e}")
            return ""

    def get_local_crosshair_data(self, local_pawn: int) -> tuple[bool, int]:
        """Return (is_scoped, item_id) for the local player pawn."""
        try:
            if not local_pawn:
                return False, -1

            is_scoped = bool(self.pm.read_bytes(local_pawn + self.m_bIsScoped, 1)[0])

            weapon_ptr = self.get_entity_weapon_ptr(local_pawn)
            if not weapon_ptr:
                return is_scoped, -1

            item_id = self.read_int(
                weapon_ptr + self.m_AttributeManager + self.m_Item + self.m_iItemDefinitionIndex
            ) & 0xFFFF

            return is_scoped, item_id

        except Exception as e:
            logger.debug(f"Failed to get local crosshair data: {e}")
            return False, -1

    def write_float(self, address: int, value: float) -> None:
        """Write a float to memory."""
        try:
            self.pm.write_float(address, value)
            logger.debug(f"Wrote float {value} to address {hex(address)}")
        except Exception as e:
            logger.error(f"Failed to write float at address {hex(address)}: {e}")
            raise

    def write_int(self, address: int, value: int) -> None:
        """Write an integer to memory."""
        try:
            self.pm.write_int(address, value)
            logger.debug(f"Wrote int {value} to address {hex(address)}")
        except Exception as e:
            logger.error(f"Failed to write int at address {hex(address)}: {e}")
            raise

    def read_vec3(self, address: int) -> dict | None:
        """
        Reads a 3D vector (three floats) from memory at the specified address.
        """
        try:
            data = self.pm.read_bytes(address, 12)
            x, y, z = struct.unpack('3f', data)
            return {"x": x, "y": y, "z": z}
        except Exception as e:
            logger.debug(f"Failed to read vec3 at address {hex(address)}: {e}")
            return {"x": 0.0, "y": 0.0, "z": 0.0}

    def read_string(self, address: int, max_length: int = 256) -> str:
        """Reads a null-terminated string from memory at the specified address."""
        try:
            data = self.pm.read_bytes(address, max_length)
            string_data = data.split(b'\x00')[0]
            return string_data.decode('utf-8', errors='replace')
        except Exception as e:
            logger.debug(f"Failed to read string at address {hex(address)}: {e}")
            return ""

    def read_floats(self, address: int, count: int) -> list[float]:
        """
        Reads an array of `count` floats from memory.
        """
        try:
            data = self.pm.read_bytes(address, count * 4)
            return list(struct.unpack(f'{count}f', data))
        except Exception as e:
            logger.debug(f"Failed to read {count} floats at address {hex(address)}: {e}")
            return []

    def read_int(self, address: int) -> int:
        """Read an integer from memory."""
        try:
            return self.pm.read_int(address)
        except Exception as e:
            logger.debug(f"Failed to read int at address {hex(address)}: {e}")
            return 0

    def read_longlong(self, address: int) -> int:
        """Read a long long from memory."""
        try:
            return self.pm.read_longlong(address)
        except Exception as e:
            logger.debug(f"Failed to read longlong at address {hex(address)}: {e}")
            return 0

    @property
    def client_dll_base(self) -> int:
        """Get the base address of client.dll."""
        return self.client_base