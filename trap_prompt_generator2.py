"""
TrapPromptGenerator2 — Enhanced Trap Music Prompt Generator

ComfyUI node for generating structured trap / hip-hop music production prompts.
14 musical categories, each with expanded option pools.  Supports three output
formats (tags, natural language, structured tokens), optional category exclusion
via "— None —", custom tag injection, and a companion JS frontend with live
preview and per-category lock/randomise controls.
"""

import random

RANDOM_TOKEN = "🎲 Random"
NONE_TOKEN = "— None —"

# ---------------------------------------------------------------------------
# Option pools
# ---------------------------------------------------------------------------

GENRE_OPTIONS = [
    "club trap", "twerk trap", "southern bounce trap", "strip club trap",
    "hypnotic club trap", "rage-bounce hybrid", "experimental trap fusion",
    "phonk", "drill trap", "Memphis trap", "cloud trap", "dark trap",
    "chill trap", "melodic trap", "hard trap", "lo-fi trap", "plugg",
    "orchestral trap",
]

BPM_OPTIONS = [
    "100", "110", "115", "120", "128", "130", "135",
    "140", "145", "148", "150", "160", "170",
]

KEY_OPTIONS = [
    "C minor", "C# minor", "D minor", "D# minor", "E minor",
    "F minor", "F# minor", "G minor", "G# minor", "A minor",
    "Bb minor", "B minor",
]

MOOD_OPTIONS = [
    "aggressive", "dark and moody", "euphoric party", "melancholic",
    "confident swagger", "eerie and haunted", "playful bounce",
    "menacing", "hypnotic trance", "dreamy and ethereal",
    "triumphant", "nocturnal",
]

ENERGY_OPTIONS = [
    "high-energy bounce", "late-night party energy", "aggressive club energy",
    "hypnotic groove", "underground dancefloor intensity", "smooth heavy bounce",
    "mellow laid-back groove", "chaotic mosh-pit energy",
    "cinematic tension", "euphoric festival energy",
]

BASS_OPTIONS = [
    "deep punchy 808s", "trunk-rattling sub bass", "rolling basslines",
    "distorted sliding 808s", "clipped hard sub hits",
    "warm analog 808", "pitch-bent 808 slides", "saturated low-end",
    "layered sub and mid bass", "boomy kick-bass combo",
]

DRUMS_OPTIONS = [
    "hard kick drums", "snappy claps", "rimshot-heavy percussion",
    "glitchy trap hats", "fast hi-hats with swing", "minimal punchy drums",
    "drill-pattern percs", "Memphis cowbell loops", "layered open hats",
    "bouncy kick patterns", "compressed acoustic snares",
    "boom-bap influenced drums",
]

RHYTHM_OPTIONS = [
    "bounce-driven rhythm", "syncopated groove pocket",
    "skittering hi-hat rolls", "triplet swing pattern",
    "stutter-edited percussion flow", "double-time hat patterns",
    "half-time groove", "polyrhythmic percussion",
    "swing-heavy pocket", "drill slide rhythm",
]

MELODY_OPTIONS = [
    "minimal dark synth stabs", "hypnotic arpeggiated synths",
    "eerie pluck melody", "ambient club pads", "stripped-back melodic loop",
    "flute-type beat melody", "guitar loop sample", "bell-tone plucks",
    "vocal chop melody", "detuned piano", "dark orchestral strings",
    "music box melody", "ethereal choir pads",
]

VOCALS_OPTIONS = [
    "chant-style vocal hooks", "repetitive hypnotic phrases",
    "ad-lib heavy vocal chops", "confident feminine vocal energy",
    "call-and-response hook patterns", "pitched vocal samples",
    "no vocals instrumental", "autotuned melodic hook",
    "whispered ad-libs", "crowd chant energy",
]

ATMOSPHERE_OPTIONS = [
    "dark neon club atmosphere", "strip-club bounce aesthetic",
    "sweaty underground dancefloor vibe", "late-night city energy",
    "hypnotic trance-like club feel", "foggy warehouse rave",
    "futuristic cyber club", "outdoor festival energy",
    "intimate studio session", "haunted Memphis night",
]

FX_OPTIONS = [
    "heavy reverb tails", "tape saturation", "vinyl crackle",
    "bit-crushed textures", "sidechain pump", "filtered sweeps",
    "lo-fi haze", "granular glitch", "delay throws",
    "phaser movement", "reverse reverb hits",
]

MIX_OPTIONS = [
    "club-ready mix", "hard compressed low-end focus",
    "wide stereo percussion", "punchy modern trap mix",
    "minimal clean arrangement", "lo-fi saturated warmth",
    "crispy digital clarity", "bass-forward car system mix",
    "spacious reverb-heavy mix", "raw unpolished grit",
]

ARRANGEMENT_OPTIONS = [
    "intro build drop", "loop-based minimal", "verse-chorus-drop",
    "slow build crescendo", "sudden switch-up",
    "ambient intro to hard drop", "breakdown to climax",
    "continuous energy", "call and response sections",
]

PROMPT_STYLES = ["tags", "natural", "structured"]

# Ordered definition: (name, pool, can_be_none)
CATEGORY_ORDER = [
    ("genre",       GENRE_OPTIONS,       False),
    ("bpm",         BPM_OPTIONS,         True),
    ("key",         KEY_OPTIONS,         True),
    ("mood",        MOOD_OPTIONS,        True),
    ("energy",      ENERGY_OPTIONS,      True),
    ("bass",        BASS_OPTIONS,        True),
    ("drums",       DRUMS_OPTIONS,       True),
    ("rhythm",      RHYTHM_OPTIONS,      True),
    ("melody",      MELODY_OPTIONS,      True),
    ("vocals",      VOCALS_OPTIONS,      True),
    ("atmosphere",  ATMOSPHERE_OPTIONS,  True),
    ("fx",          FX_OPTIONS,          True),
    ("mix",         MIX_OPTIONS,         True),
    ("arrangement", ARRANGEMENT_OPTIONS, True),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve(pool, selection, seed, offset):
    """Resolve a dropdown selection — if Random, deterministically pick."""
    if selection == RANDOM_TOKEN or selection.startswith(RANDOM_TOKEN):
        rng = random.Random(seed * 31 + offset)
        return rng.choice(pool)
    return selection


def _format_tags(resolved):
    """Comma-separated tag list."""
    parts = []
    for name, _, _ in CATEGORY_ORDER:
        if name not in resolved:
            continue
        val = resolved[name]
        if name == "bpm":
            parts.append(f"{val} BPM")
        else:
            parts.append(val)
    return ", ".join(parts)


def _format_natural(resolved):
    """Flowing natural-language description."""
    fragments = []

    # Opening: genre + bpm + key
    g = resolved.get("genre")
    opening = f"A {g} beat" if g else "A trap beat"
    if "bpm" in resolved:
        opening += f" at {resolved['bpm']} BPM"
    if "key" in resolved:
        opening += f" in {resolved['key']}"
    fragments.append(opening)

    # Character: mood + energy
    char_parts = []
    if "mood" in resolved:
        char_parts.append(resolved["mood"])
    if "energy" in resolved:
        char_parts.append(resolved["energy"])
    if char_parts:
        fragments.append(" with ".join(char_parts))

    # Rhythm section: bass + drums + rhythm
    rhythm_sec = []
    if "bass" in resolved:
        rhythm_sec.append(resolved["bass"])
    if "drums" in resolved:
        rhythm_sec.append(resolved["drums"])
    if "rhythm" in resolved:
        rhythm_sec.append(resolved["rhythm"])
    if rhythm_sec:
        fragments.append("featuring " + ", ".join(rhythm_sec))

    # Melodic: melody + vocals
    mel = []
    if "melody" in resolved:
        mel.append(resolved["melody"])
    if "vocals" in resolved:
        mel.append(resolved["vocals"])
    if mel:
        fragments.append("with " + " and ".join(mel))

    # Atmosphere + FX
    vibe = []
    if "atmosphere" in resolved:
        vibe.append(resolved["atmosphere"])
    if "fx" in resolved:
        vibe.append(resolved["fx"])
    if vibe:
        fragments.append(", ".join(vibe))

    # Production: mix + arrangement
    prod = []
    if "mix" in resolved:
        prod.append(resolved["mix"])
    if "arrangement" in resolved:
        prod.append(resolved["arrangement"] + " structure")
    if prod:
        fragments.append(", ".join(prod))

    return ", ".join(fragments)


def _format_structured(resolved):
    """Labeled-token format: [genre] value [bpm] value ..."""
    parts = []
    for name, _, _ in CATEGORY_ORDER:
        if name not in resolved:
            continue
        parts.append(f"[{name}] {resolved[name]}")
    return " ".join(parts)


_FORMATTERS = {
    "tags": _format_tags,
    "natural": _format_natural,
    "structured": _format_structured,
}


# ---------------------------------------------------------------------------
# Node
# ---------------------------------------------------------------------------

class TrapPromptGenerator2:
    """Enhanced trap music prompt generator with 14 categories, three output
    formats, optional exclusion, custom tag injection, and a JS frontend."""

    @classmethod
    def INPUT_TYPES(cls):
        required = {
            "seed": ("INT", {
                "default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF,
                "tooltip": "Seed for deterministic randomisation of 🎲 Random categories.",
            }),
            "prompt_style": (PROMPT_STYLES, {
                "default": "tags",
                "tooltip": "Output format: tags (comma list), natural (flowing sentence), structured ([label] value).",
            }),
        }
        for name, pool, can_none in CATEGORY_ORDER:
            opts = [RANDOM_TOKEN]
            if can_none:
                opts.append(NONE_TOKEN)
            opts.extend(pool)
            required[name] = (opts,)
        return {
            "required": required,
            "optional": {
                "custom_tags": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Extra text appended to the generated prompt.",
                }),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "generate"
    CATEGORY = "Lackluster/Audio/Trap"

    def generate(self, seed, prompt_style="tags", custom_tags="", **kwargs):
        # Resolve each category
        resolved = {}
        for i, (name, pool, _) in enumerate(CATEGORY_ORDER):
            sel = kwargs.get(name, RANDOM_TOKEN)
            if sel == NONE_TOKEN:
                continue
            resolved[name] = _resolve(pool, sel, seed, i + 1)

        # Format prompt
        formatter = _FORMATTERS.get(prompt_style, _format_tags)
        prompt = formatter(resolved)

        # Append custom tags
        if custom_tags and custom_tags.strip():
            sep = ", " if prompt else ""
            prompt = prompt + sep + custom_tags.strip()

        return (prompt,)


NODE_CLASS_MAPPINGS = {
    "TrapPromptGenerator2": TrapPromptGenerator2,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrapPromptGenerator2": "Trap Prompt Generator v2",
}
