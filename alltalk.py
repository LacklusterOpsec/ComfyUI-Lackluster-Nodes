"""
ComfyUI node for AllTalk TTS - makes requests to an existing AllTalk installation
"""
import requests
import os
from pathlib import Path
import folder_paths
import struct
import numpy as np

class AllTalkTTSNode:
    """
    ComfyUI node for text-to-speech generation using AllTalk TTS server.
    Makes HTTP requests to an existing AllTalk installation.
    """
    
    def __init__(self):
        self.alltalk_url = None
        self.output_dir = folder_paths.get_output_directory()
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define input parameters for the node"""
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": "Hello, this is a test."
                }),
                "character_voice": ("STRING", {
                    "default": "female_1"
                }),
                "language": (["auto", "en", "es", "fr", "de", "it", "pt", "nl", "ru", "ja", "zh", "ko"], {
                    "default": "auto"
                }),
                "speed": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.25,
                    "max": 2.0,
                    "step": 0.1
                }),
                "temperature": ("FLOAT", {
                    "default": 0.75,
                    "min": 0.1,
                    "max": 1.0,
                    "step": 0.05
                }),
                "repetition_penalty": ("FLOAT", {
                    "default": 2.5,
                    "min": 1.0,
                    "max": 20.0,
                    "step": 0.1
                }),
                "pitch": ("FLOAT", {
                    "default": 0.0,
                    "min": -10.0,
                    "max": 10.0,
                    "step": 0.5
                }),
                "alltalk_server_url": ("STRING", {
                    "default": "http://localhost:7851"
                }),
            },
            "optional": {
                "narrator_enabled": (["false", "true", "silent"], {
                    "default": "false"
                }),
                "narrator_voice": ("STRING", {
                    "default": "male_1"
                }),
            }
        }
    
    RETURN_TYPES = ("AUDIO", "STRING")
    RETURN_NAMES = ("audio", "audio_path")
    FUNCTION = "generate_tts"
    CATEGORY = "audio/tts"
    OUTPUT_NODE = True
    
    def _detect_audio_format(self, file_path):
        """
        Detect audio file format by reading file header magic bytes.
        Returns: ("format_name", "description") or ("unknown", "hex_header")
        """
        try:
            with open(file_path, "rb") as f:
                header = f.read(12)
            
            if len(header) < 4:
                return ("unknown", f"File too small ({len(header)} bytes)")
            
            # WAV: RIFF....WAVE
            if header[:4] == b'RIFF' and header[8:12] == b'WAVE':
                return ("wav", "WAV audio")
            
            # MP3: FF FB or FF FA (MPEG sync)
            if (header[0] == 0xFF) and ((header[1] & 0xE0) == 0xE0):
                return ("mp3", "MPEG MP3 audio")
            
            # OGG: OggS
            if header[:4] == b'OggS':
                return ("ogg", "OGG Vorbis audio")
            
            # M4A/AAC: ftyp (usually mp42 or isom)
            if header[4:8] == b'ftyp':
                return ("m4a", "MPEG-4 AAC audio")
            
            # FLAC: fLaC
            if header[:4] == b'fLaC':
                return ("flac", "FLAC audio")
            
            # Unknown format - show hex
            hex_header = ' '.join(f'{b:02x}' for b in header)
            return ("unknown", f"Unknown format (header: {hex_header})")
        
        except Exception as e:
            return ("error", str(e))
    
    def _parse_wav(self, file_path):
        """
        Parse WAV file and extract waveform and sample rate.
        Supports PCM (8, 16, 24, 32-bit) and IEEE 32-bit float audio.
        """
        try:
            with open(file_path, "rb") as f:
                # Read RIFF header
                riff = f.read(4)
                if riff != b'RIFF':
                    raise Exception("Not a valid WAV file")

                file_size = struct.unpack('<I', f.read(4))[0]
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
                    
                    # Chunks are word-aligned (pad to even byte boundary)
                    if chunk_size % 2 == 1:
                        f.seek(1, 1)  # Skip padding byte

                if not fmt_data:
                    raise Exception("fmt chunk data is empty")

                # Parse fmt chunk
                audio_format = struct.unpack('<H', fmt_data[0:2])[0]
                n_channels = struct.unpack('<H', fmt_data[2:4])[0]
                sample_rate = struct.unpack('<I', fmt_data[4:8])[0]
                byte_rate = struct.unpack('<I', fmt_data[8:12])[0]
                block_align = struct.unpack('<H', fmt_data[12:14])[0]
                bits_per_sample = struct.unpack('<H', fmt_data[14:16])[0]

                # audio_format: 1=PCM, 3=IEEE float, 6=mulaw, 7=alaw
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
                        # Skip this chunk
                        f.seek(chunk_size, 1)
                    
                    # Chunks are word-aligned (pad to even byte boundary)
                    if chunk_size % 2 == 1:
                        f.seek(1, 1)  # Skip padding byte

                if frames is None:
                    raise Exception("data chunk is empty")

            n_frames = len(frames) // block_align
            sample_width = bits_per_sample // 8

            # Parse audio data based on format
            if audio_format == 1:  # PCM
                if sample_width == 1:
                    dtype = np.uint8
                    max_val = 128.0
                elif sample_width == 2:
                    dtype = np.int16
                    max_val = 32768.0
                elif sample_width == 3:
                    # 24-bit: manually convert
                    audio_data = np.zeros((n_frames * n_channels,), dtype=np.int32)
                    for i in range(n_frames * n_channels):
                        offset = i * 3
                        sample = int.from_bytes(frames[offset:offset+3], byteorder='little', signed=True)
                        audio_data[i] = sample
                    audio_data = audio_data.astype(np.float32) / 8388608.0
                    audio_data = audio_data.reshape(n_frames, n_channels)
                    if n_channels > 1:
                        audio_data = audio_data.T
                    else:
                        audio_data = audio_data.reshape(1, -1)
                    return audio_data, sample_rate
                elif sample_width == 4:
                    dtype = np.int32
                    max_val = 2147483648.0
                else:
                    raise Exception(f"Unsupported sample width: {sample_width}")

                audio_data = np.frombuffer(frames, dtype=dtype).astype(np.float32) / max_val

            elif audio_format == 3:  # IEEE 32-bit float
                audio_data = np.frombuffer(frames, dtype=np.float32)
                # Already in float format, normalize to [-1, 1] if needed
                max_val = np.max(np.abs(audio_data))
                if max_val > 1.0:
                    audio_data = audio_data / max_val

            # Reshape for channel compatibility
            if n_channels > 1:
                audio_data = audio_data.reshape(-1, n_channels).T
            else:
                audio_data = audio_data.reshape(1, -1)

            return audio_data, sample_rate

        except struct.error as e:
            raise Exception(f"WAV parsing error: Invalid WAV structure - {str(e)}")
        except Exception as e:
            raise Exception(f"WAV parsing error: {str(e)}")
    
    def _parse_audio_generic(self, file_path, format_type):
        """
        Parse non-WAV audio formats using librosa if available.
        Falls back to error message if librosa not installed.
        """
        try:
            import librosa
            audio_data, sample_rate = librosa.load(file_path, sr=None, mono=False)
            
            # Ensure proper shape
            if len(audio_data.shape) == 1:
                audio_data = audio_data.reshape(1, -1)
            
            return audio_data, sample_rate
        
        except ImportError:
            raise Exception(
                f"Audio format '{format_type}' requires librosa. "
                f"Install with: pip install librosa. "
                f"Alternatively, configure AllTalk to output WAV format."
            )
        except Exception as e:
            raise Exception(f"Error parsing {format_type} audio: {str(e)}")
    
    def generate_tts(self, text, character_voice, language, speed, temperature, 
                     repetition_penalty, pitch, alltalk_server_url, 
                     narrator_enabled="false", narrator_voice="male_1"):
        """
        Generate TTS audio by making a request to AllTalk server
        """
        
        # Validate server URL
        if not alltalk_server_url.startswith("http"):
            alltalk_server_url = f"http://{alltalk_server_url}"
        
        # Remove trailing slash if present
        alltalk_server_url = alltalk_server_url.rstrip("/")
        
        # First, check if AllTalk server is ready
        try:
            ready_response = requests.get(f"{alltalk_server_url}/api/ready", timeout=5)
            if ready_response.status_code != 200:
                raise Exception("AllTalk server is not ready. Please ensure AllTalk is running.")
        except requests.exceptions.ConnectionError:
            raise Exception(f"Cannot connect to AllTalk server at {alltalk_server_url}. Please check the URL and ensure AllTalk is running.")
        except Exception as e:
            raise Exception(f"Error connecting to AllTalk: {str(e)}")
        
        # Prepare the TTS request
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
            "text_filtering": "standard",
            "output_file_name": "comfyui_output",
            "output_file_timestamp": True,
            "autoplay": False,
            "autoplay_volume": 0.5,
            "rvccharacter_voice_gen": "Disabled",
            "rvccharacter_pitch": 0.0,
            "rvcnarrator_voice_gen": "Disabled",
            "rvcnarrator_pitch": 0.0,
            "text_not_inside": "character",
        }
        
        try:
            # Make the TTS generation request
            response = requests.post(
                f"{alltalk_server_url}/api/tts-generate",
                data=tts_params,
                timeout=300  # 5 minute timeout for generation
            )
            
            if response.status_code != 200:
                error_detail = response.json().get("error", "Unknown error")
                raise Exception(f"TTS generation failed: {error_detail}")
            
            response_data = response.json()

            if response_data.get("status") != "generate-success":
                raise Exception(f"TTS generation failed: {response_data.get('error', 'Unknown error')}")

            # Get the audio file path from response
            # AllTalk V1 returns complete URL, V2 returns relative path
            audio_url = response_data.get("output_file_url") or response_data.get("output_cache_url")
            output_path = response_data.get("output_file_path")

            if not audio_url:
                raise Exception(f"No audio URL returned from AllTalk server. Response data keys: {list(response_data.keys())}")

            # Download the audio file
            if audio_url.startswith("/"):
                # Relative URL (V2) - construct full URL
                full_audio_url = f"{alltalk_server_url}{audio_url}"
            else:
                # Complete URL (V1)
                full_audio_url = audio_url

            audio_response = requests.get(full_audio_url, timeout=30)
            if audio_response.status_code != 200:
                raise Exception(f"Failed to download audio file from {full_audio_url}: {audio_response.status_code} - {audio_response.text[:200]}")

            # Save audio file to ComfyUI output directory
            output_filename = os.path.basename(output_path) if output_path else "alltalk_audio.wav"
            local_audio_path = os.path.join(self.output_dir, output_filename)

            with open(local_audio_path, "wb") as f:
                f.write(audio_response.content)
            
            # Detect audio format
            format_type, format_desc = self._detect_audio_format(local_audio_path)
            file_size = os.path.getsize(local_audio_path)

            # Parse based on format
            if format_type == "wav":
                try:
                    audio_data, sample_rate = self._parse_wav(local_audio_path)
                except Exception as e:
                    # Add debug info for WAV parsing errors
                    with open(local_audio_path, "rb") as f:
                        header = f.read(64).hex()
                    raise Exception(
                        f"WAV parsing failed: {str(e)}\n"
                        f"File: {local_audio_path}\n"
                        f"Size: {file_size} bytes\n"
                        f"Header (hex): {header[:128]}\n"
                        f"This may indicate a corrupted file or unsupported WAV format."
                    )
            elif format_type in ["mp3", "ogg", "m4a", "flac"]:
                audio_data, sample_rate = self._parse_audio_generic(local_audio_path, format_type)
            else:
                # Unknown or error format
                with open(local_audio_path, "rb") as f:
                    header = f.read(16).hex()
                raise Exception(
                    f"Audio format detection failed: {format_desc}\n"
                    f"File: {local_audio_path}\n"
                    f"Size: {file_size} bytes\n"
                    f"Header (hex): {header}\n"
                    f"Fix: Verify AllTalk is configured to output WAV format in settings."
                )

            # Convert numpy array to PyTorch tensor (required by ComfyUI)
            import torch
            audio_tensor = torch.from_numpy(audio_data)

            audio_dict = {
                "waveform": audio_tensor,
                "sample_rate": sample_rate
            }
            
            return (audio_dict, local_audio_path)
        
        except requests.exceptions.Timeout:
            raise Exception("AllTalk server request timed out. The audio generation may be taking too long.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error communicating with AllTalk: {str(e)}")
        except Exception as e:
            raise Exception(f"Error generating TTS: {str(e)}")


class AllTalkVoiceLoader:
    """
    Helper node to load available voices from AllTalk server
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "alltalk_server_url": ("STRING", {
                    "default": "http://localhost:7851"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("voices_info",)
    FUNCTION = "get_voices"
    CATEGORY = "audio/tts"
    
    def get_voices(self, alltalk_server_url):
        """Fetch available voices from AllTalk server"""
        
        alltalk_server_url = alltalk_server_url.rstrip("/")
        
        try:
            response = requests.get(f"{alltalk_server_url}/api/voices", timeout=10)
            
            if response.status_code != 200:
                return ("Error: Could not fetch voices from AllTalk server",)
            
            response_data = response.json()
            
            if response_data.get("status") == "success":
                voices = response_data.get("voices", [])
                voices_text = "Available voices:\n" + "\n".join(voices)
                return (voices_text,)
            else:
                error_msg = response_data.get("message", "Unknown error")
                return (f"Error: {error_msg}",)
        
        except Exception as e:
            return (f"Error connecting to AllTalk: {str(e)}",)


class AllTalkSettingsLoader:
    """
    Helper node to load current settings from AllTalk server
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "alltalk_server_url": ("STRING", {
                    "default": "http://localhost:7851"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("settings_info",)
    FUNCTION = "get_settings"
    CATEGORY = "audio/tts"
    
    def get_settings(self, alltalk_server_url):
        """Fetch current settings from AllTalk server"""
        
        alltalk_server_url = alltalk_server_url.rstrip("/")
        
        try:
            response = requests.get(f"{alltalk_server_url}/api/currentsettings", timeout=10)
            
            if response.status_code != 200:
                return ("Error: Could not fetch settings from AllTalk server",)
            
            settings = response.json()
            
            # Format settings nicely
            info_lines = [
                f"Engine: {settings.get('current_engine_loaded', 'Unknown')}",
                f"Model: {settings.get('current_model_loaded', 'Unknown')}",
                f"DeepSpeed: {settings.get('deepspeed_enabled', False)}",
                f"LowVRAM: {settings.get('lowvram_enabled', False)}",
                f"Streaming: {settings.get('streaming_capable', False)}",
                f"Multi-voice: {settings.get('multivoice_capable', False)}",
            ]
            
            settings_text = "AllTalk Settings:\n" + "\n".join(info_lines)
            return (settings_text,)
        
        except Exception as e:
            return (f"Error connecting to AllTalk: {str(e)}",)


# Node class mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "AllTalkTTS": AllTalkTTSNode,
    "AllTalkVoiceLoader": AllTalkVoiceLoader,
    "AllTalkSettingsLoader": AllTalkSettingsLoader,
}

NODE_DISPLAY_NAMES = {
    "AllTalkTTS": "AllTalk TTS Generator",
    "AllTalkVoiceLoader": "AllTalk Voice Loader",
    "AllTalkSettingsLoader": "AllTalk Settings Loader",
}
