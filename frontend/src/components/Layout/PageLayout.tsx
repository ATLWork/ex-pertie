'use client'

import { Layout as AntLayout, Menu, Avatar, Dropdown, Button, theme } from 'antd'
import {
  DashboardOutlined,
  ImportOutlined,
  HomeOutlined,
  TranslationOutlined,
  BookOutlined,
  FileTextOutlined,
  ExportOutlined,
  LogoutOutlined,
  UserOutlined,
} from '@ant-design/icons'
import { useRouter, usePathname } from 'next/navigation'
import { useAuthStore } from '@/stores/authStore'

const { Header, Sider, Content } = AntLayout

const menuItems = [
  { key: '/import', icon: <ImportOutlined />, label: 'Data Import' },
  { key: '/hotels', icon: <HomeOutlined />, label: 'Hotels' },
  { key: '/translate', icon: <TranslationOutlined />, label: 'Translation' },
  { key: '/terminology', icon: <BookOutlined />, label: 'Terminology' },
  { key: '/rules', icon: <FileTextOutlined />, label: 'Rules' },
  { key: '/export', icon: <ExportOutlined />, label: 'Export' },
]

export default function PageLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const { user, logout } = useAuthStore()
  const { token } = theme.useToken()

  const handleMenuClick = ({ key }: { key: string }) => {
    router.push(key)
  }

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile',
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: handleLogout,
    },
  ]

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider
        theme="light"
        style={{
          borderRight: '1px solid #f0f0f0',
        }}
      >
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          <span style={{ fontSize: 18, fontWeight: 600, color: token.colorPrimary }}>
            Ex-pertie
          </span>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ borderRight: 0, marginTop: 8 }}
        />
      </Sider>
      <AntLayout>
        <Header
          style={{
            background: '#fff',
            padding: '0 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            borderBottom: '1px solid #f0f0f0',
          }}
        >
          <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
            <Button type="text" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Avatar size="small" icon={<UserOutlined />} />
              <span>{user?.username || 'User'}</span>
            </Button>
          </Dropdown>
        </Header>
        <Content style={{ padding: 24 }}>
          {children}
        </Content>
      </AntLayout>
    </AntLayout>
  )
}
