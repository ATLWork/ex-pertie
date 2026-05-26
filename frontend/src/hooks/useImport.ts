import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/api/client'
import { isAnonymousEnabled } from '@/services/asso/config'

export interface ImportRecord {
  id: number
  type: 'hotels' | 'rooms'
  filename: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  total_rows: number
  processed_rows: number
  error_count: number
  created_at: string
  completed_at?: string
}

export function useImports() {
  // In anonymous mode, return empty data without making API calls
  const anonymous = typeof window !== 'undefined' && isAnonymousEnabled()

  const query = useQuery({
    queryKey: ['imports'],
    queryFn: async () => {
      // Skip API call in anonymous mode
      if (anonymous) {
        return []
      }
      const response = await apiClient.get('/imports')
      // API 返回结构: PagedResponse { code, message, data: { list: ImportRecord[], total, page, page_size, total_pages } }
      return (response.data.data?.list ?? []) as ImportRecord[]
    },
    enabled: !anonymous,
  })

  return {
    imports: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  }
}

export function useImport(id: number) {
  return useQuery({
    queryKey: ['import', id],
    queryFn: async () => {
      const response = await apiClient.get(`/imports/${id}`)
      return response.data.data as ImportRecord
    },
    enabled: !!id,
    refetchInterval: (query) => {
      const data = query.state.data
      if (data && data.status === 'processing') {
        return 2000
      }
      return false
    },
  })
}

export function useImportErrors(id: number) {
  return useQuery({
    queryKey: ['importErrors', id],
    queryFn: async () => {
      const response = await apiClient.get(`/imports/${id}/errors`)
      return response.data.data
    },
    enabled: !!id,
  })
}

export function useImportHotels() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      const response = await apiClient.post('/imports/hotels', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return response.data.data as ImportRecord
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['imports'] })
      queryClient.invalidateQueries({ queryKey: ['hotels'] })
    },
  })
}

export function useImportRooms() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      const response = await apiClient.post('/imports/rooms', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      return response.data.data as ImportRecord
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['imports'] })
    },
  })
}
