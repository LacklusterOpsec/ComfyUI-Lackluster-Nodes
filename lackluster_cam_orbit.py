"""
Lackluster CamOrbit — Camera Angle Control & Sequence Batching for ComfyUI
"""

from __future__ import annotations

import csv
import io as pyio
import json
import math
import os
import re

import torch

import folder_paths

_SCENE_CENTER_Y = 0.5


# ── helpers ──────────────────────────────────────────────────────────────────

def build_camera_info(azimuth: int, elevation: int, distance: float) -> dict:
    az_r = math.radians(azimuth)
    el_r = math.radians(elevation)
    vd = 2.6 - (distance / 10.0) * 2.0
    return {
        "position": {
            "x": vd * math.sin(az_r) * math.cos(el_r),
            "y": _SCENE_CENTER_Y + vd * math.sin(el_r),
            "z": vd * math.cos(az_r) * math.cos(el_r),
        },
        "target": {"x": 0.0, "y": _SCENE_CENTER_Y, "z": 0.0},
        "zoom": 1,
        "cameraType": "perspective",
    }


def _resolve_horizontal(h: int) -> str:
    h = h % 360
    if h < 22.5 or h >= 337.5:
        return "front view"
    if h < 67.5:
        return "front-right quarter view"
    if h < 112.5:
        return "right side view"
    if h < 157.5:
        return "back-right quarter view"
    if h < 202.5:
        return "back view"
    if h < 247.5:
        return "back-left quarter view"
    if h < 292.5:
        return "left side view"
    return "front-left quarter view"


def _resolve_vertical(v: int) -> str:
    if v < -15:
        return "low-angle shot"
    if v < 15:
        return "eye-level shot"
    if v < 45:
        return "elevated shot"
    return "high-angle shot"


def _resolve_distance(d: float) -> str:
    if d < 2:
        return "wide shot"
    if d < 6:
        return "medium shot"
    return "close-up"


def compute_angle_prompt(
    azimuth: int, elevation: int, distance: float,
    prefix: str = "<sks>", extra: str = "",
) -> str:
    parts = []
    if prefix.strip():
        parts.append(prefix.strip())
    parts.append(_resolve_horizontal(azimuth))
    parts.append(_resolve_vertical(elevation))
    parts.append(_resolve_distance(distance))
    if extra.strip():
        parts.append(extra.strip())
    return " ".join(parts)


def _clamp(val, lo, hi):
    return max(lo, min(hi, val))


# ── built-in angle presets ───────────────────────────────────────────────────

ANGLE_PRESETS = {
    "Custom":                     {"azimuth": 0,   "elevation": 0,  "distance": 5.0},
    "Front (eye-level)":          {"azimuth": 0,   "elevation": 0,  "distance": 5.0},
    "Front (low)":                {"azimuth": 0,   "elevation": -20,"distance": 4.0},
    "Front (high)":               {"azimuth": 0,   "elevation": 30, "distance": 6.0},
    "Right Profile":              {"azimuth": 90,  "elevation": 0,  "distance": 4.0},
    "Left Profile":               {"azimuth": 270, "elevation": 0,  "distance": 4.0},
    "Right 3/4":                  {"azimuth": 45,  "elevation": 0,  "distance": 5.0},
    "Left 3/4":                   {"azimuth": 315, "elevation": 0,  "distance": 5.0},
    "Back":                       {"azimuth": 180, "elevation": 0,  "distance": 5.0},
    "Back Right 3/4":             {"azimuth": 135, "elevation": 0,  "distance": 5.0},
    "Back Left 3/4":              {"azimuth": 225, "elevation": 0,  "distance": 5.0},
    "Overhead":                   {"azimuth": 0,   "elevation": 60, "distance": 3.0},
    "Worm's-eye":                 {"azimuth": 0,   "elevation": -30,"distance": 2.0},
    "Dutch Angle Right":          {"azimuth": 0,   "elevation": 0,  "distance": 5.0},
    "Close-up Front":             {"azimuth": 0,   "elevation": 0,  "distance": 8.5},
    "Close-up Profile":           {"azimuth": 90,  "elevation": 0,  "distance": 8.5},
}

PRESET_NAMES = list(ANGLE_PRESETS.keys())


# ─────────────────────────────────────────────────────────────────────────────
#  Node 1 — Single-shot camera angle picker
# ─────────────────────────────────────────────────────────────────────────────

class LacklusterCamOrbit:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "preset": (PRESET_NAMES, {"default": "Front (eye-level)"}),
                "azimuth": ("INT", {"default": 0, "min": 0, "max": 360, "step": 1, "tooltip": "Horizontal angle (0-360°)"}),
                "elevation": ("INT", {"default": 0, "min": -30, "max": 60, "step": 1, "tooltip": "Vertical angle (-30° to 60°)"}),
                "distance": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 10.0, "step": 0.1, "tooltip": "Camera distance (0=wide, 10=close-up)"}),
                "prefix": ("STRING", {"default": "<sks>", "tooltip": "Prefix token for each prompt"}),
                "extra_prompt": ("STRING", {"default": "", "multiline": True, "tooltip": "Extra text appended to the generated prompt"}),
                "camera_view": ("BOOLEAN", {"default": False, "tooltip": "Toggle camera perspective preview"}),
            },
            "optional": {
                "image": ("IMAGE", {"tooltip": "Optional input image for 3D scene preview"}),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("STRING", "STRING", "LOAD_3D_CAMERA")
    RETURN_NAMES = ("prompt", "label", "camera_info")
    FUNCTION = "execute"
    CATEGORY = "Lackluster/Camera"
    OUTPUT_NODE = True

    def execute(
        self, preset="Front (eye-level)", azimuth=0, elevation=0, distance=5.0,
        prefix="<sks>", extra_prompt="", camera_view=False, image=None,
        unique_id="preview",
    ):
        az = _clamp(int(azimuth), 0, 360)
        el = _clamp(int(elevation), -30, 60)
        dist = _clamp(float(distance), 0.0, 10.0)

        prompt = compute_angle_prompt(az, el, dist, prefix=prefix, extra=extra_prompt)
        camera_info = build_camera_info(az, el, dist)

        return {"ui": {}, "result": (prompt, preset, camera_info)}


# ─────────────────────────────────────────────────────────────────────────────
#  Node 2 — Sequence builder (batch queue)
# ─────────────────────────────────────────────────────────────────────────────

class LacklusterCamOrbitSequence:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "mode": ([
                    "json_sequence",
                    "csv_sequence",
                    "auto_sweep",
                ], {"default": "json_sequence"}),
                "prefix": ("STRING", {"default": "<sks>", "tooltip": "Prefix token for each prompt"}),
            },
            "optional": {
                "sequence_json": ("STRING", {
                    "default": "[]",
                    "multiline": True,
                    "tooltip": (
                        "JSON array of angle entries.\n"
                        'Each entry: {"azimuth":0,"elevation":0,"distance":5.0}\n'
                        'Optional keys: "label":"my view","extra":"text","prefix":"<sks>"'
                    ),
                }),
                "sequence_csv": ("STRING", {
                    "default": "label,azimuth,elevation,distance,extra\nFront,0,0,5.0,\nRight,90,0,4.0,",
                    "multiline": True,
                    "tooltip": "CSV with columns: label,azimuth,elevation,distance[,extra]",
                }),
                "sweep_start": ("INT", {"default": 0, "min": 0, "max": 360, "step": 1, "tooltip": "Starting azimuth for auto sweep"}),
                "sweep_end": ("INT", {"default": 360, "min": 0, "max": 360, "step": 1, "tooltip": "Ending azimuth for auto sweep"}),
                "sweep_steps": ("INT", {"default": 8, "min": 1, "max": 72, "step": 1, "tooltip": "Number of steps in sweep"}),
                "sweep_elevation": ("INT", {"default": 0, "min": -30, "max": 60, "step": 1, "tooltip": "Fixed elevation for sweep"}),
                "sweep_distance": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 10.0, "step": 0.1, "tooltip": "Fixed distance for sweep"}),
                "extra_prompt": ("STRING", {"default": "", "multiline": True, "tooltip": "Extra text appended to every prompt"}),
                "image": ("IMAGE", {"tooltip": "Optional input image for preview"}),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT", "LOAD_3D_CAMERA")
    RETURN_NAMES = ("prompts", "prompt_text", "labels_text", "count", "camera_info")
    OUTPUT_IS_LIST = (True, False, False, False, True)
    FUNCTION = "execute"
    CATEGORY = "Lackluster/Camera"
    OUTPUT_NODE = True

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _parse_json(text: str) -> list[dict]:
        if not text or not text.strip():
            return []
        parsed = json.loads(text)
        if not isinstance(parsed, list):
            raise ValueError("JSON must be an array")
        return parsed

    @staticmethod
    def _parse_csv(text: str) -> list[dict]:
        if not text or not text.strip():
            return []
        reader = csv.DictReader(pyio.StringIO(text))
        out = []
        for row in reader:
            try:
                entry = {
                    "label": row.get("label", ""),
                    "azimuth": int(row.get("azimuth", 0)),
                    "elevation": int(row.get("elevation", 0)),
                    "distance": float(row.get("distance", 5.0)),
                    "extra": row.get("extra", ""),
                }
            except (ValueError, KeyError):
                continue
            out.append(entry)
        return out

    @staticmethod
    def _build_sweep(
        start: int, end: int, steps: int,
        elevation: int, distance: float, extra: str,
    ) -> list[dict]:
        out = []
        for i in range(steps):
            frac = i / (steps - 1) if steps > 1 else 0
            az = int(round(start + (end - start) * frac)) % 360
            out.append({
                "label": f"sweep {i+1}/{steps}",
                "azimuth": az,
                "elevation": elevation,
                "distance": distance,
                "extra": extra,
            })
        return out

    @staticmethod
    def _normalize_entry(e: dict, global_extra: str = "") -> dict:
        az = _clamp(int(e.get("azimuth", 0)), 0, 360)
        el = _clamp(int(e.get("elevation", 0)), -30, 60)
        dist = _clamp(float(e.get("distance", 5.0)), 0.0, 10.0)
        extra = (e.get("extra", "") or "").strip()
        label = (e.get("label", "") or "").strip()
        prefix = (e.get("prefix", "") or "").strip()
        if global_extra.strip() and extra:
            extra = f"{extra}, {global_extra.strip()}"
        elif global_extra.strip():
            extra = global_extra.strip()
        return {
            "azimuth": az,
            "elevation": el,
            "distance": dist,
            "extra": extra,
            "label": label or f"az{az}_el{el}_d{dist:.1f}",
            "prefix": prefix,
        }

    # ── main ─────────────────────────────────────────────────────────────

    def execute(
        self, mode="json_sequence", prefix="<sks>",
        sequence_json="[]", sequence_csv="",
        sweep_start=0, sweep_end=360, sweep_steps=8,
        sweep_elevation=0, sweep_distance=5.0,
        extra_prompt="", image=None, unique_id="sequence_preview",
    ):
        if mode == "json_sequence":
            raw = self._parse_json(sequence_json)
        elif mode == "csv_sequence":
            raw = self._parse_csv(sequence_csv)
        elif mode == "auto_sweep":
            raw = self._build_sweep(
                sweep_start, sweep_end, sweep_steps,
                sweep_elevation, sweep_distance, extra_prompt,
            )
        else:
            raw = []

        if not raw:
            raw = [{"azimuth": 0, "elevation": 0, "distance": 5.0, "label": "default"}]

        entries = [self._normalize_entry(e, extra_prompt) for e in raw]

        prompts_out = []
        infos_out = []
        labels_out = []

        for e in entries:
            pfx = e["prefix"] or prefix
            p = compute_angle_prompt(
                e["azimuth"], e["elevation"], e["distance"],
                prefix=pfx, extra=e["extra"],
            )
            cam = build_camera_info(e["azimuth"], e["elevation"], e["distance"])
            prompts_out.append(p)
            infos_out.append(cam)
            labels_out.append(e["label"])

        prompt_text = "\n".join(prompts_out)
        labels_text = "\n".join(labels_out)
        count = len(prompts_out)

        return {
            "ui": {},
            "result": (prompts_out, prompt_text, labels_text, count, infos_out),
        }


# ─────────────────────────────────────────────────────────────────────────────
#  Node 3 — Glossary translate (ported standalone, no external deps)
# ─────────────────────────────────────────────────────────────────────────────

CAMERA_GLOSSARY = {
    "front view":               {"zh": "正面视角", "ja": "正面",   "ko": "정면"},
    "front-right quarter view": {"zh": "右前方视角", "ja": "右前方", "ko": "우측 전방"},
    "right side view":          {"zh": "右侧视角", "ja": "右側面",   "ko": "우측면"},
    "back-right quarter view":  {"zh": "右后方视角", "ja": "右後方", "ko": "우측 후방"},
    "back view":                {"zh": "背面视角", "ja": "背面",     "ko": "후면"},
    "back-left quarter view":   {"zh": "左后方视角", "ja": "左後方", "ko": "좌측 후방"},
    "left side view":           {"zh": "左侧视角", "ja": "左側面",   "ko": "좌측面"},
    "front-left quarter view":  {"zh": "左前方视角", "ja": "左前方", "ko": "좌측 전방"},
    "low-angle shot":           {"zh": "仰拍",   "ja": "ローアングル", "ko": "로우 앵글"},
    "eye-level shot":           {"zh": "平视",   "ja": "アイレベル",   "ko": "아이 레벨"},
    "elevated shot":            {"zh": "高角度", "ja": "ハイアングル", "ko": "하이 앵글"},
    "high-angle shot":          {"zh": "俯拍",   "ja": "俯瞰",         "ko": "부감"},
    "wide shot":                {"zh": "远景",   "ja": "ワイドショット",   "ko": "와이드 샷"},
    "medium shot":              {"zh": "中景",   "ja": "ミディアムショット", "ko": "미디엄 샷"},
    "close-up":                 {"zh": "特写",   "ja": "クローズアップ",   "ko": "클로즈업"},
}

_GLOSSARY_LANGUAGES = ["中文 (Chinese)", "日本語 (Japanese)", "한국어 (Korean)", "English"]
_GLOSSARY_CODE = {
    "中文 (Chinese)": "zh",
    "日本語 (Japanese)": "ja",
    "한국어 (Korean)": "ko",
    "English": "en",
}
_SORTED_PHRASES = sorted(CAMERA_GLOSSARY, key=len, reverse=True)
_PHRASE_RE = re.compile(
    r"(?<![A-Za-z])(" + "|".join(re.escape(p) for p in _SORTED_PHRASES) + r")(?![A-Za-z])",
    re.IGNORECASE,
)


def _translate_text(text: str, lang_code: str) -> str:
    if not text or lang_code == "en":
        return text

    def _sub(m: re.Match) -> str:
        phrase = m.group(1)
        entry = CAMERA_GLOSSARY.get(phrase.lower())
        if entry is None:
            return phrase
        return entry.get(lang_code, phrase)

    return _PHRASE_RE.sub(_sub, text)


class LacklusterCamOrbitTranslate:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
                "target_language": (_GLOSSARY_LANGUAGES, {"default": _GLOSSARY_LANGUAGES[0]}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "execute"
    CATEGORY = "Lackluster/Camera"

    def execute(self, prompt, target_language="中文 (Chinese)"):
        code = _GLOSSARY_CODE.get(target_language, "en")
        translated = _translate_text(prompt or "", code)
        return (translated,)


# ── registrations ────────────────────────────────────────────────────────────

NODE_CLASS_MAPPINGS = {
    "LacklusterCamOrbit": LacklusterCamOrbit,
    "LacklusterCamOrbitSequence": LacklusterCamOrbitSequence,
    "LacklusterCamOrbitTranslate": LacklusterCamOrbitTranslate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LacklusterCamOrbit": "CamOrbit",
    "LacklusterCamOrbitSequence": "CamOrbit Sequence",
    "LacklusterCamOrbitTranslate": "CamOrbit Translate",
}