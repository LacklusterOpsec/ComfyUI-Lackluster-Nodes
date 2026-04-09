import { app } from "../../../scripts/app.js";

// Helper to fetch voices from AllTalk server
async function fetchVoices(server_url) {
    try {
        const response = await fetch(`${server_url}/api/voices`);
        if (!response.ok) return [];
        const data = await response.json();
        return data.voices || [];
    } catch (e) {
        console.error("AllTalk: Error fetching voices", e);
        return [];
    }
}

app.registerExtension({
    name: "Lackluster.AllTalkV2",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "AllTalkTTSV2") {
            // When the TTS V2 node is created, we can add custom logic
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function () {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                
                const voiceWidget = this.widgets.find(w => w.name === "character_voice");
                const serverConfigWidget = this.inputs.find(i => i.name === "server_config");

                // Add a "Refresh Voices" button
                this.addWidget("button", "Refresh Voices", null, async () => {
                    // Try to find the connected config node to get the URL
                    let url = "http://localhost:7851"; // Default fallback
                    
                    if (this.inputs[0] && this.inputs[0].link) {
                        const link = app.graph.links[this.inputs[0].link];
                        if (link) {
                            const originNode = app.graph.getNodeById(link.origin_id);
                            if (originNode && originNode.widgets) {
                                const urlWidget = originNode.widgets.find(w => w.name === "server_url");
                                if (urlWidget) url = urlWidget.value.replace(/\/$/, "");
                            }
                        }
                    }

                    console.log("AllTalk: Refreshing voices from", url);
                    const voices = await fetchVoices(url);
                    if (voices.length > 0) {
                        voiceWidget.options.values = voices;
                        if (!voices.includes(voiceWidget.value)) {
                            voiceWidget.value = voices[0];
                        }
                        this.setDirtyCanvas(true, true);
                        alert(`Found ${voices.length} voices!`);
                    } else {
                        alert("Could not fetch voices. Check server URL and ensure AllTalk is running.");
                    }
                });

                return r;
            };
        }
    }
});
