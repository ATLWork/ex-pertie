'use client'

import { Button, Card, Spinner } from '@/components/ui'
import { useRouter, useSearchParams } from 'next/navigation'
import { Suspense, useEffect, useState } from 'react'
import { login, userStore, getUserByToken } from '@/services/asso'
import { isAnonymousEnabled, enableAnonymousMode } from '@/services/asso/config'
import apiClient from '@/api/client'

function LoginContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (isAnonymousEnabled()) {
      setIsLoading(false)
      return
    }

    const existingToken = userStore.getToken()
    if (existingToken) {
      validateAndLogin(existingToken)
      return
    }

    const assoTokenFromUrl = searchParams.get('assoToken')
    if (assoTokenFromUrl) {
      userStore.setToken(assoTokenFromUrl)
      validateAndLogin(assoTokenFromUrl)
      return
    }

    const feishuCode = searchParams.get('code')
    if (feishuCode) {
      handleFeishuCallback(feishuCode)
      return
    }

    setIsLoading(false)
  }, [searchParams])

  const validateAndLogin = async (assoToken: string) => {
    try {
      const userInfo = await getUserByToken(assoToken)
      userStore.setUserInfo(userInfo)
      userStore.setIsAuth(true)

      const response = await apiClient.post('/auth/asso/callback', { assoToken })
      const { access_token } = response.data.data
      localStorage.setItem('token', access_token)

      router.push('/import')
    } catch (error) {
      console.error('Login validation failed:', error)
      userStore.clear()
      setIsLoading(false)
    }
  }

  const handleFeishuCallback = async (code: string) => {
    try {
      const { loginByFeiShu } = await import('@/services/asso')
      const result = await loginByFeiShu(code)
      if (result.assoToken) {
        userStore.setToken(result.assoToken)
        validateAndLogin(result.assoToken)
      }
    } catch (error) {
      console.error('Feishu login failed:', error)
      userStore.clear()
      setIsLoading(false)
    }
  }

  const handleLogin = () => {
    login().goToLogin()
  }

  const handleAnonymousAccess = () => {
    enableAnonymousMode()
    router.push('/import')
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-woye via-woye/90 to-gray-700">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-woye via-woye/90 to-gray-700">
      <Card className="w-full max-w-md shadow-2xl">
        <div className="p-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-woye mb-2 tracking-tight">
              渠道通
            </h1>
            <p className="text-gray-500 text-sm">
              Expedia 酒店数据管理平台
            </p>
          </div>

          <div className="flex flex-col gap-4">
            <Button size="lg" block onClick={handleLogin}>
              使用 SSO 登录
            </Button>

            <div className="relative flex items-center py-2">
              <div className="flex-grow border-t border-gray-200" />
              <span className="flex-shrink mx-4 text-sm text-gray-400">或</span>
              <div className="flex-grow border-t border-gray-200" />
            </div>

            <Button size="lg" block variant="secondary" onClick={handleAnonymousAccess}>
              游客访问
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-woye via-woye/90 to-gray-700">
        <Spinner size="lg" />
      </div>
    }>
      <LoginContent />
    </Suspense>
  )
}