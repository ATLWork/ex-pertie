'use client'

import { useState } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Select,
  Tag,
  Modal,
  Form,
  message,
  Progress,
  Checkbox,
} from 'antd'
import { DownloadOutlined, FileExcelOutlined, FileTextOutlined } from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import PageLayout from '@/components/Layout/PageLayout'
import { useExports, useExportHotels, useExportRooms, ExportRecord } from '@/hooks/useExport'
import { useHotels } from '@/hooks/useHotels'
import dayjs from 'dayjs'

export default function ExportPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [exportType, setExportType] = useState<'hotels' | 'rooms'>('hotels')
  const [selectedHotelIds, setSelectedHotelIds] = useState<number[]>([])
  const [form] = Form.useForm()
  const { exports: exportList, isLoading, refetch } = useExports()
  const { hotels = [] } = useHotels()
  const exportHotelsMutation = useExportHotels()
  const exportRoomsMutation = useExportRooms()

  const handleExport = async () => {
    try {
      const values = await form.validateFields()
      const format = values.format || 'xlsx'

      if (exportType === 'hotels') {
        await exportHotelsMutation.mutateAsync({
          hotelIds: selectedHotelIds,
          format,
        })
      } else {
        await exportRoomsMutation.mutateAsync({
          hotelIds: selectedHotelIds,
          format,
        })
      }
      message.success('Export job created successfully')
      setIsModalOpen(false)
      form.resetFields()
      setSelectedHotelIds([])
      refetch()
    } catch {
      message.error('Export failed')
    }
  }

  const handleDownload = async (record: ExportRecord) => {
    try {
      const response = await fetch(`/api/v1/exports/${record.id}/download`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      })
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = record.filename || `export-${record.id}.xlsx`
      a.click()
      window.URL.revokeObjectURL(url)
    } catch {
      message.error('Download failed')
    }
  }

  const columns: ColumnsType<ExportRecord> = [
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={type === 'hotels' ? 'blue' : 'green'}>
          {type.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Format',
      dataIndex: 'format',
      key: 'format',
      render: (format: string) =>
        format === 'xlsx' ? (
          <FileExcelOutlined style={{ color: '#52c41a' }} />
        ) : (
          <FileTextOutlined style={{ color: '#1890ff' }} />
        ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colorMap: Record<string, string> = {
          pending: 'default',
          processing: 'processing',
          completed: 'success',
          failed: 'error',
        }
        return <Tag color={colorMap[status]}>{status.toUpperCase()}</Tag>
      },
    },
    {
      title: 'Filename',
      dataIndex: 'filename',
      key: 'filename',
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) =>
        record.status === 'completed' && (
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            onClick={() => handleDownload(record)}
          >
            Download
          </Button>
        ),
    },
  ]

  return (
    <PageLayout>
      <Card
        title="Export Center"
        extra={
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            onClick={() => setIsModalOpen(true)}
          >
            New Export
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={exportList}
          rowKey="id"
          loading={isLoading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title="Create Export"
        open={isModalOpen}
        onCancel={() => {
          setIsModalOpen(false)
          form.resetFields()
          setSelectedHotelIds([])
        }}
        onOk={handleExport}
        confirmLoading={exportHotelsMutation.isPending || exportRoomsMutation.isPending}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="type"
            label="Export Type"
            rules={[{ required: true, message: 'Please select export type' }]}
          >
            <Select
              options={[
                { label: 'Hotels', value: 'hotels' },
                { label: 'Rooms', value: 'rooms' },
              ]}
              onChange={(value) => setExportType(value)}
            />
          </Form.Item>
          <Form.Item
            name="format"
            label="Format"
            rules={[{ required: true, message: 'Please select format' }]}
          >
            <Select
              options={[
                { label: 'Excel (.xlsx)', value: 'xlsx' },
                { label: 'CSV (.csv)', value: 'csv' },
              ]}
            />
          </Form.Item>
          <Form.Item label="Select Hotels">
            <Checkbox.Group
              options={hotels.map((h) => ({ label: h.name, value: h.id }))}
              value={selectedHotelIds}
              onChange={(values) => setSelectedHotelIds(values as number[])}
              style={{ width: '100%' }}
            />
          </Form.Item>
        </Form>
      </Modal>
    </PageLayout>
  )
}
