import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/api/client'
import { useHotelStore } from '@/stores/hotelStore'

export interface Hotel {
  id: number
  name: string
  name_en?: string
  address: string
  city: string
  country: string
  star_rating?: number
  status: 'draft' | 'active' | 'inactive'
  created_at: string
  updated_at: string
}

export interface HotelListResponse {
  items: Hotel[]
  total: number
  page: number
  page_size: number
}

export function useHotels() {
  const { page, pageSize, filters } = useHotelStore()

  const query = useQuery({
    queryKey: ['hotels', page, pageSize, filters],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        ...filters,
      })
      const response = await apiClient.get<HotelListResponse>(`/hotels?${params}`)
      return response.data
    },
  })

  const setHotels = useHotelStore((state) => state.setHotels)

  return {
    hotels: query.data?.items ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
    setHotels,
  }
}

export function useHotel(id: number) {
  return useQuery({
    queryKey: ['hotel', id],
    queryFn: async () => {
      const response = await apiClient.get<Hotel>(`/hotels/${id}`)
      return response.data
    },
    enabled: !!id,
  })
}

export function useCreateHotel() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: Partial<Hotel>) => {
      const response = await apiClient.post('/hotels', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hotels'] })
    },
  })
}

export function useUpdateHotel() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: Partial<Hotel> }) => {
      const response = await apiClient.put(`/hotels/${id}`, data)
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['hotels'] })
      queryClient.invalidateQueries({ queryKey: ['hotel', variables.id] })
    },
  })
}

export function useDeleteHotel() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/hotels/${id}`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hotels'] })
    },
  })
}

export function useSearchHotels(query: string) {
  return useQuery({
    queryKey: ['hotels', 'search', query],
    queryFn: async () => {
      const response = await apiClient.get<Hotel[]>('/hotels/search', { params: { q: query } })
      return response.data
    },
    enabled: query.length >= 2,
  })
}
