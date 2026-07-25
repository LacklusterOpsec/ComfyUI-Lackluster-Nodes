import os


TRAP_OPTION_TEXT = {
    "Phonk-Style Aggressive Trap": "• Phonk-Style Aggressive Trap — Cowbells, Memphis rap chops, drift scene",
    "Dark Trap": "• Dark Trap — 808 slides, chopped rap ad-libs, horror hallway",
    "Memphis Phonk": "• Memphis Phonk — Cowbell loops, screwed vocal chops, VHS static",
    "Witch House Trap": "• Witch House Trap — Detuned bells, whispered rap chops, ritual basement",
    "Rage Trap": "• Rage Trap — Distorted 808s, shouted ad-libs, mosh pit chaos",
    "Drift Phonk": "• Drift Phonk — Engine rev samples, Memphis rap chops, night highway",
    "Horrorcore Trap": "• Horrorcore Trap — Church organ stabs, muttered rap chops, abandoned asylum",
    "Industrial Trap": "• Industrial Trap — Metal clangs, glitched vocal chops, factory floor",
    "Cloud Trap": "• Cloud Trap — Reverb pads, mumbled rap chops, foggy skyline",
    "Trap Metal": "• Trap Metal — Distorted guitar riffs, screamed rap chops, arena stage",
    "Plugg Trap": "• Plugg Trap — Sparkly plucks, pitched-up rap chops, dreamy hallway",
    "Dungeon Rap Trap": "• Dungeon Rap Trap — Sub-bass growls, gravel-voiced rap chops, candlelit cave",
    "Chopped & Screwed Trap": "• Chopped & Screwed Trap — Slowed 808s, syrup-drenched rap chops, low rider",
    "Jersey Club Trap": "• Jersey Club Trap — Bed squeaks, chopped rap ad-libs, house party",
    "Gospel Trap": "• Gospel Trap — Choir stabs, soulful rap chops, Sunday sermon",
    "Dub Trap": "• Dub Trap — Skanking bass, echoed rap chops, smoke-filled dancehall",
    "Ballroom Trap": "• Ballroom Trap — Vogue beats, sharp rap chops, runway strobe",
    "Ambient Horror Trap": "• Ambient Horror Trap — Drone pads, faint rap chops, empty morgue",
    "Glitch Trap": "• Glitch Trap — Bitcrushed hats, stuttered rap chops, corrupted signal",
    "Orchestral Cinematic Trap": "• Orchestral Cinematic Trap — String stabs, ghostly rap chops, funeral procession",
    "Southern Trap": "• Southern Trap — 808 bounce, ad-lib chops, block party",
    "Sludge Phonk": "• Sludge Phonk — Detuned cowbells, gutter vocal chops, junkyard scene",
    "Emo Trap": "• Emo Trap — Guitar arpeggios, cracked rap chops, bedroom static",
    "Vaporwave Trap": "• Vaporwave Trap — Slowed pads, warped vocal chops, mall escalator",
    "Latin Trap": "• Latin Trap — Reggaeton perc, bilingual rap chops, rooftop party",
    "Snap Trap": "• Snap Trap — Finger snaps, chopped ad-libs, block corner",
    "Drift Trap Rave": "• Drift Trap Rave — Trance stabs, pitched rap chops, underground rave",
    "Doom Phonk": "• Doom Phonk — Detuned bells, demonic vocal chops, crypt echo",
    "UK Drill Trap": "• UK Drill Trap — Sliding 808s, gritty rap chops, estate stairwell",
    "Trap Soul": "• Trap Soul — Rhodes keys, breathy vocal chops, late-night drive",
    "Bass Trap": "• Bass Trap — Sub drops, warped ad-lib chops, warehouse rave",
    "Circus Trap": "• Circus Trap — Carnival organ, twisted rap chops, funhouse mirror",
    "Aztec Trap": "• Aztec Trap — Tribal drums, chanted vocal chops, jungle temple",
    "Wave Trap": "• Wave Trap — Synth arps, pitched-down rap chops, city rooftop",
    "Sinister Phonk": "• Sinister Phonk — Cowbell stabs, growled vocal chops, back-alley chase",
    "Trap Gospel Choir": "• Trap Gospel Choir — Organ swells, layered vocal chops, cathedral echo",
    "G-Funk Trap": "• G-Funk Trap — Whining synths, laid-back rap chops, lowrider cruise",
    "Cyber Trap": "• Cyber Trap — Digital glitches, robotic vocal chops, neon server room",
    "Trap Reggaeton": "• Trap Reggaeton — Dembow perc, chopped ad-libs, beachside club",
    "Slasher Phonk": "• Slasher Phonk — Knife-slash SFX, panicked vocal chops, slasher film set",
    "Trap Funk": "• Trap Funk — Wah guitar, funky rap chops, block party stage",
    "Static Trap": "• Static Trap — White noise bursts, buried vocal chops, dead TV channel",
    "Trap Waltz": "• Trap Waltz — 3/4 piano loop, eerie rap chops, abandoned ballroom",
    "Boom Bap Trap": "• Boom Bap Trap — Vinyl crackle, old-school rap chops, basement studio",
    "Trap Cathedral": "• Trap Cathedral — Pipe organ drone, whispered vocal chops, empty nave",
    "Nightcore Trap": "• Nightcore Trap — Pitched-up synths, chipmunk rap chops, arcade lights",
    "Trap Noir": "• Trap Noir — Muted trumpet, smoky rap chops, rain-soaked alley",
    "Occult Trap": "• Occult Trap — Ritual chimes, backward vocal chops, candlelit altar",
    "Trap Breakbeat": "• Trap Breakbeat — Chopped drum breaks, fractured rap chops, warehouse rave",
    "Necro Phonk": "• Necro Phonk — Distorted cowbells, corpse-whisper vocal chops, graveyard fog",
}


class TrapStyleSelectorNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "trap_style": (["— Select a trap style —"] + list(TRAP_OPTION_TEXT.keys()),),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "generate"
    CATEGORY = "Lackluster/Audio/Trap"

    def generate(self, trap_style):
        if trap_style in TRAP_OPTION_TEXT:
            return (TRAP_OPTION_TEXT[trap_style],)
        return ("",)


NODE_CLASS_MAPPINGS = {
    "TrapStyleSelectorNode": TrapStyleSelectorNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TrapStyleSelectorNode": "Trap Style Selector",
}
