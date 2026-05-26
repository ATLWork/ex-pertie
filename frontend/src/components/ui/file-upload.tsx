'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

interface FileUploadProps {
  accept?: string
  onFileChange: (file: File) => void
  disabled?: boolean
  className?: string
}

export function FileUpload({ accept = '.xlsx,.xls,.csv', onFileChange, disabled, className }: FileUploadProps) {
  const inputRef = React.useRef<HTMLInputElement>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      onFileChange(file)
    }
  }

  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-200 bg-gray-50 p-8 cursor-pointer transition-colors hover:border-woye hover:bg-baiyan/30',
        disabled && 'opacity-50 cursor-not-allowed',
        className
      )}
      onClick={() => inputRef.current?.click()}
    >
      <input ref={inputRef} type="file" accept={accept} onChange={handleChange} disabled={disabled} className="hidden" />
      <svg className="h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
      <p className="text-sm text-gray-600">Click or drag file to upload</p>
      <p className="text-xs text-gray-400 mt-1">Support for Excel (.xlsx, .xls) and CSV files</p>
    </div>
  )
}