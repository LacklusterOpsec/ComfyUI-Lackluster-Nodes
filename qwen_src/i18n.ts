const { app } = window.comfyAPI.app

export type Locale = 'en' | 'zh' | 'ja' | 'ko'

export interface Translations {
  horizontal: string
  vertical: string
  zoom: string
  horizontalFull: string
  verticalFull: string
  zoomFull: string
  resetToDefaults: string
  frontView: string
  frontRightQuarterView: string
  rightSideView: string
  backRightQuarterView: string
  backView: string
  backLeftQuarterView: string
  leftSideView: string
  frontLeftQuarterView: string
  lowAngleShot: string
  eyeLevelShot: string
  elevatedShot: string
  highAngleShot: string
  wideShot: string
  mediumShot: string
  closeUp: string
}

const translations: Record<Locale, Translations> = {
  en: {
    horizontal: 'H',
    vertical: 'V',
    zoom: 'Z',
    horizontalFull: 'Horizontal',
    verticalFull: 'Vertical',
    zoomFull: 'Zoom',
    resetToDefaults: 'Reset to defaults',
    frontView: 'front view',
    frontRightQuarterView: 'front-right quarter view',
    rightSideView: 'right side view',
    backRightQuarterView: 'back-right quarter view',
    backView: 'back view',
    backLeftQuarterView: 'back-left quarter view',
    leftSideView: 'left side view',
    frontLeftQuarterView: 'front-left quarter view',
    lowAngleShot: 'low-angle shot',
    eyeLevelShot: 'eye-level shot',
    elevatedShot: 'elevated shot',
    highAngleShot: 'high-angle shot',
    wideShot: 'wide shot',
    mediumShot: 'medium shot',
    closeUp: 'close-up'
  },
  zh: {
    horizontal: '水平',
    vertical: '垂直',
    zoom: '距离',
    horizontalFull: '水平角度',
    verticalFull: '垂直角度',
    zoomFull: '距离',
    resetToDefaults: '重置为默认值',
    frontView: '正面视角',
    frontRightQuarterView: '右前方视角',
    rightSideView: '右侧视角',
    backRightQuarterView: '右后方视角',
    backView: '背面视角',
    backLeftQuarterView: '左后方视角',
    leftSideView: '左侧视角',
    frontLeftQuarterView: '左前方视角',
    lowAngleShot: '仰拍',
    eyeLevelShot: '平视',
    elevatedShot: '高角度',
    highAngleShot: '俯拍',
    wideShot: '远景',
    mediumShot: '中景',
    closeUp: '特写'
  },
  ja: {
    horizontal: '水平',
    vertical: '垂直',
    zoom: '距離',
    horizontalFull: '水平角度',
    verticalFull: '垂直角度',
    zoomFull: '距離',
    resetToDefaults: 'デフォルトにリセット',
    frontView: '正面',
    frontRightQuarterView: '右前方',
    rightSideView: '右側面',
    backRightQuarterView: '右後方',
    backView: '背面',
    backLeftQuarterView: '左後方',
    leftSideView: '左側面',
    frontLeftQuarterView: '左前方',
    lowAngleShot: 'ローアングル',
    eyeLevelShot: 'アイレベル',
    elevatedShot: 'ハイアングル',
    highAngleShot: '俯瞰',
    wideShot: 'ワイドショット',
    mediumShot: 'ミディアムショット',
    closeUp: 'クローズアップ'
  },
  ko: {
    horizontal: '수평',
    vertical: '수직',
    zoom: '거리',
    horizontalFull: '수평 각도',
    verticalFull: '수직 각도',
    zoomFull: '거리',
    resetToDefaults: '기본값으로 재설정',
    frontView: '정면',
    frontRightQuarterView: '우측 전방',
    rightSideView: '우측면',
    backRightQuarterView: '우측 후방',
    backView: '후면',
    backLeftQuarterView: '좌측 후방',
    leftSideView: '좌측면',
    frontLeftQuarterView: '좌측 전방',
    lowAngleShot: '로우 앵글',
    eyeLevelShot: '아이 레벨',
    elevatedShot: '하이 앵글',
    highAngleShot: '부감',
    wideShot: '와이드 샷',
    mediumShot: '미디엄 샷',
    closeUp: '클로즈업'
  }
}

let currentLocale: Locale = 'en'

export function detectLocale(): Locale {
  try {
    const comfyLocale = app.ui?.settings?.getSettingValue?.('Comfy.Locale')
    if (comfyLocale) {
      const localeStr = String(comfyLocale).toLowerCase()
      if (localeStr.startsWith('zh')) return 'zh'
      if (localeStr.startsWith('ja')) return 'ja'
      if (localeStr.startsWith('ko')) return 'ko'
      return 'en'
    }
  } catch (e) {}

  const browserLang = navigator.language || (navigator as unknown as { userLanguage?: string }).userLanguage || 'en'
  if (browserLang.startsWith('zh')) return 'zh'
  if (browserLang.startsWith('ja')) return 'ja'
  if (browserLang.startsWith('ko')) return 'ko'

  return 'en'
}

export function initI18n(): void {
  currentLocale = detectLocale()
}

export function getLocale(): Locale {
  return currentLocale
}

export function setLocale(locale: Locale): void {
  currentLocale = locale
}

export function t(key: keyof Translations): string {
  return translations[currentLocale][key] || translations.en[key] || key
}

export function getTranslations(): Translations {
  return translations[currentLocale]
}

initI18n()
