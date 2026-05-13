import os
import sys

from classes.config_manager import ConfigManager, COLOR_CHOICES
from classes.logger import Logger
import classes.error_codes as EC

from classes import game_process as _gp
from classes import offset_fetcher as _of
from constants.vk_codes import get_vk_code as _get_vk_code

logger = Logger.get_logger(__name__)

class Utility:
    @staticmethod
    def is_game_active() -> bool:
        return _gp.is_game_active()

    @staticmethod
    def is_game_running() -> bool:
        return _gp.is_game_running()

    @staticmethod
    def load_offset_sources() -> dict:
        return _of.load_offset_sources()

    @staticmethod
    def fetch_offsets():
        return _of.fetch_offsets()

    @staticmethod
    def get_available_offset_sources() -> list[dict]:
        return _of.get_available_offset_sources()

    @staticmethod
    def check_for_updates(current_version: str) -> tuple:
        return _of.check_for_updates(current_version)

    @staticmethod
    def get_vk_code(key: str) -> int:
        return _get_vk_code(key)

    @staticmethod
    def resource_path(relative_path: str) -> str:
        """Return the absolute path to a bundled resource."""
        try:
            if hasattr(sys, "_MEIPASS"):
                return os.path.join(sys._MEIPASS, relative_path)
            return os.path.join(os.path.abspath("."), relative_path)
        except Exception as exc:
            Logger.error_code(EC.E0001, "%s", exc)
            return relative_path

    @staticmethod
    def get_color_name_from_hex(hex_color: str) -> str:
        for name, code in COLOR_CHOICES.items():
            if code == hex_color:
                return name
        return "Black"

    _TRANSLITERATE_TABLE = str.maketrans({
        'А': 'A',  'а': 'a',  'Б': 'B',  'б': 'b',  'В': 'V',  'в': 'v',
        'Г': 'G',  'г': 'g',  'Д': 'D',  'д': 'd',  'Е': 'E',  'е': 'e',
        'Ё': 'Yo', 'ё': 'yo', 'Ж': 'Zh', 'ж': 'zh', 'З': 'Z',  'з': 'z',
        'И': 'I',  'и': 'i',  'Й': 'I',  'й': 'i',  'К': 'K',  'к': 'k',
        'Л': 'L',  'л': 'l',  'М': 'M',  'м': 'm',  'Н': 'N',  'н': 'n',
        'О': 'O',  'о': 'o',  'П': 'P',  'п': 'p',  'Р': 'R',  'р': 'r',
        'С': 'S',  'с': 's',  'Т': 'T',  'т': 't',  'У': 'U',  'у': 'u',
        'Ф': 'F',  'ф': 'f',  'Х': 'Kh', 'х': 'kh', 'Ц': 'Ts', 'ц': 'ts',
        'Ч': 'Ch', 'ч': 'ch', 'Ш': 'Sh', 'ш': 'sh', 'Щ': 'Shch', 'щ': 'shch',
        'Ъ': '',   'ъ': '',   'Ы': 'Y',  'ы': 'y',  'Ь': '',   'ь': '',
        'Э': 'E',  'э': 'e',  'Ю': 'Yu', 'ю': 'yu', 'Я': 'Ya', 'я': 'ya',
    })

    @staticmethod
    def transliterate(text: str) -> str:
        return text.translate(Utility._TRANSLITERATE_TABLE)

    @staticmethod
    def extract_offsets(offsets: dict, client_data: dict, buttons_data: dict) -> dict | None:
        try:
            client = offsets.get("client.dll", {})
            buttons = buttons_data.get("client.dll", {})
            classes = client_data.get("client.dll", {}).get("classes", {})

            def get_field(class_name: str, field_name: str):
                class_info = classes.get(class_name)
                if not class_info:
                    raise KeyError(f"Class '{class_name}' not found")
                field = class_info.get("fields", {}).get(field_name)
                if field is not None:
                    return field
                parent = class_info.get("parent")
                if parent:
                    return get_field(parent, field_name)
                raise KeyError(f"'{field_name}' not found in '{class_name}' or its parents")

            extracted = {
                "dwEntityList":           client.get("dwEntityList"),
                "dwLocalPlayerPawn":      client.get("dwLocalPlayerPawn"),
                "dwLocalPlayerController": client.get("dwLocalPlayerController"),
                "dwViewMatrix":           client.get("dwViewMatrix"),
                "dwForceJump":            buttons.get("jump"),
                "m_iHealth":              get_field("C_BaseEntity", "m_iHealth"),
                "m_iTeamNum":             get_field("C_BaseEntity", "m_iTeamNum"),
                "m_pGameSceneNode":       get_field("C_BaseEntity", "m_pGameSceneNode"),
                "m_vOldOrigin":           get_field("C_BasePlayerPawn", "m_vOldOrigin"),
                "m_vecAbsOrigin":         get_field("CGameSceneNode", "m_vecAbsOrigin"),
                "m_pWeaponServices":      get_field("C_BasePlayerPawn", "m_pWeaponServices"),
                "m_iIDEntIndex":          get_field("C_CSPlayerPawn", "m_iIDEntIndex"),
                "m_flFlashBangTime":      get_field("C_CSPlayerPawnBase", "m_flFlashBangTime"),
                "m_hPlayerPawn":          get_field("CCSPlayerController", "m_hPlayerPawn"),
                "m_iszPlayerName":        get_field("CBasePlayerController", "m_iszPlayerName"),
                "m_hActiveWeapon":        get_field("CPlayer_WeaponServices", "m_hActiveWeapon"),
                "m_bDormant":             get_field("CGameSceneNode", "m_bDormant"),
                "m_AttributeManager":     get_field("C_EconEntity", "m_AttributeManager"),
                "m_Item":                 get_field("C_AttributeContainer", "m_Item"),
                "m_iItemDefinitionIndex": get_field("C_EconItemView", "m_iItemDefinitionIndex"),
                "m_pBoneArray":           get_field("CSkeletonInstance", "m_modelState") + 0x80,
            }

            missing = [k for k, v in extracted.items() if v is None]
            if missing:
                Logger.error_code(EC.E2007, "Missing: %s", missing)
                return None

            return extracted

        except KeyError as exc:
            Logger.error_code(EC.E2007, "Key: %s", exc)
            return None