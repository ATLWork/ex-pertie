import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/api/client'

export interface Translation {
  id: number
  source_text: string
  translated_text: string
  source_lang: string
  target_lang: string
  context?: string
  status: 'pending' | 'completed' | 'failed'
  created_at: string
}

export interface Glossary {
  id: number
  term: string
  translation: string
  category?: string
  created_at: string
}

export interface TranslationRule {
  id: number
  pattern: string
  replacement: string
  description?: string
  priority: number
  enabled: boolean
  created_at: string
}

export function useTranslate() {
  return useMutation({
    mutationFn: async ({ text, sourceLang, targetLang, context }: {
      text: string
      sourceLang: string
      targetLang: string
      context?: string
    }) => {
      const response = await apiClient.post('/translation/translate', {
        text,
        source_lang: sourceLang,
        target_lang: targetLang,
        context,
      })
      return response.data
    },
  })
}

export function useBatchTranslate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ texts, sourceLang, targetLang }: {
      texts: string[]
      sourceLang: string
      targetLang: string
    }) => {
      const response = await apiClient.post('/translation/batch', {
        texts,
        source_lang: sourceLang,
        target_lang: targetLang,
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['translations'] })
    },
  })
}

export function useGlossary() {
  return useQuery({
    queryKey: ['glossary'],
    queryFn: async () => {
      const response = await apiClient.get<Glossary[]>('/translation/glossary')
      return response.data
    },
  })
}

export function useGlossaryItem(id: number) {
  return useQuery({
    queryKey: ['glossary', id],
    queryFn: async () => {
      const response = await apiClient.get<Glossary>(`/translation/glossary/${id}`)
      return response.data
    },
    enabled: !!id,
  })
}

export function useCreateGlossary() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: Partial<Glossary>) => {
      const response = await apiClient.post('/translation/glossary', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['glossary'] })
    },
  })
}

export function useUpdateGlossary() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<Glossary> }) => {
      const response = await apiClient.put(`/translation/glossary/${id}`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['glossary'] })
    },
  })
}

export function useDeleteGlossary() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/translation/glossary/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['glossary'] })
    },
  })
}

export function useTranslationRules() {
  return useQuery({
    queryKey: ['translationRules'],
    queryFn: async () => {
      const response = await apiClient.get<TranslationRule[]>('/translation/rules')
      return response.data
    },
  })
}

export function useTranslationRule(id: number) {
  return useQuery({
    queryKey: ['translationRule', id],
    queryFn: async () => {
      const response = await apiClient.get<TranslationRule>(`/translation/rules/${id}`)
      return response.data
    },
    enabled: !!id,
  })
}

export function useCreateTranslationRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: Partial<TranslationRule>) => {
      const response = await apiClient.post('/translation/rules', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['translationRules'] })
    },
  })
}

export function useUpdateTranslationRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<TranslationRule> }) => {
      const response = await apiClient.put(`/translation/rules/${id}`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['translationRules'] })
    },
  })
}

export function useDeleteTranslationRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/translation/rules/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['translationRules'] })
    },
  })
}

export function useTranslationReferences() {
  return useQuery({
    queryKey: ['translationReferences'],
    queryFn: async () => {
      const response = await apiClient.get('/translation/references')
      return response.data
    },
  })
}

export function useCreateTranslationReference() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: FormData) => {
      const response = await apiClient.post('/translation/references', data, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['translationReferences'] })
    },
  })
}
