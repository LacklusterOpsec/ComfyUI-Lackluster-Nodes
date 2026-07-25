import importlib


def _load_node_module(module_name: str):
    try:
        return importlib.import_module("." + module_name, __package__)
    except Exception:
        return None


def _get_module_mapping(module, attr_name: str):
    if module is None:
        return {}
    return getattr(module, attr_name, {})


alltalk_module = _load_node_module("alltalk")
first_last_frame_selector_module = _load_node_module("first_last_frame_selector")
text_multiline_module = _load_node_module("text_multiline")
uv_outdated_module = _load_node_module("uv_outdated")
trap_prompt_generator_module = _load_node_module("trap_prompt_generator")
lackluster_prompt_enhancer_module = _load_node_module("lackluster_prompt_enhancer")
trap_prompt_generator2_module = _load_node_module("trap_prompt_generator2")
trap_style_selector_module = _load_node_module("trap_style_selector")
lackluster_qwen_multiangle_module = _load_node_module("lackluster_qwen_multiangle")
lackluster_cam_orbit_module = _load_node_module("lackluster_cam_orbit")
lackluster_shot_queue_module = _load_node_module("lackluster_shot_queue")
lackluster_shot_queue_v2_module = _load_node_module("lackluster_shot_queue_v2")

ALLTALK_NODE_CLASS_MAPPINGS = _get_module_mapping(alltalk_module, "NODE_CLASS_MAPPINGS")
ALLTALK_NODE_DISPLAY_NAMES = _get_module_mapping(alltalk_module, "NODE_DISPLAY_NAMES")
FRAME_SELECTOR_NODE_CLASS_MAPPINGS = _get_module_mapping(first_last_frame_selector_module, "NODE_CLASS_MAPPINGS")
FRAME_SELECTOR_NODE_DISPLAY_NAME_MAPPINGS = _get_module_mapping(first_last_frame_selector_module, "NODE_DISPLAY_NAME_MAPPINGS")
TEXT_MULTILINE_NODE_CLASS_MAPPINGS = _get_module_mapping(text_multiline_module, "NODE_CLASS_MAPPINGS")
TEXT_MULTILINE_NODE_DISPLAY_NAME_MAPPINGS = _get_module_mapping(text_multiline_module, "NODE_DISPLAY_NAME_MAPPINGS")
UV_OUTDATED_NODE_CLASS_MAPPINGS = _get_module_mapping(uv_outdated_module, "NODE_CLASS_MAPPINGS")
UV_OUTDATED_NODE_DISPLAY_NAME_MAPPINGS = _get_module_mapping(uv_outdated_module, "NODE_DISPLAY_NAME_MAPPINGS")
TRAP_NODE_CLASS_MAPPINGS = _get_module_mapping(trap_prompt_generator_module, "NODE_CLASS_MAPPINGS")
TRAP_NODE_DISPLAY_NAME_MAPPINGS = _get_module_mapping(trap_prompt_generator_module, "NODE_DISPLAY_NAME_MAPPINGS")
LACKLUSTER_PROMPT_ENHANCER_NODE_CLASS_MAPPINGS = _get_module_mapping(lackluster_prompt_enhancer_module, "NODE_CLASS_MAPPINGS")
LACKLUSTER_PROMPT_ENHANCER_NODE_DISPLAY_NAME_MAPPINGS = _get_module_mapping(lackluster_prompt_enhancer_module, "NODE_DISPLAY_NAME_MAPPINGS")
TRAP2_NODE_CLASS_MAPPINGS = _get_module_mapping(trap_prompt_generator2_module, "NODE_CLASS_MAPPINGS")
TRAP2_NODE_DISPLAY_NAME_MAPPINGS = _get_module_mapping(trap_prompt_generator2_module, "NODE_DISPLAY_NAME_MAPPINGS")
TRAP_STYLE_SELECTOR_NODE_CLASS_MAPPINGS = _get_module_mapping(trap_style_selector_module, "NODE_CLASS_MAPPINGS")
TRAP_STYLE_SELECTOR_NODE_DISPLAY_NAME_MAPPINGS = _get_module_mapping(trap_style_selector_module, "NODE_DISPLAY_NAME_MAPPINGS")
QWEN_MULTIANGLE_NODE_CLASS_MAPPINGS = _get_module_mapping(lackluster_qwen_multiangle_module, "NODE_CLASS_MAPPINGS")
QWEN_MULTIANGLE_NODE_DISPLAY_NAME_MAPPINGS = _get_module_mapping(lackluster_qwen_multiangle_module, "NODE_DISPLAY_NAME_MAPPINGS")
CAM_ORBIT_NODE_CLASS_MAPPINGS = _get_module_mapping(lackluster_cam_orbit_module, "NODE_CLASS_MAPPINGS")
CAM_ORBIT_NODE_DISPLAY_NAME_MAPPINGS = _get_module_mapping(lackluster_cam_orbit_module, "NODE_DISPLAY_NAME_MAPPINGS")
SHOT_QUEUE_NODE_CLASS_MAPPINGS = _get_module_mapping(lackluster_shot_queue_module, "NODE_CLASS_MAPPINGS")
SHOT_QUEUE_NODE_DISPLAY_NAME_MAPPINGS = _get_module_mapping(lackluster_shot_queue_module, "NODE_DISPLAY_NAME_MAPPINGS")
SHOT_QUEUE_V2_NODE_CLASS_MAPPINGS = _get_module_mapping(lackluster_shot_queue_v2_module, "NODE_CLASS_MAPPINGS")
SHOT_QUEUE_V2_NODE_DISPLAY_NAME_MAPPINGS = _get_module_mapping(lackluster_shot_queue_v2_module, "NODE_DISPLAY_NAME_MAPPINGS")

NODE_CLASS_MAPPINGS = {**ALLTALK_NODE_CLASS_MAPPINGS, **FRAME_SELECTOR_NODE_CLASS_MAPPINGS, **TEXT_MULTILINE_NODE_CLASS_MAPPINGS, **UV_OUTDATED_NODE_CLASS_MAPPINGS, **TRAP_NODE_CLASS_MAPPINGS, **LACKLUSTER_PROMPT_ENHANCER_NODE_CLASS_MAPPINGS, **TRAP2_NODE_CLASS_MAPPINGS, **TRAP_STYLE_SELECTOR_NODE_CLASS_MAPPINGS, **QWEN_MULTIANGLE_NODE_CLASS_MAPPINGS, **CAM_ORBIT_NODE_CLASS_MAPPINGS, **SHOT_QUEUE_NODE_CLASS_MAPPINGS, **SHOT_QUEUE_V2_NODE_CLASS_MAPPINGS}
NODE_DISPLAY_NAME_MAPPINGS = {**ALLTALK_NODE_DISPLAY_NAMES, **FRAME_SELECTOR_NODE_DISPLAY_NAME_MAPPINGS, **TEXT_MULTILINE_NODE_DISPLAY_NAME_MAPPINGS, **UV_OUTDATED_NODE_DISPLAY_NAME_MAPPINGS, **TRAP_NODE_DISPLAY_NAME_MAPPINGS, **LACKLUSTER_PROMPT_ENHANCER_NODE_DISPLAY_NAME_MAPPINGS, **TRAP2_NODE_DISPLAY_NAME_MAPPINGS, **TRAP_STYLE_SELECTOR_NODE_DISPLAY_NAME_MAPPINGS, **QWEN_MULTIANGLE_NODE_DISPLAY_NAME_MAPPINGS, **CAM_ORBIT_NODE_DISPLAY_NAME_MAPPINGS, **SHOT_QUEUE_NODE_DISPLAY_NAME_MAPPINGS, **SHOT_QUEUE_V2_NODE_DISPLAY_NAME_MAPPINGS}
WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

