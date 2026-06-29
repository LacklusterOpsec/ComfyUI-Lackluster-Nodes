/**
 * BerniniPromptEnhancer - Editor JS v1.0
 *
 * Frontend for the BerniniPromptEnhancer ComfyUI node.
 * Task-aware editor with guidance display, system prompt preview,
 * and LLM prompt enhancement.
 */
const { app } = window.comfyAPI.app;
const { api } = window.comfyAPI.api;

const C = {
    bg:       "#18181b",
    panel:    "#27272a",
    deep:     "#111113",
    input:    "#0a0a0b",
    border:   "#3f3f46",
    borderIn: "#52525b",
    text:     "#e4e4e7",
    muted:    "#a1a1aa",
    dim:      "#71717a",
    accent:   "#f43f5e",
    accentDim:"#be123c",
    amber:    "#fbbf24",
    green:    "#4ade80",
    cyan:     "#22d3ee",
};

const HIDDEN_WIDGETS = [
    "task_type", "prompt", "negative_prompt",
    "ollama_url", "ollama_model", "use_default_neg",
    "api_format", "auto_enhance", "unload_ollama",
    "temperature", "max_tokens", "seed", "prepend_system_prompt",
];

const TASK_META = {
    "v2v":   { label: "Video Edit",           wire: "source_video",                       guidance: "v2v_apg",
               desc: "General video editing: add, remove, or replace objects, restyle, change camera, colorize, inpaint. Prompt describes modifications + what to preserve." },
    "rv2v":  { label: "Ref + Video Edit",     wire: "source_video + image0",   guidance: "rv2v",
               desc: "Edit a video guided by reference image(s). The reference provides the appearance for replacements or additions.",
               refHint: "Reference images in your prompt as: image0, image1, image2 (not reference_image_0). e.g. 'Replace the man with the person from image0'." },
    "r2v":   { label: "Reference to Video",   wire: "image0",                  guidance: "r2v_apg",
               desc: "Generate a new video starring the subject(s) from your reference image(s). No source video needed.",
               refHint: "Reference subjects as: image0, image1, etc. e.g. 'The woman from image0 walks through a park'." },
    "t2v":   { label: "Text to Video",        wire: "none",                               guidance: "t2v_apg",
               desc: "Pure text-to-video generation. No source media. Describe the scene, subjects, motion, and camera work." },
    "t2i":   { label: "Text to Image",        wire: "none",                               guidance: "t2v_apg",
               desc: "Pure text-to-image generation. No source media. Describe composition, lighting, and subject matter." },
    "r2i":   { label: "Reference to Image",   wire: "image0",                  guidance: "r2v_apg",
               desc: "Generate a new still image featuring the subject(s) from your reference image(s).",
               refHint: "Reference subjects as: image0, image1, etc. e.g. 'The man from image0 sitting at a desk'." },
    "i2i":   { label: "Image to Image",       wire: "source_video (1 frame)",             guidance: "v2v",
               desc: "Standard image editing. Feed a single image as source_video. Add, remove, replace objects, restyle, relighting, inpaint, outpaint." },
    "i2v":   { label: "Image to Video",       wire: "image0",                  guidance: "r2v_apg",
               desc: "Animate a static reference image into a video.",
               refHint: "Reference the image as: image0. e.g. 'The scene from image0 comes to life as the camera slowly pushes in'." },
    "mv2v":  { label: "Motion Edit",          wire: "source_video",                       guidance: "v2v_apg",
               desc: "Change the motion, pose, or action of subjects in a video while preserving their identity and the scene. e.g. 'the person begins dancing'." },
    "vi2v":  { label: "Content Propagation",  wire: "source_video + image0",   guidance: "v2v_apg",
               desc: "Propagate an edit from the first frame to the full video, or composite reference content into the source video.",
               refHint: "Reference the content as: image0. e.g. 'Integrate the object from image0 into the video'." },
    "ads2v": { label: "Ads Insertion",        wire: "source_video + image0",   guidance: "v2v_apg",
               desc: "Insert a logo, ad, or branded element into a video scene. Bernini matches perspective, lighting, and occlusion.",
               refHint: "The ad/logo is image0. e.g. 'Add the image0 logo on the billboard on the left'." },
    "vrc2v": { label: "Video Retarget",       wire: "source_video + image0",   guidance: "rv2v",
               desc: "Retarget or adjust a subject's position, action, or framing using reference guidance.",
               refHint: "Reference the guide as: image0. e.g. 'Match the pose of the person in image0'." },
};

const SYSTEM_PROMPTS = {
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
    "vrc2v": "You are a helpful assistant for editing. You may need to adjust the subject's action or position.",
    "mv2v": "You are a helpful assistant for editing. You might need to adjust the video's style, lighting, colors, textures, and the subject's pose or action.",
};

function hideWidget(w) {
    if (!w) return;
    w.__bernini_hidden = true;
    w.computeSize = () => [0, -4];
    w.draw = () => {};
    const elems = [w.inputEl, w.element].filter(Boolean);
    for (const el of elems) {
        el.style.display = "none";
        el.hidden = true;
        let p = el.parentElement;
        let hops = 0;
        while (p && hops < 6) {
            if (p.classList && p.classList.contains("dom-widget")) {
                p.style.display = "none";
                p.style.height = "0px";
                p.style.minHeight = "0px";
                p.style.padding = "0";
                p.style.margin = "0";
                break;
            }
            p = p.parentElement;
            hops++;
        }
    }
}

function findWidget(node, name) {
    return (node.widgets || []).find(w => w.name === name);
}

function swallowKeys(el) {
    el.addEventListener("keydown", e => e.stopPropagation());
    el.addEventListener("keyup", e => e.stopPropagation());
    el.addEventListener("keypress", e => e.stopPropagation());
}

function el(tag, styles, text) {
    const e = document.createElement(tag);
    if (styles) Object.assign(e.style, styles);
    if (text !== undefined) e.textContent = text;
    return e;
}

class BerniniEnhancerEditor {
    constructor(node, mount) {
        this.node = node;
        this.mount = mount;
        node._berniniEnhancerEditor = this;
        this.taskWidget = findWidget(node, "task_type");
        this.promptWidget = findWidget(node, "prompt");
        this.negWidget = findWidget(node, "negative_prompt");
        this.urlWidget = findWidget(node, "ollama_url");
        this.modelWidget = findWidget(node, "ollama_model");
        this.apiFormatWidget = findWidget(node, "api_format");
        this.autoEnhanceWidget = findWidget(node, "auto_enhance");
        this.unloadOllamaWidget = findWidget(node, "unload_ollama");
        this.tempWidget = findWidget(node, "temperature");
        this.maxTokensWidget = findWidget(node, "max_tokens");
        this.seedWidget = findWidget(node, "seed");
        this.prependSysWidget = findWidget(node, "prepend_system_prompt");
        this.ollamaOpen = false;
        this._build();
    }

    _si(el) {
        Object.assign(el.style, {
            width: "100%", minWidth: "0", boxSizing: "border-box",
            background: C.input, color: C.text,
            border: "1px solid " + C.borderIn, borderRadius: "4px",
            padding: "4px 6px", fontFamily: "inherit", fontSize: "11px", outline: "none",
        });
        el.onfocus = () => el.style.borderColor = C.accent;
        el.onblur  = () => el.style.borderColor = C.borderIn;
    }

    _sta(el) {
        this._si(el);
        el.style.resize = "none";
    }

    _build() {
        for (const name of HIDDEN_WIDGETS) hideWidget(findWidget(this.node, name));

        this.root = el("div", {
            display: "flex", flexDirection: "column", gap: "8px",
            background: C.bg, color: C.text, padding: "10px",
            borderRadius: "6px", fontFamily: "ui-sans-serif, system-ui, sans-serif",
            fontSize: "12px", width: "100%", height: "100%", boxSizing: "border-box",
            boxShadow: "inset 0 2px 5px rgba(0,0,0,0.5)",
        });
        this.mount.appendChild(this.root);

        /* header */
        const header = el("div", {
            display: "flex", justifyContent: "space-between", alignItems: "center",
            paddingBottom: "6px", borderBottom: "1px solid " + C.border,
        });
        header.appendChild(el("div", {
            fontWeight: "700", fontSize: "14px", color: C.accent, letterSpacing: "0.5px",
        }, "Bernini Prompt Enhancer"));
        const badges = el("div", { display: "flex", gap: "4px", alignItems: "center" });
        this.guidanceBadge = el("span", {
            fontSize: "9px", color: C.cyan, background: "rgba(34,211,238,0.1)",
            padding: "2px 6px", borderRadius: "3px", border: "1px solid rgba(34,211,238,0.25)",
            fontFamily: "monospace",
        }, "");
        badges.appendChild(this.guidanceBadge);
        this.imageIndicator = el("span", {
            fontSize: "9px", color: C.dim, background: C.deep,
            padding: "2px 6px", borderRadius: "3px", border: "1px solid " + C.borderIn,
            display: "none",
        }, "");
        badges.appendChild(this.imageIndicator);
        this.layoutBtn = el("button", {
            background: "transparent", color: C.dim, border: "1px solid " + C.borderIn,
            borderRadius: "3px", padding: "1px 7px", fontSize: "9px", cursor: "pointer",
        }, "Layout");
        this.layoutBtn.onclick = () => {
            this._layoutMode = this._layoutMode === "split" ? "stacked" : "split";
            try { localStorage.setItem("berniniEnhancerLayout", this._layoutMode); } catch (e) {}
            this._applyLayout();
        };
        badges.appendChild(this.layoutBtn);
        badges.appendChild(el("span", {
            fontSize: "9px", color: C.muted, background: C.deep,
            padding: "2px 6px", borderRadius: "3px", border: "1px solid " + C.borderIn,
        }, "v1.0"));
        header.appendChild(badges);
        this.root.appendChild(header);

        /* task selector */
        const taskBox = el("div", {
            background: C.panel, border: "1px solid " + C.borderIn,
            borderRadius: "4px", padding: "8px",
            display: "flex", flexDirection: "column", gap: "5px",
        });
        taskBox.appendChild(el("div", {
            fontWeight: "600", fontSize: "10px", color: C.muted,
            textTransform: "uppercase", letterSpacing: "0.5px",
        }, "Task Mode"));

        this.taskSelect = document.createElement("select");
        this._si(this.taskSelect);
        if (this.taskWidget && this.taskWidget.options && this.taskWidget.options.values) {
            for (const v of this.taskWidget.options.values) {
                const opt = document.createElement("option");
                opt.value = v;
                const meta = TASK_META[v] || {};
                opt.textContent = v + " - " + (meta.label || v);
                if (this.taskWidget.value === v) opt.selected = true;
                this.taskSelect.appendChild(opt);
            }
        }
        taskBox.appendChild(this.taskSelect);

        this.hintBox = el("div", {
            fontSize: "10px", color: C.amber,
            background: "rgba(251,191,36,0.06)", padding: "5px 8px",
            borderRadius: "3px", border: "1px solid rgba(251,191,36,0.15)",
            lineHeight: "1.5", display: "flex", flexDirection: "column", gap: "2px",
        });
        taskBox.appendChild(this.hintBox);

        this.taskSelect.onchange = () => {
            if (this.taskWidget) this.taskWidget.value = this.taskSelect.value;
            this._updateTaskDisplay();
        };

        this.root.appendChild(taskBox);

        /* system prompt preview */
        const sysBox = el("div", {
            background: C.deep, border: "1px solid " + C.borderIn,
            borderRadius: "4px", padding: "6px 8px",
            display: "flex", flexDirection: "column", gap: "3px",
        });
        const sysHeader = el("div", {
            display: "flex", justifyContent: "space-between", alignItems: "center",
            cursor: "pointer", userSelect: "none",
        });
        const sysLabel = el("div", {
            fontWeight: "600", fontSize: "10px", color: C.dim,
            textTransform: "uppercase", letterSpacing: "0.5px",
        }, "System Prompt (auto-prepended)");
        this.sysArrow = el("span", { fontSize: "9px", color: C.dim, transition: "transform 0.2s", marginRight: "4px" }, "\u25B6");
        const sysLeft = el("div", { display: "flex", alignItems: "center", gap: "4px" });
        sysLeft.appendChild(this.sysArrow);
        sysLeft.appendChild(sysLabel);
        sysHeader.appendChild(sysLeft);

        const copyBtn = el("button", {
            background: "transparent", color: C.dim, border: "1px solid " + C.borderIn,
            borderRadius: "3px", padding: "1px 6px", fontSize: "9px", cursor: "pointer",
        }, "Copy");
        copyBtn.onclick = (e) => {
            e.stopPropagation();
            const sp = SYSTEM_PROMPTS[this.taskSelect.value] || SYSTEM_PROMPTS["default"];
            navigator.clipboard.writeText(sp).then(() => {
                copyBtn.textContent = "Copied";
                setTimeout(() => { copyBtn.textContent = "Copy"; }, 1500);
            });
        };
        sysHeader.appendChild(copyBtn);
        sysBox.appendChild(sysHeader);

        this.sysPromptEl = el("div", {
            fontSize: "10px", color: C.muted, fontStyle: "italic",
            lineHeight: "1.4", wordBreak: "break-word",
        });
        sysBox.appendChild(this.sysPromptEl);

        /* expandable template editor */
        this.templateBox = el("div", {
            display: "none", flexDirection: "column", gap: "4px",
            marginTop: "4px", borderTop: "1px solid " + C.borderIn, paddingTop: "6px",
        });
        this.templateBox.appendChild(el("div", {
            fontSize: "9px", color: C.dim,
        }, "LLM Enhancement Template (editable -- changes apply to next Enhance click):"));
        this.templateArea = document.createElement("textarea");
        this.templateArea.rows = 8;
        this._sta(this.templateArea);
        this.templateArea.style.fontSize = "9px";
        this.templateArea.style.lineHeight = "1.4";
        swallowKeys(this.templateArea);

        const templateBtnRow = el("div", { display: "flex", gap: "4px", justifyContent: "flex-end" });
        const resetBtn = el("button", {
            background: "transparent", color: C.dim, border: "1px solid " + C.borderIn,
            borderRadius: "3px", padding: "1px 8px", fontSize: "9px", cursor: "pointer",
        }, "Reset to Default");
        resetBtn.onclick = () => {
            this.templateArea.value = this._currentDefaultTemplate || "";
        };
        templateBtnRow.appendChild(resetBtn);
        this.templateBox.appendChild(this.templateArea);
        this.templateBox.appendChild(templateBtnRow);
        sysBox.appendChild(this.templateBox);

        this._templateOpen = false;
        sysHeader.onclick = () => {
            this._templateOpen = !this._templateOpen;
            this.templateBox.style.display = this._templateOpen ? "flex" : "none";
            this.sysArrow.style.transform = this._templateOpen ? "rotate(90deg)" : "rotate(0deg)";
            if (this._templateOpen && !this.templateArea.value) {
                this._fetchTemplate();
            }
        };

        this.root.appendChild(sysBox);

        /* prompt areas */
        const promptBox = el("div", {
            background: C.panel, border: "1px solid " + C.borderIn,
            borderRadius: "4px", padding: "8px",
            display: "flex", flexDirection: "column", gap: "5px",
            flex: "1 1 auto", minHeight: "120px",
        });
        promptBox.appendChild(el("div", {
            fontWeight: "600", fontSize: "10px", color: C.muted,
            textTransform: "uppercase", letterSpacing: "0.5px",
        }, "Prompt"));

        this.promptArea = document.createElement("textarea");
        this.promptArea.rows = 4;
        this._sta(this.promptArea);
        this.promptArea.style.flex = "1 1 60px";
        this.promptArea.style.minHeight = "60px";
        swallowKeys(this.promptArea);
        this.promptArea.value = this.promptWidget ? this.promptWidget.value : "";
        this.promptArea.placeholder = "Describe your edit or generation...";
        this.promptArea.oninput = () => {
            if (this.promptWidget) this.promptWidget.value = this.promptArea.value;
        };
        promptBox.appendChild(this.promptArea);

        /* negative prompt */
        const negRow = el("div", { display: "flex", justifyContent: "space-between", alignItems: "center" });
        negRow.appendChild(el("div", {
            fontSize: "10px", color: C.muted,
        }, "Negative Prompt"));

        const defNegLabel = el("label", {
            display: "flex", alignItems: "center", gap: "4px",
            fontSize: "9px", color: C.dim, cursor: "pointer",
        });
        this.defNegCheck = document.createElement("input");
        this.defNegCheck.type = "checkbox";
        this.defNegCheck.checked = !(this.negWidget && this.negWidget.value && this.negWidget.value.trim());
        this.defNegCheck.style.cssText = "width:12px;height:12px;cursor:pointer;accent-color:" + C.accent;
        this.defNegCheck.onchange = () => {
            if (!this.defNegCheck.checked) {
                this.negArea.placeholder = "Enter custom negative prompt...";
            } else {
                this.negArea.value = "";
                if (this.negWidget) this.negWidget.value = "";
                this.negArea.placeholder = "(Bernini default Chinese neg will be used)";
            }
        };
        defNegLabel.appendChild(this.defNegCheck);
        defNegLabel.appendChild(document.createTextNode("Use Bernini default if empty"));
        negRow.appendChild(defNegLabel);
        promptBox.appendChild(negRow);

        this.negArea = document.createElement("textarea");
        this.negArea.rows = 2;
        this._sta(this.negArea);
        this.negArea.style.flex = "0 1 35px";
        this.negArea.style.minHeight = "35px";
        swallowKeys(this.negArea);
        this.negArea.value = this.negWidget ? this.negWidget.value : "";
        this.negArea.placeholder = this.defNegCheck.checked ? "(Bernini default Chinese neg will be used)" : "Enter custom negative prompt...";
        this.negArea.oninput = () => {
            if (this.negWidget) this.negWidget.value = this.negArea.value;
        };
        promptBox.appendChild(this.negArea);
        this.root.appendChild(promptBox);

        /* LLM Prompt Enhancer (collapsible) */
        const ollamaHeader = el("div", {
            display: "flex", justifyContent: "space-between", alignItems: "center",
            background: C.deep, border: "1px solid " + C.borderIn,
            borderRadius: "4px", padding: "6px 8px", cursor: "pointer",
            userSelect: "none",
        });
        const ollamaTitle = el("div", {
            fontWeight: "600", fontSize: "10px", color: C.dim,
            textTransform: "uppercase", letterSpacing: "0.5px",
        }, "LLM Prompt Enhancer");
        this.ollamaArrow = el("span", { fontSize: "10px", color: C.dim, transition: "transform 0.2s" }, "\u25B6");
        ollamaHeader.appendChild(ollamaTitle);
        ollamaHeader.appendChild(this.ollamaArrow);
        ollamaHeader.onclick = () => this._toggleOllama();
        this.root.appendChild(ollamaHeader);

        this.ollamaBody = el("div", {
            background: C.deep, border: "1px solid " + C.borderIn,
            borderTop: "none", borderRadius: "0 0 4px 4px",
            padding: "8px", display: "none",
            flexDirection: "column", gap: "6px", marginTop: "-5px",
        });

        this.ollamaBody.appendChild(el("div", {
            fontSize: "9px", color: C.dim, lineHeight: "1.4",
        }, "Rewrites your short instruction using Bernini's official per-task prompt templates. Connect to an LLM endpoint (Ollama or OpenAI-compatible) to enhance your prompts with cinematic detail."));

        /* API format toggle */
        const formatRow = el("div", { display: "flex", gap: "6px", alignItems: "center" });
        formatRow.appendChild(el("div", { fontSize: "10px", color: C.muted, whiteSpace: "nowrap" }, "API:"));
        this.apiFormatSelect = document.createElement("select");
        this._si(this.apiFormatSelect);
        this.apiFormatSelect.style.flex = "0 0 auto";
        this.apiFormatSelect.style.width = "auto";
        for (const [val, label] of [["Ollama", "Ollama (/api/chat)"], ["OpenAI / vLLM", "OpenAI / vLLM (/v1/chat)"]]) {
            const o = document.createElement("option");
            o.value = val; o.textContent = label;
            if (this.apiFormatWidget && this.apiFormatWidget.value === val) o.selected = true;
            this.apiFormatSelect.appendChild(o);
        }
        this.apiFormatSelect.onchange = () => {
            if (this.apiFormatWidget) this.apiFormatWidget.value = this.apiFormatSelect.value;
            this._fetchModels();
        };
        formatRow.appendChild(this.apiFormatSelect);
        this.ollamaBody.appendChild(formatRow);

        /* URL input */
        const urlRow = el("div", { display: "flex", gap: "6px" });
        this.urlInput = document.createElement("input");
        this.urlInput.type = "text";
        this.urlInput.placeholder = "http://127.0.0.1:11434";
        this._si(this.urlInput);
        this.urlInput.style.flex = "1 1 auto";
        this.urlInput.style.minWidth = "0";
        this.urlInput.value = this.urlWidget ? this.urlWidget.value : "http://127.0.0.1:11434";
        this.urlInput.oninput = () => { if (this.urlWidget) this.urlWidget.value = this.urlInput.value; };
        swallowKeys(this.urlInput);
        urlRow.appendChild(this.urlInput);

        const refreshBtn = el("button", {
            background: C.panel, color: C.text, border: "1px solid " + C.borderIn,
            borderRadius: "4px", padding: "2px 8px", fontSize: "10px",
            cursor: "pointer", whiteSpace: "nowrap",
        }, "Refresh");
        refreshBtn.onclick = () => this._fetchModels();
        urlRow.appendChild(refreshBtn);
        this.ollamaBody.appendChild(urlRow);

        /* model select */
        this.modelSelect = document.createElement("select");
        this._si(this.modelSelect);
        const blank = document.createElement("option");
        blank.value = "";
        blank.textContent = "(Select a model)";
        this.modelSelect.appendChild(blank);
        if (this.modelWidget && this.modelWidget.value) {
            const o = document.createElement("option");
            o.value = this.modelWidget.value;
            o.textContent = this.modelWidget.value;
            o.selected = true;
            this.modelSelect.appendChild(o);
        }
        this.modelSelect.onchange = () => {
            if (this.modelWidget) this.modelWidget.value = this.modelSelect.value;
        };
        this.ollamaBody.appendChild(this.modelSelect);

        /* temperature + max tokens row */
        const genRow = el("div", { display: "flex", gap: "6px" });
        const tempLabel = el("span", { fontSize: "10px", color: C.muted, whiteSpace: "nowrap", alignSelf: "center" }, "Temp:");
        genRow.appendChild(tempLabel);
        this.tempInput = document.createElement("input");
        this.tempInput.type = "number";
        this.tempInput.min = 0;
        this.tempInput.max = 2;
        this.tempInput.step = 0.01;
        this._si(this.tempInput);
        this.tempInput.style.flex = "1";
        this.tempInput.style.minWidth = "0";
        this.tempInput.value = this.tempWidget ? this.tempWidget.value : 0.7;
        this.tempInput.oninput = () => {
            if (this.tempWidget) this.tempWidget.value = parseFloat(this.tempInput.value || "0.7");
        };
        swallowKeys(this.tempInput);
        genRow.appendChild(this.tempInput);

        const mtLabel = el("span", { fontSize: "10px", color: C.muted, whiteSpace: "nowrap", alignSelf: "center" }, "Max tok:");
        genRow.appendChild(mtLabel);
        this.maxTokensInput = document.createElement("input");
        this.maxTokensInput.type = "number";
        this.maxTokensInput.min = 64;
        this.maxTokensInput.max = 8192;
        this.maxTokensInput.step = 64;
        this._si(this.maxTokensInput);
        this.maxTokensInput.style.flex = "1";
        this.maxTokensInput.style.minWidth = "0";
        this.maxTokensInput.value = this.maxTokensWidget ? this.maxTokensWidget.value : 2048;
        this.maxTokensInput.oninput = () => {
            if (this.maxTokensWidget) this.maxTokensWidget.value = parseInt(this.maxTokensInput.value || "2048", 10);
        };
        swallowKeys(this.maxTokensInput);
        genRow.appendChild(this.maxTokensInput);
        this.ollamaBody.appendChild(genRow);

        /* seed row */
        const seedRow = el("div", { display: "flex", gap: "6px", alignItems: "center" });
        seedRow.appendChild(el("span", { fontSize: "10px", color: C.muted, whiteSpace: "nowrap" }, "Seed:"));
        this.seedInput = document.createElement("input");
        this.seedInput.type = "number";
        this.seedInput.min = 0;
        this.seedInput.max = 2147483647;
        this._si(this.seedInput);
        this.seedInput.style.flex = "1";
        this.seedInput.style.minWidth = "0";
        this.seedInput.value = this.seedWidget ? this.seedWidget.value : 0;
        this.seedInput.oninput = () => {
            if (this.seedWidget) this.seedWidget.value = parseInt(this.seedInput.value || "0", 10);
        };
        swallowKeys(this.seedInput);
        seedRow.appendChild(this.seedInput);
        this.ollamaBody.appendChild(seedRow);

        /* prepend system prompt toggle */
        const prependRow = el("div", { display: "flex", alignItems: "center", gap: "6px" });
        this.prependCheck = document.createElement("input");
        this.prependCheck.type = "checkbox";
        this.prependCheck.checked = this.prependSysWidget ? this.prependSysWidget.value !== false : true;
        this.prependCheck.style.cssText = "width:12px;height:12px;cursor:pointer;accent-color:" + C.accent;
        this.prependCheck.onchange = () => {
            if (this.prependSysWidget) this.prependSysWidget.value = this.prependCheck.checked;
        };
        prependRow.appendChild(this.prependCheck);
        const prependLabel = el("span", { fontSize: "10px", color: C.muted, cursor: "pointer" },
            "Prepend system prompt to output");
        prependLabel.onclick = () => {
            this.prependCheck.checked = !this.prependCheck.checked;
            this.prependCheck.dispatchEvent(new Event("change"));
        };
        prependRow.appendChild(prependLabel);
        this.ollamaBody.appendChild(prependRow);

        /* enhance button */
        this.enhanceBtn = el("button", {
            background: C.accent, color: "white", border: "none",
            borderRadius: "4px", padding: "6px", fontWeight: "600",
            fontSize: "11px", cursor: "pointer", transition: "background 0.3s, opacity 0.2s",
        }, "Enhance Prompt");
        this.enhanceBtn.onmouseover = () => { if (!this.enhanceBtn.disabled) this.enhanceBtn.style.opacity = "0.85"; };
        this.enhanceBtn.onmouseout  = () => { if (!this.enhanceBtn.disabled) this.enhanceBtn.style.opacity = "1"; };
        this.enhanceBtn.onclick = () => this._enhancePrompt();
        this.ollamaBody.appendChild(this.enhanceBtn);

        /* auto-enhance toggle */
        const autoRow = el("div", {
            display: "flex", alignItems: "center", gap: "6px", marginTop: "2px",
        });
        this.autoEnhanceCheck = document.createElement("input");
        this.autoEnhanceCheck.type = "checkbox";
        this.autoEnhanceCheck.checked = this.autoEnhanceWidget ? this.autoEnhanceWidget.value : false;
        this.autoEnhanceCheck.style.cssText = "width:12px;height:12px;cursor:pointer;accent-color:" + C.accent;
        this.autoEnhanceCheck.onchange = () => {
            if (this.autoEnhanceWidget) this.autoEnhanceWidget.value = this.autoEnhanceCheck.checked;
        };
        autoRow.appendChild(this.autoEnhanceCheck);
        autoRow.appendChild(el("span", { fontSize: "10px", color: C.muted, cursor: "pointer" },
            "Auto-enhance on queue (check ComfyUI console for enhanced text)"));
        autoRow.onclick = (e) => {
            if (e.target !== this.autoEnhanceCheck) {
                this.autoEnhanceCheck.checked = !this.autoEnhanceCheck.checked;
                this.autoEnhanceCheck.dispatchEvent(new Event("change"));
            }
        };
        this.ollamaBody.appendChild(autoRow);

        /* unload Ollama toggle + button */
        const unloadRow = el("div", {
            display: "flex", alignItems: "center", gap: "6px",
        });
        this.unloadCheck = document.createElement("input");
        this.unloadCheck.type = "checkbox";
        this.unloadCheck.checked = this.unloadOllamaWidget ? this.unloadOllamaWidget.value : false;
        this.unloadCheck.style.cssText = "width:12px;height:12px;cursor:pointer;accent-color:" + C.accent;
        this.unloadCheck.onchange = () => {
            if (this.unloadOllamaWidget) this.unloadOllamaWidget.value = this.unloadCheck.checked;
        };
        unloadRow.appendChild(this.unloadCheck);
        const unloadLabel = el("span", { fontSize: "10px", color: C.muted, cursor: "pointer", flex: "1" },
            "Auto-unload after enhance (Ollama only)");
        unloadLabel.onclick = () => {
            this.unloadCheck.checked = !this.unloadCheck.checked;
            this.unloadCheck.dispatchEvent(new Event("change"));
        };
        unloadRow.appendChild(unloadLabel);

        this.unloadBtn = el("button", {
            background: C.panel, color: C.text, border: "1px solid " + C.borderIn,
            borderRadius: "4px", padding: "2px 10px", fontSize: "10px",
            cursor: "pointer", whiteSpace: "nowrap",
        }, "Unload Now");
        this.unloadBtn.onclick = () => this._unloadOllama();
        unloadRow.appendChild(this.unloadBtn);
        this.ollamaBody.appendChild(unloadRow);

        this.statusEl = el("div", {
            fontSize: "10px", color: C.dim, minHeight: "14px", textAlign: "center",
        });
        this.ollamaBody.appendChild(this.statusEl);
        this.root.appendChild(this.ollamaBody);

        /* inject CSS pulse animation */
        if (!document.getElementById("bernini-enhancer-pulse-css")) {
            const style = document.createElement("style");
            style.id = "bernini-enhancer-pulse-css";
            style.textContent = `
                @keyframes bernini-enhancer-pulse {
                    0%, 100% { background: #d97706; transform: scale(1); }
                    50% { background: #92400e; transform: scale(1.01); }
                }
            `;
            document.head.appendChild(style);
        }

        /* layout sections */
        this._layoutSections = {
            header: header,
            left: [taskBox, sysBox, promptBox],
            right: [ollamaHeader, this.ollamaBody],
        };
        this._layoutMode = "stacked";
        try {
            const saved = localStorage.getItem("berniniEnhancerLayout");
            if (saved === "split") this._layoutMode = "split";
        } catch (e) {}
        this._applyLayout();

        this._updateTaskDisplay();
        this._fetchModels(true);

        /* poll for image connection changes */
        this._imagePollInterval = setInterval(() => {
            this._updateImageIndicator();
        }, 1000);

        /* listen for server-side auto-enhance results */
        const nodeId = String(this.node.id);
        api.addEventListener("bernini_enhanced", (event) => {
            const d = event.detail;
            if (d && String(d.node) === nodeId && d.text) {
                this.promptArea.value = d.text;
                if (this.promptWidget) this.promptWidget.value = d.text;
                this.statusEl.textContent = "Auto-enhanced on queue (" + d.text.length + " chars)";
            }
        });
    }

    _updateTaskDisplay() {
        const task = this.taskSelect.value;
        const meta = TASK_META[task] || {};
        const sysp = SYSTEM_PROMPTS[task] || SYSTEM_PROMPTS["default"];

        this.guidanceBadge.textContent = meta.guidance || "?";

        this._updateImageIndicator();

        this.hintBox.innerHTML = "";
        if (meta.desc) {
            const descLine = el("div", {
                color: C.text, fontSize: "10px", lineHeight: "1.4",
                paddingBottom: "3px", marginBottom: "3px",
                borderBottom: "1px solid rgba(251,191,36,0.12)",
            }, meta.desc);
            this.hintBox.appendChild(descLine);
        }
        if (meta.refHint) {
            const refLine = el("div", {
                color: C.cyan, fontSize: "10px", lineHeight: "1.4",
                paddingBottom: "3px", marginBottom: "3px",
                borderBottom: "1px solid rgba(251,191,36,0.12)",
            }, meta.refHint);
            this.hintBox.appendChild(refLine);
        }
        const wireText = meta.wire === "none" ? "No media inputs needed" : "Wire: " + meta.wire;
        const infoRow = el("div", {
            display: "flex", justifyContent: "space-between", alignItems: "center",
            flexWrap: "wrap", gap: "4px",
        });
        infoRow.appendChild(el("span", { color: C.amber, fontSize: "10px" }, wireText));
        infoRow.appendChild(el("span", { color: C.dim, fontSize: "9px", fontFamily: "monospace" },
            "guidance: " + (meta.guidance || "?")));
        this.hintBox.appendChild(infoRow);

        this.sysPromptEl.textContent = sysp;

        if (meta.refHint) {
            this.promptArea.placeholder = "e.g. 'Replace the man with the person from image0' (use image0, image1... not reference_image_0)";
        } else if (meta.wire === "none") {
            this.promptArea.placeholder = "Describe the scene, subjects, and action...";
        } else {
            this.promptArea.placeholder = "Describe your edit (what to change + what to preserve)...";
        }

        if (this._templateOpen) {
            this._fetchTemplate();
        }
    }

    async _fetchTemplate() {
        try {
            const resp = await api.fetchApi("/bernini_enhancer/get_template", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ task_type: this.taskSelect.value }),
            });
            const data = await resp.json();
            if (data.template) {
                this._currentDefaultTemplate = data.template;
                this.templateArea.value = data.template;
            }
        } catch (e) {
            console.warn("[BerniniEnhancer] Failed to fetch template:", e);
        }
    }

    _updateImageIndicator() {
        const hasImage = this.node.inputs && this.node.inputs.some(
            inp => inp.name === "image" && inp.link != null
        );
        if (hasImage) {
            this.imageIndicator.style.display = "inline";
            this.imageIndicator.textContent = "Img";
            this.imageIndicator.style.color = C.green;
            this.imageIndicator.style.borderColor = "rgba(74,222,128,0.3)";
            this.imageIndicator.style.background = "rgba(74,222,128,0.08)";
        } else {
            this.imageIndicator.style.display = "none";
        }
    }

    _toggleOllama() {
        this.ollamaOpen = !this.ollamaOpen;
        this.ollamaBody.style.display = this.ollamaOpen ? "flex" : "none";
        this.ollamaArrow.style.transform = this.ollamaOpen ? "rotate(90deg)" : "rotate(0deg)";
    }

    async _fetchModels(silent) {
        if (!silent) this.statusEl.textContent = "Fetching models...";
        const fmt = this.apiFormatSelect ? this.apiFormatSelect.value : "Ollama";
        try {
            const resp = await api.fetchApi("/bernini_enhancer/models", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    ollama_url: this.urlInput.value,
                    api_format: fmt,
                }),
            });
            const data = await resp.json();
            if (!resp.ok) {
                if (!silent) this.statusEl.textContent = (fmt === "OpenAI / vLLM" ? "vLLM" : "Ollama") + ": " + (data.error || resp.status);
                return;
            }
            const models = data.models || [];
            this.modelSelect.innerHTML = "";
            const b = document.createElement("option");
            b.value = "";
            b.textContent = "(Select a model)";
            this.modelSelect.appendChild(b);
            for (const m of models) {
                const o = document.createElement("option");
                o.value = m;
                o.textContent = m;
                this.modelSelect.appendChild(o);
            }
            const prior = this.modelWidget ? this.modelWidget.value : "";
            if (prior && models.includes(prior)) this.modelSelect.value = prior;
            if (!silent) this.statusEl.textContent = models.length + " model(s) found.";
        } catch (e) {
            if (!silent) this.statusEl.textContent = "Could not reach server.";
        }
    }

    async _enhancePrompt() {
        const model = this.modelSelect.value;
        if (!model) { this.statusEl.textContent = "Select a model first."; return; }
        if (!this.promptArea.value.trim()) { this.statusEl.textContent = "Enter an instruction to enhance."; return; }

        const hasImage = this.node.inputs && this.node.inputs.some(
            inp => inp.name === "image" && inp.link != null
        );

        this._setEnhanceBusy(true, "Asking " + model + (hasImage ? " (with image)..." : " (text-only)..."));
        const fmt = this.apiFormatSelect ? this.apiFormatSelect.value : "Ollama";

        const customTemplate = (this.templateArea && this.templateArea.value.trim() !== this._currentDefaultTemplate)
            ? this.templateArea.value.trim() : "";

        // Try to capture image from connected node's output via canvas
        let imageBase64 = null;
        if (hasImage) {
            try {
                const canvas = document.querySelector("canvas");
                if (canvas) {
                    imageBase64 = canvas.toDataURL("image/png").split(",")[1];
                }
            } catch (e) {
                console.warn("[BerniniEnhancer] Failed to capture canvas image:", e);
            }
        }

        try {
            const resp = await api.fetchApi("/bernini_enhancer/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    ollama_url: this.urlInput.value,
                    model: model,
                    prompt: this.promptArea.value,
                    task_type: this.taskSelect.value,
                    image_num: 1,
                    image: imageBase64,
                    api_format: fmt,
                    unload_ollama: this.unloadCheck ? this.unloadCheck.checked : false,
                    custom_template: customTemplate,
                }),
            });
            const data = await resp.json();
            if (data.response) {
                this.promptArea.value = data.response;
                if (this.promptWidget) this.promptWidget.value = data.response;
                this.statusEl.textContent = "Enhanced with " + this.taskSelect.value + " template" + (imageBase64 ? " (with image)" : "");
            } else {
                this.statusEl.textContent = "Failed: " + (data.error || "Unknown error");
            }
        } catch (e) {
            this.statusEl.textContent = "Error: " + e.message;
        } finally {
            this._setEnhanceBusy(false);
        }
    }

    async _unloadOllama() {
        const model = this.modelSelect.value;
        if (!model) { this.statusEl.textContent = "Select a model first."; return; }
        this.unloadBtn.disabled = true;
        this.unloadBtn.textContent = "Unloading...";
        this.statusEl.textContent = "Unloading " + model + " from VRAM...";
        try {
            const resp = await api.fetchApi("/bernini_enhancer/unload", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    ollama_url: this.urlInput.value,
                    model: model,
                }),
            });
            const data = await resp.json();
            if (data.status === "unloaded") {
                this.statusEl.textContent = model + " unloaded from VRAM.";
            } else {
                this.statusEl.textContent = "Unload failed: " + (data.error || "unknown");
            }
        } catch (e) {
            this.statusEl.textContent = "Unload error: " + e.message;
        } finally {
            this.unloadBtn.disabled = false;
            this.unloadBtn.textContent = "Unload Now";
        }
    }

    _setEnhanceBusy(busy, statusText) {
        if (busy) {
            this.enhanceBtn.disabled = true;
            this.enhanceBtn.textContent = "Enhancing...";
            this.enhanceBtn.style.background = "#d97706";
            this.enhanceBtn.style.animation = "bernini-enhancer-pulse 1.4s ease-in-out infinite";
            this.enhanceBtn.style.cursor = "wait";
            this.enhanceBtn.style.opacity = "1";
            if (statusText) this.statusEl.textContent = statusText;
        } else {
            this.enhanceBtn.disabled = false;
            this.enhanceBtn.textContent = "Enhance Prompt";
            this.enhanceBtn.style.background = C.accent;
            this.enhanceBtn.style.animation = "";
            this.enhanceBtn.style.opacity = "1";
            this.enhanceBtn.style.cursor = "pointer";
        }
    }

    /* layout toggle: stacked (default) or two-column */
    _applyLayout() {
        const sec = this._layoutSections || {};
        if (this._layoutMode === "split") {
            this.root.style.flexDirection = "row";
            this.root.style.gap = "8px";
            this.root.style.alignItems = "stretch";
            this.root.style.flexWrap = "wrap";

            const leftCol = el("div", { display: "flex", flexDirection: "column", gap: "8px", flex: "1 1 260px", minWidth: "200px" });
            const rightCol = el("div", { display: "flex", flexDirection: "column", gap: "8px", flex: "1 1 260px", minWidth: "200px" });

            // move header to top spanning both
            if (sec.header && sec.header.parentNode) sec.header.style.width = "100%";

            // collect left panels
            if (sec.left) {
                for (const panel of sec.left) {
                    if (panel.parentNode) leftCol.appendChild(panel);
                }
            }
            // collect right panels
            if (sec.right) {
                for (const panel of sec.right) {
                    if (panel.parentNode) rightCol.appendChild(panel);
                }
            }

            // Rebuild root: header, then row of columns
            while (this.root.firstChild) this.root.removeChild(this.root.firstChild);
            if (sec.header) this.root.appendChild(sec.header);
            const row = el("div", { display: "flex", gap: "8px", flex: "1", flexWrap: "wrap" });
            row.appendChild(leftCol);
            row.appendChild(rightCol);
            this.root.appendChild(row);
            this.layoutBtn.textContent = "Stacked";
        } else {
            // stacked: header, then everything in order
            const all = [sec.header]
                .concat(sec.left || [])
                .concat(sec.right || []);
            while (this.root.firstChild) this.root.removeChild(this.root.firstChild);
            for (const panel of all) {
                if (panel) this.root.appendChild(panel);
            }
            this.layoutBtn.textContent = "Layout";
        }
        // Reset manual widget height on layout change so it can recalculate based on the new layout
        const widget = (this.node.widgets || []).find(w => w.name === "bernini_enhancer_editor");
        if (widget) {
            widget.customHeight = undefined;
        }

        requestAnimationFrame(() => {
            if (widget && this.node.size) {
                const horizontalMargin = 30;
                widget.width = Math.max(200, this.node.size[0] - horizontalMargin);
                if (widget.element) {
                    widget.element.style.width = widget.width + "px";
                }
            }
            if (this.node.computeSize && this.node.size) this.node.size[1] = this.node.computeSize()[1];
            if (this.node.graph) this.node.graph.setDirtyCanvas(true, true);
        });
    }

    _syncFromWidgets() {
        if (this.taskWidget && this.taskSelect) {
            const v = this.taskWidget.value;
            if (v && this.taskSelect.value !== v) this.taskSelect.value = v;
        }
        if (this.promptWidget && this.promptArea) {
            const v = this.promptWidget.value || "";
            if (this.promptArea.value !== v) this.promptArea.value = v;
        }
        if (this.negWidget && this.negArea) {
            const v = this.negWidget.value || "";
            if (this.negArea.value !== v) this.negArea.value = v;
            this.defNegCheck.checked = !v.trim();
        }
        if (this.urlWidget && this.urlInput) {
            const v = this.urlWidget.value || "";
            if (this.urlInput.value !== v) this.urlInput.value = v;
        }
        if (this.modelWidget && this.modelSelect) {
            const v = this.modelWidget.value || "";
            if (v && this.modelSelect.value !== v) this.modelSelect.value = v;
        }
        if (this.apiFormatWidget && this.apiFormatSelect) {
            const v = this.apiFormatWidget.value;
            if (v && this.apiFormatSelect.value !== v) this.apiFormatSelect.value = v;
        }
        if (this.autoEnhanceWidget && this.autoEnhanceCheck) {
            this.autoEnhanceCheck.checked = !!this.autoEnhanceWidget.value;
        }
        if (this.unloadOllamaWidget && this.unloadCheck) {
            this.unloadCheck.checked = !!this.unloadOllamaWidget.value;
        }
        if (this.tempWidget && this.tempInput) {
            const v = parseFloat(this.tempWidget.value);
            if (!isNaN(v)) this.tempInput.value = v;
        }
        if (this.maxTokensWidget && this.maxTokensInput) {
            const v = parseInt(this.maxTokensWidget.value, 10);
            if (!isNaN(v)) this.maxTokensInput.value = v;
        }
        if (this.seedWidget && this.seedInput) {
            const v = parseInt(this.seedWidget.value, 10);
            if (!isNaN(v)) this.seedInput.value = v;
        }
        if (this.prependSysWidget && this.prependCheck) {
            this.prependCheck.checked = this.prependSysWidget.value !== false;
        }
        this._updateTaskDisplay();
        this._updateImageIndicator();
    }

    _getMinHeight() {
        const ed = this.root;
        if (!ed) return 400;

        const origHeight = ed.style.height;
        ed.style.height = "auto";

        let origPromptHeight, origNegHeight;
        if (this.promptArea) {
            origPromptHeight = this.promptArea.style.height;
            this.promptArea.style.height = "";
        }
        if (this.negArea) {
            origNegHeight = this.negArea.style.height;
            this.negArea.style.height = "";
        }

        const height = ed.scrollHeight;

        ed.style.height = origHeight;
        if (this.promptArea) this.promptArea.style.height = origPromptHeight;
        if (this.negArea) this.negArea.style.height = origNegHeight;

        return height;
    }
}

/* register the custom node type */
app.registerExtension({
    name: "BerniniPromptEnhancer.Editor",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "BerniniPromptEnhancer") return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

            try {
                for (const name of HIDDEN_WIDGETS) hideWidget(findWidget(this, name));

                const mount = document.createElement("div");
                mount.style.cssText = "width:100%;height:100%;box-sizing:border-box;";
                const getEditorHeight = () => {
                    const editor = this._berniniEnhancerEditor;
                    return editor ? editor._getMinHeight() : 400;
                };

                const editorWidget = this.addDOMWidget("bernini_enhancer_editor", "div", mount, {
                    serialize: false, hideOnZoom: false, getHeight: getEditorHeight,
                });
                if (editorWidget) {
                    editorWidget.computeSize = function (width) {
                        const minHeight = getEditorHeight();
                        if (editorWidget.customHeight) {
                            return [width, Math.max(minHeight, editorWidget.customHeight)];
                        }
                        return [width, minHeight];
                    };
                }

                new BerniniEnhancerEditor(this, mount);

                requestAnimationFrame(() => {
                    const widget = (this.widgets || []).find(w => w.name === "bernini_enhancer_editor");
                    if (widget && this.size) {
                        const horizontalMargin = 30;
                        widget.width = Math.max(200, this.size[0] - horizontalMargin);
                        if (widget.element) {
                            widget.element.style.width = widget.width + "px";
                        }
                    }
                    if (this.computeSize && this.size) this.size[1] = this.computeSize()[1];
                    if (this.graph) this.graph.setDirtyCanvas(true, true);
                });
            } catch (err) {
                console.error("[BerniniPromptEnhancer] Editor setup error:", err);
            }

            return r;
        };

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function (data) {
            const r = onConfigure ? onConfigure.apply(this, arguments) : undefined;
            if (this._berniniEnhancerEditor) {
                const widget = (this.widgets || []).find(w => w.name === "bernini_enhancer_editor");
                if (widget && this.size) {
                    const titleHeight = this.title_height || 30;
                    const bottomMargin = 15;
                    const minHeight = this._berniniEnhancerEditor._getMinHeight();
                    const availableHeight = this.size[1] - titleHeight - bottomMargin;
                    widget.customHeight = Math.max(minHeight, availableHeight);

                    const horizontalMargin = 30;
                    widget.width = Math.max(200, this.size[0] - horizontalMargin);
                    if (widget.element) {
                        widget.element.style.width = widget.width + "px";
                    }
                }
                requestAnimationFrame(() => {
                    this._berniniEnhancerEditor._syncFromWidgets();
                    if (this.computeSize && this.size) this.size[1] = this.computeSize()[1];
                    if (this.graph) this.graph.setDirtyCanvas(true, true);
                });
            }
            return r;
        };

        const onResize = nodeType.prototype.onResize;
        nodeType.prototype.onResize = function (size) {
            if (onResize) onResize.apply(this, arguments);
            const widget = (this.widgets || []).find(w => w.name === "bernini_enhancer_editor");
            if (widget) {
                const horizontalMargin = 30;
                widget.width = Math.max(200, size[0] - horizontalMargin);
                
                if (widget.element) {
                    widget.element.style.width = widget.width + "px";
                    
                    let yOffset = widget.last_y;
                    if (!yOffset) {
                        yOffset = this.title_height || 30;
                    }
                    const bottomMargin = 15;
                    const remainingHeight = size[1] - yOffset - bottomMargin;
                    
                    const editor = this._berniniEnhancerEditor;
                    const minHeight = editor ? editor._getMinHeight() : 400;
                    const finalHeight = Math.max(minHeight, remainingHeight);
                    
                    widget.element.style.height = finalHeight + "px";
                    widget.customHeight = finalHeight;
                }
            }
        };
    },
});
