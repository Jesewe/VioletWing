import struct
import time
from typing import Dict, Iterator, Optional

import pyMeow as overlay
from pynput.keyboard import Listener as KeyboardListener

from src.features.base_feature import BaseFeature
from src.utils.config_manager import ConfigManager, Colors, COLOR_CHOICES
from src.core.game_process import is_game_active
from src.utils.logger import Logger
import src.utils.error_codes as EC
from src.core.memory_manager import MemoryManager
from src.utils.utility import Utility

logger = Logger.get_logger(__name__)

MAIN_LOOP_SLEEP = 0.05
ENTITY_COUNT = 64          # Full server coverage (was 32)
ENTITY_ENTRY_SIZE = 112

SKELETON_BONES = {
    1:  [3, 17, 20],
    3:  [4],
    4:  [23],
    23: [6],
    6:  [7, 9, 13],
    9:  [10],
    10: [11],
    13: [14],
    14: [15],
    17: [18],
    18: [19],
    20: [21],
    21: [22],
}
ALL_BONE_IDS = set(SKELETON_BONES.keys())
for _bones in SKELETON_BONES.values():
    ALL_BONE_IDS.update(_bones)
MAX_BONE_ID = max(ALL_BONE_IDS) if ALL_BONE_IDS else 0

class Entity:
    """Game entity with cached per-frame data."""
    def __init__(self, controller_ptr: int, pawn_ptr: int, mm: MemoryManager) -> None:
        self.controller_ptr = controller_ptr
        self.pawn_ptr = pawn_ptr
        self.memory_manager = mm
        self.pos2d: Optional[Dict[str, float]] = None
        self.head_pos2d: Optional[Dict[str, float]] = None
        self.name: str = ""
        self.health: int = 0
        self.armor: int = 0
        self.team: int = -1
        self.pos: Dict[str, float] = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.dormant: bool = True
        self.all_bones_pos_3d: Optional[Dict[int, Dict[str, float]]] = None
        self.weapon_name: str = ""
        self.is_scoped: bool = False
        self.is_reloading: bool = False
        self.is_flashed: bool = False
        self.is_defusing: bool = False

    def update(self, skeleton_enabled: bool, draw_weapon_names: bool = False) -> bool:
        try:
            self.health = self.memory_manager.read_int(self.pawn_ptr + self.memory_manager.m_iHealth)
            self.armor = self.memory_manager.read_int(self.pawn_ptr + self.memory_manager.m_ArmorValue)
            if self.health <= 0:
                return False
            self.dormant = bool(self.memory_manager.read_int(self.pawn_ptr + self.memory_manager.m_bDormant))
            if self.dormant:
                return False
            self.team = self.memory_manager.read_int(self.pawn_ptr + self.memory_manager.m_iTeamNum)
            self.pos = self.memory_manager.read_vec3(self.pawn_ptr + self.memory_manager.m_vOldOrigin)
            raw = self.memory_manager.read_string(self.controller_ptr + self.memory_manager.m_iszPlayerName)
            self.name = Utility.transliterate(raw)
            self.all_bones_pos_3d = self._all_bone_pos() if skeleton_enabled else None
            self.weapon_name = self.memory_manager.get_entity_weapon_name(self.pawn_ptr) if draw_weapon_names else ""
            
            # Read new status flags
            try:
                self.is_defusing = bool(self.memory_manager.pm.read_bytes(self.pawn_ptr + self.memory_manager.m_bIsDefusing, 1)[0])
            except Exception:
                self.is_defusing = False
                
            try:
                flashed = struct.unpack('f', self.memory_manager.pm.read_bytes(self.pawn_ptr + self.memory_manager.m_flFlashOverlayAlpha, 4))[0]
                self.is_flashed = flashed > 0.0
            except Exception:
                self.is_flashed = False
                
            try:
                self.is_scoped = bool(self.memory_manager.pm.read_bytes(self.pawn_ptr + self.memory_manager.m_bIsScoped, 1)[0])
            except Exception:
                self.is_scoped = False
                
            try:
                weapon_ptr = self.memory_manager.get_entity_weapon_ptr(self.pawn_ptr)
                if weapon_ptr:
                    self.is_reloading = bool(self.memory_manager.pm.read_bytes(weapon_ptr + self.memory_manager.m_bInReload, 1)[0])
                else:
                    self.is_reloading = False
            except Exception:
                self.is_reloading = False
                
            return True
        except Exception as exc:
            logger.debug("Entity update failed: %s", exc)
            return False

    def bone_pos(self, bone: int) -> Dict[str, float]:
        if self.all_bones_pos_3d and bone in self.all_bones_pos_3d:
            return self.all_bones_pos_3d[bone]
        try:
            scene = self.memory_manager.read_longlong(self.pawn_ptr + self.memory_manager.m_pGameSceneNode)
            arr = self.memory_manager.read_longlong(scene + self.memory_manager.m_pBoneArray)
            return self.memory_manager.read_vec3(arr + bone * 32)
        except Exception as exc:
            logger.debug("Failed to get bone %d: %s", bone, exc)
            return {"x": 0.0, "y": 0.0, "z": 0.0}

    def _all_bone_pos(self) -> Optional[Dict[int, Dict[str, float]]]:
        try:
            scene = self.memory_manager.read_longlong(self.pawn_ptr + self.memory_manager.m_pGameSceneNode)
            arr = self.memory_manager.read_longlong(scene + self.memory_manager.m_pBoneArray)
            if not arr:
                return None
            data = self.memory_manager.pm.read_bytes(arr, (MAX_BONE_ID + 1) * 32)
            if not data:
                return None
            result = {}
            for i in ALL_BONE_IDS:
                try:
                    x, y, z = struct.unpack_from("fff", data, i * 32)
                    result[i] = {"x": x, "y": y, "z": z}
                except struct.error:
                    continue
            return result
        except Exception as exc:
            logger.debug("Failed to get all bone positions: %s", exc)
            return None

    @staticmethod
    def validate_screen_position(pos: Dict[str, float]) -> bool:
        return (
            0 <= pos["x"] <= overlay.get_screen_width()
            and 0 <= pos["y"] <= overlay.get_screen_height()
        )

class CS2Overlay(BaseFeature):
    def __init__(self, memory_manager: MemoryManager) -> None:
        super().__init__(memory_manager)
        self.config = ConfigManager.load_config()
        self.local_team: Optional[int] = None
        self.screen_width = overlay.get_screen_width()
        self.screen_height = overlay.get_screen_height()
        self.load_configuration()

    def load_configuration(self) -> None:
        s = self.config["Overlay"]
        self.enable_box = s["enable_box"]
        self.enable_skeleton = s.get("enable_skeleton", True)
        self.draw_snaplines = s["draw_snaplines"]
        self.snaplines_color_hex = s["snaplines_color_hex"]
        self.box_line_thickness = s["box_line_thickness"]
        self.box_color_hex = s["box_color_hex"]
        self.text_color_hex = s["text_color_hex"]
        self.draw_bomb_timer = s.get("draw_bomb_timer", False)
        self.bomb_timer_position = s.get("bomb_timer_position", "Center-Left")
        self.draw_health_numbers = s["draw_health_numbers"]
        self.draw_nicknames = s["draw_nicknames"]
        self.draw_weapon_names = s.get("draw_weapon_names", True)
        self.weapon_color_hex = s.get("weapon_color_hex", "#FFFFFF")
        self.draw_armor = s.get("draw_armor", True)
        self.draw_teammates = s["draw_teammates"]
        self.teammate_color_hex = s["teammate_color_hex"]
        self.target_fps = int(s["target_fps"])
        self.draw_scoped = s.get("draw_scoped", False)
        self.draw_reloading = s.get("draw_reloading", False)
        self.draw_flashed = s.get("draw_flashed", False)
        self.draw_defusing = s.get("draw_defusing", False)
        self.draw_distance = s.get("draw_distance", False)
        self._resolve_colors()

    def update_config(self, config: dict) -> None:
        self.config = config
        self.load_configuration()
        logger.debug("Overlay configuration updated.")

    def start(self) -> None:
        self.is_running = True
        # Clear here so stop() can always set it reliably.
        self.stop_event.clear()

        try:
            overlay.overlay_init("Counter-Strike 2", fps=0)
            try:
                font_path = Utility.resource_path("assets/fonts/RobotoCondensed-Bold.ttf")
                self.custom_font = overlay.load_font(font_path, 1)
            except Exception:
                self.custom_font = None
        except Exception as exc:
            Logger.error_code(EC.E3005, "%s", exc)
            self.is_running = False
            return

        sleep = time.sleep

        while not self.stop_event.is_set():
            frame_time = 1.0 / max(self.target_fps, 1)
            start = time.time()
            try:
                game_active = is_game_active()

                if game_active:
                    vm = self.memory_manager.read_floats(
                        self.memory_manager.client_dll_base + self.memory_manager.dwViewMatrix, 16
                    )
                    local_ctrl = self.memory_manager.read_longlong(
                        self.memory_manager.client_dll_base + self.memory_manager.dwLocalPlayerController
                    )
                    local_ping = 0
                    local_pos = None
                    if local_ctrl:
                        local_pawn = self.memory_manager.read_longlong(
                            self.memory_manager.client_dll_base + self.memory_manager.dwLocalPlayerPawn
                        )
                        self.local_team = (
                            self.memory_manager.read_int(local_pawn + self.memory_manager.m_iTeamNum)
                            if local_pawn else None
                        )
                        try:
                            local_ping = self.memory_manager.read_int(local_ctrl + self.memory_manager.m_iPing)
                        except Exception:
                            local_ping = 0
                        try:
                            local_pos = self.memory_manager.read_vec3(local_pawn + self.memory_manager.m_vOldOrigin) if local_pawn else None
                        except Exception:
                            local_pos = None
                    else:
                        self.local_team = None
                    self.local_pos = local_pos
                    entities = list(self._iterate_entities(local_ctrl))
                else:
                    entities = []

                if overlay.overlay_loop():
                    overlay.begin_drawing()
                    if game_active:
                        self._draw_watermark(local_ping)
                        self._draw_bomb_timer()
                        for ent in entities:
                            is_teammate = self.local_team is not None and ent.team == self.local_team
                            if is_teammate and not self.draw_teammates:
                                continue
                            self._draw_entity(ent, vm, is_teammate)
                    overlay.end_drawing()

                elapsed = time.time() - start
                slack = frame_time - elapsed
                if slack > 0:
                    sleep(slack)

            except Exception:
                Logger.error_code(EC.E3006, exc_info=True)
                sleep(MAIN_LOOP_SLEEP)

        overlay.overlay_close()
        logger.debug("Overlay loop ended.")

    def stop(self) -> None:
        self.is_running = False
        self.stop_event.set()
        time.sleep(0.1)
        logger.debug("Overlay stopped.")

    def _resolve_colors(self) -> None:
        try:
            self._color_box        = overlay.get_color(self.box_color_hex)
            self._color_teammate   = overlay.get_color(self.teammate_color_hex)
            self._color_text       = overlay.get_color(self.text_color_hex)
            self._color_weapon     = overlay.get_color(self.weapon_color_hex)
            self._color_snapline   = overlay.get_color(self.snaplines_color_hex)
            self._color_health_bg  = overlay.get_color("black")
            self._color_health_low = overlay.get_color("red")
            self._color_health_mid = overlay.get_color("yellow")
            self._color_health_ok  = overlay.get_color("green")
            self._color_panel_bg   = overlay.fade_color(overlay.get_color("#1A1A1A"), 0.72)
            self._color_panel_border = overlay.fade_color(overlay.get_color("#606060"), 0.82)
        except Exception:
            self._color_box = self._color_teammate = self._color_text = self._color_weapon = None
            self._color_snapline = self._color_health_bg = None
            self._color_health_low = self._color_health_mid = self._color_health_ok = None
            self._color_panel_bg = self._color_panel_border = None

    def _world_to_screen(self, vm: list, pos: dict) -> dict | None:
        sx = overlay.get_screen_width() / 2
        sy = overlay.get_screen_height() / 2
        w = vm[12]*pos["x"] + vm[13]*pos["y"] + vm[14]*pos["z"] + vm[15]
        if w < 0.1:
            return None
            
        x = vm[0]*pos["x"] + vm[1]*pos["y"] + vm[2]*pos["z"] + vm[3]
        y = vm[4]*pos["x"] + vm[5]*pos["y"] + vm[6]*pos["z"] + vm[7]
        
        ndc_x = x / w
        ndc_y = y / w
        
        screen_x = sx * ndc_x + sx
        screen_y = -sy * ndc_y + sy
        
        return {"x": screen_x, "y": screen_y, "z": w}

    def _iterate_entities(self, local_ctrl: int) -> Iterator[Entity]:
        try:
            ent_list = self.memory_manager.read_longlong(
                self.memory_manager.client_dll_base + self.memory_manager.dwEntityList
            )
        except Exception as exc:
            logger.debug("Error reading entity list: %s", exc)
            return

        for i in range(1, ENTITY_COUNT + 1):
            try:
                list_idx = (i & 0x7FFF) >> 9
                ent_idx = i & 0x1FF
                entry = self.memory_manager.read_longlong(ent_list + (8 * list_idx) + 16)
                if not entry:
                    continue
                ctrl = self.memory_manager.read_longlong(entry + ENTITY_ENTRY_SIZE * ent_idx)
                if not ctrl or ctrl == local_ctrl:
                    continue
                ctrl_pawn = self.memory_manager.read_longlong(ctrl + self.memory_manager.m_hPlayerPawn)
                if not ctrl_pawn:
                    continue
                list_entry = self.memory_manager.read_longlong(
                    ent_list + 8 * ((ctrl_pawn & 0x7FFF) >> 9) + 16
                )
                if not list_entry:
                    continue
                pawn = self.memory_manager.read_longlong(
                    list_entry + ENTITY_ENTRY_SIZE * (ctrl_pawn & 0x1FF)
                )
                if not pawn:
                    continue
                ent = Entity(ctrl, pawn, self.memory_manager)
                if ent.update(self.enable_skeleton, self.draw_weapon_names):
                    yield ent
            except Exception as exc:
                logger.debug("Failed to read entity %d: %s", i, exc)

    def _draw_watermark(self, ping: int = 0) -> None:
        text = f"VioletWing | {overlay.get_fps()} fps, {ping} ms"
        size = 16
        pad_x, pad_y = 8, 5
        w = overlay.measure_text(text, size)
        sw = overlay.get_screen_width()
        fw = w + pad_x * 2
        fh = size + pad_y * 2
        fx = sw - fw - 10
        fy = 8
        overlay.draw_rectangle(fx, fy, fw, fh, self._color_panel_bg)
        overlay.draw_rectangle_lines(fx, fy, fw, fh, self._color_panel_border, 1)
        overlay.draw_text(text, fx + pad_x, fy + pad_y, size, self._color_text)

    def _draw_bomb_timer(self) -> None:
        if not self.draw_bomb_timer:
            return

        bomb_info = self.memory_manager.get_bomb_info()
        if not bomb_info or not bomb_info["is_planted"]:
            return

        curtime = bomb_info["curtime"]
        
        if bomb_info["is_defusing"]:
            time_left = max(0.0, bomb_info["defuse_countdown"] - curtime)
            action_text = "Defusing"
        else:
            time_left = max(0.0, bomb_info["blow_time"] - curtime)
            action_text = "C4"

        if bomb_info["is_defused"]:
            text = f"[ BOMB DEFUSED ] Site {bomb_info['bomb_site']}"
            color = self._color_health_ok
        elif bomb_info["has_exploded"] or (time_left <= 0 and not bomb_info["is_defusing"]):
            text = f"[ BOMB EXPLODED ] Site {bomb_info['bomb_site']}"
            color = self._color_health_low
        else:
            if bomb_info["is_defusing"]:
                text = f"[ DEFUSING ] Site {bomb_info['bomb_site']} | {time_left:.1f}s left"
                color = overlay.get_color("#7FC6FF") # Brighter blue for defusing
            else:
                if time_left < 5.0:
                    text = f"[ RUN! ] Site {bomb_info['bomb_site']} | {time_left:.1f}s"
                    color = self._color_health_low
                elif time_left < 10.0:
                    text = f"[ NO TIME W/O KIT ] Site {bomb_info['bomb_site']} | {time_left:.1f}s"
                    color = self._color_health_mid
                else:
                    text = f"[ C4 PLANTED ] Site {bomb_info['bomb_site']} | {time_left:.1f}s"
                    color = overlay.get_color("white")

        size = 18
        pad_x, pad_y = 12, 8
        w = overlay.measure_text(text, size)
        sw = overlay.get_screen_width()
        sh = overlay.get_screen_height()
        fw = w + pad_x * 2
        fh = size + pad_y * 2
        
        pos = getattr(self, "bomb_timer_position", "Center-Left")
        if pos == "Center-Left":
            fx = 20
            fy = sh / 2 - fh / 2
        elif pos == "Center-Right":
            fx = sw - fw - 20
            fy = sh / 2 - fh / 2
        elif pos == "Center-Top":
            fx = sw / 2 - fw / 2
            fy = 20
        elif pos == "Center-Bottom":
            fx = sw / 2 - fw / 2
            fy = sh - fh - 20
        else:
            fx = 20
            fy = sh / 2 - fh / 2
        
        overlay.draw_rectangle(fx, fy, fw, fh, self._color_panel_bg)
        overlay.draw_rectangle_lines(fx, fy, fw, fh, self._color_panel_border, 1)
        
        # Draw the text manually to handle custom font for bomb timer if available
        if getattr(self, "custom_font", None):
            overlay.draw_font(self.custom_font, text, fx + pad_x, fy + pad_y, size, 1.0, color)
        else:
            overlay.draw_text(text, fx + pad_x, fy + pad_y, size, color)

    def _draw_skeleton(self, ent: Entity, vm: list, color: tuple) -> None:
        if not ent.all_bones_pos_3d:
            return
        try:
            pts: Dict[int, Dict[str, float]] = {}
            for bid in ALL_BONE_IDS:
                if bid in ent.all_bones_pos_3d:
                    p2 = self._world_to_screen(vm, ent.all_bones_pos_3d[bid])
                    if p2 and ent.validate_screen_position(p2):
                        pts[bid] = p2
            for start, ends in SKELETON_BONES.items():
                if start in pts:
                    for end in ends:
                        if end in pts:
                            overlay.draw_line(pts[start]["x"], pts[start]["y"],
                                              pts[end]["x"], pts[end]["y"], color, 1.5)
        except Exception as exc:
            logger.error("Error drawing skeleton: %s", exc)

    def _draw_custom_text(self, text: str, x: float, y: float, size: int, color: tuple) -> None:
        if getattr(self, "custom_font", None):
            overlay.draw_font(self.custom_font, text, x, y, size, 1.0, color)
        else:
            overlay.draw_text(text, x, y, size, color)

    def _measure_custom_text(self, text: str, size: int) -> float:
        if getattr(self, "custom_font", None):
            try:
                # pyMeow doesn't easily expose measure_font, so fallback to default measure_text
                # It's usually close enough for horizontal centering.
                return overlay.measure_text(text, size)
            except Exception:
                return overlay.measure_text(text, size)
        else:
            return overlay.measure_text(text, size)

    def _draw_entity(self, ent: Entity, vm: list, is_teammate: bool = False) -> None:
        try:
            head3d = ent.bone_pos(7)
            pos2d = self._world_to_screen(vm, ent.pos)
            head2d = self._world_to_screen(vm, head3d)
            if pos2d is None or head2d is None:
                return
            if not ent.validate_screen_position(pos2d) or not ent.validate_screen_position(head2d):
                return

            ent.pos2d = pos2d
            ent.head_pos2d = head2d

            h = pos2d["y"] - head2d["y"]
            w = h / 2
            hw = w / 2
            
            top_left = {"x": head2d["x"] - hw, "y": head2d["y"] - hw / 2}
            bottom_right = {"x": head2d["x"] + hw, "y": head2d["y"] + h}
            
            color = self._color_teammate if is_teammate else self._color_box

            if self.draw_snaplines:
                self._render_player_tracers(head2d)

            if self.enable_box:
                self._render_player_box(top_left, bottom_right, color)

            if self.enable_skeleton and ent.all_bones_pos_3d:
                self._draw_skeleton(ent, vm, color)

            self._render_player_bars(ent, top_left, bottom_right)
            self._render_player_flags(ent, top_left, bottom_right, color)
        except Exception as exc:
            logger.debug("Error drawing entity: %s", exc)

    def _render_player_box(self, tl: dict, br: dict, color: tuple) -> None:
        width = br["x"] - tl["x"]
        height = br["y"] - tl["y"]
        overlay.draw_rectangle_lines(tl["x"], tl["y"], width, height, color, self.box_line_thickness)

    def _render_player_bars(self, ent: Entity, tl: dict, br: dict) -> None:
        bg_color = overlay.get_color("black")
        
        # Health Bar
        if self.draw_health_numbers: # Using this toggle for health bar for now
            x_start = tl["x"] - 6
            x_end = x_start + 2
            y_start = tl["y"]
            y_end = br["y"]
            height = y_end - y_start
            
            pct = max(0, min(ent.health, 100))
            filled_height = height * (pct / 100.0)
            
            overlay.draw_rectangle(x_start - 1, y_start - 1, 4, height + 2, bg_color)
            overlay.draw_rectangle(x_start, y_end - filled_height, 2, filled_height, overlay.get_color("#64FF64"))
            
            if pct < 100:
                txt = str(ent.health)
                fs = 10
                tw = self._measure_custom_text(txt, fs)
                # Centered over the health bar unfilled space
                self._draw_custom_text(txt, (x_start + x_end) / 2 - tw / 2, y_end - filled_height - fs / 2 - 4, fs, self._color_text)

        # Armor Bar
        if getattr(self, "draw_armor", False):
            y_start = br["y"] + 4
            y_end = y_start + 2
            x_start = tl["x"]
            x_end = br["x"]
            width = x_end - x_start
            
            pct_armor = max(0, min(ent.armor, 100))
            filled_width = width * (pct_armor / 100.0)
            
            overlay.draw_rectangle(x_start - 1, y_start - 1, width + 2, 4, bg_color)
            overlay.draw_rectangle(x_start, y_start, filled_width, 2, overlay.get_color("#9696FF"))

    def _render_player_flags(self, ent: Entity, tl: dict, br: dict, color: tuple) -> None:
        if self.draw_nicknames:
            name = f"{ent.name} (Bot)" if getattr(ent, "is_bot", False) else ent.name
            fs = 12
            nw = self._measure_custom_text(name, fs)
            self._draw_custom_text(name, (tl["x"] + br["x"]) / 2 - nw / 2, tl["y"] - 20, fs, self._color_text)

        if self.draw_weapon_names and ent.weapon_name:
            fs = 12
            ww = self._measure_custom_text(ent.weapon_name, fs)
            # Offset by 10 below if armor is drawn, else 6
            y_offset = br["y"] + (10 if getattr(self, "draw_armor", False) else 6)
            self._draw_custom_text(ent.weapon_name, (tl["x"] + br["x"]) / 2 - ww / 2, y_offset, fs, getattr(self, "_color_weapon", self._color_text))

        if self.draw_distance:
            local_pos = getattr(self, "local_pos", None)
            if local_pos and ent.pos:
                dx = local_pos["x"] - ent.pos["x"]
                dy = local_pos["y"] - ent.pos["y"]
                dz = local_pos["z"] - ent.pos["z"]
                dist_m = ((dx*dx + dy*dy + dz*dz) ** 0.5) / 52.49
                dist_text = f"{dist_m:.0f}m"
                fs = 11
                dw = self._measure_custom_text(dist_text, fs)
                y_base = br["y"] + (10 if getattr(self, "draw_armor", False) else 6)
                if self.draw_weapon_names and ent.weapon_name:
                    y_base += 14
                self._draw_custom_text(dist_text, (tl["x"] + br["x"]) / 2 - dw / 2, y_base, fs, self._color_text)
            
        # Draw status flags on the right side of the box
        flags = []
        if getattr(self, "draw_scoped", False) and ent.is_scoped:
            flags.append(("[Scoped]", overlay.get_color("#4A90E2")))
        if getattr(self, "draw_flashed", False) and ent.is_flashed:
            flags.append(("[Flashed]", overlay.get_color("white")))
        if getattr(self, "draw_reloading", False) and ent.is_reloading:
            flags.append(("[Reloading]", overlay.get_color("#4A90E2")))
        if getattr(self, "draw_defusing", False) and ent.is_defusing:
            flags.append(("[Defusing]", overlay.get_color("#E24A4A")))
            
        if flags:
            fs = 10
            x_offset = br["x"] + 4
            y_offset = tl["y"]
            for flag_text, flag_color in flags:
                self._draw_custom_text(flag_text, x_offset, y_offset, fs, flag_color)
                y_offset += fs + 2

    def _render_player_tracers(self, head2d: dict) -> None:
        screen_w = overlay.get_screen_width()
        screen_h = overlay.get_screen_height()
        overlay.draw_line(screen_w / 2, screen_h / 2,
                          head2d["x"], head2d["y"], self._color_snapline, 2)