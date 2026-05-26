'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string
  description?: string
  extra?: React.ReactNode
}

const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, title, description, extra, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'rounded-xl border border-gray-200 bg-white shadow-md',
        className
      )}
      {...props}
    >
      {(title || extra) && (
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div>
            <h3 className="font-semibold text-woye text-lg">{title}</h3>
            {description && <p className="text-sm text-gray-500 mt-0.5">{description}</p>}
          </div>
          {extra && <div>{extra}</div>}
        </div>
      )}
      <div className="px-6 py-5">{children}</div>
    </div>
  )
)
Card.displayName = 'Card'

export { Card }