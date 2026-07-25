import { ref, watch } from 'vue'
import { CameraWidget, buildAnglePrompt } from '../CameraWidget'
import type { CameraState, SequenceItem } from '../types'

export function useCameraWidget(
  initialState: Partial<CameraState> = {},
  onExternalStateChange?: (state: CameraState) => void
) {
  const azimuth = ref(initialState.azimuth ?? 0)
  const elevation = ref(initialState.elevation ?? 0)
  const distance = ref(initialState.distance ?? 5)
  const imageUrl = ref<string | null>(null)
  const prompt = ref('<sks> front view eye-level shot medium shot')
  const sequenceList = ref<SequenceItem[]>(initialState.sequence ?? [])

  let widget: CameraWidget | null = null
  let updatingFromWidget = false
  let updatingFromExternal = false

  function notifyParent() {
    onExternalStateChange?.({
      azimuth: azimuth.value,
      elevation: elevation.value,
      distance: distance.value,
      imageUrl: imageUrl.value,
      sequence: sequenceList.value
    })
  }

  function initScene(container: HTMLElement) {
    widget = new CameraWidget({
      container,
      initialState: {
        azimuth: azimuth.value,
        elevation: elevation.value,
        distance: distance.value
      },
      onStateChange: (state: CameraState) => {
        updatingFromWidget = true
        azimuth.value = state.azimuth
        elevation.value = state.elevation
        distance.value = state.distance
        prompt.value = widget!.generatePrompt()
        updatingFromWidget = false
        notifyParent()
      }
    })
    prompt.value = widget.generatePrompt()
  }

  watch([azimuth, elevation, distance], () => {
    if (!updatingFromWidget && !updatingFromExternal && widget) {
      widget.setState({
        azimuth: azimuth.value,
        elevation: elevation.value,
        distance: distance.value
      })
      prompt.value = widget.generatePrompt()
      notifyParent()
    }
  }, { flush: 'sync' })

  function setState(state: Partial<CameraState>) {
    updatingFromExternal = true
    if (state.azimuth !== undefined) azimuth.value = state.azimuth
    if (state.elevation !== undefined) elevation.value = state.elevation
    if (state.distance !== undefined) distance.value = state.distance
    if (state.sequence !== undefined) sequenceList.value = state.sequence
    widget?.setState(state)
    if (widget) prompt.value = widget.generatePrompt()
    updatingFromExternal = false
  }

  function addCurrentAngle() {
    const p = buildAnglePrompt(azimuth.value, elevation.value, distance.value)
    sequenceList.value.push({
      id: Math.random().toString(36).substring(2, 9),
      azimuth: Math.round(azimuth.value),
      elevation: Math.round(elevation.value),
      distance: Math.round(distance.value * 10) / 10,
      prompt: p
    })
    notifyParent()
  }

  function addPreset(type: '4-turnaround' | '8-turnaround') {
    const angles = type === '4-turnaround' ? [0, 90, 180, 270] : [0, 45, 90, 135, 180, 225, 270, 315]
    for (const az of angles) {
      const p = buildAnglePrompt(az, elevation.value, distance.value)
      sequenceList.value.push({
        id: Math.random().toString(36).substring(2, 9),
        azimuth: az,
        elevation: Math.round(elevation.value),
        distance: Math.round(distance.value * 10) / 10,
        prompt: p
      })
    }
    notifyParent()
  }

  function removeAngle(index: number) {
    if (index >= 0 && index < sequenceList.value.length) {
      sequenceList.value.splice(index, 1)
      notifyParent()
    }
  }

  function moveAngle(from: number, to: number) {
    if (from >= 0 && from < sequenceList.value.length && to >= 0 && to < sequenceList.value.length) {
      const item = sequenceList.value.splice(from, 1)[0]
      sequenceList.value.splice(to, 0, item)
      notifyParent()
    }
  }

  function previewAngle(item: SequenceItem) {
    setState({
      azimuth: item.azimuth,
      elevation: item.elevation,
      distance: item.distance
    })
  }

  function clearSequence() {
    sequenceList.value = []
    notifyParent()
  }

  function setSequence(seq: SequenceItem[]) {
    sequenceList.value = seq
    notifyParent()
  }

  function updateImage(url: string | null) {
    imageUrl.value = url
    widget?.updateImage(url)
  }

  function setCameraView(enabled: boolean) {
    widget?.setCameraView(enabled)
  }

  function reset() {
    updatingFromExternal = true
    azimuth.value = 0
    elevation.value = 0
    distance.value = 5
    updatingFromExternal = false
    widget?.setState({ azimuth: 0, elevation: 0, distance: 5 })
    if (widget) prompt.value = widget.generatePrompt()
    notifyParent()
  }

  function cleanup() {
    widget?.dispose()
    widget = null
  }

  return {
    azimuth,
    elevation,
    distance,
    imageUrl,
    prompt,
    sequenceList,
    initScene,
    setState,
    addCurrentAngle,
    addPreset,
    removeAngle,
    moveAngle,
    previewAngle,
    clearSequence,
    setSequence,
    updateImage,
    setCameraView,
    reset,
    cleanup
  }
}
