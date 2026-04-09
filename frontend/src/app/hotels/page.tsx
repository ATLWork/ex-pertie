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
} from 'antd'
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import PageLayout from '@/components/Layout/PageLayout'
import { useHotels, useCreateHotel, useUpdateHotel, useDeleteHotel, Hotel } from '@/hooks/useHotels'
import { useHotelStore } from '@/stores/hotelStore'

const { Search } = Input

export default function HotelsPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingHotel, setEditingHotel] = useState<Hotel | null>(null)
  const [form] = Form.useForm()
  const { hotels, total, isLoading, refetch } = useHotels()
  const { page, pageSize, setPage, setPageSize, filters, setFilters } = useHotelStore()
  const createHotelMutation = useCreateHotel()
  const updateHotelMutation = useUpdateHotel()
  const deleteHotelMutation = useDeleteHotel()

  const handleSearch = (value: string) => {
    setFilters({ ...filters, search: value })
  }

  const handleStatusFilter = (value: string) => {
    setFilters({ ...filters, status: value })
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      if (editingHotel) {
        await updateHotelMutation.mutateAsync({ id: editingHotel.id, data: values })
        message.success('Hotel updated successfully')
      } else {
        await createHotelMutation.mutateAsync(values)
        message.success('Hotel created successfully')
      }
      setIsModalOpen(false)
      form.resetFields()
      setEditingHotel(null)
      refetch()
    } catch {
      message.error('Operation failed')
    }
  }

  const handleEdit = (hotel: Hotel) => {
    setEditingHotel(hotel)
    form.setFieldsValue(hotel)
    setIsModalOpen(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteHotelMutation.mutateAsync(id)
      message.success('Hotel deleted successfully')
      refetch()
    } catch {
      message.error('Delete failed')
    }
  }

  const columns: ColumnsType<Hotel> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'English Name',
      dataIndex: 'name_en',
      key: 'name_en',
    },
    {
      title: 'City',
      dataIndex: 'city',
      key: 'city',
    },
    {
      title: 'Country',
      dataIndex: 'country',
      key: 'country',
    },
    {
      title: 'Star Rating',
      dataIndex: 'star_rating',
      key: 'star_rating',
      render: (rating: number) => rating ? `${rating} Star${rating > 1 ? 's' : ''}` : '-',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          draft: 'default',
          active: 'success',
          inactive: 'error',
        }
        return <Tag color={colorMap[status]}>{status.toUpperCase()}</Tag>
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="Are you sure you want to delete this hotel?"
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
        title="Hotels"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditingHotel(null)
              form.resetFields()
              setIsModalOpen(true)
            }}
          >
            Add Hotel
          </Button>
        }
      >
        <Space style={{ marginBottom: 16 }} wrap>
          <Search
            placeholder="Search hotels..."
            onSearch={handleSearch}
            style={{ width: 250 }}
            allowClear
          />
          <Select
            placeholder="Filter by status"
            style={{ width: 150 }}
            allowClear
            onChange={handleStatusFilter}
            options={[
              { label: 'Draft', value: 'draft' },
              { label: 'Active', value: 'active' },
              { label: 'Inactive', value: 'inactive' },
            ]}
          />
        </Space>
        <Table
          columns={columns}
          dataSource={hotels}
          rowKey="id"
          loading={isLoading}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showTotal: (t) => `Total ${t} hotels`,
            onChange: (p, ps) => {
              setPage(p)
              setPageSize(ps)
            },
          }}
        />
      </Card>

      <Modal
        title={editingHotel ? 'Edit Hotel' : 'Add Hotel'}
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false)
          form.resetFields()
          setEditingHotel(null)
        }}
        onOk={handleSubmit}
        confirmLoading={createHotelMutation.isPending || updateHotelMutation.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="Hotel Name"
            rules={[{ required: true, message: 'Please enter hotel name' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="name_en" label="English Name">
            <Input />
          </Form.Item>
          <Form.Item
            name="address"
            label="Address"
            rules={[{ required: true, message: 'Please enter address' }]}
          >
            <Input />
          </Form.Item>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item
              name="city"
              label="City"
              rules={[{ required: true, message: 'Please enter city' }]}
              style={{ flex: 1 }}
            >
              <Input />
            </Form.Item>
            <Form.Item
              name="country"
              label="Country"
              rules={[{ required: true, message: 'Please enter country' }]}
              style={{ flex: 1 }}
            >
              <Input />
            </Form.Item>
          </Space>
          <Space style={{ width: '100%' }} size="large">
            <Form.Item name="star_rating" label="Star Rating" style={{ flex: 1 }}>
              <Select
                allowClear
                options={[
                  { label: '1 Star', value: 1 },
                  { label: '2 Stars', value: 2 },
                  { label: '3 Stars', value: 3 },
                  { label: '4 Stars', value: 4 },
                  { label: '5 Stars', value: 5 },
                ]}
              />
            </Form.Item>
            <Form.Item name="status" label="Status" style={{ flex: 1 }}>
              <Select
                options={[
                  { label: 'Draft', value: 'draft' },
                  { label: 'Active', value: 'active' },
                  { label: 'Inactive', value: 'inactive' },
                ]}
              />
            </Form.Item>
          </Space>
        </Form>
      </Modal>
    </PageLayout>
  )
}
