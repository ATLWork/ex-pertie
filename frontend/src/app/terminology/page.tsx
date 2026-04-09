'use client'

import { useState } from 'react'
import {
  Card,
  Table,
  Button,
  Input,
  Select,
  Space,
  Modal,
  Form,
  message,
  Tag,
  Popconfirm,
  Upload,
} from 'antd'
import { PlusOutlined, DeleteOutlined, EditOutlined, UploadOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import PageLayout from '@/components/Layout/PageLayout'
import {
  useGlossary,
  useCreateGlossary,
  useUpdateGlossary,
  useDeleteGlossary,
  Glossary,
} from '@/hooks/useTranslation'

export default function TerminologyPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<Glossary | null>(null)
  const [filterCategory, setFilterCategory] = useState<string | undefined>()
  const [searchTerm, setSearchTerm] = useState('')
  const [form] = Form.useForm()
  const { data: glossary = [], isLoading, refetch } = useGlossary()
  const createMutation = useCreateGlossary()
  const updateMutation = useUpdateGlossary()
  const deleteMutation = useDeleteGlossary()

  const filteredData = glossary.filter((item) => {
    const matchesSearch =
      !searchTerm ||
      item.term.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.translation.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = !filterCategory || item.category === filterCategory
    return matchesSearch && matchesCategory
  })

  const categories = [...new Set(glossary.map((item) => item.category).filter(Boolean))]

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editingItem) {
        await updateMutation.mutateAsync({ id: editingItem.id, data: values })
        message.success('Term updated successfully')
      } else {
        await createMutation.mutateAsync(values)
        message.success('Term added successfully')
      }
      setIsModalOpen(false)
      form.resetFields()
      setEditingItem(null)
      refetch()
    } catch {
      message.error('Operation failed')
    }
  }

  const handleEdit = (item: Glossary) => {
    setEditingItem(item)
    form.setFieldsValue(item)
    setIsModalOpen(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteMutation.mutateAsync(id)
      message.success('Term deleted successfully')
      refetch()
    } catch {
      message.error('Delete failed')
    }
  }

  const columns: ColumnsType<Glossary> = [
    {
      title: 'Term',
      dataIndex: 'term',
      key: 'term',
    },
    {
      title: 'Translation',
      dataIndex: 'translation',
      key: 'translation',
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (category: string) => category && <Tag>{category}</Tag>,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          <Popconfirm
            title="Are you sure you want to delete this term?"
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
        title="Terminology Management"
        extra={
          <Space>
            <Button icon={<UploadOutlined />}>Import</Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => {
                setEditingItem(null)
                form.resetFields()
                setIsModalOpen(true)
              }}
            >
              Add Term
            </Button>
          </Space>
        }
      >
        <Space style={{ marginBottom: 16 }} wrap>
          <Input
            placeholder="Search terms..."
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ width: 200 }}
            allowClear
          />
          <Select
            placeholder="Filter by category"
            style={{ width: 150 }}
            allowClear
            value={filterCategory}
            onChange={setFilterCategory}
            options={categories.map((c) => ({ label: c, value: c }))}
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
        title={editingItem ? 'Edit Term' : 'Add Term'}
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false)
          form.resetFields()
          setEditingItem(null)
        }}
        onOk={handleSubmit}
        confirmLoading={createMutation.isPending || updateMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="term"
            label="Term"
            rules={[{ required: true, message: 'Please enter the term' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="translation"
            label="Translation"
            rules={[{ required: true, message: 'Please enter the translation' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="category" label="Category">
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </PageLayout>
  )
}
