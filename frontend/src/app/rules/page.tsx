'use client'

import { useState, useEffect, useRef } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DataTable } from '@/components/ui/data-table'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
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
  useTranslationRules,
  useCreateTranslationRule,
  useUpdateTranslationRule,
  useDeleteTranslationRule,
  useParsePdfRules,
  useImportPdfRules,
  TranslationRule,
} from '@/hooks/useTranslation'
import apiClient from '@/api/client'

export default function RulesPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingRule, setEditingRule] = useState<TranslationRule | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [page, setPage] = useState(1)

  // Form fields - aligned with backend TranslationRule model
  const [name, setName] = useState('')
  const [sourceLang, setSourceLang] = useState('zh')
  const [targetLang, setTargetLang] = useState('en')
  const [fieldName, setFieldName] = useState('general')
  const [ruleType, setRuleType] = useState<'direct' | 'glossary' | 'ai'>('direct')
  const [ruleValue, setRuleValue] = useState('')
  const [region, setRegion] = useState('')
  const [province, setProvince] = useState('')
  const [city, setCity] = useState('')
  const [priority, setPriority] = useState(100)
  const [isActive, setIsActive] = useState(true)

  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [showPreview, setShowPreview] = useState(false)
  const [previewRules, setPreviewRules] = useState<any[]>([])
  const [previewSummary, setPreviewSummary] = useState('')
  const [previewType, setPreviewType] = useState('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const pdfInputRef = useRef<HTMLInputElement>(null)

  const { toast } = useToast()
  const { data: rulesData, isLoading: queryLoading, refetch } = useTranslationRules(page, 20)
  const createMutation = useCreateTranslationRule()
  const updateMutation = useUpdateTranslationRule()
  const deleteMutation = useDeleteTranslationRule()
  const parsePdfMutation = useParsePdfRules()
  const importPdfMutation = useImportPdfRules()

  const rules = rulesData?.list ?? []

  const [isClientReady, setIsClientReady] = useState(false)
  useEffect(() => {
    setIsClientReady(true)
  }, [])

  const isLoading = !isClientReady || queryLoading

  const filteredData = rules.filter(
    (rule: TranslationRule) =>
      !searchTerm ||
      rule.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rule.field_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rule.rule_value?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const handleSubmit = async () => {
    if (!name.trim()) {
      toast({ title: '请输入规则名称', variant: 'error' })
      return
    }
    if (!ruleValue.trim()) {
      toast({ title: '请输入规则配置', variant: 'error' })
      return
    }

    try {
      const values = {
        name,
        source_lang: sourceLang,
        target_lang: targetLang,
        field_name: fieldName,
        rule_type: ruleType,
        rule_value: ruleValue,
        region: region || undefined,
        province: province || undefined,
        city: city || undefined,
        priority,
        is_active: isActive,
      }

      if (editingRule) {
        await updateMutation.mutateAsync({ id: editingRule.id, data: values })
        toast({ title: '规则更新成功', variant: 'success' })
      } else {
        await createMutation.mutateAsync(values)
        toast({ title: '规则创建成功', variant: 'success' })
      }
      setIsModalOpen(false)
      resetForm()
      refetch()
    } catch {
      toast({ title: '操作失败', variant: 'error' })
    }
  }

  const handleEdit = (rule: TranslationRule) => {
    setEditingRule(rule)
    setName(rule.name || '')
    setSourceLang(rule.source_lang || 'zh')
    setTargetLang(rule.target_lang || 'en')
    setFieldName(rule.field_name || 'general')
    setRuleType(rule.rule_type || 'direct')
    setRuleValue(rule.rule_value || '')
    setRegion(rule.region || '')
    setProvince(rule.province || '')
    setCity(rule.city || '')
    setPriority(rule.priority || 100)
    setIsActive(rule.is_active ?? true)
    setIsModalOpen(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await deleteMutation.mutateAsync(id)
      toast({ title: '规则删除成功', variant: 'success' })
      refetch()
    } catch {
      toast({ title: '删除失败', variant: 'error' })
    }
    setDeleteConfirmId(null)
  }

  const handleToggleEnabled = async (rule: TranslationRule) => {
    try {
      await updateMutation.mutateAsync({
        id: rule.id,
        data: { is_active: !rule.is_active },
      })
      toast({ title: '规则更新成功', variant: 'success' })
      refetch()
    } catch {
      toast({ title: '更新失败', variant: 'error' })
    }
  }

  const resetForm = () => {
    setName('')
    setSourceLang('zh')
    setTargetLang('en')
    setFieldName('general')
    setRuleType('direct')
    setRuleValue('')
    setRegion('')
    setProvince('')
    setCity('')
    setPriority(100)
    setIsActive(true)
    setEditingRule(null)
  }

  const openAddModal = () => {
    resetForm()
    setIsModalOpen(true)
  }

  // PDF upload handlers
  const handlePdfFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      toast({ title: '请选择 PDF 文件', variant: 'error' })
      return
    }

    setUploadProgress(30)
    try {
      // First parse the PDF to preview rules
      const result = await parsePdfMutation.mutateAsync({ file, useAi: true })
      setPreviewRules(result.rules || [])
      setPreviewSummary(result.summary || '')
      setPreviewType(result.document_type || '')
      setUploadProgress(100)
      setShowPreview(true)
      toast({ title: 'PDF 解析成功', variant: 'success', description: `发现 ${result.rules_count} 条规则` })
    } catch {
      toast({ title: 'PDF 解析失败', variant: 'error' })
      setUploadProgress(0)
    }

    if (pdfInputRef.current) pdfInputRef.current.value = ''
  }

  const handleImportPdf = async (overwrite = false) => {
    const file = fileInputRef.current?.files?.[0]
    if (!file) {
      toast({ title: '请先选择 PDF 文件', variant: 'error' })
      return
    }

    setUploadProgress(50)
    try {
      const result = await importPdfMutation.mutateAsync({ file, useAi: true, overwrite })
      toast({
        title: '导入完成',
        variant: 'success',
        description: `成功导入 ${result.imported_count} 条规则`,
      })
      setShowPreview(false)
      setPreviewRules([])
      if (fileInputRef.current) fileInputRef.current.value = ''
      refetch()
    } catch {
      toast({ title: '导入失败', variant: 'error' })
    }
    setUploadProgress(0)
  }

  const columns = [
    { key: 'name', title: '规则名称', render: (val: string) => <span className="font-medium">{val || '-'}</span> },
    { key: 'field_name', title: '字段', render: (val: string) => <Badge variant="outline">{val || '-'}</Badge> },
    { key: 'rule_type', title: '类型', render: (val: string) => (
      <Badge variant={val === 'direct' ? 'default' : val === 'ai' ? 'warning' : 'info'}>
        {val === 'direct' ? '直接' : val === 'ai' ? 'AI' : '术语'}
      </Badge>
    )},
    { key: 'region', title: '地区', render: (val: string) => val || '-' },
    { key: 'priority', title: '优先级', render: (val: number) => val || 100 },
    {
      key: 'is_active',
      title: '启用',
      render: (val: boolean, record: TranslationRule) => (
        <Switch checked={val} onCheckedChange={() => handleToggleEnabled(record)} />
      ),
    },
    {
      key: 'actions',
      title: '操作',
      render: (_: any, record: TranslationRule) => (
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

  return (
    <PageLayout>
      <Toaster />
      <div className="space-y-6">
        {/* PDF Upload Section */}
        <Card title="从 PDF 导入规则">
          <div className="flex items-center gap-4">
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handlePdfFileChange}
              className="hidden"
            />
            <Button
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
              loading={parsePdfMutation.isPending}
            >
              选择 PDF 文件
            </Button>
            <span className="text-sm text-gray-500">
              支持 SOP、指南等翻译规则文档
            </span>
          </div>
          {uploadProgress > 0 && uploadProgress < 100 && (
            <div className="mt-4">
              <Progress value={uploadProgress} />
              <p className="text-sm text-gray-500 mt-1">正在解析 PDF...</p>
            </div>
          )}
        </Card>

        {/* Rules List */}
        <Card
          title="翻译规则"
          extra={
            <div className="flex items-center gap-3">
              <Input
                placeholder="搜索规则..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-48"
              />
              <Button onClick={openAddModal}>添加规则</Button>
            </div>
          }
        >
          <DataTable
            columns={columns}
            data={filteredData}
            loading={isLoading}
            rowKey="id"
            pagination={{
              pageSize: 20,
              current: page,
              total: rulesData?.total || 0,
              onChange: (p) => setPage(p),
            }}
          />
        </Card>
      </div>

      {/* Add/Edit Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>{editingRule ? '编辑规则' : '添加规则'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4 max-h-96 overflow-y-auto">
            <div>
              <label className="text-sm font-medium text-woye mb-1 block">规则名称 *</label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="例如: 房型翻译-大床"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-woye mb-1 block">源语言</label>
                <select
                  value={sourceLang}
                  onChange={(e) => setSourceLang(e.target.value)}
                  className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
                >
                  <option value="zh">中文 (zh)</option>
                  <option value="en">英文 (en)</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-woye mb-1 block">目标语言</label>
                <select
                  value={targetLang}
                  onChange={(e) => setTargetLang(e.target.value)}
                  className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
                >
                  <option value="en">英文 (en)</option>
                  <option value="zh">中文 (zh)</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-woye mb-1 block">字段名称</label>
                <select
                  value={fieldName}
                  onChange={(e) => setFieldName(e.target.value)}
                  className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
                >
                  <option value="general">通用 (general)</option>
                  <option value="room_type">房型 (room_type)</option>
                  <option value="amenity">设施 (amenity)</option>
                  <option value="hotel_name">酒店名称 (hotel_name)</option>
                  <option value="meal">餐食 (meal)</option>
                  <option value="policy">政策 (policy)</option>
                  <option value="description">描述 (description)</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-woye mb-1 block">规则类型</label>
                <select
                  value={ruleType}
                  onChange={(e) => setRuleType(e.target.value as 'direct' | 'glossary' | 'ai')}
                  className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm"
                >
                  <option value="direct">直接映射 (direct)</option>
                  <option value="glossary">术语库 (glossary)</option>
                  <option value="ai">AI 增强 (ai)</option>
                </select>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium text-woye mb-1 block">规则配置 (JSON) *</label>
              <textarea
                value={ruleValue}
                onChange={(e) => setRuleValue(e.target.value)}
                rows={4}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm font-mono"
                placeholder='例如: {"mappings": {"大床": "King Suite"}}'
              />
              <p className="text-xs text-gray-500 mt-1">
                规则配置，格式为 JSON。例如：映射规则 &#123;&quot;mappings&quot;: &#123;&quot;大床&quot;: &quot;King Suite&quot;&#125;&#125;
              </p>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="text-sm font-medium text-woye mb-1 block">国家/地区</label>
                <Input
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                  placeholder="如: CN"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-woye mb-1 block">省份</label>
                <Input
                  value={province}
                  onChange={(e) => setProvince(e.target.value)}
                  placeholder="如: 上海"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-woye mb-1 block">城市</label>
                <Input
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  placeholder="如: 上海市"
                />
              </div>
              <div>
                <label className="text-sm font-medium text-woye mb-1 block">优先级</label>
                <Input
                  type="number"
                  value={priority}
                  onChange={(e) => setPriority(Number(e.target.value))}
                  min={1}
                  max={1000}
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Switch checked={isActive} onCheckedChange={setIsActive} />
              <span className="text-sm">启用此规则</span>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsModalOpen(false)}>取消</Button>
            <Button onClick={handleSubmit} loading={createMutation.isPending || updateMutation.isPending}>
              {editingRule ? '更新' : '创建'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* PDF Preview Modal */}
      <Dialog open={showPreview} onOpenChange={setShowPreview}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>PDF 解析预览</DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-hidden flex flex-col">
            <div className="mb-4 p-4 bg-gray-50 rounded-lg">
              <p className="text-sm"><span className="font-medium">文档类型:</span> {previewType || '未知'}</p>
              <p className="text-sm mt-1"><span className="font-medium">规则摘要:</span> {previewSummary || '无'}</p>
              <p className="text-sm mt-1"><span className="font-medium">发现规则:</span> {previewRules.length} 条</p>
            </div>
            <div className="flex-1 overflow-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-100 sticky top-0">
                  <tr>
                    <th className="px-3 py-2 text-left font-medium">规则名称</th>
                    <th className="px-3 py-2 text-left font-medium">字段</th>
                    <th className="px-3 py-2 text-left font-medium">类型</th>
                    <th className="px-3 py-2 text-left font-medium">配置</th>
                  </tr>
                </thead>
                <tbody>
                  {previewRules.map((rule: any, idx: number) => (
                    <tr key={idx} className="border-t">
                      <td className="px-3 py-2">{rule.name || '-'}</td>
                      <td className="px-3 py-2">{rule.field_name || '-'}</td>
                      <td className="px-3 py-2">{rule.rule_type || 'direct'}</td>
                      <td className="px-3 py-2 font-mono text-xs max-w-xs truncate">
                        {rule.rule_value || '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {previewRules.length > 0 && (
              <div className="mt-4 flex items-center justify-end gap-3">
                <Button variant="outline" onClick={() => setShowPreview(false)}>
                  取消
                </Button>
                <Button onClick={() => handleImportPdf(false)} loading={importPdfMutation.isPending}>
                  导入规则
                </Button>
                <Button variant="destructive" onClick={() => handleImportPdf(true)} loading={importPdfMutation.isPending}>
                  覆盖导入
                </Button>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <AlertDialog open={deleteConfirmId !== null} onOpenChange={() => setDeleteConfirmId(null)}>
        <AlertDialogContent>
          <AlertDialogTitle>删除规则</AlertDialogTitle>
          <AlertDialogDescription>
            确定要删除这条规则吗？此操作无法撤销。
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
