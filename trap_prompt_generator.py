import random

RANDOM_TOKEN = "🎲 Random"

GENRE_OPTIONS = [
    "club trap",
    "twerk trap",
    "southern bounce trap",
    "strip club trap",
    "hypnotic club trap",
    "rage-bounce hybrid",
    "experimental trap fusion",
]

BPM_OPTIONS = ["110", "128", "135", "140", "148"]

ENERGY_OPTIONS = [
    "high-energy bounce",
    "late-night party energy",
    "aggressive club energy",
    "hypnotic groove",
    "underground dancefloor intensity",
    "smooth heavy bounce",
]

BASS_OPTIONS = [
    "deep punchy 808s",
    "trunk-rattling sub bass",
    "rolling basslines",
    "distorted sliding 808s",
    "clipped hard sub hits",
]

DRUMS_OPTIONS = [
    "hard kick drums",
    "snappy claps",
    "rimshot-heavy percussion",
    "glitchy trap hats",
    "fast hi-hats with swing",
    "minimal punchy drums",
]

RHYTHM_OPTIONS = [
    "bounce-driven rhythm",
    "syncopated groove pocket",
    "skittering hi-hat rolls",
    "triplet swing pattern",
    "stutter-edited percussion flow",
]

MELODY_OPTIONS = [
    "minimal dark synth stabs",
    "hypnotic arpeggiated synths",
    "eerie pluck melody",
    "ambient club pads",
    "stripped-back melodic loop",
]

VOCALS_OPTIONS = [
    "chant-style vocal hooks",
    "repetitive hypnotic phrases",
    "ad-lib heavy vocal chops",
    "confident feminine vocal energy",
    "call-and-response hook patterns",
]

ATMOSPHERE_OPTIONS = [
    "dark neon club atmosphere",
    "strip-club bounce aesthetic",
    "sweaty underground dancefloor vibe",
    "late-night city energy",
    "hypnotic trance-like club feel",
]

MIX_OPTIONS = [
    "club-ready mix",
    "hard compressed low-end focus",
    "wide stereo percussion",
    "punchy modern trap mix",
    "minimal clean arrangement",
]


def _resolve(pool, selection, seed, offset):
    if selection.startswith(RANDOM_TOKEN):
        random.seed(seed + offset)
        return random.choice(pool)
    return selection


class TrapPromptGenerator:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF}),
                "genre": ([RANDOM_TOKEN] + GENRE_OPTIONS,),
                "bpm": ([RANDOM_TOKEN] + BPM_OPTIONS,),
                "energy": ([RANDOM_TOKEN] + ENERGY_OPTIONS,),
                "bass": ([RANDOM_TOKEN] + BASS_OPTIONS,),
                "drums": ([RANDOM_TOKEN] + DRUMS_OPTIONS,),
                "rhythm": ([RANDOM_TOKEN] + RHYTHM_OPTIONS,),
                "melody": ([RANDOM_TOKEN] + MELODY_OPTIONS,),
                "vocals": ([RANDOM_TOKEN] + VOCALS_OPTIONS,),
                "atmosphere": ([RANDOM_TOKEN] + ATMOSPHERE_OPTIONS,),
                "mix": ([RANDOM_TOKEN] + MIX_OPTIONS,),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    FUNCTION = "generate"
    CATEGORY = "Lackluster/Audio/Trap"

    def generate(self, seed, genre, bpm, energy, bass, drums, rhythm, melody, vocals, atmosphere, mix):
        pools = [
            (GENRE_OPTIONS, genre, 1),
            (BPM_OPTIONS, bpm, 2),
            (ENERGY_OPTIONS, energy, 3),
            (BASS_OPTIONS, bass, 4),
            (DRUMS_OPTIONS, drums, 5),
            (RHYTHM_OPTIONS, rhythm, 6),
            (MELODY_OPTIONS, melody, 7),
            (VOCALS_OPTIONS, vocals, 8),
            (ATMOSPHERE_OPTIONS, atmosphere, 9),
            (MIX_OPTIONS, mix, 10),
        ]

        parts = [_resolve(pool, sel, seed, off) for pool, sel, off in pools]
        prompt = f"{parts[0]}, {parts[1]} BPM, {parts[2]}, {parts[3]}, {parts[4]}, {parts[5]}, {parts[6]}, {parts[7]}, {parts[8]}, {parts[9]}"
        return (prompt,)


NODE_CLASS_MAPPINGS = {
    "TrapPromptGenerator": TrapPromptGenerator,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrapPromptGenerator": "Trap Prompt Generator",
}