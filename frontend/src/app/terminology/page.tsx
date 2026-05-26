'use client'

import { useState, useEffect, useRef } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { DataTable } from '@/components/ui/data-table'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogAction,
  AlertDialogCancel,
} from '@/components/ui/alert-dialog'
import { useToast, Toaster } from '@/components/ui/use-toast'
import PageLayout from '@/components/Layout/PageLayout'
import {
  useGlossary,
  useCreateGlossary,
  useUpdateGlossary,
  useDeleteGlossary,
  useGlossaryReviewStats,
  useExportGlossary,
  Glossary,
} from '@/hooks/useTranslation'

export default function TerminologyPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<Glossary | null>(null)
  const [filterCategory, setFilterCategory] = useState<string | undefined>()
  const [searchTerm, setSearchTerm] = useState('')
  const [term, setTerm] = useState('')
  const [translation, setTranslation] = useState('')
  const [category, setCategory] = useState('')
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null)
  const [isImportModalOpen, setIsImportModalOpen] = useState(false)
  const [csvContent, setCsvContent] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()
  const { data: glossary = [], isLoading: queryLoading, refetch } = useGlossary()
  const { data: reviewStats } = useGlossaryReviewStats()
  const createMutation = useCreateGlossary()
  const updateMutation = useUpdateGlossary()
  const deleteMutation = useDeleteGlossary()
  const exportMutation = useExportGlossary()

  const [isClientReady, setIsClientReady] = useState(false)
  useEffect(() => {
    setIsClientReady(true)
  }, [])

  const isLoading = !isClientReady || queryLoading

  const filteredData = glossary.filter((item: Glossary) => {
    const matchesSearch =
      !searchTerm ||
      item.term.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.translation.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = !filterCategory || item.category === filterCategory
    return matchesSearch && matchesCategory
  })

  const categories = [...new Set<string>(glossary.map((item: Glossary) => item.category).filter(Boolean) as string[])]

  const handleSubmit = async () => {
    if (!term.trim()) {
      toast({ title: '请输入术语', variant: 'error' })
      return
    }
    if (!translation.trim()) {
      toast({ title: '请输入翻译', variant: 'error' })
      return
    }
    try {
      const values = { term, translation, category }
      if (editingItem) {
        await updateMutation.mutateAsync({ id: editingItem.id, data: values })
        toast({ title: '术语更新成功', variant: 'success' })
      } else {
        await createMutation.mutateAsync(values)
        toast({ title: '术语添加成功', variant: 'success' })
      }
      setIsModalOpen(false)
      resetForm()
      refetch()
    } catch {
      toast({ title: '操作失败', variant: 'error' })
    }
  }

  const handleEdit = (item: Glossary) => {
    setEditingItem(item)
    setTerm(item.term)
    setTranslation(item.translation)
    setCategory(item.category || '')
    setIsModalOpen(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteMutation.mutateAsync(id)
      toast({ title: '术语删除成功', variant: 'success' })
      refetch()
    } catch {
      toast({ title: '删除失败', variant: 'error' })
    }
    setDeleteConfirmId(null)
  }

  const handleExport = async () => {
    try {
      const result = await exportMutation.mutateAsync({})
      if (result?.csv_content) {
        const blob = new Blob([result.csv_content], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `glossary_export_${new Date().toISOString().slice(0, 10)}.csv`
        a.click()
        URL.revokeObjectURL(url)
        toast({ title: '导出成功', variant: 'success' })
      }
    } catch {
      toast({ title: '导出失败', variant: 'error' })
    }
  }

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (event) => {
        const content = event.target?.result as string
        setCsvContent(content)
      }
      reader.readAsText(file)
    }
  }

  const handleImport = async () => {
    if (!csvContent.trim()) {
      toast({ title: '请输入 CSV 内容', variant: 'error' })
      return
    }
    try {
      const response = await fetch('/api/v1/translation/glossary/import/csv', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ csv_content: csvContent }),
      })
      const data = await response.json()
      if (data.code === 200 || data.code === 207) {
        toast({ title: data.message, variant: 'success' })
        setIsImportModalOpen(false)
        setCsvContent('')
        refetch()
      } else {
        toast({ title: data.message || '导入失败', variant: 'error' })
      }
    } catch {
      toast({ title: '导入失败', variant: 'error' })
    }
  }

  const resetForm = () => {
    setTerm('')
    setTranslation('')
    setCategory('')
    setEditingItem(null)
  }

  const openAddModal = () => {
    resetForm()
    setIsModalOpen(true)
  }

  const reviewColumns = [
    { key: 'term', title: '术语' },
    { key: 'translation', title: '翻译' },
    {
      key: 'category',
      title: '分类',
      render: (val: string) => val ? <Badge variant="info">{val}</Badge> : '-',
    },
    { key: 'source_lang', title: '源语言' },
    { key: 'target_lang', title: '目标语言' },
  ]

  const columns = [
    { key: 'term', title: '术语' },
    { key: 'translation', title: '翻译' },
    {
      key: 'category',
      title: '分类',
      render: (val: string) => val ? <Badge variant="info">{val}</Badge> : '-',
    },
    {
      key: 'actions',
      title: '操作',
      render: (_: any, record: Glossary) => (
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Button variant="ghost" size="sm" className="text-red-500 hover:text-red-600" onClick={() => setDeleteConfirmId(record.id)}>
            删除
          </Button>
        </div>
      ),
    },
  ]

  const stats = reviewStats || { pending: 0, approved: 0, rejected: 0 }

  return (
    <PageLayout>
      <Toaster />
      <div className="mb-4 flex gap-2">
        <Button variant="outline" onClick={() => setIsImportModalOpen(true)}>导入</Button>
        <Button variant="outline" onClick={handleExport} loading={exportMutation.isPending}>导出</Button>
      </div>

      <Card
        title="术语库"
        description={`待审核: ${stats.pending} | 已审核: ${stats.approved} | 已拒绝: ${stats.rejected}`}
        extra={
          <Button onClick={openAddModal}>添加术语</Button>
        }
      >
        <div className="flex flex-wrap gap-4 mb-4">
          <Input
            placeholder="搜索术语..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-48"
          />
          <select
            value={filterCategory || ''}
            onChange={(e) => setFilterCategory(e.target.value || undefined)}
            className="h-10 w-40 rounded-md border border-gray-200 px-3 text-sm"
          >
            <option value="">全部分类</option>
            {categories.map((c: string) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>
        <DataTable
          columns={columns}
          data={filteredData}
          loading={isLoading}
          rowKey="id"
          pagination={{ pageSize: 20 }}
        />
      </Card>

      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingItem ? '编辑术语' : '添加术语'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium text-woye mb-1 block">术语</label>
              <Input value={term} onChange={(e) => setTerm(e.target.value)} placeholder="输入术语" />
            </div>
            <div>
              <label className="text-sm font-medium text-woye mb-1 block">翻译</label>
              <Input value={translation} onChange={(e) => setTranslation(e.target.value)} placeholder="输入翻译" />
            </div>
            <div>
              <label className="text-sm font-medium text-woye mb-1 block">分类</label>
              <Input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="输入分类" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsModalOpen(false)}>取消</Button>
            <Button onClick={handleSubmit} loading={createMutation.isPending || updateMutation.isPending}>
              {editingItem ? '更新' : '创建'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={isImportModalOpen} onOpenChange={setIsImportModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>导入术语库</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <p className="text-sm text-gray-600">
              CSV 格式要求：第一行为表头，包含 term,translation,source_lang,target_lang,category,notes 字段
            </p>
            <div>
              <label className="text-sm font-medium text-woye mb-1 block">上传 CSV 文件</label>
              <input
                type="file"
                ref={fileInputRef}
                accept=".csv"
                onChange={handleFileUpload}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
              />
            </div>
            <div className="text-center text-gray-400">或</div>
            <div>
              <label className="text-sm font-medium text-woye mb-1 block">粘贴 CSV 内容</label>
              <textarea
                value={csvContent}
                onChange={(e) => setCsvContent(e.target.value)}
                placeholder="term,translation,source_lang,target_lang,category,notes&#10;酒店,hotel,zh,en,general,"
                className="w-full h-40 p-2 border rounded text-sm font-mono"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsImportModalOpen(false)}>取消</Button>
            <Button onClick={handleImport} loading={false}>导入</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteConfirmId !== null} onOpenChange={() => setDeleteConfirmId(null)}>
        <AlertDialogContent>
          <AlertDialogTitle>删除术语</AlertDialogTitle>
          <AlertDialogDescription>
            确定要删除这个术语吗？此操作无法撤销。
          </AlertDialogDescription>
          <AlertDialogFooter>
            <AlertDialogCancel>取消</AlertDialogCancel>
            <AlertDialogAction onClick={() => deleteConfirmId && handleDelete(deleteConfirmId)}>
              删除
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </PageLayout>
  )
}