<template>
  <div ref="container" class="scene-canvas" />
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

const props = defineProps<{
  initScene: (container: HTMLElement) => void
}>()

const container = ref<HTMLElement | null>(null)

onMounted(() => {
  if (container.value) {
    props.initScene(container.value)
  }
})
</script>

<style scoped>
.scene-canvas {
  width: 100%;
  height: 100%;
  position: relative;
}
</style>
