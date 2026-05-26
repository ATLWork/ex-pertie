'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { DataTable } from '@/components/ui/data-table'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Checkbox } from '@/components/ui/checkbox'
import { Spinner } from '@/components/ui/spinner'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { useToast, Toaster } from '@/components/ui/use-toast'
import PageLayout from '@/components/Layout/PageLayout'
import { useExports, useExportHotels, useExportRooms, ExportRecord } from '@/hooks/useExport'
import { useHotels } from '@/hooks/useHotels'
import dayjs from 'dayjs'

export default function ExportPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [exportType, setExportType] = useState<'hotels' | 'rooms'>('hotels')
  const [selectedHotelIds, setSelectedHotelIds] = useState<string[]>([])
  const [format, setFormat] = useState('xlsx')
  const { toast } = useToast()
  const { exports: exportList, isLoading: queryLoading, refetch } = useExports()
  const { hotels = [] } = useHotels()
  const exportHotelsMutation = useExportHotels()
  const exportRoomsMutation = useExportRooms()

  const [isClientLoading, setIsClientLoading] = useState(true)
  useEffect(() => {
    setIsClientLoading(false)
  }, [])

  const isLoading = queryLoading || isClientLoading

  const handleExport = async () => {
    try {
      if (exportType === 'hotels') {
        await exportHotelsMutation.mutateAsync({
          hotelIds: selectedHotelIds,
          format: format as 'xlsx' | 'csv',
        })
      } else {
        await exportRoomsMutation.mutateAsync({
          hotelIds: selectedHotelIds,
          format: format as 'xlsx' | 'csv',
        })
      }
      toast({ title: '导出任务创建成功', variant: 'success' })
      setIsModalOpen(false)
      setSelectedHotelIds([])
      refetch()
    } catch {
      toast({ title: '导出失败', variant: 'error' })
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
      toast({ title: '下载失败', variant: 'error' })
    }
  }

  const columns = [
    {
      key: 'type',
      title: '类型',
      render: (val: string) => (
        <Badge variant={val === 'hotels' ? 'info' : 'success'}>{val === 'hotels' ? '酒店' : '房间'}</Badge>
      ),
    },
    {
      key: 'format',
      title: '格式',
      render: (val: string) => (val === 'xlsx' ? 'Excel' : 'CSV'),
    },
    {
      key: 'status',
      title: '状态',
      render: (val: string) => {
        const variant = val === 'completed' ? 'success' : val === 'failed' ? 'error' : val === 'processing' ? 'warning' : 'default'
        const labels: Record<string, string> = { completed: '已完成', failed: '失败', processing: '处理中', pending: '等待中' }
        return <Badge variant={variant}>{labels[val] || val}</Badge>
      },
    },
    { key: 'filename', title: '文件名' },
    {
      key: 'created_at',
      title: '创建时间',
      render: (val: string) => dayjs(val).format('YYYY-MM-DD HH:mm'),
    },
    {
      key: 'actions',
      title: '操作',
      render: (_: any, record: ExportRecord) =>
        record.status === 'completed' && (
          <Button onClick={() => handleDownload(record)}>下载</Button>
        ),
    },
  ]

  return (
    <PageLayout>
      <Toaster />
      <Card
        title="导出中心"
        extra={
          <Button onClick={() => setIsModalOpen(true)}>新建导出</Button>
        }
      >
        {isLoading ? (
          <div className="flex justify-center py-12"><Spinner size="lg" /></div>
        ) : (
          <DataTable
            columns={columns}
            data={exportList}
            rowKey="id"
            pagination={{ pageSize: 10 }}
          />
        )}
      </Card>

      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>创建导出任务</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium text-woye mb-2 block">导出类型</label>
              <select
                value={exportType}
                onChange={(e) => setExportType(e.target.value as 'hotels' | 'rooms')}
                className="h-10 w-full rounded-md border border-gray-200 px-3 text-sm"
              >
                <option value="hotels">酒店</option>
                <option value="rooms">房间</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-woye mb-2 block">文件格式</label>
              <select
                value={format}
                onChange={(e) => setFormat(e.target.value)}
                className="h-10 w-full rounded-md border border-gray-200 px-3 text-sm"
              >
                <option value="xlsx">Excel (.xlsx)</option>
                <option value="csv">CSV (.csv)</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-woye mb-2 block">选择酒店</label>
              <div className="max-h-48 overflow-y-auto space-y-2 border rounded-md p-3">
                {hotels.map((h) => (
                  <label key={h.id} className="flex items-center gap-2 cursor-pointer">
                    <Checkbox
                      checked={selectedHotelIds.includes(h.id)}
                      onCheckedChange={(checked) => {
                        if (checked) {
                          setSelectedHotelIds([...selectedHotelIds, h.id])
                        } else {
                          setSelectedHotelIds(selectedHotelIds.filter((id) => id !== h.id))
                        }
                      }}
                    />
                    <span className="text-sm">{h.name_cn}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsModalOpen(false)}>取消</Button>
            <Button onClick={handleExport} loading={exportHotelsMutation.isPending || exportRoomsMutation.isPending}>
              创建导出
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </PageLayout>
  )
}