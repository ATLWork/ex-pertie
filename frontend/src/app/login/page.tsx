'use client'

import { Form, Input, Button, Card, message, Tabs } from 'antd'
import { UserOutlined, LockOutlined, MailOutlined } from '@ant-design/icons'
import { useRouter } from 'next/navigation'
import { useLogin, useRegister } from '@/hooks/useAuth'
import { useEffect } from 'react'

export default function LoginPage() {
  const router = useRouter()
  const loginMutation = useLogin()
  const registerMutation = useRegister()
  const [loginForm] = Form.useForm()
  const [registerForm] = Form.useForm()

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (token) {
      router.push('/import')
    }
  }, [router])

  const handleLogin = async (values: { username: string; password: string }) => {
    try {
      await loginMutation.mutateAsync(values)
      message.success('Login successful')
      router.push('/import')
    } catch {
      message.error('Login failed. Please check your credentials.')
    }
  }

  const handleRegister = async (values: { username: string; email: string; password: string }) => {
    try {
      await registerMutation.mutateAsync(values)
      message.success('Registration successful! Please login.')
      loginForm.setFieldsValue({ username: values.username })
      registerForm.resetFields()
    } catch {
      message.error('Registration failed. Please try again.')
    }
  }

  const tabItems = [
    {
      key: 'login',
      label: 'Login',
      children: (
        <Form
          form={loginForm}
          layout="vertical"
          onFinish={handleLogin}
          style={{ maxWidth: 320 }}
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: 'Please enter your username' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="Username"
              size="large"
            />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[{ required: true, message: 'Please enter your password' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Password"
              size="large"
            />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              block
              loading={loginMutation.isPending}
            >
              Login
            </Button>
          </Form.Item>
        </Form>
      ),
    },
    {
      key: 'register',
      label: 'Register',
      children: (
        <Form
          form={registerForm}
          layout="vertical"
          onFinish={handleRegister}
          style={{ maxWidth: 320 }}
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: 'Please enter a username' },
              { min: 3, message: 'Username must be at least 3 characters' },
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="Username"
              size="large"
            />
          </Form.Item>
          <Form.Item
            name="email"
            rules={[
              { required: true, message: 'Please enter your email' },
              { type: 'email', message: 'Please enter a valid email' },
            ]}
          >
            <Input
              prefix={<MailOutlined />}
              placeholder="Email"
              size="large"
            />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[
              { required: true, message: 'Please enter a password' },
              { min: 6, message: 'Password must be at least 6 characters' },
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Password"
              size="large"
            />
          </Form.Item>
          <Form.Item
            name="confirmPassword"
            dependencies={['password']}
            rules={[
              { required: true, message: 'Please confirm your password' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('Passwords do not match'))
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Confirm Password"
              size="large"
            />
          </Form.Item>
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              block
              loading={registerMutation.isPending}
            >
              Register
            </Button>
          </Form.Item>
        </Form>
      ),
    },
  ]

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      }}
    >
      <Card
        style={{ width: 420, boxShadow: '0 8px 32px rgba(0,0,0,0.1)' }}
        styles={{ body: { padding: 32 } }}
      >
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8, color: '#1890ff' }}>
            Ex-pertie
          </h1>
          <p style={{ color: '#666' }}>Expedia Hotel Data Management Platform</p>
        </div>
        <Tabs items={tabItems} defaultActiveKey="login" centered />
      </Card>
    </div>
  )
}
