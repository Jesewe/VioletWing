import struct
import time
from typing import Dict, Iterator, Optional

import pyMeow as overlay
from pynput.keyboard import Listener as KeyboardListener

from classes.base_feature import BaseFeature
from classes.config_manager import ConfigManager, Colors, COLOR_CHOICES
from classes.game_process import is_game_active
from classes.logger import Logger
import classes.error_codes as EC
from classes.memory_manager import MemoryManager
from classes.utility import Utility

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
        self.team: int = -1
        self.pos: Dict[str, float] = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.dormant: bool = True
        self.all_bones_pos_3d: Optional[Dict[int, Dict[str, float]]] = None

    def update(self, use_transliteration: bool, skeleton_enabled: bool) -> bool:
        try:
            self.health = self.memory_manager.read_int(self.pawn_ptr + self.memory_manager.m_iHealth)
            if self.health <= 0:
                return False
            self.dormant = bool(self.memory_manager.read_int(self.pawn_ptr + self.memory_manager.m_bDormant))
            if self.dormant:
                return False
            self.team = self.memory_manager.read_int(self.pawn_ptr + self.memory_manager.m_iTeamNum)
            self.pos = self.memory_manager.read_vec3(self.pawn_ptr + self.memory_manager.m_vOldOrigin)
            raw = self.memory_manager.read_string(self.controller_ptr + self.memory_manager.m_iszPlayerName)
            self.name = Utility.transliterate(raw) if use_transliteration else raw
            self.all_bones_pos_3d = self._all_bone_pos() if skeleton_enabled else None
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
        self.draw_health_numbers = s["draw_health_numbers"]
        self.use_transliteration = s["use_transliteration"]
        self.draw_nicknames = s["draw_nicknames"]
        self.draw_teammates = s["draw_teammates"]
        self.teammate_color_hex = s["teammate_color_hex"]
        self.target_fps = int(s["target_fps"])
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
        except Exception as exc:
            Logger.error_code(EC.E3005, "%s", exc)
            self.is_running = False
            return

        sleep = time.sleep

        while not self.stop_event.is_set():
            frame_time = 1.0 / max(self.target_fps, 1)
            start = time.time()
            try:
                if not is_game_active():
                    sleep(MAIN_LOOP_SLEEP)
                    continue

                vm = self.memory_manager.read_floats(
                    self.memory_manager.client_dll_base + self.memory_manager.dwViewMatrix, 16
                )
                local_ctrl = self.memory_manager.read_longlong(
                    self.memory_manager.client_dll_base + self.memory_manager.dwLocalPlayerController
                )
                if local_ctrl:
                    local_pawn = self.memory_manager.read_longlong(
                        self.memory_manager.client_dll_base + self.memory_manager.dwLocalPlayerPawn
                    )
                    self.local_team = (
                        self.memory_manager.read_int(local_pawn + self.memory_manager.m_iTeamNum)
                        if local_pawn else None
                    )
                else:
                    self.local_team = None

                entities = list(self._iterate_entities(local_ctrl))

                if overlay.overlay_loop():
                    overlay.begin_drawing()
                    self._draw_watermark()
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
            self._color_snapline   = overlay.get_color(self.snaplines_color_hex)
            self._color_health_bg  = overlay.get_color("black")
            self._color_health_low = overlay.get_color("red")
            self._color_health_mid = overlay.get_color("yellow")
            self._color_health_ok  = overlay.get_color("green")
            self._color_panel_bg   = overlay.fade_color(overlay.get_color("#1A1A1A"), 0.72)
            self._color_panel_border = overlay.fade_color(overlay.get_color("#606060"), 0.82)
        except Exception:
            self._color_box = self._color_teammate = self._color_text = None
            self._color_snapline = self._color_health_bg = None
            self._color_health_low = self._color_health_mid = self._color_health_ok = None
            self._color_panel_bg = self._color_panel_border = None

    def _world_to_screen(self, vm: list, pos: dict) -> dict | None:
        sx = overlay.get_screen_width() / 2
        sy = overlay.get_screen_height() / 2
        w = vm[12]*pos["x"] + vm[13]*pos["y"] + vm[14]*pos["z"] + vm[15]
        if w <= 0.01:
            return None
        x = sx + (vm[0]*pos["x"] + vm[1]*pos["y"] + vm[2]*pos["z"] + vm[3]) / w * sx
        y = sy - (vm[4]*pos["x"] + vm[5]*pos["y"] + vm[6]*pos["z"] + vm[7]) / w * sy
        return {"x": x, "y": y}

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
                if ent.update(self.use_transliteration, self.enable_skeleton):
                    yield ent
            except Exception as exc:
                logger.debug("Failed to read entity %d: %s", i, exc)

    def _draw_watermark(self) -> None:
        text = f"VioletWing | {overlay.get_fps()}"
        size = 14
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
            color = self._color_teammate if is_teammate else self._color_box

            if self.enable_skeleton and ent.all_bones_pos_3d:
                self._draw_skeleton(ent, vm, color)

            if self.draw_snaplines:
                overlay.draw_line(
                    self.screen_width / 2, self.screen_height / 2,
                    head2d["x"], head2d["y"], self._color_snapline, 2,
                )

            if self.enable_box:
                overlay.draw_rectangle(
                    head2d["x"] - hw, head2d["y"] - hw / 2, w, h + hw / 2, Colors.grey
                )
                overlay.draw_rectangle_lines(
                    head2d["x"] - hw, head2d["y"] - hw / 2, w, h + hw / 2,
                    color, self.box_line_thickness,
                )

            if self.draw_nicknames:
                fs = 11
                nw = overlay.measure_text(ent.name, fs)
                overlay.draw_text(ent.name, head2d["x"] - nw // 2,
                                  head2d["y"] - hw / 2 - 15, fs, self._color_text)

            bar_w, bar_m = 4, 2
            bx = head2d["x"] - hw - bar_w - bar_m
            by = head2d["y"] - hw / 2
            bh = h + hw / 2
            overlay.draw_rectangle(bx, by, bar_w, bh, self._color_health_bg)
            pct = max(0, min(ent.health, 100))
            fill_h = (pct / 100.0) * bh
            fill_color = (
                self._color_health_low if pct <= 20
                else self._color_health_mid if pct <= 50
                else self._color_health_ok
            )
            overlay.draw_rectangle(bx, by + (bh - fill_h), bar_w, fill_h, fill_color)

            if self.draw_health_numbers:
                overlay.draw_text(
                    str(ent.health), int(bx - 25), int(by + bh / 2 - 5),
                    10, self._color_text,
                )
        except Exception as exc:
            logger.debug("Error drawing entity: %s", exc)