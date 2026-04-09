'use client'

import { useState } from 'react'
import {
  Card,
  Table,
  Button,
  Input,
  Space,
  Modal,
  Form,
  message,
  Switch,
  Popconfirm,
} from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import PageLayout from '@/components/Layout/PageLayout'
import {
  useTranslationRules,
  useCreateTranslationRule,
  useUpdateTranslationRule,
  useDeleteTranslationRule,
  TranslationRule,
} from '@/hooks/useTranslation'

export default function RulesPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingRule, setEditingRule] = useState<TranslationRule | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [form] = Form.useForm()
  const { data: rules = [], isLoading, refetch } = useTranslationRules()
  const createMutation = useCreateTranslationRule()
  const updateMutation = useUpdateTranslationRule()
  const deleteMutation = useDeleteTranslationRule()

  const filteredData = rules.filter(
    (rule) =>
      !searchTerm ||
      rule.pattern.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rule.description?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editingRule) {
        await updateMutation.mutateAsync({ id: editingRule.id, data: values })
        message.success('Rule updated successfully')
      } else {
        await createMutation.mutateAsync(values)
        message.success('Rule created successfully')
      }
      setIsModalOpen(false)
      form.resetFields()
      setEditingRule(null)
      refetch()
    } catch {
      message.error('Operation failed')
    }
  }

  const handleEdit = (rule: TranslationRule) => {
    setEditingRule(rule)
    form.setFieldsValue(rule)
    setIsModalOpen(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteMutation.mutateAsync(id)
      message.success('Rule deleted successfully')
      refetch()
    } catch {
      message.error('Delete failed')
    }
  }

  const handleToggleEnabled = async (rule: TranslationRule) => {
    try {
      await updateMutation.mutateAsync({
        id: rule.id,
        data: { enabled: !rule.enabled },
      })
      message.success('Rule updated successfully')
      refetch()
    } catch {
      message.error('Update failed')
    }
  }

  const columns: ColumnsType<TranslationRule> = [
    {
      title: 'Pattern',
      dataIndex: 'pattern',
      key: 'pattern',
      render: (pattern: string) => <code style={{ background: '#f5f5f5', padding: '2px 6px' }}>{pattern}</code>,
    },
    {
      title: 'Replacement',
      dataIndex: 'replacement',
      key: 'replacement',
      render: (replacement: string) => <code style={{ background: '#e6f7ff', padding: '2px 6px' }}>{replacement}</code>,
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      width: 80,
    },
    {
      title: 'Enabled',
      dataIndex: 'enabled',
      key: 'enabled',
      width: 100,
      render: (enabled: boolean, record) => (
        <Switch checked={enabled} onChange={() => handleToggleEnabled(record)} />
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Popconfirm
            title="Are you sure you want to delete this rule?"
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button type="link" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <PageLayout>
      <Card
        title="Translation Rules"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditingRule(null)
              form.resetFields()
              setIsModalOpen(true)
            }}
          >
            Add Rule
          </Button>
        }
      >
        <Space style={{ marginBottom: 16 }}>
          <Input
            placeholder="Search rules..."
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ width: 250 }}
            allowClear
          />
        </Space>
        <Table
          columns={columns}
          dataSource={filteredData}
          rowKey="id"
          loading={isLoading}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      <Modal
        title={editingRule ? 'Edit Rule' : 'Add Rule'}
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false)
          form.resetFields()
          setEditingRule(null)
        }}
        onOk={handleSubmit}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="pattern"
            label="Pattern (regex)"
            rules={[{ required: true, message: 'Please enter the pattern' }]}
          >
            <Input placeholder="e.g., Hotel" />
          </Form.Item>
          <Form.Item
            name="replacement"
            label="Replacement"
            rules={[{ required: true, message: 'Please enter the replacement text' }]}
          >
            <Input placeholder="e.g., 酒店" />
          </Form.Item>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={2} />
          </Form.Item>
          <Space style={{ width: '100%' }}>
            <Form.Item name="priority" label="Priority" style={{ flex: 1 }}>
              <Input type="number" min={1} max={100} defaultValue={10} />
            </Form.Item>
            <Form.Item name="enabled" label="Enabled" valuePropName="checked" initialValue={true}>
              <Switch />
            </Form.Item>
          </Space>
        </Form>
      </Modal>
    </PageLayout>
  )
}
