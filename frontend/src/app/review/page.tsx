'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { useToast, Toaster } from '@/components/ui/use-toast'
import PageLayout from '@/components/Layout/PageLayout'
import apiClient from '@/api/client'
import dayjs from 'dayjs'

interface TranslationRecord {
  id: number
  source_text: string
  translated_text: string
  booking_reference?: string
  source_lang: string
  target_lang: string
  review_status: 'pending' | 'approved' | 'rejected'
  review_notes?: string
  operator_name?: string
  created_at: string
}

interface ReviewStats {
  pending: number
  approved: number
  rejected: number
}

export default function ReviewPage() {
  const [activeTab, setActiveTab] = useState<'pending' | 'approved' | 'rejected'>('pending')
  const [records, setRecords] = useState<TranslationRecord[]>([])
  const [stats, setStats] = useState<ReviewStats>({ pending: 0, approved: 0, rejected: 0 })
  const [isLoading, setIsLoading] = useState(false)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [editingRecord, setEditingRecord] = useState<TranslationRecord | null>(null)
  const [editText, setEditText] = useState('')
  const { toast } = useToast()

  const pageSize = 20

  useEffect(() => {
    fetchRecords()
    fetchStats()
  }, [activeTab, page, searchTerm])

  const fetchRecords = async () => {
    setIsLoading(true)
    try {
      const statusMap = { pending: 'pending', approved: 'approved', rejected: 'rejected' }
      const response = await apiClient.get(`/translation/review/by-status`, {
        params: {
          status: statusMap[activeTab],
          page,
          page_size: pageSize,
        },
      })
      const data = response.data.data
      setRecords(data.list || [])
      setTotal(data.total || 0)
    } catch {
      toast({ title: '获取翻译记录失败', variant: 'error' })
    } finally {
      setIsLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await apiClient.get('/translation/review/stats/summary')
      setStats(response.data.data || { pending: 0, approved: 0, rejected: 0 })
    } catch {
      // ignore
    }
  }

  const handleApprove = async (id: number) => {
    try {
      await apiClient.post(`/translation/review/${id}/approve`)
      toast({ title: '已批准', variant: 'success' })
      fetchRecords()
      fetchStats()
    } catch {
      toast({ title: '操作失败', variant: 'error' })
    }
  }

  const handleReject = async (id: number, notes?: string) => {
    try {
      await apiClient.post(`/translation/review/${id}/reject`, null, {
        params: { review_notes: notes },
      })
      toast({ title: '已拒绝', variant: 'success' })
      fetchRecords()
      fetchStats()
    } catch {
      toast({ title: '操作失败', variant: 'error' })
    }
  }

  const handleBatchAction = async (action: 'approve' | 'reject') => {
    if (selectedIds.length === 0) {
      toast({ title: '请先选择要操作的记录', variant: 'error' })
      return
    }
    try {
      await apiClient.post('/translation/review/batch', {
        ids: selectedIds,
        action,
      })
      toast({ title: `批量${action === 'approve' ? '批准' : '拒绝'}成功`, variant: 'success' })
      setSelectedIds([])
      fetchRecords()
      fetchStats()
    } catch {
      toast({ title: '操作失败', variant: 'error' })
    }
  }

  const handleToggleSelect = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    )
  }

  const handleSelectAll = () => {
    if (selectedIds.length === records.length) {
      setSelectedIds([])
    } else {
      setSelectedIds(records.map((r) => r.id))
    }
  }

  const handleOpenEdit = (record: TranslationRecord) => {
    setEditingRecord(record)
    setEditText(record.translated_text)
  }

  const handleSaveEdit = async () => {
    if (!editingRecord) return
    try {
      await apiClient.put(`/translation/review/${editingRecord.id}`, null, {
        params: { translated_text: editText },
      })
      toast({ title: '翻译已更新', variant: 'success' })
      setEditingRecord(null)
      fetchRecords()
    } catch {
      toast({ title: '更新失败', variant: 'error' })
    }
  }

  const langLabel = (code: string) => {
    const map: Record<string, string> = { zh: '中文', en: '英文', ja: '日文', ko: '韩文' }
    return map[code] || code
  }

  return (
    <PageLayout>
      <Toaster />
      <Tabs value={activeTab} onValueChange={(v) => { setActiveTab(v as typeof activeTab); setPage(1); setSelectedIds([]) }}>
        <TabsList>
          <TabsTrigger value="pending">
            待审核 ({stats.pending || 0})
          </TabsTrigger>
          <TabsTrigger value="approved">
            已通过 ({stats.approved || 0})
          </TabsTrigger>
          <TabsTrigger value="rejected">
            已拒绝 ({stats.rejected || 0})
          </TabsTrigger>
        </TabsList>

        <div className="mt-4 flex flex-wrap gap-4">
          <Input
            placeholder="搜索原文或译文..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-64"
          />
        </div>

        {activeTab === 'pending' && records.length > 0 && (
          <div className="mt-4 flex gap-2">
            <Button variant="outline" size="sm" onClick={handleSelectAll}>
              {selectedIds.length === records.length ? '取消全选' : '全选'}
            </Button>
            <Button
              variant="default"
              size="sm"
              onClick={() => handleBatchAction('approve')}
              disabled={selectedIds.length === 0}
            >
              批量批准 ({selectedIds.length})
            </Button>
            <Button
              variant="destructive"
              size="sm"
              onClick={() => handleBatchAction('reject')}
              disabled={selectedIds.length === 0}
            >
              批量拒绝 ({selectedIds.length})
            </Button>
          </div>
        )}

        <TabsContent value="pending" className="mt-4">
          <ReviewTable
            records={records}
            isLoading={isLoading}
            showActions
            showCheckbox
            selectedIds={selectedIds}
            onToggleSelect={handleToggleSelect}
            onApprove={handleApprove}
            onReject={handleReject}
            onEdit={handleOpenEdit}
            langLabel={langLabel}
          />
        </TabsContent>

        <TabsContent value="approved" className="mt-4">
          <ReviewTable
            records={records}
            isLoading={isLoading}
            showActions={false}
            showCheckbox={false}
            langLabel={langLabel}
          />
        </TabsContent>

        <TabsContent value="rejected" className="mt-4">
          <ReviewTable
            records={records}
            isLoading={isLoading}
            showActions={false}
            showCheckbox={false}
            langLabel={langLabel}
          />
        </TabsContent>
      </Tabs>

      {total > pageSize && (
        <div className="mt-4 flex justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
          >
            上一页
          </Button>
          <span className="flex items-center text-sm text-gray-500">
            第 {page} / {Math.ceil(total / pageSize)} 页
          </span>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setPage((p) => p + 1)}
            disabled={page >= Math.ceil(total / pageSize)}
          >
            下一页
          </Button>
        </div>
      )}

      <Dialog open={!!editingRecord} onOpenChange={() => setEditingRecord(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>修改翻译</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium text-woye mb-1 block">原文</label>
              <p className="text-gray-600 bg-gray-50 p-2 rounded">{editingRecord?.source_text}</p>
            </div>
            <div>
              <label className="text-sm font-medium text-woye mb-1 block">译文</label>
              <textarea
                value={editText}
                onChange={(e) => setEditText(e.target.value)}
                rows={4}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingRecord(null)}>取消</Button>
            <Button onClick={handleSaveEdit}>保存</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </PageLayout>
  )
}

interface ReviewTableProps {
  records: TranslationRecord[]
  isLoading: boolean
  showActions?: boolean
  showCheckbox?: boolean
  selectedIds?: number[]
  onToggleSelect?: (id: number) => void
  onApprove?: (id: number) => void
  onReject?: (id: number) => void
  onEdit?: (record: TranslationRecord) => void
  langLabel: (code: string) => string
}

function ReviewTable({
  records,
  isLoading,
  showActions,
  showCheckbox,
  selectedIds = [],
  onToggleSelect,
  onApprove,
  onReject,
  onEdit,
  langLabel,
}: ReviewTableProps) {
  if (isLoading) {
    return <div className="text-center py-8 text-gray-500">加载中...</div>
  }

  if (records.length === 0) {
    return <div className="text-center py-8 text-gray-500">暂无数据</div>
  }

  return (
    <div className="space-y-3">
      {records.map((record) => (
        <Card key={record.id} className="p-4">
          <div className="flex items-start gap-3">
            {showCheckbox && onToggleSelect && (
              <input
                type="checkbox"
                checked={selectedIds.includes(record.id)}
                onChange={() => onToggleSelect(record.id)}
                className="mt-1 h-4 w-4"
              />
            )}
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap gap-2 mb-2 text-xs text-gray-500">
                <Badge variant="outline">{langLabel(record.source_lang)} → {langLabel(record.target_lang)}</Badge>
                <span>{dayjs(record.created_at).format('YYYY-MM-DD HH:mm')}</span>
                {record.operator_name && <span>操作员: {record.operator_name}</span>}
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="text-xs text-gray-500 block mb-1">原文</label>
                  <p className="text-sm bg-gray-50 p-2 rounded break-words">{record.source_text}</p>
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">Booking 参考</label>
                  <p className="text-sm bg-blue-50 p-2 rounded break-words">
                    {record.booking_reference || '-'}
                  </p>
                </div>
                <div>
                  <label className="text-xs text-gray-500 block mb-1">译文</label>
                  <p className="text-sm bg-green-50 p-2 rounded break-words">
                    {record.translated_text}
                  </p>
                </div>
              </div>
              {record.review_notes && (
                <div className="mt-2 text-xs text-red-500">
                  备注: {record.review_notes}
                </div>
              )}
            </div>
            {showActions && onApprove && onReject && onEdit && (
              <div className="flex flex-col gap-1">
                <Button variant="ghost" size="sm" onClick={() => onApprove(record.id)}>
                  批准
                </Button>
                <Button variant="ghost" size="sm" className="text-red-500" onClick={() => onReject(record.id)}>
                  拒绝
                </Button>
                <Button variant="ghost" size="sm" onClick={() => onEdit(record)}>
                  修改
                </Button>
              </div>
            )}
          </div>
        </Card>
      ))}
    </div>
  )
}