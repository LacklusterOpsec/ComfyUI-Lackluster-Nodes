import requests
import os
import torch
import torchaudio
import numpy as np
import folder_paths
import struct
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

    def _parse_wav(self, file_path):
        """
        Fallback WAV parser for environments where torchaudio/ffmpeg is broken.
        Supports PCM (8, 16, 24, 32-bit) and IEEE 32-bit float audio.
        """
        try:
            with open(file_path, "rb") as f:
                # Read RIFF header
                riff = f.read(4)
                if riff != b'RIFF':
                    raise Exception("Not a valid WAV file")

                struct.unpack('<I', f.read(4))[0] # file_size
                wave_header = f.read(4)
                if wave_header != b'WAVE':
                    raise Exception("Not a valid WAV file")

                # Find fmt chunk
                fmt_data = None
                while True:
                    chunk_id = f.read(4)
                    if not chunk_id or len(chunk_id) < 4:
                        raise Exception("fmt chunk not found")
                    chunk_size = struct.unpack('<I', f.read(4))[0]
                    
                    if chunk_id == b'fmt ':
                        fmt_data = f.read(chunk_size)
                        break
                    else:
                        # Skip this chunk
                        f.seek(chunk_size, 1)
                    
                    # Chunks are word-aligned
                    if chunk_size % 2 == 1:
                        f.seek(1, 1)

                if not fmt_data:
                    raise Exception("fmt chunk data is empty")

                # Parse fmt chunk
                audio_format = struct.unpack('<H', fmt_data[0:2])[0]
                n_channels = struct.unpack('<H', fmt_data[2:4])[0]
                sample_rate = struct.unpack('<I', fmt_data[4:8])[0]
                bits_per_sample = struct.unpack('<H', fmt_data[14:16])[0]
                block_align = struct.unpack('<H', fmt_data[12:14])[0]

                # 1=PCM, 3=IEEE float
                if audio_format not in [1, 3]:
                    raise Exception(f"Unsupported audio format tag: {audio_format}")

                # Read data chunk
                frames = None
                while True:
                    chunk_id = f.read(4)
                    if not chunk_id or len(chunk_id) < 4:
                        raise Exception("data chunk not found")
                    chunk_size = struct.unpack('<I', f.read(4))[0]
                    
                    if chunk_id == b'data':
                        frames = f.read(chunk_size)
                        break
                    else:
                        f.seek(chunk_size, 1)
                    
                    if chunk_size % 2 == 1:
                        f.seek(1, 1)

                if frames is None:
                    raise Exception("data chunk is empty")

            n_frames = len(frames) // block_align
            sample_width = bits_per_sample // 8

            if audio_format == 1:  # PCM
                if sample_width == 1:
                    audio_data = np.frombuffer(frames, dtype=np.uint8).astype(np.float32) / 128.0
                elif sample_width == 2:
                    audio_data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                elif sample_width == 3:
                    # 24-bit
                    audio_data = np.zeros((n_frames * n_channels,), dtype=np.float32)
                    for i in range(n_frames * n_channels):
                        offset = i * 3
                        sample = int.from_bytes(frames[offset:offset+3], byteorder='little', signed=True)
                        audio_data[i] = sample / 8388608.0
                elif sample_width == 4:
                    audio_data = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0
                else:
                    raise Exception(f"Unsupported sample width: {sample_width}")
            elif audio_format == 3:  # IEEE float
                audio_data = np.frombuffer(frames, dtype=np.float32).copy()
            
            # Reshape
            if n_channels > 1:
                audio_data = audio_data.reshape(-1, n_channels).T
            else:
                audio_data = audio_data.reshape(1, -1)

            return audio_data, sample_rate

        except Exception as e:
            raise Exception(f"WAV parsing fallback failed: {str(e)}")

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
        except Exception as e_torch:
            # Fallback for broken torchaudio/ffmpeg environments
            try:
                audio_data, sample_rate = self._parse_wav(local_path)
                waveform = torch.from_numpy(audio_data).unsqueeze(0)
            except Exception as e_fallback:
                raise Exception(f"Audio load failed. Torchaudio error: {str(e_torch)} | Fallback error: {str(e_fallback)}")
            
        audio_dict = {"waveform": waveform, "sample_rate": sample_rate}
        return (audio_dict, local_path)


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
