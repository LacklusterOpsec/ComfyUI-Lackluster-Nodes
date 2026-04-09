"""
ComfyUI node for AllTalk TTS - makes requests to an existing AllTalk installation
"""
import requests
import os
from pathlib import Path
import folder_paths

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
            audio_url = response_data.get("output_cache_url") or response_data.get("output_file_url")
            output_path = response_data.get("output_file_path")
            
            if not audio_url:
                raise Exception("No audio URL returned from AllTalk server")
            
            # Download the audio file
            if audio_url.startswith("/"):
                # Relative URL - construct full URL
                full_audio_url = f"{alltalk_server_url}{audio_url}"
            else:
                full_audio_url = audio_url
            
            audio_response = requests.get(full_audio_url, timeout=30)
            if audio_response.status_code != 200:
                raise Exception(f"Failed to download audio file: {audio_response.status_code}")
            
            # Save audio file to ComfyUI output directory
            output_filename = os.path.basename(output_path) if output_path else "alltalk_audio.wav"
            local_audio_path = os.path.join(self.output_dir, output_filename)
            
            with open(local_audio_path, "wb") as f:
                f.write(audio_response.content)
            
            # Return audio data and path
            # ComfyUI expects audio as a dictionary with "waveform" and "sample_rate"
            import wave
            with wave.open(local_audio_path, "rb") as wav_file:
                sample_rate = wav_file.getframerate()
                frames = wav_file.readframes(wav_file.getnframes())
                
                import numpy as np
                audio_data = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
                
                # Reshape for stereo/mono compatibility
                if len(audio_data.shape) == 1:
                    audio_data = audio_data.reshape(1, -1)
                else:
                    audio_data = audio_data.T
            
            audio_dict = {
                "waveform": audio_data,
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
