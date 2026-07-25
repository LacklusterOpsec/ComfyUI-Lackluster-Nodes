"""
Lackluster Shot Queue Node v2
Interactive 3D camera widget for selecting angles, queue up to 10 shots,
then run ComfyUI to execute each shot sequentially.

Inspired by LacklusterQwenMultiangleSequenceNode but uses the interactive
3D scene widget to pick camera angles instead of preset buttons.
"""

from __future__ import annotations

import json
import math
import os

try:
    from comfy_api.latest import FolderType
    from comfy_api.latest._ui import ImageSaveHelper
except ImportError:
    FolderType = None
    ImageSaveHelper = None

_SCENE_CENTER_Y = 0.5


def build_camera_info(horizontal_angle: int, vertical_angle: int, zoom: float) -> dict:
    az_rad = math.radians(horizontal_angle)
    el_rad = math.radians(vertical_angle)
    visual_dist = 2.6 - (zoom / 10.0) * 2.0

    cam_x = visual_dist * math.sin(az_rad) * math.cos(el_rad)
    cam_y = _SCENE_CENTER_Y + visual_dist * math.sin(el_rad)
    cam_z = visual_dist * math.cos(az_rad) * math.cos(el_rad)

    return {
        "position": {"x": cam_x, "y": cam_y, "z": cam_z},
        "target": {"x": 0.0, "y": _SCENE_CENTER_Y, "z": 0.0},
        "zoom": 1,
        "cameraType": "perspective",
    }


def compute_angle_prompt(
    horizontal_angle: int,
    vertical_angle: int,
    zoom: float,
    prefix: str = "<sks>",
) -> str:
    h_angle = horizontal_angle % 360

    if h_angle < 22.5 or h_angle >= 337.5:
        h_direction = "front view"
    elif h_angle < 67.5:
        h_direction = "front-right quarter view"
    elif h_angle < 112.5:
        h_direction = "right side view"
    elif h_angle < 157.5:
        h_direction = "back-right quarter view"
    elif h_angle < 202.5:
        h_direction = "back view"
    elif h_angle < 247.5:
        h_direction = "back-left quarter view"
    elif h_angle < 292.5:
        h_direction = "left side view"
    else:
        h_direction = "front-left quarter view"

    if vertical_angle < -15:
        v_direction = "low-angle shot"
    elif vertical_angle < 15:
        v_direction = "eye-level shot"
    elif vertical_angle < 45:
        v_direction = "elevated shot"
    else:
        v_direction = "high-angle shot"

    if zoom < 2:
        distance = "wide shot"
    elif zoom < 6:
        distance = "medium shot"
    else:
        distance = "close-up"

    prefix_clean = prefix.strip() if prefix and prefix.strip() else ""
    if prefix_clean:
        return f"{prefix_clean} {h_direction} {v_direction} {distance}"
    return f"{h_direction} {v_direction} {distance}"


class LacklusterShotQueueNode:
    """
    Shot Queue Node v2
    Use the interactive 3D scene to pick camera angles, add them to a queue (max 10),
    then run ComfyUI to execute all shots sequentially.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "horizontal_angle": ("INT", {"default": 0, "min": 0, "max": 360, "step": 1, "tooltip": "Camera azimuth angle (0-360°)"}),
                "vertical_angle": ("INT", {"default": 0, "min": -30, "max": 60, "step": 1, "tooltip": "Camera elevation angle (-30° to 60°)"}),
                "zoom": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 10.0, "step": 0.1, "tooltip": "Camera distance (0=wide, 10=close-up)"}),
                "camera_view": ("BOOLEAN", {"default": False, "tooltip": "Toggle camera perspective preview"}),
                "custom_prefix": ("STRING", {"default": "<sks>", "tooltip": "Prefix appended to each prompt"}),
            },
            "optional": {
                "sequence_json": ("STRING", {"default": "[]", "multiline": True, "tooltip": "JSON array of queued shots"}),
                "image": ("IMAGE", {"tooltip": "Optional input image to display in 3D scene"}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "LOAD_3D_CAMERA", "INT")
    RETURN_NAMES = ("prompts", "prompt_text", "camera_info", "queue_count")
    OUTPUT_IS_LIST = (True, False, True, False)
    FUNCTION = "execute"
    CATEGORY = "Lackluster/Camera"
    OUTPUT_NODE = True

    def execute(
        self,
        horizontal_angle=0,
        vertical_angle=0,
        zoom=5.0,
        camera_view=False,
        custom_prefix="<sks>",
        sequence_json="[]",
        image=None,
        unique_id="shot_queue",
    ):
        h_angle = max(0, min(360, int(horizontal_angle)))
        v_angle = max(-30, min(60, int(vertical_angle)))
        z_val = max(0.0, min(10.0, float(zoom)))

        items = []
        if sequence_json and sequence_json.strip():
            try:
                parsed = json.loads(sequence_json)
                if isinstance(parsed, list):
                    items = parsed
            except Exception as e:
                print(f"[LacklusterShotQueue] Warning: Could not parse sequence_json: {e}")

        if not items:
            items = [{
                "azimuth": h_angle,
                "elevation": v_angle,
                "distance": z_val,
            }]

        prompts_list = []
        camera_infos_list = []

        for item in items:
            az = item.get("azimuth", h_angle)
            el = item.get("elevation", v_angle)
            dist = item.get("distance", z_val)
            p = compute_angle_prompt(az, el, dist, prefix=custom_prefix)
            cam = build_camera_info(az, el, dist)
            prompts_list.append(p)
            camera_infos_list.append(cam)

        prompt_text = "\n".join(prompts_list)
        count = len(prompts_list)

        updated_json = json.dumps(items)

        ui_results = []
        if image is not None:
            try:
                prefix = f"lackluster_shotqueue_{unique_id}_"
                ui_results = ImageSaveHelper.save_images(
                    image[:1],
                    filename_prefix=prefix,
                    folder_type=FolderType.temp,
                    cls=None,
                    compress_level=1,
                )
            except Exception as e:
                print(f"[LacklusterShotQueue] Error saving preview image: {e}")

        return {
            "ui": {
                "preview_images": ui_results,
                "sequence_json": updated_json,
                "queue_count": count,
            },
            "result": (prompts_list, prompt_text, camera_infos_list, count),
        }


NODE_CLASS_MAPPINGS = {
    "LacklusterShotQueueNode": LacklusterShotQueueNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LacklusterShotQueueNode": "Lackluster-Shot Queue (v2 3D Widget)",
}