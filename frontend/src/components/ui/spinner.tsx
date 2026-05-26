'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

interface SpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg'
}

const sizeMap = {
  sm: 'h-4 w-4',
  md: 'h-8 w-8',
  lg: 'h-12 w-12',
}

const Spinner: React.FC<SpinnerProps> = ({ className, size = 'md', ...props }) => {
  return (
    <div
      className={cn(
        'inline-block animate-spin rounded-full border-2 border-woye border-t-transparent',
        sizeMap[size],
        className
      )}
      {...props}
    />
  )
}

export { Spinner }