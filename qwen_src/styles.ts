export const WIDGET_STYLES = `
  .qwen-multiangle-container {
    width: 100%;
    height: 100%;
    position: relative;
    background: #0a0a0f;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    border-radius: 8px;
    overflow: hidden;
  }

  .qwen-multiangle-canvas {
    width: 100%;
    height: 100%;
    display: block;
    position: relative;
  }

  .qwen-multiangle-prompt {
    position: absolute;
    top: 8px;
    left: 8px;
    right: 8px;
    background: rgba(10, 10, 15, 0.9);
    border: 1px solid rgba(233, 61, 130, 0.3);
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 11px;
    color: #E93D82;
    backdrop-filter: blur(4px);
    font-family: 'Consolas', 'Monaco', monospace;
    word-break: break-all;
    line-height: 1.4;
  }

  .qwen-multiangle-info {
    position: absolute;
    bottom: 8px;
    left: 8px;
    right: 8px;
    background: rgba(10, 10, 15, 0.9);
    border: 1px solid rgba(233, 61, 130, 0.3);
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 11px;
    color: #e0e0e0;
    display: flex;
    flex-direction: column;
    gap: 4px;
    backdrop-filter: blur(4px);
  }

  .qwen-multiangle-info-row {
    display: flex;
    justify-content: space-around;
    align-items: center;
  }

  .qwen-multiangle-control {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .qwen-multiangle-param {
    text-align: center;
  }

  .qwen-multiangle-param-value {
    font-weight: 600;
    font-size: 13px;
  }

  .qwen-multiangle-param-value.azimuth {
    color: #E93D82;
  }

  .qwen-multiangle-param-value.elevation {
    color: #00FFD0;
  }

  .qwen-multiangle-param-value.zoom {
    color: #FFB800;
  }

  .qwen-multiangle-reset {
    width: 24px;
    height: 24px;
    border-radius: 4px;
    border: 1px solid rgba(233, 61, 130, 0.4);
    background: rgba(10, 10, 15, 0.8);
    color: #E93D82;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    transition: all 0.2s ease;
    flex-shrink: 0;
  }

  .qwen-multiangle-reset:hover {
    background: rgba(233, 61, 130, 0.2);
    border-color: #E93D82;
  }
`
