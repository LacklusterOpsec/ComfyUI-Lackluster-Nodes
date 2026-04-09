import requests
import os
import torch
import torchaudio
import numpy as np
import folder_paths
from pathlib import Path

class AllTalkServerConfigV2:
    """
    Configuration node to centralize AllTalk server settings.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "server_url": ("STRING", {"default": "http://localhost:7851"}),
            }
        }
    
    RETURN_TYPES = ("ALLTALK_SERVER_CONFIG",)
    RETURN_NAMES = ("config",)
    FUNCTION = "get_config"
    CATEGORY = "audio/tts/v2"

    def get_config(self, server_url):
        return ({"url": server_url.rstrip("/")},)


class AllTalkTTSNodeV2:
    """
    Improved AllTalk TTS node with RVC support, text filtering, and robust audio loading.
    """
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.temp_dir = folder_paths.get_temp_directory()
        self.input_dir = folder_paths.get_input_directory()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "server_config": ("ALLTALK_SERVER_CONFIG",),
                "text": ("STRING", {"multiline": True, "default": "Hello, this is AllTalk V2."}),
                "character_voice": ("STRING", {"default": "female_1"}),
                "language": (["auto", "en", "es", "fr", "de", "it", "pt", "nl", "ru", "ja", "zh", "ko"], {"default": "auto"}),
                "speed": ("FLOAT", {"default": 1.0, "min": 0.25, "max": 2.0, "step": 0.1}),
                "temperature": ("FLOAT", {"default": 0.75, "min": 0.1, "max": 1.0, "step": 0.05}),
                "repetition_penalty": ("FLOAT", {"default": 2.5, "min": 1.0, "max": 20.0, "step": 0.1}),
                "pitch": ("FLOAT", {"default": 0.0, "min": -10.0, "max": 10.0, "step": 0.5}),
                "text_filtering": (["none", "standard", "heavy"], {"default": "standard"}),
                "output_location": (["output", "temp", "input"], {"default": "output"}),
            },
            "optional": {
                "narrator_enabled": (["false", "true", "silent"], {"default": "false"}),
                "narrator_voice": ("STRING", {"default": "male_1"}),
                "rvc_character": ("STRING", {"default": "Disabled"}),
                "rvc_pitch": ("FLOAT", {"default": 0.0, "min": -24.0, "max": 24.0, "step": 1.0}),
            }
        }

    RETURN_TYPES = ("AUDIO", "STRING")
    RETURN_NAMES = ("audio", "audio_path")
    FUNCTION = "generate_tts"
    CATEGORY = "audio/tts/v2"
    OUTPUT_NODE = True

    def generate_tts(self, server_config, text, character_voice, language, speed, temperature, 
                     repetition_penalty, pitch, text_filtering, output_location,
                     narrator_enabled="false", narrator_voice="male_1", 
                     rvc_character="Disabled", rvc_pitch=0.0):
        
        server_url = server_config["url"]
        
        # 1. Readiness Check
        try:
            requests.get(f"{server_url}/api/ready", timeout=5).raise_for_status()
        except Exception as e:
            raise Exception(f"AllTalk server not ready at {server_url}: {str(e)}")

        # 2. Prepare Request
        tts_params = {
            "text_input": text,
            "character_voice_gen": character_voice,
            "language": language,
            "speed": speed,
            "temperature": temperature,
            "repetition_penalty": repetition_penalty,
            "pitch": pitch,
            "narrator_enabled": narrator_enabled,
            "narrator_voice_gen": narrator_voice,
            "text_filtering": text_filtering,
            "output_file_name": f"alltalk_v2_{os.urandom(4).hex()}",
            "output_file_timestamp": True,
            "autoplay": False,
            "rvccharacter_voice_gen": rvc_character,
            "rvccharacter_pitch": rvc_pitch,
        }

        # 3. Request Generation
        response = requests.post(f"{server_url}/api/tts-generate", data=tts_params, timeout=300)
        response.raise_for_status()
        resp_data = response.json()

        if resp_data.get("status") != "generate-success":
            raise Exception(f"TTS Failed: {resp_data.get('error', 'Unknown error')}")

        # 4. Download Audio
        audio_url = resp_data.get("output_file_url") or resp_data.get("output_cache_url")
        if not audio_url.startswith("http"):
            audio_url = f"{server_url}{audio_url}"
        
        audio_resp = requests.get(audio_url, timeout=30)
        audio_resp.raise_for_status()

        # 5. Save Audio
        target_dir = {
            "output": self.output_dir,
            "temp": self.temp_dir,
            "input": self.input_dir
        }.get(output_location, self.output_dir)
        
        filename = f"{resp_data.get('output_file_name', 'alltalk_gen')}.wav"
        local_path = os.path.join(target_dir, filename)
        
        with open(local_path, "wb") as f:
            f.write(audio_resp.content)

        # 6. Load with torchaudio (Robust)
        try:
            waveform, sample_rate = torchaudio.load(local_path)
            # ComfyUI expects (batch, channels, samples)
            if waveform.dim() == 2:
                waveform = waveform.unsqueeze(0)
            
            audio_dict = {"waveform": waveform, "sample_rate": sample_rate}
            return (audio_dict, local_path)
        except Exception as e:
            raise Exception(f"Failed to load generated audio with torchaudio: {str(e)}")


class AllTalkVoiceLoaderV2:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"server_config": ("ALLTALK_SERVER_CONFIG",)}}
    
    RETURN_TYPES = ("STRING", "COMBO")
    RETURN_NAMES = ("voices_text", "voices_list")
    FUNCTION = "get_voices"
    CATEGORY = "audio/tts/v2"

    def get_voices(self, server_config):
        url = server_config["url"]
        try:
            resp = requests.get(f"{url}/api/voices", timeout=10)
            resp.raise_for_status()
            voices = resp.json().get("voices", [])
            return ("\n".join(voices), voices)
        except Exception as e:
            return (f"Error: {str(e)}", [])


class AllTalkSettingsLoaderV2:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"server_config": ("ALLTALK_SERVER_CONFIG",)}}
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("settings_info",)
    FUNCTION = "get_settings"
    CATEGORY = "audio/tts/v2"

    def get_settings(self, server_config):
        url = server_config["url"]
        try:
            resp = requests.get(f"{url}/api/currentsettings", timeout=10)
            resp.raise_for_status()
            s = resp.json()
            info = [
                f"Engine: {s.get('current_engine_loaded')}",
                f"Model: {s.get('current_model_loaded')}",
                f"LowVRAM: {s.get('lowvram_enabled')}",
                f"DeepSpeed: {s.get('deepspeed_enabled')}"
            ]
            return ("\n".join(info),)
        except Exception as e:
            return (f"Error: {str(e)}",)


NODE_CLASS_MAPPINGS = {
    "AllTalkServerConfigV2": AllTalkServerConfigV2,
    "AllTalkTTSV2": AllTalkTTSNodeV2,
    "AllTalkVoiceLoaderV2": AllTalkVoiceLoaderV2,
    "AllTalkSettingsLoaderV2": AllTalkSettingsLoaderV2,
}

NODE_DISPLAY_NAMES = {
    "AllTalkServerConfigV2": "AllTalk Server Config V2",
    "AllTalkTTSV2": "AllTalk TTS Generator V2",
    "AllTalkVoiceLoaderV2": "AllTalk Voice Loader V2",
    "AllTalkSettingsLoaderV2": "AllTalk Settings Loader V2",
}
