class Lackluster_Text_Multiline:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "", "multiline": True, "dynamicPrompts": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "process_text"

    CATEGORY = "Lackluster/Text"

    def process_text(self, text):
        # Split text into lines
        lines = text.splitlines()
        
        processed_lines = []
        for line in lines:
            processed_lines.append(line)
        
        # Rejoin the lines
        result = "\n".join(processed_lines)

        return (result,)

NODE_CLASS_MAPPINGS = {
    "Lackluster_Text_Multiline": Lackluster_Text_Multiline
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Lackluster_Text_Multiline": "Text Multiline (Lackluster)"
}
