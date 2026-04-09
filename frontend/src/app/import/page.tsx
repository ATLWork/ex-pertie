'use client'

import { useState } from 'react'
import { Card, Upload, Button, Table, Tag, Progress, message, Tabs, Modal } from 'antd'
import { InboxOutlined, FileExcelOutlined, UploadOutlined } from '@ant-design/icons'
import type { UploadFile, UploadProps } from 'antd'
import PageLayout from '@/components/Layout/PageLayout'
import { useImports, useImportHotels, useImportRooms, useImportErrors } from '@/hooks/useImport'
import dayjs from 'dayjs'

const { Dragger } = Upload

export default function ImportPage() {
  const [activeTab, setActiveTab] = useState('hotels')
  const [selectedImport, setSelectedImport] = useState<number | null>(null)
  const [showErrors, setShowErrors] = useState(false)
  const { imports, isLoading } = useImports()
  const importHotelsMutation = useImportHotels()
  const importRoomsMutation = useImportRooms()
  const { data: errors } = useImportErrors(selectedImport || 0)

  const handleUpload: UploadProps['customRequest'] = async (options) => {
    const { file, onSuccess, onError } = options
    try {
      if (activeTab === 'hotels') {
        await importHotelsMutation.mutateAsync(file as File)
      } else {
        await importRoomsMutation.mutateAsync(file as File)
      }
      message.success('File imported successfully')
      onSuccess?.(file)
    } catch {
      message.error('Import failed')
      onError?.(new Error('Import failed'))
    }
  }

  const columns = [
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
      title: 'Filename',
      dataIndex: 'filename',
      key: 'filename',
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
      title: 'Progress',
      key: 'progress',
      render: (_: unknown, record: { total_rows: number; processed_rows: number }) => (
        <Progress
          percent={Math.round((record.processed_rows / record.total_rows) * 100) || 0}
          size="small"
        />
      ),
    },
    {
      title: 'Errors',
      dataIndex: 'error_count',
      key: 'error_count',
      render: (count: number) => (
        <span style={{ color: count > 0 ? '#ff4d4f' : 'inherit' }}>{count}</span>
      ),
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
      render: (_: unknown, record: { id: number; error_count: number }) => (
        record.error_count > 0 && (
          <Button
            type="link"
            onClick={() => {
              setSelectedImport(record.id)
              setShowErrors(true)
            }}
          >
            View Errors
          </Button>
        )
      ),
    },
  ]

  const tabItems = [
    {
      key: 'hotels',
      label: 'Import Hotels',
      children: (
        <Card title="Upload Hotel Data">
          <Dragger
            accept=".xlsx,.xls,.csv"
            customRequest={handleUpload}
            showUploadList={false}
            disabled={importHotelsMutation.isPending}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">Click or drag file to upload</p>
            <p className="ant-upload-hint">Support for Excel (.xlsx, .xls) and CSV files</p>
          </Dragger>
          {importHotelsMutation.isPending && (
            <div style={{ marginTop: 16 }}>
              <Progress percent={50} status="active" />
              <p style={{ color: '#666', marginTop: 8 }}>Importing hotels...</p>
            </div>
          )}
        </Card>
      ),
    },
    {
      key: 'rooms',
      label: 'Import Rooms',
      children: (
        <Card title="Upload Room Data">
          <Dragger
            accept=".xlsx,.xls,.csv"
            customRequest={handleUpload}
            showUploadList={false}
            disabled={importRoomsMutation.isPending}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">Click or drag file to upload</p>
            <p className="ant-upload-hint">Support for Excel (.xlsx, .xls) and CSV files</p>
          </Dragger>
          {importRoomsMutation.isPending && (
            <div style={{ marginTop: 16 }}>
              <Progress percent={50} status="active" />
              <p style={{ color: '#666', marginTop: 8 }}>Importing rooms...</p>
            </div>
          )}
        </Card>
      ),
    },
  ]

  return (
    <PageLayout>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={tabItems}
        style={{ marginBottom: 24 }}
      />
      <Card title="Import History">
        <Table
          columns={columns}
          dataSource={imports}
          rowKey="id"
          loading={isLoading}
          pagination={{ pageSize: 10 }}
        />
      </Card>
      <Modal
        title="Import Errors"
        open={showErrors}
        onCancel={() => setShowErrors(false)}
        footer={null}
        width={800}
      >
        <pre style={{ maxHeight: 400, overflow: 'auto' }}>
          {JSON.stringify(errors, null, 2)}
        </pre>
      </Modal>
    </PageLayout>
  )
}
