import subprocess

class Lackluster_UV_Outdated:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "check": ("BOOLEAN", {"default": True}),
                "use_uv": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("outdated_packages",)
    FUNCTION = "get_outdated"

    CATEGORY = "Lackluster/System"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        # Always run and don't cache
        return float("NaN")

    def get_outdated(self, check, use_uv):
        if not check:
            return ("Check disabled. Set check to True to run.",)
            
        try:
            cmd = ["uv", "pip", "list", "--outdated"] if use_uv else ["pip", "list", "--outdated"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            output = result.stdout.strip()
            
            if result.returncode != 0:
                error_msg = result.stderr.strip()
                return (f"Command failed with error:\n{error_msg}",)
                
            if not output:
                output = "All packages are up to date."
                
            return (output,)
            
        except FileNotFoundError:
            cmd_name = "uv" if use_uv else "pip"
            return (f"Error: '{cmd_name}' command not found. Please ensure it is installed and in your PATH.",)
        except Exception as e:
            return (f"An error occurred: {str(e)}",)

NODE_CLASS_MAPPINGS = {
    "Lackluster_UV_Outdated": Lackluster_UV_Outdated
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Lackluster_UV_Outdated": "Pip/UV Outdated Packages (Lackluster)"
}
