import type { Metadata } from 'next'
import QueryProvider from '@/components/QueryProvider'
import './globals.css'

export const metadata: Metadata = {
  title: '渠道通 - Expedia Hotel Data Management',
  description: 'Hotel data management tool for Expedia channel operations',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>
          {children}
        </QueryProvider>
      </body>
    </html>
  )
}