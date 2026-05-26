'use client'

import * as React from 'react'
import { ToastProvider, ToastViewport } from './toast'

type ToastVariant = 'default' | 'success' | 'error'

interface Toast {
  id: string
  title?: string
  description?: string
  variant?: ToastVariant
}

interface UseToastReturn {
  toast: (props: Omit<Toast, 'id'>) => void
  dismiss: (id: string) => void
}

let toasts: Toast[] = []
let listeners: Array<(toasts: Toast[]) => void> = []
let count = 0

function generateId() {
  count = (count + 1) % Number.MAX_SAFE_INTEGER
  return `toast-${count}`
}

export function useToast(): UseToastReturn {
  const [, setToastState] = React.useState<Toast[]>([])

  React.useEffect(() => {
    const listener = (newToasts: Toast[]) => {
      setToastState([...newToasts])
    }
    listeners.push(listener)
    return () => {
      listeners = listeners.filter((l) => l !== listener)
    }
  }, [])

  const toast = React.useCallback(({ title, description, variant = 'default' }: Omit<Toast, 'id'>) => {
    const id = generateId()
    const newToast: Toast = { id, title, description, variant }
    toasts = [...toasts, newToast]
    listeners.forEach((listener) => listener(toasts))
  }, [])

  const dismiss = React.useCallback((id: string) => {
    toasts = toasts.filter((t) => t.id !== id)
    listeners.forEach((listener) => listener(toasts))
  }, [])

  return { toast, dismiss }
}

export function Toaster() {
  const [toastList, setToastList] = React.useState<Toast[]>([])

  React.useEffect(() => {
    const listener = (newToasts: Toast[]) => {
      setToastList([...newToasts])
    }
    listeners.push(listener)
    return () => {
      listeners = listeners.filter((l) => l !== listener)
    }
  }, [])

  return (
    <ToastProvider>
      {toastList.map(function mapToasts({ id, title, description, variant }) {
        const className = `fixed bottom-4 right-4 z-50 w-full max-w-sm rounded-lg border p-4 shadow-lg ${variant === 'success' ? 'border-green-500 bg-green-50' : variant === 'error' ? 'border-red-500 bg-red-50' : 'border-gray-200 bg-white'}`
        return (
          <div key={id} className={className}>
            {title && <div className="text-sm font-medium">{title}</div>}
            {description && <div className="text-sm text-gray-500 mt-1">{description}</div>}
          </div>
        )
      })}
      <ToastViewport />
    </ToastProvider>
  )
}