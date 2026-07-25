"""
Lackluster Shot Queue Node v2
Adds a dedicated camera-preset queue that can hold up to 10 shots and emit them
sequentially for ComfyUI execution.
"""

from __future__ import annotations

import json
import math
import os
from typing import Any

CAMERA_PRESETS = [
    "front_close_up",
    "front_medium",
    "front_wide",
    "low_angle_hero",
    "low_angle_close_up",
    "high_angle_shot",
    "over_shoulder",
    "right_profile",
    "back_view",
    "left_profile",
    "three_quarter_front",
    "dutch_angle",
    "aerial_shot",
    "extreme_close_up",
    "cowboy_shot",
]

PRESET_DISPLAY_NAMES = {
    "front_close_up": "Front Close-Up",
    "front_medium": "Front Medium Shot",
    "front_wide": "Front Wide Shot",
    "low_angle_hero": "Low Angle Hero Shot",
    "low_angle_close_up": "Low Angle Close-Up",
    "high_angle_shot": "High Angle Shot",
    "over_shoulder": "Over Shoulder",
    "right_profile": "Right Profile",
    "back_view": "Back View",
    "left_profile": "Left Profile",
    "three_quarter_front": "Three-Quarter Front",
    "dutch_angle": "Dutch Angle",
    "aerial_shot": "Aerial Shot",
    "extreme_close_up": "Extreme Close-Up",
    "cowboy_shot": "Cowboy Shot",
}

PRESET_VALUES = {
    "front_close_up": {"azimuth": 0, "elevation": 0, "distance": 8.0},
    "front_medium": {"azimuth": 0, "elevation": 0, "distance": 4.0},
    "front_wide": {"azimuth": 0, "elevation": 0, "distance": 1.0},
    "low_angle_hero": {"azimuth": 0, "elevation": -30, "distance": 4.0},
    "low_angle_close_up": {"azimuth": 0, "elevation": -30, "distance": 8.0},
    "high_angle_shot": {"azimuth": 0, "elevation": 60, "distance": 4.0},
    "over_shoulder": {"azimuth": 45, "elevation": 0, "distance": 5.0},
    "right_profile": {"azimuth": 90, "elevation": 0, "distance": 5.0},
    "back_view": {"azimuth": 180, "elevation": 0, "distance": 5.0},
    "left_profile": {"azimuth": 270, "elevation": 0, "distance": 5.0},
    "three_quarter_front": {"azimuth": 315, "elevation": 0, "distance": 5.0},
    "dutch_angle": {"azimuth": 0, "elevation": -15, "distance": 4.0},
    "aerial_shot": {"azimuth": 0, "elevation": 60, "distance": 2.0},
    "extreme_close_up": {"azimuth": 0, "elevation": 0, "distance": 10.0},
    "cowboy_shot": {"azimuth": 0, "elevation": -10, "distance": 4.0},
}

_SCENE_CENTER_Y = 0.5
MAX_QUEUE_SIZE = 10


def build_camera_info(azimuth: float, elevation: float, distance: float) -> dict[str, Any]:
    az_rad = math.radians(azimuth)
    el_rad = math.radians(elevation)
    visual_dist = 2.6 - (distance / 10.0) * 2.0

    cam_x = visual_dist * math.sin(az_rad) * math.cos(el_rad)
    cam_y = _SCENE_CENTER_Y + visual_dist * math.sin(el_rad)
    cam_z = visual_dist * math.cos(az_rad) * math.cos(el_rad)

    return {
        "position": {"x": cam_x, "y": cam_y, "z": cam_z},
        "target": {"x": 0.0, "y": _SCENE_CENTER_Y, "z": 0.0},
        "zoom": 1,
        "cameraType": "perspective",
    }


def compute_angle_prompt(azimuth: float, elevation: float, distance: float, prefix: str = "<sks>") -> str:
    h_angle = int(azimuth) % 360

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

    if elevation < -15:
        v_direction = "low-angle shot"
    elif elevation < 15:
        v_direction = "eye-level shot"
    elif elevation < 45:
        v_direction = "elevated shot"
    else:
        v_direction = "high-angle shot"

    if distance < 2:
        dist_label = "wide shot"
    elif distance < 6:
        dist_label = "medium shot"
    else:
        dist_label = "close-up"

    prefix_clean = prefix.strip() if prefix and prefix.strip() else ""
    if prefix_clean:
        return f"{prefix_clean} {h_direction} {v_direction} {dist_label}"
    return f"{h_direction} {v_direction} {dist_label}"


class LacklusterShotQueueNodeV2:
    """
    Queue camera presets up to 10 shots and emit them sequentially.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "camera_preset": (CAMERA_PRESETS, {"default": "front_medium"}),
                "add_to_queue": ("BOOLEAN", {"default": False, "tooltip": "Add the selected preset to the queue"}),
                "run_queue": ("BOOLEAN", {"default": False, "tooltip": "Execute every queued shot sequentially"}),
                "clear_queue": ("BOOLEAN", {"default": False, "tooltip": "Clear all queued shots"}),
                "custom_prefix": ("STRING", {"default": "<sks>", "tooltip": "Prefix for each generated prompt"}),
            },
            "optional": {
                "sequence_json": ("STRING", {"default": "[]", "multiline": True, "tooltip": "JSON array of queued shots"}),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("STRING", "STRING", "LOAD_3D_CAMERA", "INT")
    RETURN_NAMES = ("prompts", "prompt_text", "camera_info", "queue_count")
    OUTPUT_IS_LIST = (True, False, True, False)
    FUNCTION = "execute"
    CATEGORY = "Lackluster/Camera"
    OUTPUT_NODE = True

    def execute(
        self,
        camera_preset="front_medium",
        add_to_queue=False,
        run_queue=False,
        clear_queue=False,
        custom_prefix="<sks>",
        sequence_json="[]",
        unique_id="shot_queue_v2",
    ):
        items = []
        if sequence_json and sequence_json.strip():
            try:
                parsed = json.loads(sequence_json)
                if isinstance(parsed, list):
                    items = parsed
            except Exception as exc:
                print(f"[LacklusterShotQueueV2] Warning: Could not parse sequence_json: {exc}")

        if clear_queue:
            items = []

        if add_to_queue and camera_preset in PRESET_VALUES:
            preset_values = PRESET_VALUES[camera_preset]
            prompt = compute_angle_prompt(
                preset_values["azimuth"],
                preset_values["elevation"],
                preset_values["distance"],
                prefix=custom_prefix,
            )
            if len(items) >= MAX_QUEUE_SIZE:
                prompts_list = []
                camera_infos_list = []
                for item in items:
                    az = item.get("azimuth", 0)
                    el = item.get("elevation", 0)
                    dist = item.get("distance", 5.0)
                    prompt_item = item.get("prompt", "")
                    if not prompt_item:
                        prompt_item = compute_angle_prompt(az, el, dist, prefix=custom_prefix)
                    prompts_list.append(prompt_item)
                    camera_infos_list.append(build_camera_info(az, el, dist))

                prompt_text = "\n".join(prompts_list)
                count = len(prompts_list)
                updated_json = json.dumps(items)
                return {
                    "ui": {
                        "sequence_json": updated_json,
                        "queue_count": count,
                        "queue_items": items,
                    },
                    "result": (prompts_list, prompt_text, camera_infos_list, count),
                }

            new_item = {
                "id": os.urandom(4).hex(),
                "preset": camera_preset,
                "azimuth": preset_values["azimuth"],
                "elevation": preset_values["elevation"],
                "distance": preset_values["distance"],
                "prompt": prompt,
                "label": PRESET_DISPLAY_NAMES.get(camera_preset, camera_preset),
            }
            items.append(new_item)

        if not items:
            preset_values = PRESET_VALUES.get(camera_preset, PRESET_VALUES["front_medium"])
            prompt = compute_angle_prompt(
                preset_values["azimuth"],
                preset_values["elevation"],
                preset_values["distance"],
                prefix=custom_prefix,
            )
            items = [
                {
                    "id": os.urandom(4).hex(),
                    "preset": camera_preset,
                    "azimuth": preset_values["azimuth"],
                    "elevation": preset_values["elevation"],
                    "distance": preset_values["distance"],
                    "prompt": prompt,
                    "label": PRESET_DISPLAY_NAMES.get(camera_preset, camera_preset),
                }
            ]

        prompts_list = []
        camera_infos_list = []
        for item in items:
            az = item.get("azimuth", 0)
            el = item.get("elevation", 0)
            dist = item.get("distance", 5.0)
            prompt_item = item.get("prompt", "")
            if not prompt_item:
                prompt_item = compute_angle_prompt(az, el, dist, prefix=custom_prefix)
            prompts_list.append(prompt_item)
            camera_infos_list.append(build_camera_info(az, el, dist))

        prompt_text = "\n".join(prompts_list)
        count = len(prompts_list)
        updated_json = json.dumps(items)

        return {
            "ui": {
                "sequence_json": updated_json,
                "queue_count": count,
                "queue_items": items,
            },
            "result": (prompts_list, prompt_text, camera_infos_list, count),
        }


NODE_CLASS_MAPPINGS = {"LacklusterShotQueueNodeV2": LacklusterShotQueueNodeV2}
NODE_DISPLAY_NAME_MAPPINGS = {"LacklusterShotQueueNodeV2": "Lackluster-Shot Queue V2"}
