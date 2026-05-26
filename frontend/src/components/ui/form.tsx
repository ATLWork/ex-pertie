'use client'

import * as React from 'react'
import { useForm, UseFormReturn, SubmitHandler } from 'react-hook-form'
import { cn } from '@/lib/utils'
import { Label } from './label'

interface FieldProps extends React.HTMLAttributes<HTMLDivElement> {
  label?: string
  error?: string
}

const Field = React.forwardRef<HTMLDivElement, FieldProps>(({ className, label, error, children, ...props }, ref) => (
  <div ref={ref} className={cn('space-y-2', className)} {...props}>
    {label && <Label>{label}</Label>}
    {children}
    {error && <p className="text-sm text-red-500">{error}</p>}
  </div>
))
Field.displayName = 'Field'

interface FormProps<T extends Record<string, any>> {
  form: UseFormReturn<T>
  onSubmit: SubmitHandler<T>
  children: React.ReactNode
  className?: string
}

function Form<T extends Record<string, any>>({ form, onSubmit, children, className }: FormProps<T>) {
  return (
    <form onSubmit={form.handleSubmit(onSubmit)} className={className}>
      {children}
    </form>
  )
}

export { Form, Field, useForm }