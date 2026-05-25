'use client'

import { useState, useEffect, useRef } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { DataTable } from '@/components/ui/data-table'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useToast, Toaster } from '@/components/ui/use-toast'
import PageLayout from '@/components/Layout/PageLayout'
import { useImports, useImportHotels, useImportRooms, useImportErrors } from '@/hooks/useImport'
import apiClient from '@/api/client'
import dayjs from 'dayjs'

export default function ImportPage() {
  const [activeTab, setActiveTab] = useState('hotels')
  const [selectedImport, setSelectedImport] = useState<number | null>(null)
  const [showErrors, setShowErrors] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()
  const { imports, isLoading: queryLoading } = useImports()
  const importHotelsMutation = useImportHotels()
  const importRoomsMutation = useImportRooms()
  const { data: errors } = useImportErrors(selectedImport || 0)

  const [isClientReady, setIsClientReady] = useState(false)
  useEffect(() => {
    setIsClientReady(true)
  }, [])

  const isLoading = !isClientReady || queryLoading

  const downloadTemplate = async (type: 'hotels' | 'rooms') => {
    try {
      const response = await apiClient.get(`/imports/template/${type}`, {
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `import_${type}_template.xlsx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      toast({ title: '模板下载成功', variant: 'success' })
    } catch {
      toast({ title: '模板下载失败', variant: 'error' })
    }
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploadProgress(50)
    try {
      if (activeTab === 'hotels') {
        await importHotelsMutation.mutateAsync(file)
      } else {
        await importRoomsMutation.mutateAsync(file)
      }
      toast({ title: '文件导入成功', variant: 'success' })
    } catch {
      toast({ title: '导入失败', variant: 'error' })
    }
    setUploadProgress(0)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const columns = [
    {
      key: 'type',
      title: '类型',
      render: (val: string) => (
        <Badge variant={val === 'hotels' ? 'info' : 'success'}>{val === 'hotels' ? '酒店' : '房间'}</Badge>
      ),
    },
    { key: 'filename', title: '文件名' },
    {
      key: 'status',
      title: '状态',
      render: (val: string) => {
        const variant = val === 'completed' ? 'success' : val === 'failed' ? 'error' : val === 'processing' ? 'warning' : 'default'
        const labels: Record<string, string> = { completed: '已完成', failed: '失败', processing: '处理中', pending: '等待中' }
        return <Badge variant={variant}>{labels[val] || val}</Badge>
      },
    },
    {
      key: 'progress',
      title: '进度',
      render: (_: any, record: { total_rows: number; processed_rows: number }) => (
        <Progress value={Math.round((record.processed_rows / record.total_rows) * 100) || 0} />
      ),
    },
    {
      key: 'error_count',
      title: '错误数',
      render: (val: number) => <span className={val > 0 ? 'text-red-500' : ''}>{val}</span>,
    },
    {
      key: 'created_at',
      title: '创建时间',
      render: (val: string) => dayjs(val).format('YYYY-MM-DD HH:mm'),
    },
    {
      key: 'actions',
      title: '操作',
      render: (_: any, record: { id: number; error_count: number }) =>
        record.error_count > 0 && (
          <Button variant="ghost" size="sm" onClick={() => { setSelectedImport(record.id); setShowErrors(true) }}>
            查看错误
          </Button>
        ),
    },
  ]

  return (
    <PageLayout>
      <Toaster />
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="hotels">导入酒店</TabsTrigger>
          <TabsTrigger value="rooms">导入房间</TabsTrigger>
        </TabsList>
        <TabsContent value="hotels">
          <Card title="上传酒店数据">
            <div className="mb-4 flex items-center gap-3">
              <Button variant="outline" size="sm" onClick={() => downloadTemplate('hotels')}>
                下载酒店导入模板
              </Button>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={handleFileChange}
              className="hidden"
            />
            <div
              onClick={() => !importHotelsMutation.isPending && fileInputRef.current?.click()}
              className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-200 bg-gray-50 p-8 cursor-pointer transition-colors hover:border-woye hover:bg-baiyan/30 ${importHotelsMutation.isPending ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <svg className="h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-sm text-gray-600">点击或拖拽文件上传</p>
              <p className="text-xs text-gray-400 mt-1">支持 Excel (.xlsx, .xls) 和 CSV 文件</p>
            </div>
            {importHotelsMutation.isPending && (
              <div className="mt-4">
                <Progress value={uploadProgress} />
                <p className="text-sm text-gray-500 mt-2">正在导入酒店...</p>
              </div>
            )}
          </Card>
        </TabsContent>
        <TabsContent value="rooms">
          <Card title="上传房间数据">
            <div className="mb-4 flex items-center gap-3">
              <Button variant="outline" size="sm" onClick={() => downloadTemplate('rooms')}>
                下载房间导入模板
              </Button>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={handleFileChange}
              className="hidden"
            />
            <div
              onClick={() => !importRoomsMutation.isPending && fileInputRef.current?.click()}
              className={`flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-200 bg-gray-50 p-8 cursor-pointer transition-colors hover:border-woye hover:bg-baiyan/30 ${importRoomsMutation.isPending ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <svg className="h-12 w-12 text-gray-400 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 13h6m-3-3v6m5 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-sm text-gray-600">点击或拖拽文件上传</p>
              <p className="text-xs text-gray-400 mt-1">支持 Excel (.xlsx, .xls) 和 CSV 文件</p>
            </div>
            {importRoomsMutation.isPending && (
              <div className="mt-4">
                <Progress value={uploadProgress} />
                <p className="text-sm text-gray-500 mt-2">正在导入房间...</p>
              </div>
            )}
          </Card>
        </TabsContent>
      </Tabs>

      <Card title="导入历史" className="mt-6">
        <DataTable
          columns={columns}
          data={imports}
          loading={isLoading}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Dialog open={showErrors} onOpenChange={setShowErrors}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>导入错误</DialogTitle>
          </DialogHeader>
          <pre className="max-h-96 overflow-auto bg-gray-50 p-4 rounded text-sm">
            {JSON.stringify(errors, null, 2)}
          </pre>
        </DialogContent>
      </Dialog>
    </PageLayout>
  )
}