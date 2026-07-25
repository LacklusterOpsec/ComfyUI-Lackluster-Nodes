export interface SequenceItem {
  id: string
  azimuth: number
  elevation: number
  distance: number
  prompt: string
}

export interface CameraState {
  azimuth: number
  elevation: number
  distance: number
  imageUrl: string | null
  sequence?: SequenceItem[]
}

export interface CameraWidgetOptions {
  container: HTMLElement
  initialState?: Partial<CameraState>
  onStateChange?: (state: CameraState) => void
}

export interface AppExposed {
  updateImage: (url: string | null) => void
  setCameraView: (enabled: boolean) => void
  setState: (state: Partial<CameraState>) => void
  setSequence: (sequence: SequenceItem[]) => void
  cleanup: () => void
}

export type QwenMultiangleNode = ComfyNode
