import type { Metadata } from 'next'
import { AntdRegistry } from '@ant-design/nextjs-registry'
import { ConfigProvider } from 'antd'
import QueryProvider from '@/components/QueryProvider'
import './globals.css'

export const metadata: Metadata = {
  title: 'Ex-pertie - Expedia Hotel Data Management',
  description: 'Hotel data management tool for Expedia channel operations',
}

const theme = {
  token: {
    colorPrimary: '#1677ff',
    borderRadius: 6,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <AntdRegistry>
          <ConfigProvider theme={theme}>
            <QueryProvider>
              {children}
            </QueryProvider>
          </ConfigProvider>
        </AntdRegistry>
      </body>
    </html>
  )
}
