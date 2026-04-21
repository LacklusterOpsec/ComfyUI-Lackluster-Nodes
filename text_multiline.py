class Lackluster_Text_Multiline:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"default": "", "multiline": True, "dynamicPrompts": True}),
                "strip_comments": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "process_text"

    CATEGORY = "Lackluster Nodes/Text"

    def process_text(self, text, strip_comments):
        # Split text into lines
        lines = text.splitlines()
        
        processed_lines = []
        for line in lines:
            # Optionally skip lines that start with '#' after stripping whitespace
            if strip_comments and line.strip().startswith('#'):
                continue
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
