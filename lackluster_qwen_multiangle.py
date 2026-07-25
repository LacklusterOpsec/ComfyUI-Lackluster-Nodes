"""
Lackluster Qwen Multiangle Camera & Sequence Nodes
Provides 3D interactive camera angle control and sequential batch angle queuing for ComfyUI.
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

try:
    from .qwen_camera_glossary import (
        TARGET_LANGUAGE_OPTIONS,
        label_to_code,
        translate_camera_terms,
    )
except ImportError:
    from qwen_camera_glossary import (
        TARGET_LANGUAGE_OPTIONS,
        label_to_code,
        translate_camera_terms,
    )



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


class LacklusterQwenMultiangleCameraNode:
    """
    Single 3D Camera Angle Control Node
    Outputs formatted prompt and camera metadata for multi-angle generation.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "horizontal_angle": ("INT", {"default": 0, "min": 0, "max": 360, "step": 1, "tooltip": "Camera azimuth angle (0-360°)"}),
                "vertical_angle": ("INT", {"default": 0, "min": -30, "max": 60, "step": 1, "tooltip": "Camera elevation angle (-30° to 60°)"}),
                "zoom": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 10.0, "step": 0.1, "tooltip": "Camera distance (0=wide, 10=close-up)"}),
                "default_prompts": ("BOOLEAN", {"default": True}),
                "camera_view": ("BOOLEAN", {"default": False, "tooltip": "Toggle camera perspective preview"}),
            },
            "optional": {
                "image": ("IMAGE", {"tooltip": "Optional input image to display in 3D scene"}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STRING", "LOAD_3D_CAMERA")
    RETURN_NAMES = ("prompt", "camera_info")
    FUNCTION = "execute"
    CATEGORY = "Lackluster/Camera"
    OUTPUT_NODE = True

    def execute(
        self,
        horizontal_angle,
        vertical_angle,
        zoom,
        default_prompts=True,
        camera_view=False,
        image=None,
        unique_id="preview",
    ):
        h_angle = max(0, min(360, int(horizontal_angle)))
        v_angle = max(-30, min(60, int(vertical_angle)))
        z_val = max(0.0, min(10.0, float(zoom)))

        prompt = compute_angle_prompt(h_angle, v_angle, z_val, prefix="<sks>")
        camera_info = build_camera_info(h_angle, v_angle, z_val)

        ui_results = []
        if image is not None:
            try:
                prefix = f"lackluster_qwen_{unique_id}_"
                ui_results = ImageSaveHelper.save_images(
                    image[:1],
                    filename_prefix=prefix,
                    folder_type=FolderType.temp,
                    cls=None,
                    compress_level=1,
                )
            except Exception as e:
                print(f"[LacklusterQwenMultiangle] Error saving preview image: {e}")

        return {
            "ui": {"preview_images": ui_results},
            "result": (prompt, camera_info),
        }


class LacklusterQwenMultiangleSequenceNode:
    """
    3D Camera Angle Sequence & Batch Queue Node
    Queue up multiple angles in an interactive list to batch process sequentially in ComfyUI.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "output_mode": (["sequential_batch", "multiline_text"], {"default": "sequential_batch", "tooltip": "sequential_batch outputs a list triggering batch execution for each angle; multiline_text outputs concatenated prompts."}),
                "custom_prefix": ("STRING", {"default": "<sks>", "tooltip": "Prefix appended to each prompt (e.g. <sks>)"}),
                "horizontal_angle": ("INT", {"default": 0, "min": 0, "max": 360, "step": 1}),
                "vertical_angle": ("INT", {"default": 0, "min": -30, "max": 60, "step": 1}),
                "zoom": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 10.0, "step": 0.1}),
                "camera_view": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "sequence_json": ("STRING", {"default": "[]", "multiline": True, "tooltip": "JSON array of queued sequence angles"}),
                "image": ("IMAGE", {"tooltip": "Optional input image to display in 3D scene"}),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "LOAD_3D_CAMERA", "INT")
    RETURN_NAMES = ("prompts", "prompt_text", "camera_info", "sequence_count")
    OUTPUT_IS_LIST = (True, False, True, False)
    FUNCTION = "execute"
    CATEGORY = "Lackluster/Camera"
    OUTPUT_NODE = True

    def execute(
        self,
        output_mode="sequential_batch",
        custom_prefix="<sks>",
        horizontal_angle=0,
        vertical_angle=0,
        zoom=5.0,
        camera_view=False,
        sequence_json="[]",
        image=None,
        unique_id="sequence_preview",
    ):
        items = []
        if sequence_json and sequence_json.strip():
            try:
                parsed = json.loads(sequence_json)
                if isinstance(parsed, list):
                    items = parsed
            except Exception as e:
                print(f"[LacklusterQwenMultiangleSequence] Warning: Could not parse sequence_json: {e}")

        if not items:
            items = [{
                "azimuth": horizontal_angle,
                "elevation": vertical_angle,
                "distance": zoom,
            }]

        prompts_list = []
        camera_infos_list = []

        for item in items:
            az = item.get("azimuth", horizontal_angle)
            el = item.get("elevation", vertical_angle)
            dist = item.get("distance", zoom)

            p = compute_angle_prompt(az, el, dist, prefix=custom_prefix)
            cam = build_camera_info(az, el, dist)

            prompts_list.append(p)
            camera_infos_list.append(cam)

        prompt_text = "\n".join(prompts_list)
        count = len(prompts_list)

        ui_results = []
        if image is not None:
            try:
                prefix = f"lackluster_qwen_seq_{unique_id}_"
                ui_results = ImageSaveHelper.save_images(
                    image[:1],
                    filename_prefix=prefix,
                    folder_type=FolderType.temp,
                    cls=None,
                    compress_level=1,
                )
            except Exception as e:
                print(f"[LacklusterQwenMultiangleSequence] Error saving preview image: {e}")

        if output_mode == "multiline_text":
            return {
                "ui": {"preview_images": ui_results},
                "result": ([prompt_text], prompt_text, camera_infos_list, count),
            }

        return {
            "ui": {"preview_images": ui_results},
            "result": (prompts_list, prompt_text, camera_infos_list, count),
        }


class LacklusterQwenMultiangleCameraTranslateNode:
    """
    Camera Glossary Translation Node
    Translates camera/shot terms in prompts to target languages via maintained glossary.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "target_language": (TARGET_LANGUAGE_OPTIONS, {"default": TARGET_LANGUAGE_OPTIONS[0]}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "execute"
    CATEGORY = "Lackluster/Camera"

    def execute(self, prompt, target_language):
        lang_code = label_to_code(target_language)
        translated = translate_camera_terms(prompt or "", lang_code)
        return (translated,)


NODE_CLASS_MAPPINGS = {
    "LacklusterCameraNode": LacklusterQwenMultiangleCameraNode,
    "LacklusterCameraSequenceNode": LacklusterQwenMultiangleSequenceNode,
    "LacklusterCameraTranslateNode": LacklusterQwenMultiangleCameraTranslateNode,
    "LacklusterQwenMultiangleCameraNode": LacklusterQwenMultiangleCameraNode,
    "LacklusterQwenMultiangleSequenceNode": LacklusterQwenMultiangleSequenceNode,
    "LacklusterQwenMultiangleCameraTranslateNode": LacklusterQwenMultiangleCameraTranslateNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LacklusterCameraNode": "Lackluster-Camera",
    "LacklusterCameraSequenceNode": "Lackluster-Camera Sequence",
    "LacklusterCameraTranslateNode": "Lackluster-Camera Translate",
    "LacklusterQwenMultiangleCameraNode": "Lackluster-Camera",
    "LacklusterQwenMultiangleSequenceNode": "Lackluster-Camera Sequence",
    "LacklusterQwenMultiangleCameraTranslateNode": "Lackluster-Camera Translate",
}

