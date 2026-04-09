import { create } from 'zustand'

interface Hotel {
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

interface HotelFilters {
  search?: string
  status?: string
  city?: string
}

interface HotelState {
  hotels: Hotel[]
  total: number
  page: number
  pageSize: number
  filters: HotelFilters
  setPage: (page: number) => void
  setPageSize: (pageSize: number) => void
  setFilters: (filters: HotelFilters) => void
  setHotels: (hotels: Hotel[], total: number) => void
}

export const useHotelStore = create<HotelState>((set) => ({
  hotels: [],
  total: 0,
  page: 1,
  pageSize: 10,
  filters: {},

  setPage: (page) => set({ page }),
  setPageSize: (pageSize) => set({ pageSize, page: 1 }),
  setFilters: (filters) => set({ filters, page: 1 }),
  setHotels: (hotels, total) => set({ hotels, total }),
}))
