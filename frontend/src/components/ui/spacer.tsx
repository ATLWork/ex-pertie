'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

interface SpacerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  direction?: 'horizontal' | 'vertical'
}

const sizeMap = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
}

const Spacer: React.FC<SpacerProps> = ({
  className,
  size = 'md',
  direction = 'horizontal',
  style,
  ...props
}) => {
  const isHorizontal = direction === 'horizontal'
  return (
    <div
      className={cn(isHorizontal ? 'inline-block' : 'block', className)}
      style={{
        [isHorizontal ? 'width' : 'height']: sizeMap[size],
        ...style,
      }}
      {...props}
    />
  )
}

export { Spacer }