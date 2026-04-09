import { create } from 'zustand'

interface Translation {
  id: number
  source_text: string
  translated_text: string
  source_lang: string
  target_lang: string
  status: 'pending' | 'completed' | 'failed'
  created_at: string
}

interface TranslationState {
  translations: Translation[]
  currentTranslation: Translation | null
  setTranslations: (translations: Translation[]) => void
  setCurrentTranslation: (translation: Translation | null) => void
}

export const useTranslationStore = create<TranslationState>((set) => ({
  translations: [],
  currentTranslation: null,
  setTranslations: (translations) => set({ translations }),
  setCurrentTranslation: (currentTranslation) => set({ currentTranslation }),
}))
