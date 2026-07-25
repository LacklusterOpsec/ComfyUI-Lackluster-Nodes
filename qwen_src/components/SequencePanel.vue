<template>
  <div class="sequence-panel" :class="{ collapsed: isCollapsed }">
    <div class="panel-header" @click="isCollapsed = !isCollapsed">
      <div class="header-title">
        <span>🎬 Angle Queue ({{ sequence.length }})</span>
      </div>
      <div class="header-actions">
        <button
          class="add-btn"
          title="Add current angle to queue"
          @click.stop="$emit('add-angle')"
        >
          + Add Angle
        </button>
        <button
          class="collapse-toggle"
          :title="isCollapsed ? 'Expand sequence list' : 'Collapse sequence list'"
        >
          {{ isCollapsed ? '▲' : '▼' }}
        </button>
      </div>
    </div>

    <div v-if="!isCollapsed" class="panel-body">
      <div class="preset-row">
        <span class="preset-label">Presets:</span>
        <button class="preset-btn" @click="$emit('add-preset', '4-turnaround')" title="Add 4 cardinal angles (0°, 90°, 180°, 270°)">
          + 4 Turnaround
        </button>
        <button class="preset-btn" @click="$emit('add-preset', '8-turnaround')" title="Add 8 direction angles (every 45°)">
          + 8 Angles
        </button>
        <button
          v-if="sequence.length > 0"
          class="clear-btn"
          @click="$emit('clear-sequence')"
          title="Clear all queued angles"
        >
          Clear
        </button>
      </div>

      <div v-if="sequence.length === 0" class="empty-state">
        No angles queued. Rotate 3D view and click <strong>+ Add Angle</strong> or pick a preset.
      </div>

      <div v-else class="sequence-list">
        <div
          v-for="(item, index) in sequence"
          :key="item.id"
          class="sequence-item"
        >
          <div class="item-index">#{{ index + 1 }}</div>
          <div class="item-details" @click="$emit('preview-angle', item)">
            <div class="item-prompt">{{ item.prompt }}</div>
            <div class="item-params">
              H: {{ Math.round(item.azimuth) }}° | V: {{ Math.round(item.elevation) }}° | Z: {{ item.distance.toFixed(1) }}
            </div>
          </div>
          <div class="item-actions">
            <button
              class="icon-btn"
              title="Preview in 3D"
              @click="$emit('preview-angle', item)"
            >
              👁️
            </button>
            <button
              class="icon-btn"
              :disabled="index === 0"
              title="Move Up"
              @click="$emit('move-angle', { from: index, to: index - 1 })"
            >
              ▲
            </button>
            <button
              class="icon-btn"
              :disabled="index === sequence.length - 1"
              title="Move Down"
              @click="$emit('move-angle', { from: index, to: index + 1 })"
            >
              ▼
            </button>
            <button
              class="icon-btn remove-btn"
              title="Delete Angle"
              @click="$emit('remove-angle', index)"
            >
              ✕
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { SequenceItem } from '../types'

defineProps<{
  sequence: SequenceItem[]
  azimuth: number
  elevation: number
  distance: number
}>()

defineEmits<{
  'add-angle': []
  'add-preset': [type: '4-turnaround' | '8-turnaround']
  'remove-angle': [index: number]
  'move-angle': [payload: { from: number; to: number }]
  'preview-angle': [item: SequenceItem]
  'clear-sequence': []
}>()

const isCollapsed = ref(false)
</script>

<style scoped>
.sequence-panel {
  position: absolute;
  top: 40px;
  right: 8px;
  width: 250px;
  max-height: 280px;
  background: rgba(10, 10, 15, 0.92);
  border: 1px solid rgba(233, 61, 130, 0.4);
  border-radius: 6px;
  padding: 6px;
  font-size: 11px;
  color: #e0e0e0;
  display: flex;
  flex-direction: column;
  backdrop-filter: blur(6px);
  z-index: 20;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  transition: max-height 0.2s ease;
}

.sequence-panel.collapsed {
  max-height: 36px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  user-select: none;
  padding-bottom: 4px;
}

.header-title {
  font-weight: 600;
  color: #00FFD0;
  font-size: 11px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.add-btn {
  background: rgba(233, 61, 130, 0.25);
  border: 1px solid #E93D82;
  color: #fff;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.add-btn:hover {
  background: rgba(233, 61, 130, 0.5);
}

.collapse-toggle {
  background: transparent;
  border: none;
  color: #888;
  cursor: pointer;
  font-size: 10px;
}

.panel-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  overflow: hidden;
  margin-top: 4px;
  border-top: 1px dashed rgba(255, 255, 255, 0.15);
  padding-top: 6px;
}

.preset-row {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: wrap;
}

.preset-label {
  font-size: 9px;
  color: #aaa;
}

.preset-btn {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #e0e0e0;
  border-radius: 3px;
  padding: 2px 5px;
  font-size: 9px;
  cursor: pointer;
}

.preset-btn:hover {
  background: rgba(0, 255, 208, 0.2);
  border-color: #00FFD0;
  color: #00FFD0;
}

.clear-btn {
  background: rgba(255, 50, 50, 0.15);
  border: 1px solid rgba(255, 50, 50, 0.3);
  color: #ff6b6b;
  border-radius: 3px;
  padding: 2px 5px;
  font-size: 9px;
  cursor: pointer;
  margin-left: auto;
}

.clear-btn:hover {
  background: rgba(255, 50, 50, 0.3);
}

.empty-state {
  font-size: 10px;
  color: #888;
  padding: 8px 4px;
  text-align: center;
  line-height: 1.3;
}

.sequence-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 170px;
  overflow-y: auto;
  padding-right: 2px;
}

.sequence-list::-webkit-scrollbar {
  width: 4px;
}

.sequence-list::-webkit-scrollbar-thumb {
  background: rgba(233, 61, 130, 0.4);
  border-radius: 2px;
}

.sequence-item {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(20, 20, 30, 0.8);
  border: 1px solid rgba(100, 100, 120, 0.3);
  border-radius: 4px;
  padding: 3px 5px;
}

.sequence-item:hover {
  border-color: rgba(0, 255, 208, 0.4);
}

.item-index {
  font-size: 10px;
  font-weight: bold;
  color: #FFB800;
  min-width: 18px;
}

.item-details {
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.item-prompt {
  font-size: 9px;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.item-params {
  font-size: 8px;
  color: #888;
}

.item-actions {
  display: flex;
  gap: 2px;
}

.icon-btn {
  background: transparent;
  border: none;
  color: #aaa;
  font-size: 9px;
  cursor: pointer;
  padding: 1px 3px;
  border-radius: 2px;
}

.icon-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.icon-btn:disabled {
  opacity: 0.2;
  cursor: default;
}

.remove-btn:hover:not(:disabled) {
  color: #ff6b6b;
  background: rgba(255, 50, 50, 0.2);
}
</style>
