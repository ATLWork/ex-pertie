import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/api/client'
import { isAnonymousEnabled } from '@/services/asso/config'

export interface ExportRecord {
  id: number
  type: 'hotels' | 'rooms'
  format: 'xlsx' | 'csv'
  status: 'pending' | 'processing' | 'completed' | 'failed'
  filename?: string
  download_url?: string
  created_at: string
  completed_at?: string
}

export function useExports() {
  // In anonymous mode, return empty data without making API calls
  const anonymous = typeof window !== 'undefined' && isAnonymousEnabled()

  const query = useQuery({
    queryKey: ['exports'],
    queryFn: async () => {
      if (anonymous) {
        return []
      }
      const response = await apiClient.get('/exports')
      // API 返回结构: PagedResponse { code, message, data: { list: ExportRecord[], total, page, page_size, total_pages } }
      return (response.data.data?.list ?? []) as ExportRecord[]
    },
    enabled: !anonymous,
  })

  return {
    exports: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  }
}

export function useExport(id: number) {
  return useQuery({
    queryKey: ['export', id],
    queryFn: async () => {
      const response = await apiClient.get(`/exports/${id}`)
      return response.data.data as ExportRecord
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

export function useExportHotels() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ hotelIds, format }: { hotelIds: string[]; format: 'xlsx' | 'csv' }) => {
      const response = await apiClient.post('/exports/hotels', { hotel_ids: hotelIds, format })
      return response.data.data as ExportRecord
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exports'] })
    },
  })
}

export function useExportRooms() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ hotelIds, format }: { hotelIds: string[]; format: 'xlsx' | 'csv' }) => {
      const response = await apiClient.post('/exports/rooms', { hotel_ids: hotelIds, format })
      return response.data.data as ExportRecord
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['exports'] })
    },
  })
}

export function useDownloadExport(id: number) {
  return useMutation({
    mutationFn: async () => {
      const response = await apiClient.get(`/exports/${id}/download`, {
        responseType: 'blob',
      })
      return response.data
    },
  })
}
