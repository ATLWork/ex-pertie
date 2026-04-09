import { create } from 'zustand'

interface ImportRecord {
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

interface ImportState {
  imports: ImportRecord[]
  currentImport: ImportRecord | null
  setImports: (imports: ImportRecord[]) => void
  setCurrentImport: (record: ImportRecord | null) => void
}

export const useImportStore = create<ImportState>((set) => ({
  imports: [],
  currentImport: null,
  setImports: (imports) => set({ imports }),
  setCurrentImport: (record) => set({ currentImport: record }),
}))
