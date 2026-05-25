import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '@/api/client'
import { useHotelStore } from '@/stores/hotelStore'
import { isAnonymousEnabled } from '@/services/asso/config'

export interface Hotel {
  id: number
  name_cn: string
  name_en?: string
  address_cn: string
  city: string
  country: string
  star_rating?: number
  status: 'draft' | 'active' | 'inactive'
  created_at: string
  updated_at: string
  // Extension fields
  description?: string
  description_cn?: string
  cancellation_policy?: string
  cancellation_policy_cn?: string
  prepayment_policy?: string
  prepayment_policy_cn?: string
  kid_policy?: string
  pet_policy?: string
  services?: string
  services_cn?: string
  facilities?: string
  facilities_cn?: string
  check_in_time?: string
  check_out_time?: string
  phone?: string
  email?: string
}

export interface HotelExtensionUpdate {
  description?: string
  description_cn?: string
  cancellation_policy?: string
  cancellation_policy_cn?: string
  prepayment_policy?: string
  prepayment_policy_cn?: string
  kid_policy?: string
  pet_policy?: string
  services?: string
  services_cn?: string
  facilities?: string
  facilities_cn?: string
  check_in_time?: string
  check_out_time?: string
  phone?: string
  email?: string
}

export interface HotelListResponse {
  items: Hotel[]
  total: number
  page: number
  page_size: number
}

export function useHotels() {
  const { page, pageSize, filters } = useHotelStore()
  // In anonymous mode, return empty data without making API calls
  const anonymous = typeof window !== 'undefined' && isAnonymousEnabled()

  const query = useQuery({
    queryKey: ['hotels', page, pageSize, filters],
    queryFn: async () => {
      if (anonymous) {
        return { items: [], total: 0, page: 1, page_size: 20 }
      }
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        ...filters,
      })
      const response = await apiClient.get(`/hotels?${params}`)
      return response.data.data as HotelListResponse
    },
    enabled: !anonymous,
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
      const response = await apiClient.get(`/hotels/${id}`)
      return response.data.data as Hotel
    },
    enabled: !!id,
  })
}

export function useCreateHotel() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: Partial<Hotel>) => {
      const response = await apiClient.post('/hotels', data)
      return response.data.data as Hotel
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
      return response.data.data as Hotel
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
      const response = await apiClient.get('/hotels/search', { params: { q: query } })
      return (response.data.data ?? []) as Hotel[]
    },
    enabled: query.length >= 2,
  })
}

export function useUpdateHotelExtension() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ hotelId, data }: { hotelId: number; data: HotelExtensionUpdate }) => {
      const response = await apiClient.put(`/hotels/${hotelId}/extension`, data)
      return response.data.data as Hotel
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['hotels'] })
      queryClient.invalidateQueries({ queryKey: ['hotel', variables.hotelId] })
    },
  })
}
