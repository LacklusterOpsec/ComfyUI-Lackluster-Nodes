import { createApp, type App as VueApp } from 'vue'

const { app } = window.comfyAPI.app
const { api } = window.comfyAPI.api

import App from './App.vue'
import type { CameraState, AppExposed, QwenMultiangleNode, SequenceItem } from './types'

// Inject CSS from built assets
;(() => {
  const cssUrl = new URL(/* @vite-ignore */ './assets/main.css', import.meta.url).href
  const link = document.createElement('link')
  link.rel = 'stylesheet'
  link.href = cssUrl
  document.head.appendChild(link)
})()

interface QwenInstance {
  container: HTMLElement
  vueApp: VueApp
  exposed: AppExposed
  currentNode: QwenMultiangleNode
  widget: DOMWidgetInstance | null
  cleanupTimer: number | null
}

const instances = new WeakMap<QwenMultiangleNode, QwenInstance>()
const CLEANUP_DELAY_MS = 200

const PROP_KEY = 'qwenCameraState'

interface StoredCameraState {
  azimuth: number
  elevation: number
  distance: number
  cameraView: boolean
  sequence: SequenceItem[]
}

function getWidgetValue(
  node: QwenMultiangleNode,
  name: string,
  defaultValue: number
): number {
  const widget = node.widgets?.find(w => w.name === name)
  return widget ? Number(widget.value) : defaultValue
}

function readStoredProps(node: QwenMultiangleNode): Partial<StoredCameraState> | null {
  const raw = node.properties?.[PROP_KEY]
  if (!raw || typeof raw !== 'object') return null
  return raw as Partial<StoredCameraState>
}

function writeStoredProps(
  node: QwenMultiangleNode,
  patch: Partial<StoredCameraState>
): void {
  if (!node.properties) node.properties = {}
  const existing = (node.properties[PROP_KEY] as Partial<StoredCameraState>) ?? {}
  node.properties[PROP_KEY] = { ...existing, ...patch }
}

function readStateFromNode(node: QwenMultiangleNode): Partial<CameraState> {
  const stored = readStoredProps(node)
  let sequence = stored?.sequence
  if (!sequence) {
    const seqWidget = node.widgets?.find(w => w.name === 'sequence_json')
    if (seqWidget && typeof seqWidget.value === 'string' && seqWidget.value) {
      try {
        sequence = JSON.parse(seqWidget.value)
      } catch (e) {}
    }
  }
  return {
    azimuth: stored?.azimuth ?? getWidgetValue(node, 'horizontal_angle', 0),
    elevation: stored?.elevation ?? getWidgetValue(node, 'vertical_angle', 0),
    distance: stored?.distance ?? getWidgetValue(node, 'zoom', 5.0),
    sequence: sequence ?? []
  }
}

function readCameraViewFromNode(node: QwenMultiangleNode): boolean {
  const stored = readStoredProps(node)
  if (stored?.cameraView !== undefined) return Boolean(stored.cameraView)
  const w = node.widgets?.find(w => w.name === 'camera_view')
  return Boolean(w?.value)
}

function syncWidgetsFromState(
  node: QwenMultiangleNode,
  state: Partial<StoredCameraState>
): void {
  const h = node.widgets?.find(w => w.name === 'horizontal_angle')
  const v = node.widgets?.find(w => w.name === 'vertical_angle')
  const z = node.widgets?.find(w => w.name === 'zoom')
  const cv = node.widgets?.find(w => w.name === 'camera_view')
  const seqW = node.widgets?.find(w => w.name === 'sequence_json')
  if (state.azimuth !== undefined && h) h.value = state.azimuth
  if (state.elevation !== undefined && v) v.value = state.elevation
  if (state.distance !== undefined && z) z.value = state.distance
  if (state.cameraView !== undefined && cv) cv.value = state.cameraView
  if (state.sequence !== undefined && seqW) seqW.value = JSON.stringify(state.sequence)
}

function createInstance(node: QwenMultiangleNode): QwenInstance {
  const container = document.createElement('div')
  container.id = `lackluster-qwen-widget-${node.id}`
  container.style.width = '100%'
  container.style.height = '100%'
  container.style.minHeight = '350px'

  const instance = {} as QwenInstance
  instance.container = container
  instance.currentNode = node
  instance.widget = null
  instance.cleanupTimer = null

  const vueApp = createApp(App, {
    initialState: readStateFromNode(node),
    onStateChange: (state: CameraState) => {
      const live = instance.currentNode
      syncWidgetsFromState(live, {
        azimuth: state.azimuth,
        elevation: state.elevation,
        distance: state.distance,
        sequence: state.sequence
      })
      writeStoredProps(live, {
        azimuth: state.azimuth,
        elevation: state.elevation,
        distance: state.distance,
        sequence: state.sequence
      })
      app.graph?.setDirtyCanvas(true, true)
    }
  })
  const mounted = vueApp.mount(container)
  instance.vueApp = vueApp
  instance.exposed = mounted as unknown as AppExposed

  instances.set(node, instance)
  return instance
}

function bindWidgetCallbacks(
  node: QwenMultiangleNode,
  exposed: AppExposed
): void {
  const wire = (name: string, apply: (value: unknown) => void) => {
    const w = node.widgets?.find(widget => widget.name === name)
    if (!w) return
    const origCallback = w.callback
    w.callback = (value: unknown) => {
      origCallback?.call(w, value)
      apply(value)
    }
  }

  wire('horizontal_angle', v => {
    const azimuth = Number(v)
    exposed.setState({ azimuth })
    writeStoredProps(node, { azimuth })
  })
  wire('vertical_angle', v => {
    const elevation = Number(v)
    exposed.setState({ elevation })
    writeStoredProps(node, { elevation })
  })
  wire('zoom', v => {
    const distance = Number(v)
    exposed.setState({ distance })
    writeStoredProps(node, { distance })
  })
  wire('camera_view', v => {
    const cameraView = Boolean(v)
    exposed.setCameraView(cameraView)
    writeStoredProps(node, { cameraView })
  })
}

function createCameraWidget(node: QwenMultiangleNode): DOMWidgetInstance {
  let instance = instances.get(node)

  if (instance) {
    if (instance.cleanupTimer !== null) {
      clearTimeout(instance.cleanupTimer)
      instance.cleanupTimer = null
    }
    instance.currentNode = node
    instance.exposed.setState(readStateFromNode(node))
    instance.exposed.setCameraView(readCameraViewFromNode(node))
  } else {
    instance = createInstance(node)
    if (readCameraViewFromNode(node)) {
      instance.exposed.setCameraView(true)
    }
  }

  const widget = node.addDOMWidget(
    'camera_preview',
    'lackluster-qwen-multiangle',
    instance.container,
    {
      getMinHeight: () => 370,
      hideOnZoom: false,
      serialize: false
    }
  )

  instance.widget = widget
  bindWidgetCallbacks(node, instance.exposed)

  const baseOnRemove = widget.onRemove?.bind(widget)
  widget.onRemove = () => {
    baseOnRemove?.()

    const current = instances.get(node)
    if (!current || current.widget !== widget) return

    current.cleanupTimer = window.setTimeout(() => {
      const still = instances.get(node)
      if (!still || still.widget !== widget) return
      still.exposed.cleanup()
      still.vueApp.unmount()
      instances.delete(node)
    }, CLEANUP_DELAY_MS)
  }

  return widget
}

function setupImageInput(node: QwenMultiangleNode): void {
  const originalOnConnectionsChange = node.onConnectionsChange

  node.onConnectionsChange = function(
    slotType: number,
    slotIndex: number,
    isConnected: boolean,
    link: unknown,
    ioSlot: unknown
  ) {
    if (originalOnConnectionsChange) {
      originalOnConnectionsChange.call(this, slotType, slotIndex, isConnected, link, ioSlot)
    }

    if (slotType === 1 && slotIndex === 0) {
      const inst = instances.get(node)
      if (inst && !isConnected) {
        inst.exposed.updateImage(null)
      }
    }
  }
}

type PreviewImage = { filename: string; subfolder: string; type: string }

function applyPreviewImageFromOutput(
  instance: QwenInstance,
  output: unknown
): void {
  if (!output || typeof output !== 'object') return
  const images = (output as { preview_images?: PreviewImage[] }).preview_images
  if (!images || images.length === 0) return
  const img = images[0]
  const params = new URLSearchParams({
    filename: img.filename,
    subfolder: img.subfolder,
    type: img.type
  })
  const url = api.apiURL(`/view?${params.toString()}`)
  instance.exposed.updateImage(url)
}

function setupOnExecuted(node: QwenMultiangleNode, instance: QwenInstance): void {
  const originalOnExecuted = node.onExecuted
  node.onExecuted = function(output: unknown) {
    originalOnExecuted?.call(this, output)
    applyPreviewImageFromOutput(instance, output)
  }
}

function setupOnPropertyChanged(
  node: QwenMultiangleNode,
  instance: QwenInstance
): void {
  const originalOnPropertyChanged = node.onPropertyChanged
  node.onPropertyChanged = function(key: string, value: unknown) {
    originalOnPropertyChanged?.call(this, key, value)
    if (key !== PROP_KEY) return
    if (!value || typeof value !== 'object') return

    const state = value as Partial<StoredCameraState>
    instance.exposed.setState({
      azimuth: state.azimuth,
      elevation: state.elevation,
      distance: state.distance,
      sequence: state.sequence
    })
    if (state.cameraView !== undefined) {
      instance.exposed.setCameraView(Boolean(state.cameraView))
    }
    syncWidgetsFromState(node, state)
  }
}

app.registerExtension({
  name: 'ComfyUI.LacklusterQwenMultiangle',

  nodeCreated(node: QwenMultiangleNode) {
    const comfyClass = (node.constructor as unknown as { comfyClass?: string })?.comfyClass || node.type
    if (
      comfyClass !== 'LacklusterCameraNode' &&
      comfyClass !== 'LacklusterCameraSequenceNode' &&
      comfyClass !== 'LacklusterQwenMultiangleCameraNode' &&
      comfyClass !== 'LacklusterQwenMultiangleSequenceNode'
    ) {
      return
    }

    const [oldWidth, oldHeight] = node.size
    const isSeq = comfyClass === 'LacklusterCameraSequenceNode' || comfyClass === 'LacklusterQwenMultiangleSequenceNode'
    node.setSize([Math.max(oldWidth, isSeq ? 420 : 350), Math.max(oldHeight, isSeq ? 560 : 520)])


    createCameraWidget(node)
    setupImageInput(node)
    const inst = instances.get(node)
    if (inst) {
      setupOnExecuted(node, inst)
      setupOnPropertyChanged(node, inst)
    }
  }
})
