'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DataTable } from '@/components/ui/data-table'
import { Badge } from '@/components/ui/badge'
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
import { useHotels, useCreateHotel, useUpdateHotel, useDeleteHotel, useUpdateHotelExtension, Hotel, HotelExtensionUpdate } from '@/hooks/useHotels'
import { useHotelStore } from '@/stores/hotelStore'

export default function HotelsPage() {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [editingHotel, setEditingHotel] = useState<Hotel | null>(null)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const [nameCn, setNameCn] = useState('')
  const [nameEn, setNameEn] = useState('')
  const [addressCn, setAddressCn] = useState('')
  const [province, setProvince] = useState('')
  const [city, setCity] = useState('')
  const [countryCode, setCountryCode] = useState('CN')
  const [status, setStatus] = useState('draft')
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null)
  // Extension fields
  const [description, setDescription] = useState('')
  const [cancellationPolicy, setCancellationPolicy] = useState('')
  const [prepaymentPolicy, setPrepaymentPolicy] = useState('')
  const [kidPolicy, setKidPolicy] = useState('')
  const [petPolicy, setPetPolicy] = useState('')
  const [services, setServices] = useState('')
  const [facilities, setFacilities] = useState('')
  const [checkInTime, setCheckInTime] = useState('')
  const [checkOutTime, setCheckOutTime] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const { toast } = useToast()
  const { hotels, total, isLoading: queryLoading, refetch } = useHotels()
  const { page, pageSize, setPage, setPageSize, filters, setFilters } = useHotelStore()
  const createHotelMutation = useCreateHotel()
  const updateHotelMutation = useUpdateHotel()
  const updateHotelExtensionMutation = useUpdateHotelExtension()
  const deleteHotelMutation = useDeleteHotel()

  const [isClientReady, setIsClientReady] = useState(false)
  useEffect(() => {
    setIsClientReady(true)
  }, [])

  const isLoading = !isClientReady || queryLoading

  const handleSearch = (value: string) => {
    setSearch(value)
  }

  const handleSubmit = async () => {
    if (!nameCn.trim()) {
      toast({ title: '请输入酒店名称', variant: 'error' })
      return
    }
    if (!addressCn.trim()) {
      toast({ title: '请输入地址', variant: 'error' })
      return
    }
    if (!province.trim()) {
      toast({ title: '请输入省份', variant: 'error' })
      return
    }
    try {
      const values = {
        name_cn: nameCn, name_en: nameEn,
        address_cn: addressCn,
        province, city, country_code: countryCode,
        status: status as 'draft' | 'pending_review' | 'approved' | 'published' | 'suspended',
        // Extension fields
        check_in_time: checkInTime, check_out_time: checkOutTime,
        cancellation_policy: cancellationPolicy, prepayment_policy: prepaymentPolicy,
        kid_policy: kidPolicy, pet_policy: petPolicy,
        services, facilities, description,
        phone, email,
      }
      if (editingHotel) {
        await updateHotelMutation.mutateAsync({ id: editingHotel.id, data: values })
        toast({ title: '酒店更新成功', variant: 'success' })
      } else {
        await createHotelMutation.mutateAsync(values)
        toast({ title: '酒店创建成功', variant: 'success' })
      }
      setIsModalOpen(false)
      resetForm()
      refetch()
    } catch {
      toast({ title: '操作失败', variant: 'error' })
    }
  }

  const handleEdit = (hotel: Hotel) => {
    setEditingHotel(hotel)
    setNameCn(hotel.name_cn)
    setNameEn(hotel.name_en || '')
    setAddressCn(hotel.address_cn)
    setProvince(hotel.province)
    setCity(hotel.city)
    setCountryCode(hotel.country_code || 'CN')
    setStatus(hotel.status || 'draft')
    setDescription(hotel.description || '')
    setCancellationPolicy(hotel.cancellation_policy || '')
    setPrepaymentPolicy(hotel.prepayment_policy || '')
    setKidPolicy(hotel.kid_policy || '')
    setPetPolicy(hotel.pet_policy || '')
    setServices(hotel.services || '')
    setFacilities(hotel.facilities || '')
    setCheckInTime(hotel.check_in_time || '')
    setCheckOutTime(hotel.check_out_time || '')
    setPhone(hotel.phone || '')
    setEmail(hotel.email || '')
    setIsModalOpen(true)
  }

  const handleDelete = async (id: string) => {
    try {
      await deleteHotelMutation.mutateAsync(id)
      toast({ title: '酒店删除成功', variant: 'success' })
      refetch()
    } catch {
      toast({ title: '删除失败', variant: 'error' })
    }
    setDeleteConfirmId(null)
  }

  const resetForm = () => {
    setNameCn('')
    setNameEn('')
    setAddressCn('')
    setProvince('')
    setCity('')
    setCountryCode('CN')
    setStatus('draft')
    setEditingHotel(null)
    setDescription('')
    setCancellationPolicy('')
    setPrepaymentPolicy('')
    setKidPolicy('')
    setPetPolicy('')
    setServices('')
    setFacilities('')
    setCheckInTime('')
    setCheckOutTime('')
    setPhone('')
    setEmail('')
  }

  const openAddModal = () => {
    resetForm()
    setIsModalOpen(true)
  }

  const columns = [
    { key: 'id', title: 'ID' },
    { key: 'name_cn', title: '名称' },
    { key: 'name_en', title: '英文名' },
    { key: 'city', title: '城市' },
    { key: 'province', title: '省份' },
    {
      key: 'status',
      title: '状态',
      render: (val: string) => {
        const variant = val === 'approved' || val === 'published' ? 'success' : val === 'suspended' ? 'error' : 'default'
        const labels: Record<string, string> = { draft: '草稿', pending_review: '待审核', approved: '已审核', published: '已发布', suspended: '已下线' }
        return <Badge variant={variant}>{labels[val] || val}</Badge>
      },
    },
    {
      key: 'actions',
      title: '操作',
      render: (_: any, record: Hotel) => (
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
      <Card
        title="酒店管理"
        extra={<Button onClick={openAddModal}>添加酒店</Button>}
      >
        <div className="flex flex-wrap gap-4 mb-4">
          <Input
            placeholder="搜索酒店..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-64"
          />
          <select
            value={statusFilter || ''}
            onChange={(e) => setStatusFilter(e.target.value || undefined)}
            className="h-10 w-40 rounded-md border border-gray-200 px-3 text-sm"
          >
            <option value="">全部状态</option>
            <option value="draft">草稿</option>
            <option value="active">启用</option>
            <option value="inactive">停用</option>
          </select>
        </div>
        <DataTable
          columns={columns}
          data={hotels}
          loading={isLoading}
          rowKey="id"
          pagination={{
            pageSize: pageSize,
            current: page,
            total,
          }}
        />
      </Card>

      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingHotel ? '编辑酒店' : '添加酒店'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium text-woye mb-1 block">酒店名称</label>
              <Input value={nameCn} onChange={(e) => setNameCn(e.target.value)} placeholder="输入酒店名称" />
            </div>
            <div>
              <label className="text-sm font-medium text-woye mb-1 block">英文名称</label>
              <Input value={nameEn} onChange={(e) => setNameEn(e.target.value)} placeholder="输入英文名称" />
            </div>
            <div>
              <label className="text-sm font-medium text-woye mb-1 block">地址</label>
              <Input value={addressCn} onChange={(e) => setAddressCn(e.target.value)} placeholder="输入地址" />
            </div>
            <div className="flex gap-4">
              <div className="flex-1">
                <label className="text-sm font-medium text-woye mb-1 block">省份</label>
                <Input value={province} onChange={(e) => setProvince(e.target.value)} placeholder="省份" />
              </div>
              <div className="flex-1">
                <label className="text-sm font-medium text-woye mb-1 block">城市</label>
                <Input value={city} onChange={(e) => setCity(e.target.value)} placeholder="城市" />
              </div>
            </div>
            <div className="flex gap-4">
              <div className="flex-1">
                <label className="text-sm font-medium text-woye mb-1 block">国家代码</label>
                <Input value={countryCode} onChange={(e) => setCountryCode(e.target.value)} placeholder="CN" />
              </div>
              <div className="flex-1">
                <label className="text-sm font-medium text-woye mb-1 block">状态</label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="h-10 w-full rounded-md border border-gray-200 px-3 text-sm"
                >
                  <option value="draft">草稿</option>
                  <option value="pending_review">待审核</option>
                  <option value="approved">已审核</option>
                  <option value="published">已发布</option>
                  <option value="suspended">已下线</option>
                </select>
              </div>
            </div>
            {/* Extension Fields */}
            <div className="border-t pt-4 mt-4">
              <h3 className="text-sm font-medium text-woye mb-3">扩展信息</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-woye mb-1 block">入住时间</label>
                  <Input value={checkInTime} onChange={(e) => setCheckInTime(e.target.value)} placeholder="14:00" />
                </div>
                <div>
                  <label className="text-sm font-medium text-woye mb-1 block">退房时间</label>
                  <Input value={checkOutTime} onChange={(e) => setCheckOutTime(e.target.value)} placeholder="12:00" />
                </div>
              </div>
              <div className="mt-3">
                <label className="text-sm font-medium text-woye mb-1 block">取消政策</label>
                <Input value={cancellationPolicy} onChange={(e) => setCancellationPolicy(e.target.value)} placeholder="免费取消政策" />
              </div>
              <div className="mt-3">
                <label className="text-sm font-medium text-woye mb-1 block">预付款政策</label>
                <Input value={prepaymentPolicy} onChange={(e) => setPrepaymentPolicy(e.target.value)} placeholder="预付款要求" />
              </div>
              <div className="grid grid-cols-2 gap-4 mt-3">
                <div>
                  <label className="text-sm font-medium text-woye mb-1 block">儿童政策</label>
                  <Input value={kidPolicy} onChange={(e) => setKidPolicy(e.target.value)} placeholder="儿童入住政策" />
                </div>
                <div>
                  <label className="text-sm font-medium text-woye mb-1 block">宠物政策</label>
                  <Input value={petPolicy} onChange={(e) => setPetPolicy(e.target.value)} placeholder="宠物入住政策" />
                </div>
              </div>
              <div className="mt-3">
                <label className="text-sm font-medium text-woye mb-1 block">服务设施</label>
                <Input value={services} onChange={(e) => setServices(e.target.value)} placeholder="酒店服务设施描述" />
              </div>
              <div className="mt-3">
                <label className="text-sm font-medium text-woye mb-1 block">设施详情</label>
                <Input value={facilities} onChange={(e) => setFacilities(e.target.value)} placeholder="详细设施列表" />
              </div>
              <div className="mt-3">
                <label className="text-sm font-medium text-woye mb-1 block">酒店描述</label>
                <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="酒店描述" />
              </div>
              <div className="grid grid-cols-2 gap-4 mt-3">
                <div>
                  <label className="text-sm font-medium text-woye mb-1 block">联系电话</label>
                  <Input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+86-21-xxxx" />
                </div>
                <div>
                  <label className="text-sm font-medium text-woye mb-1 block">邮箱</label>
                  <Input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="info@hotel.com" />
                </div>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsModalOpen(false)}>取消</Button>
            <Button onClick={handleSubmit} loading={createHotelMutation.isPending || updateHotelMutation.isPending || updateHotelExtensionMutation.isPending}>
              {editingHotel ? '更新' : '创建'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={deleteConfirmId !== null} onOpenChange={() => setDeleteConfirmId(null)}>
        <AlertDialogContent>
          <AlertDialogTitle>删除酒店</AlertDialogTitle>
          <AlertDialogDescription>
            确定要删除这家酒店吗？此操作无法撤销。
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