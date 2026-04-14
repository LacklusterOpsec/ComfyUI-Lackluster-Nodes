import torch

class LacklusterFirstLastFrameSelector:
    """
    A node that takes a batch of images and returns either the first or last frame
    based on a switch input.
    """

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE",),
                "mode": (["first", "last"], {"default": "first"}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("frame",)
    FUNCTION = "get_frame"
    CATEGORY = "Lackluster/Video"

    def get_frame(self, images: torch.Tensor, mode: str):
        # The input 'images' is a PyTorch tensor with shape (batch_size, height, width, channels)
        batch_size = images.shape[0]

        # Select frame based on mode
        if mode == "first":
            frame = images[0:1]
        else:  # mode == "last"
            frame = images[-1:]

        print(f"[LacklusterFirstLastFrameSelector] Input batch size: {batch_size}. Selected {mode} frame.")

        return (frame,)


NODE_CLASS_MAPPINGS = {"LacklusterFirstLastFrameSelector": LacklusterFirstLastFrameSelector}
NODE_DISPLAY_NAME_MAPPINGS = {"LacklusterFirstLastFrameSelector": "First/Last Frame Selector"}
