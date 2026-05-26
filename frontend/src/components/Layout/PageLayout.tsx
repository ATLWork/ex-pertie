'use client'

import { useRouter, usePathname } from 'next/navigation'
import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useAuthStore } from '@/stores/authStore'
import { isAnonymousEnabled } from '@/services/asso/config'

const menuItems = [
  { key: '/import', label: '数据导入' },
  { key: '/hotels', label: '酒店管理' },
  { key: '/translate', label: '翻译工具' },
  { key: '/review', label: '翻译审核' },
  { key: '/terminology', label: '术语库' },
  { key: '/rules', label: '翻译规则' },
  { key: '/export', label: '数据导出' },
]

export default function PageLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const { user, logout } = useAuthStore()

  const [anonymousMode, setAnonymousMode] = useState(false)

  useEffect(() => {
    setAnonymousMode(isAnonymousEnabled())
  }, [])

  const handleMenuClick = (key: string) => {
    router.push(key)
  }

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  const handleLogin = () => {
    router.push('/login')
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-100 flex flex-col">
        <div className="h-16 flex items-center justify-center border-b border-gray-100">
          <span className="text-xl font-bold text-woye tracking-tight">渠道通</span>
        </div>
        <nav className="flex-1 py-4">
          {menuItems.map((item) => {
            const isActive = pathname === item.key
            return (
              <button
                key={item.key}
                onClick={() => handleMenuClick(item.key)}
                className={`w-full px-6 py-3.5 text-left text-sm flex items-center gap-3 transition-all duration-200 ${
                  isActive
                    ? 'bg-baiyan/50 text-woye font-semibold border-l-[3px] border-woye pl-5'
                    : 'text-gray-600 hover:bg-baiyan/30 hover:text-woye border-l-[3px] border-transparent'
                }`}
              >
                <span>{item.label}</span>
              </button>
            )
          })}
        </nav>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-h-screen">
        {/* Header */}
        <header className="h-16 bg-white border-b border-gray-100 px-6 flex items-center justify-end">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center gap-3 px-3">
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="bg-baiyan text-woye text-sm font-medium">
                    {anonymousMode ? 'G' : (user?.username?.[0]?.toUpperCase() || 'U')}
                  </AvatarFallback>
                </Avatar>
                <span className="text-sm font-medium text-gray-700">
                  {anonymousMode ? '游客' : (user?.username || '用户')}
                </span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 py-2">
              {anonymousMode ? (
                <DropdownMenuItem onClick={handleLogin} className="px-4 py-2 cursor-pointer">
                  登录
                </DropdownMenuItem>
              ) : (
                <>
                  <DropdownMenuItem className="px-4 py-2 cursor-pointer hover:bg-baiyan/30">
                    个人资料
                  </DropdownMenuItem>
                  <DropdownMenuSeparator className="my-2 border-gray-100" />
                  <DropdownMenuItem onClick={handleLogout} className="px-4 py-2 cursor-pointer hover:bg-baiyan/30 text-red-500">
                    退出登录
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        </header>

        {/* Content */}
        <main className="p-6 flex-1">
          {children}
        </main>
      </div>
    </div>
  )
}