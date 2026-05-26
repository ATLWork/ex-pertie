import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/api/client'
import { isAnonymousEnabled } from '@/services/asso/config'

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
  source_lang: string
  target_lang: string
  category?: string
  notes?: string
  is_active: boolean
  review_status?: 'pending' | 'approved' | 'rejected'
  reviewed_by?: string
  reviewed_at?: string
  reviewed_notes?: string
  created_at: string
  updated_at: string
}

export interface TranslationRule {
  id: number
  name: string
  source_lang: string
  target_lang: string
  field_name: string
  rule_type: 'direct' | 'glossary' | 'ai'
  rule_value: string
  region?: string
  province?: string
  city?: string
  priority: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ParsedRule {
  name: string
  source_lang: string
  target_lang: string
  field_name: string
  rule_type: string
  rule_value: string
  is_active: boolean
}

export interface PdfParseResult {
  rules_count: number
  rules: ParsedRule[]
  summary: string
  document_type: string
  warning?: string
}

export interface PdfImportResult {
  imported_count: number
  skipped_count: number
  error_count: number
  errors: Array<{ rule: string; error: string }>
  summary: string
}

export function useTranslate() {
  return useMutation({
    mutationFn: async ({ text, sourceLang, targetLang, context, useAiEnhance }: {
      text: string
      sourceLang: string
      targetLang: string
      context?: string
      useAiEnhance?: boolean
    }) => {
      const response = await apiClient.post('/translation/translate', {
        text,
        source_lang: sourceLang,
        target_lang: targetLang,
        context,
        use_ai_enhance: useAiEnhance,
      })
      return response.data.data
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
      return response.data.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['translations'] })
    },
  })
}

export function useGlossary() {
  // In anonymous mode, return empty data without making API calls
  const anonymous = typeof window !== 'undefined' && isAnonymousEnabled()

  return useQuery({
    queryKey: ['glossary'],
    queryFn: async () => {
      if (anonymous) {
        return []
      }
      const response = await apiClient.get('/translation/glossary')
      // API 返回结构: PagedResponse { code, message, data: { list: GlossaryResponse[], total, page, page_size, total_pages } }
      return response.data.data?.list ?? []
    },
    enabled: !anonymous,
  })
}

export function useGlossaryItem(id: number) {
  return useQuery({
    queryKey: ['glossary', id],
    queryFn: async () => {
      const response = await apiClient.get(`/translation/glossary/${id}`)
      return response.data.data
    },
    enabled: !!id,
  })
}

export function useCreateGlossary() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: Partial<Glossary>) => {
      const response = await apiClient.post('/translation/glossary', data)
      return response.data.data
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
      return response.data.data
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

export function useGlossaryReviewStats() {
  return useQuery({
    queryKey: ['glossaryReviewStats'],
    queryFn: async () => {
      const response = await apiClient.get('/translation/glossary/review/stats')
      return response.data.data
    },
  })
}

export function useGlossaryPendingReviews(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ['glossaryPendingReviews', page, pageSize],
    queryFn: async () => {
      const response = await apiClient.get('/translation/glossary/review/pending', {
        params: { page, page_size: pageSize },
      })
      return response.data.data
    },
  })
}

export function useGlossaryByStatus(status: string, page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ['glossaryByStatus', status, page, pageSize],
    queryFn: async () => {
      const response = await apiClient.get('/translation/glossary/review/by-status', {
        params: { status, page, page_size: pageSize },
      })
      return response.data.data
    },
    enabled: !!status,
  })
}

export function useApproveGlossary() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      const response = await apiClient.post(`/translation/glossary/${id}/approve`)
      return response.data.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['glossaryPendingReviews'] })
      queryClient.invalidateQueries({ queryKey: ['glossaryReviewStats'] })
    },
  })
}

export function useRejectGlossary() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, reviewNotes }: { id: number; reviewNotes?: string }) => {
      const response = await apiClient.post(`/translation/glossary/${id}/reject`, null, {
        params: { review_notes: reviewNotes },
      })
      return response.data.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['glossaryPendingReviews'] })
      queryClient.invalidateQueries({ queryKey: ['glossaryReviewStats'] })
    },
  })
}

export function useExportGlossary() {
  return useMutation({
    mutationFn: async (params: { source_lang?: string; target_lang?: string; category?: string; status?: string }) => {
      const response = await apiClient.get('/translation/glossary/do-export', { params })
      return response.data.data
    },
  })
}

export function useTranslationRules(
  page = 1,
  pageSize = 20,
  sourceLang?: string,
  targetLang?: string,
  fieldName?: string,
) {
  return useQuery({
    queryKey: ['translationRules', page, pageSize, sourceLang, targetLang, fieldName],
    queryFn: async () => {
      const response = await apiClient.get('/translation/rules', {
        params: { page, page_size: pageSize, source_lang: sourceLang, target_lang: targetLang, field_name: fieldName },
      })
      // API 返回结构: PagedResponse { code, message, data: { list: TranslationRule[], total, page, page_size, total_pages } }
      return response.data.data ?? { list: [], total: 0, page: 1, page_size: pageSize, total_pages: 0 }
    },
  })
}

export function useTranslationRule(id: number) {
  return useQuery({
    queryKey: ['translationRule', id],
    queryFn: async () => {
      const response = await apiClient.get(`/translation/rules/${id}`)
      return response.data.data
    },
    enabled: !!id,
  })
}

export function useCreateTranslationRule() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: {
      name: string
      source_lang: string
      target_lang: string
      field_name: string
      rule_type: 'direct' | 'glossary' | 'ai'
      rule_value: string
      is_active?: boolean
    }) => {
      const response = await apiClient.post('/translation/rules', data)
      return response.data.data
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
      return response.data.data
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

export function useParsePdfRules() {
  return useMutation({
    mutationFn: async ({ file, useAi = true }: { file: File; useAi?: boolean }) => {
      const formData = new FormData()
      formData.append('file', file)
      const response = await apiClient.post('/translation/rules/parse-pdf', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        params: { use_ai: useAi },
      })
      return response.data.data as PdfParseResult
    },
  })
}

export function useImportPdfRules() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ file, useAi = true, overwrite = false }: { file: File; useAi?: boolean; overwrite?: boolean }) => {
      const formData = new FormData()
      formData.append('file', file)
      const response = await apiClient.post('/translation/rules/import-pdf', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        params: { use_ai: useAi, overwrite },
      })
      return response.data.data as PdfImportResult
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['translationRules'] })
    },
  })
}

export function useEvaluateQuality() {
  return useMutation({
    mutationFn: async ({ sourceText, translatedText, sourceLang, targetLang }: {
      sourceText: string
      translatedText: string
      sourceLang: string
      targetLang: string
    }) => {
      const response = await apiClient.post('/translation/evaluate-quality', null, {
        params: {
          original_text: sourceText,
          translated_text: translatedText,
          source_lang: sourceLang,
          target_lang: targetLang,
        },
      })
      return response.data.data
    },
  })
}

export function useTranslationReferences() {
  return useQuery({
    queryKey: ['translationReferences'],
    queryFn: async () => {
      const response = await apiClient.get('/translation/references')
      // API 返回结构: PagedResponse { code, message, data: { list: Reference[], total, page, page_size, total_pages } }
      return response.data.data?.list ?? []
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
      return response.data.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['translationReferences'] })
    },
  })
}
