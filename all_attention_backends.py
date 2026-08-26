"""
ComfyUI custom node: Lackluster All Attention Backends

Dynamically exposes every attention backend registered by the running
ComfyUI build, including third-party backends that use ComfyUI's attention
registration API.

Designed for ComfyUI builds containing ModelPatcher.set_model_optimized_attention(),
including the changes from ComfyUI PR #15479.
"""

import logging

try:
    import comfy.ldm.modules.attention as comfy_attention
except Exception:
    comfy_attention = None


# Core backends in a useful/stable order. Any additional registered backend is
# appended automatically, so this node does not need updating for new plugins.
_PREFERRED_ORDER = (
    "pytorch",
    "comfy_kitchen_int8",
    "sage",
    "sage3",
    "flash",
    "xformers",
    "sub_quad",
    "split",
)


def _registered_backends():
    """Return the attention backends registered in this ComfyUI process."""
    if comfy_attention is None:
        return ["pytorch"]

    registry = getattr(comfy_attention, "REGISTERED_ATTENTION_FUNCTIONS", None)
    if not isinstance(registry, dict) or not registry:
        return ["pytorch"]

    names = list(registry.keys())

    # Keep known core backends predictable, then include anything registered
    # by newer ComfyUI versions or third-party custom nodes.
    ordered = [name for name in _PREFERRED_ORDER if name in registry]
    ordered.extend(sorted(name for name in names if name not in _PREFERRED_ORDER))

    return ordered or ["pytorch"]


class LacklusterModelAttentionBackend:
    """Patch a MODEL to use any attention backend registered by ComfyUI."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "attention": (_registered_backends(),),
            }
        }

    @classmethod
    def VALIDATE_INPUTS(cls, attention, **kwargs):
        # Validate against the live registry at queue/validation time
        registry = getattr(comfy_attention, "REGISTERED_ATTENTION_FUNCTIONS", {}) if comfy_attention else {}
        if registry and attention not in registry:
            return f"Attention backend '{attention}' is not registered. Available: {', '.join(registry.keys())}"
        return True

    RETURN_TYPES = ("MODEL",)
    RETURN_NAMES = ("model",)
    FUNCTION = "patch"
    CATEGORY = "Lackluster/Model"
    DESCRIPTION = (
        "Select any attention backend currently registered and available in "
        "ComfyUI. The list is generated dynamically from ComfyUI's attention "
        "registry."
    )

    def patch(self, model, attention):
        registry = getattr(comfy_attention, "REGISTERED_ATTENTION_FUNCTIONS", {}) if comfy_attention else {}

        if attention not in registry:
            available = ", ".join(registry.keys()) if registry else "none"
            raise RuntimeError(
                f"Attention backend '{attention}' is not currently available. "
                f"Available backends: {available}"
            )

        attention_function = comfy_attention.get_attention_function(attention)

        m = model.clone()

        if not hasattr(m, "set_model_optimized_attention"):
            raise RuntimeError(
                "This ComfyUI build does not have "
                "ModelPatcher.set_model_optimized_attention(). "
                "Update/apply ComfyUI PR #15479 or a newer build."
            )

        # Use ComfyUI's official model-level attention override. This is
        # important for container-aware backends such as comfy_kitchen_int8:
        # ComfyUI copies the backend's container_function when present.
        m.set_model_optimized_attention(attention_function)

        logging.info(
            "[Lackluster] Selected attention backend: %s",
            attention,
        )
        return (m,)


# Compatibility alias
ModelAttentionBackendAll = LacklusterModelAttentionBackend

NODE_CLASS_MAPPINGS = {
    "LacklusterModelAttentionBackend": LacklusterModelAttentionBackend,
    "ModelAttentionBackendAll": ModelAttentionBackendAll,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LacklusterModelAttentionBackend": "Lackluster Model Attention Backend (All)",
    "ModelAttentionBackendAll": "Model Attention Backend (All)",
}
