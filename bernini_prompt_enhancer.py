"""
BerniniPromptEnhancer v1.0

Lightweight ComfyUI node: prompt enhancement via LLM with task mode selection.
Uses Bernini's official per-task prompt templates to rewrite short instructions
into detailed editing/generation prompts.

Standalone -- no dependencies on ComfyUI-BerniniStudio.
"""

import base64
import json
import logging
import os
import re
from io import BytesIO

import numpy as np
from PIL import Image as PILImage

log = logging.getLogger("BerniniPromptEnhancer")

TASK_TYPES = [
    "v2v", "rv2v", "r2v", "t2v", "t2i", "r2i", "i2i",
    "i2v", "mv2v", "vi2v", "ads2v", "vrc2v",
]

SYSTEM_PROMPTS = {
    "default": "You are a helpful assistant.",
    "t2i": "You are a helpful assistant specialized in text-to-image generation.",
    "t2v": "You are a helpful assistant specialized in text-to-video generation.",
    "i2i": "You are a helpful assistant specialized in image editing.",
    "r2i": "You are a helpful assistant specialized in subject-to-image generation.",
    "i2v": "You are a helpful assistant specialized in image-to-video generation.",
    "v2v": "You are a helpful assistant specialized in video editing.",
    "r2v": "You are a helpful assistant specialized in subject-to-video generation.",
    "vi2v": "You are a helpful assistant specialized in video editing on content propagation.",
    "rv2v": "You are a helpful assistant specialized in video editing with reference.",
    "ads2v": "You are a helpful assistant specialized in ads insertion.",
    "vrc2v": (
        "You are a helpful assistant for editing. "
        "You may need to adjust the subject's action or position."
    ),
    "mv2v": (
        "You are a helpful assistant for editing. "
        "You might need to adjust the video's style, lighting, colors, "
        "textures, and the subject's pose or action."
    ),
}

DEFAULT_NEG_PROMPT = (
    "\u8272\u8c03\u8273\u4e3d\uff0c\u8fc7\u66dd\uff0c\u9759\u6001\uff0c"
    "\u7ec6\u8282\u6a21\u7cca\u4e0d\u6e05\uff0c\u5b57\u5e55\uff0c\u98ce"
    "\u683c\uff0c\u4f5c\u54c1\uff0c\u753b\u4f5c\uff0c\u753b\u9762\uff0c"
    "\u9759\u6b62\uff0c\u6574\u4f53\u53d1\u7070\uff0c\u6700\u5dee\u8d28"
    "\u91cf\uff0c\u4f4e\u8d28\u91cf\uff0cJPEG\u538b\u7f29\u6b8b\u7559"
    "\uff0c\u4e11\u964b\u7684\uff0c\u6b8b\u7f3a\u7684\uff0c\u591a\u4f59"
    "\u7684\u624b\u6307\uff0c\u753b\u5f97\u4e0d\u597d\u7684\u624b\u90e8"
    "\uff0c\u753b\u5f97\u4e0d\u597d\u7684\u8138\u90e8\uff0c\u7578\u5f62"
    "\u7684\uff0c\u6bc1\u5bb9\u7684\uff0c\u5f62\u6001\u7578\u5f62\u7684"
    "\u80a2\u4f53\uff0c\u624b\u6307\u878d\u5408\uff0c\u9759\u6b62\u4e0d"
    "\u52a8\u7684\u753b\u9762\uff0c\u6742\u4e71\u7684\u80cc\u666f\uff0c"
    "\u4e09\u6761\u817f\uff0c\u80cc\u666f\u4eba\u5f88\u591a\uff0c\u5012"
    "\u7740\u8d70"
)

ENHANCE_TEMPLATES = {
    "v2v": """Task: Video Editing
# ROLE
You are an expert Video-to-Video (V2V) Prompt Engineer. Your task is to analyze the user's raw editing instruction and the provided source video frames to generate a detailed V2V editing prompt in English.

# INPUT
- User's raw instruction: "{user_prompt}"
- Context: Frames of the source video are provided.

# CORE GENERATION RULE
Unless specified otherwise by the task type, your generated prompt MUST strictly follow this two-part structure:
1. Modifications: Specifically describe what needs to be changed. Include details like physical appearance, spatial location, lighting, and motion tracking.
2. Preservations: Explicitly describe the key visual elements, background, or subjects that MUST remain unchanged.
3. Concretization: If the user's instruction contains vague references to characters, objects, outfits, or styles, you MUST replace them with specific, well-known, named instances that match the existing visual style.
Note: Describe it naturally, for example, "Add an apple. The table and curtains remain unchanged."

# TASK CATEGORIES & TEMPLATES
Analyze the instruction and determine the specific editing task type, then generate using the corresponding template:
1. Replacement: "Replace [original element] with [new element]."
2. Addition: "Add [element] + [location/action]."
3. Object/Background Removal: "Delete [object description] + [location]."
4. Subtitle Removal: "Remove subtitles from the video."
5. Depth-to-Video: "Generate video with depth map. [Detailed description]"
6. Sketch-to-Video: Provide a detailed T2V-style description.
7. Colorization: "Colorize the video. [Scene and color description]"
8. Inpainting: "Inpaint this video. [Scene description to fill]"
9. Detection: "Detect the mask region of the [specific object]."
10. Stylization: "Convert the video to [style name]: [brief style details]."
11. Mixed Tasks: Seamlessly integrate all requirements into a single, cohesive instruction.
12. Camera Movement: "Apply camera motion: [Camera Movement Description]"
13. Change Camera Perspective: "Switch the camera to a [first/third]-person perspective" or "Move the camera [description]"
14. Change Focus: "Shift the focus to [subject], making it sharp. Blur [objects to be blurred]."
15. Other Tasks: Generate logically based on the specific situation.

# OUTPUT REQUIREMENT
Output ONLY the final enhanced English prompt. Do not include any explanations, greetings, or the category name.
Do not imagine things that do not appear in the video.""",

    "i2i": """Task: Image Editing
# ROLE
You are an expert Image-to-Image (I2I) Prompt Engineer. Your task is to analyze the user's raw editing instruction and the provided source image to generate a detailed I2I editing prompt in English.

# INPUT
- User's raw instruction: "{user_prompt}"
- Context: The source image is provided.

# CORE GENERATION RULE
Your generated prompt MUST follow this structure:
1. Modifications: Specifically describe what needs to be changed, including physical appearance, spatial location, lighting, shadows, and perspective consistency.
2. Preservations: Explicitly describe key visual elements that MUST remain unchanged.
3. Concretization: Replace vague references with specific, well-known, named instances matching the existing visual style.
Describe it naturally, e.g., "Add an apple. The table and curtains remain unchanged."

# TASK CATEGORIES
1. Replacement: "Replace [original] with [new]."
2. Addition: "Add [element] + [location]."
3. Removal: "Delete [object] + [location]."
4. Text/Watermark Removal: "Remove [text/watermark] from the image."
5. Depth-to-Image: "Generate image with depth map. [Target description]"
6. Sketch-to-Image: Detailed T2I description.
7. Colorization: "Colorize the image. [Scene and colors]"
8. Inpainting: "Inpaint this image. [Region description]"
9. Outpainting: "Extend the image [direction]. [Extended content]"
10. Detection: "Detect the mask region of the [specific object]."
11. Stylization: "Convert the image to [style]: [details]."
12. Relighting: "Relight the image: [direction, temperature, intensity, shadows]."
13. Pose/Expression: "Change the [subject]'s [pose/expression] to [target]."
14. Viewpoint Change: "View the scene from [target viewpoint]."
15. Focus Change: "Shift focus to [subject]. Blur [objects] with bokeh."
16. Mixed: Integrate all requirements cohesively.

# OUTPUT REQUIREMENT
Output ONLY the final enhanced English prompt. Do not imagine things not in the image.""",

    "rv2v": """You are an expert at writing prompts for reference-image-guided video editing. I'm providing you with:
1. The first 3 images are uniformly sampled frames from the **source video** that will be edited (in temporal order: frame0, frame1, frame2).
2. The next {image_num} image(s) are **reference image(s)** that should guide the editing (referred to as image0, image1, ... in order).
3. An original editing instruction.

Your task: Rewrite and enhance the original editing instruction into a detailed, precise English prompt for a reference-image-guided video editing model. The output is a single paragraph: **editing instruction + detailed description of the target edited video**.

Follow these rules strictly:
1. Output format: editing instruction followed by detailed target video description, as one continuous paragraph.
2. Match the edit type: use the verb matching the intent -- "Replace...", "Remove...", "Add...", "Restyle...", "Transfer the motion/pose of... to...", etc.
3. Add != Replace: for addition tasks, write as additions, not replacements.
4. Allow natural shape/size differences.
5. Describe the target video directly: don't use "after editing..." or "in the edited video...".
6. Faithful reference appearance: match what's visible in the reference image.
7. Screen-perspective left/right: all directions from camera perspective.
8. Preserve unchanged elements explicitly: camera framing, lighting, background, motion, etc.
9. For style/motion references: describe resulting style/motion in concrete language.
10. No parentheses in output.
11. English only.
12. Keep detail level similar to this example:

"Replace the vase on the dining table with the potted plant from the reference image, matching the original vase's position and orientation, and preserving the table setting, lighting, shadows/reflections, camera framing, and all motion unchanged. A bright, modern dining/living room in soft daylight with a light-wood rectangular dining table..."

Return ONLY a JSON object with key "rewritten_text". No extra text.

Original instruction:
{user_prompt}""",

    "r2v": """You are an expert at writing subject-driven video generation prompts. I'm providing you with:
1. {image_num} reference image(s) of the subject(s) that will appear in the video (referred to as image0, image1, image2, ... in order).
2. An original video description text.

Your task is to rewrite the original description into TWO parts concatenated together:

**Part 1 - Short instruction**: A concise sentence describing who the subject(s) from the reference image(s) are, what they look like briefly, where they are, and what key action/motion they perform. Reference the subject(s) using "image0", "image1", etc.

**Part 2 - Long instruction**: A detailed "Generate a video where..." paragraph that describes:
- The subject(s) with detailed appearance (hair, clothing, accessories, expression), referencing as "the person/man/woman from image0" etc.
- The scene/environment in detail (background, lighting, objects, atmosphere).
- The motion and actions in a step-by-step temporal sequence.

Requirements:
- Reference each subject using "image0", "image1", etc.
- Appearance description based on what you actually see in the reference image(s).
- English only.
- Return ONLY a JSON object with key "rewritten_text".

Original description:
{user_prompt}""",

    "r2i": """You are an expert at writing subject-driven image generation prompts. I'm providing you with:
1. {image_num} reference image(s) of the subject(s) (referred to as image0, image1, ... in order).
2. An original image description text.

Rewrite into TWO parts concatenated together:
**Part 1 - Short instruction**: Concise sentence about the subjects, their appearance, location, and composition.
**Part 2 - Long instruction**: Detailed "Generate an image where..." paragraph with appearance, scene, and composition.

Reference subjects using "image0", "image1", etc. English only.
Return ONLY a JSON object with key "rewritten_text".

Original description:
{user_prompt}""",

    "t2v": """You are a film director enhancing a text-to-video prompt. Add cinematic elements: lighting (source, intensity, angle), camera (shot size, angle, composition), color tone, and detailed motion sequences. Keep the original intent. Output 60-200 words, English only.

If the prompt describes a specific style (anime, 2D illustration, etc.), do NOT add film/cinematography aesthetics that contradict it. For non-realistic styles, focus on composition, color palette, and motion only.

Original prompt: {user_prompt}""",

    "t2i": """You are a photographer enhancing a text-to-image prompt. Add photographic elements: lighting (source, intensity, angle), camera (shot size, angle, composition), color tone, and spatial composition. Do NOT describe any motion, camera movement, or temporal sequences -- this is a static image. Output 60-200 words, English only.

If the prompt describes a non-photographic style, focus on composition, color, and spatial arrangement only.

Original prompt: {user_prompt}""",

    "vi2v": """Task: Video Content Propagation / Reference Insertion
User's editing instruction: "{user_prompt}"

Determine which sub-task applies based on the instruction:
- Propagation: Return exactly "edit the video following the first frame."
- Reference insertion: Format as "Integrate the [object] from the image into the video in a reasonable way."
- Reference replacement: Describe replacing the source object with the reference object.

Output ONLY the final English prompt.""",

    "ads2v": """Task: Ads Insertion in Video
User's instruction: "{user_prompt}"

Generate a concise English ad insertion instruction in one sentence.
Example: "Add Starbucks Latte wallpaper on the second floor across the street"

Output ONLY the final English prompt.""",

    "i2v": """Task: Image-to-Video Generation
User's prompt: "{user_prompt}"

Generate an English prompt describing the video content (actions, camera movement, scene).
Describe motion and temporal flow. Output ONLY the final English prompt.""",

    "default": """You are a helpful assistant that enhances prompts for video generation and editing. Rewrite the following instruction to be more detailed and specific, adding visual details, motion descriptions, and preservation notes where appropriate. English only.

Instruction: {user_prompt}""",
}


def _get_system_prompt(task_type):
    return SYSTEM_PROMPTS.get(task_type, SYSTEM_PROMPTS["default"])


def _get_enhance_template(task_type):
    return ENHANCE_TEMPLATES.get(task_type, ENHANCE_TEMPLATES["default"])


def _llm_headers(api_format="Ollama", include_json=True):
    headers = {}
    if include_json:
        headers["Content-Type"] = "application/json"
    if api_format != "Ollama":
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        org_id = os.environ.get("OPENAI_ORG_ID", "").strip()
        if org_id:
            headers["OpenAI-Organization"] = org_id
        project_id = os.environ.get("OPENAI_PROJECT_ID", "").strip()
        if project_id:
            headers["OpenAI-Project"] = project_id
    return headers


def _is_openai_new_completion_model(model):
    model = (model or "").strip().lower()
    return model.startswith(("gpt-5", "o1", "o3", "o4"))


def _apply_openai_generation_options(payload, model, max_tokens=2048, temperature=0.7):
    if _is_openai_new_completion_model(model):
        payload["max_completion_tokens"] = max_tokens
    else:
        payload["max_tokens"] = max_tokens
        payload["temperature"] = temperature


class BerniniPromptEnhancer:
    """Prompt-only Bernini enhancement node.

    Takes a raw prompt + task mode, optionally enhances it through an LLM,
    and outputs the enhanced STRING. No VAE, no conditioning, no latents.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Raw instruction or generation prompt. Use the Enhance button "
                               "or enable auto-enhance to rewrite with the task template.",
                }),
                "task_type": (TASK_TYPES, {
                    "default": "v2v",
                    "tooltip": "Bernini task mode. Determines the enhancement template and "
                               "system prompt used by the LLM.",
                }),
                "ollama_url": ("STRING", {
                    "default": "http://127.0.0.1:11434",
                    "tooltip": "LLM endpoint URL (Ollama or vLLM/OpenAI-compatible).",
                }),
                "ollama_model": ("STRING", {
                    "default": "",
                    "tooltip": "LLM model name. Leave empty to skip enhancement (pass-through).",
                }),
                "api_format": (["Ollama", "OpenAI / vLLM"], {
                    "default": "Ollama",
                    "tooltip": "Ollama uses /api/chat. OpenAI/vLLM uses /v1/chat/completions.",
                }),
                "auto_enhance": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "When enabled, enhances the prompt server-side on every queue.",
                }),
            },
            "optional": {
                "image": ("IMAGE", {
                    "tooltip": "Input image for vision-enabled LLM enhancement (i2i, i2v, etc.). "
                               "Converted to base64 and sent to multimodal models.",
                }),
                "text_input": ("STRING", {
                    "forceInput": True,
                    "multiline": True,
                    "tooltip": "Text node connection input. If connected, replaces the prompt field.",
                }),
                "negative_prompt": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Custom negative prompt. Leave empty to use Bernini's default.",
                }),
                "temperature": ("FLOAT", {
                    "default": 0.7, "min": 0.0, "max": 2.0, "step": 0.01,
                    "tooltip": "LLM temperature. Lower = more deterministic. GPT-5 / o-series "
                               "models ignore this and use their internal default.",
                }),
                "max_tokens": ("INT", {
                    "default": 2048, "min": 64, "max": 8192, "step": 64,
                    "tooltip": "Maximum tokens in the LLM response.",
                }),
                "seed": ("INT", {
                    "default": 0, "min": 0, "max": 2147483647,
                    "tooltip": "LLM seed for reproducibility. 0 = random. "
                               "Ollama only; ignored by OpenAI/vLLM endpoints.",
                }),
                "prepend_system_prompt": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Prepend the task system prompt to the enhanced output. "
                               "Useful for CLIPTextEncode / T5 conditioning.",
                }),
                "unload_ollama": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Tell Ollama to unload the model from VRAM after enhancement.",
                }),
            },
            "hidden": {
                "unique_id": "UNIQUE_ID",
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("enhanced_prompt", "negative_prompt")
    FUNCTION = "execute"
    CATEGORY = "Lackluster/Prompt"

    def execute(
        self,
        prompt,
        task_type,
        ollama_url="http://127.0.0.1:11434",
        ollama_model="",
        api_format="Ollama",
        auto_enhance=False,
        image=None,
        text_input="",
        negative_prompt="",
        temperature=0.7,
        max_tokens=2048,
        seed=0,
        prepend_system_prompt=True,
        unload_ollama=False,
        unique_id=None,
    ):
        working_prompt = (text_input if text_input.strip() else prompt).strip()
        neg_prompt = negative_prompt.strip() if negative_prompt.strip() else DEFAULT_NEG_PROMPT

        if auto_enhance and ollama_model and working_prompt:
            log.info("[BerniniPromptEnhancer] Auto-enhance triggered (model=%s, task=%s)",
                     ollama_model, task_type)
            enhanced = _server_enhance(
                working_prompt, task_type, ollama_url, ollama_model,
                api_format, temperature, max_tokens, seed, unload_ollama,
                image=image,
            )
            if enhanced:
                if prepend_system_prompt:
                    sys_prompt = _get_system_prompt(task_type)
                    enhanced = sys_prompt + " " + enhanced
                log.info("[BerniniPromptEnhancer] Enhanced prompt (%d chars)", len(enhanced))
                try:
                    from server import PromptServer
                    PromptServer.instance.send_sync("bernini_enhanced", {
                        "node": unique_id, "text": enhanced,
                    })
                except Exception:
                    pass
                return (enhanced, neg_prompt)
            log.warning("[BerniniPromptEnhancer] Enhancement returned nothing; using original")

        if prepend_system_prompt and working_prompt:
            working_prompt = _get_system_prompt(task_type) + " " + working_prompt

        return (working_prompt, neg_prompt)


def _tensor_to_base64(image_tensor):
    i = image_tensor[0].cpu().numpy() * 255
    img = PILImage.fromarray(np.clip(i, 0, 255).astype(np.uint8))
    buf = BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _server_enhance(user_prompt, task_type, url, model, api_format,
                    temperature=0.7, max_tokens=2048, seed=0, unload_ollama=False,
                    image=None):
    import urllib.request
    import urllib.error

    url = url.rstrip("/")
    template = _get_enhance_template(task_type)
    formatted = template.format(user_prompt=user_prompt, image_num=1)
    sys_prompt = _get_system_prompt(task_type)

    image_b64 = _tensor_to_base64(image) if image is not None else None

    if api_format == "Ollama":
        options = {"temperature": temperature, "num_ctx": 8192}
        if seed > 0:
            options["seed"] = seed
        messages = [
            {"role": "system", "content": sys_prompt},
        ]
        user_msg = {"role": "user", "content": formatted}
        if image_b64:
            user_msg["images"] = [image_b64]
        messages.append(user_msg)
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": options,
        }
        if unload_ollama:
            payload["keep_alive"] = 0
        endpoint = f"{url}/api/chat"
    else:
        user_content = [{"type": "text", "text": formatted}]
        if image_b64:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_b64}"},
            })
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_content},
            ],
            "stream": False,
        }
        _apply_openai_generation_options(payload, model, max_tokens=max_tokens, temperature=temperature)
        if seed > 0:
            payload["seed"] = seed
        endpoint = f"{url}/v1/chat/completions"

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            endpoint, data=data,
            headers=_llm_headers(api_format, include_json=True),
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        if api_format == "Ollama":
            text = (result.get("message", {}).get("content") or "").strip()
        else:
            text = (result.get("choices", [{}])[0]
                    .get("message", {}).get("content") or "").strip()

        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        json_text = json_match.group(1).strip() if json_match else text.strip()
        if json_text.startswith("{"):
            try:
                parsed = json.loads(json_text)
                if isinstance(parsed, dict) and "rewritten_text" in parsed:
                    text = parsed["rewritten_text"]
            except Exception:
                pass

        return text if text else None
    except Exception as e:
        log.warning("[BerniniPromptEnhancer] Enhance failed: %s: %s", type(e).__name__, e)
        return None


NODE_CLASS_MAPPINGS = {"BerniniPromptEnhancer": BerniniPromptEnhancer}
NODE_DISPLAY_NAME_MAPPINGS = {"BerniniPromptEnhancer": "Bernini Prompt Enhancer"}


try:
    from server import PromptServer
    from aiohttp import web
    import aiohttp

    _routes = PromptServer.instance.routes

    @_routes.post("/bernini_enhancer/models")
    async def _be_models(request):
        try:
            data = await request.json()
        except Exception:
            data = {}
        url = (data.get("ollama_url") or "http://127.0.0.1:11434").rstrip("/")
        api_format = data.get("api_format", "Ollama")
        try:
            async with aiohttp.ClientSession() as session:
                if api_format == "Ollama":
                    async with session.get(
                        f"{url}/api/tags",
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as r:
                        if r.status != 200:
                            text = await r.text()
                            return web.json_response(
                                {"error": f"Ollama HTTP {r.status}: {text[:200]}"},
                                status=502,
                            )
                        tags = await r.json()
                    models = sorted(
                        (m.get("name") or m.get("model") or "")
                        for m in tags.get("models", []) if m
                    )
                else:
                    async with session.get(
                        f"{url}/v1/models",
                        headers=_llm_headers(api_format, include_json=False),
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as r:
                        if r.status != 200:
                            text = await r.text()
                            return web.json_response(
                                {"error": f"OpenAI HTTP {r.status}: {text[:200]}"},
                                status=502,
                            )
                        resp = await r.json()
                    models = sorted(
                        m.get("id", "") for m in resp.get("data", []) if m
                    )
            return web.json_response({"models": [m for m in models if m]})
        except Exception as e:
            return web.json_response(
                {"error": f"Failed: {type(e).__name__}: {e}"}, status=502
            )

    @_routes.post("/bernini_enhancer/generate")
    async def _be_generate(request):
        try:
            data = await request.json()
        except Exception as e:
            return web.json_response({"error": f"Invalid JSON: {e}"}, status=400)

        url = (data.get("ollama_url") or "http://127.0.0.1:11434").rstrip("/")
        model = data.get("model")
        if not model:
            return web.json_response({"error": "No model selected"}, status=400)

        user_prompt = (data.get("prompt") or "").strip()
        if not user_prompt:
            return web.json_response({"error": "Empty prompt"}, status=400)

        task_type = data.get("task_type", "default")
        api_format = data.get("api_format", "Ollama")
        image_num = data.get("image_num", 1)
        unload_ollama = data.get("unload_ollama", False)
        temperature = data.get("temperature", 0.7)
        max_tokens = data.get("max_tokens", 2048)
        seed_val = data.get("seed", 0)
        image_b64 = data.get("image", None)

        custom_template = data.get("custom_template", "")
        template = custom_template if custom_template.strip() else _get_enhance_template(task_type)
        formatted_prompt = template.format(user_prompt=user_prompt, image_num=image_num)
        sys_prompt = _get_system_prompt(task_type)

        if api_format == "Ollama":
            options = {"temperature": temperature, "num_ctx": 8192}
            if seed_val > 0:
                options["seed"] = seed_val
            messages = [
                {"role": "system", "content": sys_prompt},
            ]
            user_msg = {"role": "user", "content": formatted_prompt}
            if image_b64:
                user_msg["images"] = [image_b64]
            messages.append(user_msg)
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": options,
            }
            if unload_ollama:
                payload["keep_alive"] = 0
            endpoint = f"{url}/api/chat"
        else:
            user_content = [{"type": "text", "text": formatted_prompt}]
            if image_b64:
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                })
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_content},
                ],
                "stream": False,
            }
            _apply_openai_generation_options(payload, model, max_tokens=max_tokens, temperature=temperature)
            if seed_val > 0:
                payload["seed"] = seed_val
            endpoint = f"{url}/v1/chat/completions"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=payload,
                    headers=_llm_headers(api_format, include_json=True),
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as r:
                    if r.status != 200:
                        text = await r.text()
                        return web.json_response(
                            {"error": f"LLM HTTP {r.status}: {text[:300]}"},
                            status=502,
                        )
                    resp = await r.json()

            if api_format == "Ollama":
                text = (resp.get("message", {}).get("content") or "").strip()
            else:
                text = (resp.get("choices", [{}])[0]
                        .get("message", {}).get("content") or "").strip()

            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            json_text = json_match.group(1).strip() if json_match else text.strip()
            if json_text.startswith("{"):
                try:
                    parsed = json.loads(json_text)
                    if isinstance(parsed, dict) and "rewritten_text" in parsed:
                        text = parsed["rewritten_text"]
                except Exception:
                    pass

            return web.json_response({"response": text})
        except Exception as e:
            return web.json_response(
                {"error": f"Failed: {type(e).__name__}: {e}"}, status=502
            )

    @_routes.post("/bernini_enhancer/unload")
    async def _be_unload(request):
        try:
            data = await request.json()
        except Exception:
            data = {}
        url = (data.get("ollama_url") or "http://127.0.0.1:11434").rstrip("/")
        model = data.get("model")
        if not model:
            return web.json_response({"error": "No model selected"}, status=400)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{url}/api/generate",
                    json={"model": model, "keep_alive": 0},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as r:
                    if r.status != 200:
                        text = await r.text()
                        return web.json_response(
                            {"error": f"Ollama HTTP {r.status}: {text[:200]}"},
                            status=502,
                        )
                    await r.read()
            log.info("[BerniniEnhancer] Unloaded model '%s' from Ollama VRAM", model)
            return web.json_response({"status": "unloaded", "model": model})
        except Exception as e:
            return web.json_response(
                {"error": f"Failed: {type(e).__name__}: {e}"}, status=502
            )

    @_routes.post("/bernini_enhancer/get_template")
    async def _be_get_template(request):
        try:
            data = await request.json()
        except Exception:
            data = {}
        task = data.get("task_type", "default")
        return web.json_response({
            "template": _get_enhance_template(task),
            "task_type": task,
        })

except ImportError:
    log.warning("[BerniniEnhancer] PromptServer not available; server routes not registered.")