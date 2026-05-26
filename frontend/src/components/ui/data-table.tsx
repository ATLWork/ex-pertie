'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

interface Column<T> {
  key: string
  title: string
  render?: (value: any, record: T, index: number) => React.ReactNode
}

interface DataTableProps<T> {
  columns: Column<T>[]
  data: T[]
  loading?: boolean
  rowKey?: keyof T | ((row: T) => string | number)
  pagination?: { pageSize?: number; current?: number; total?: number; onChange?: (page: number, pageSize: number) => void }
}

export function DataTable<T extends Record<string, any>>({
  columns,
  data,
  loading,
  rowKey = 'id' as keyof T,
  pagination,
}: DataTableProps<T>) {
  const getRowKey = (row: T, index: number) => {
    if (typeof rowKey === 'function') return rowKey(row)
    return row[rowKey] ?? index
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="h-10 w-10 animate-spin rounded-full border-3 border-woye border-t-transparent" />
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-gray-100 overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="bg-baiyan border-b border-gray-200">
            {columns.map((col) => (
              <th key={col.key} className="px-5 py-4 text-left text-sm font-semibold text-woye">
                {col.title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="h-32 text-center text-gray-400">
                暂无数据
              </td>
            </tr>
          ) : (
            data.map((row, index) => (
              <tr key={getRowKey(row, index)} className="border-b border-gray-100 hover:bg-baiyan/30 transition-colors">
                {columns.map((col) => (
                  <td key={col.key} className="px-5 py-4 text-sm text-gray-700">
                    {col.render
                      ? col.render(row[col.key], row, index)
                      : row[col.key]}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
      {pagination && (
        <div className="flex items-center justify-between border-t border-gray-100 px-5 py-4 bg-gray-50/50">
          <div className="text-sm text-gray-500">
            共 {pagination.total || data.length} 条
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => pagination.onChange?.((pagination.current || 1) - 1, pagination.pageSize || 20)}
              disabled={pagination.current === 1}
              className="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:border-woye hover:text-woye disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              上一页
            </button>
            <button
              onClick={() => pagination.onChange?.((pagination.current || 1) + 1, pagination.pageSize || 20)}
              disabled={data.length < (pagination.pageSize || 20)}
              className="px-4 py-2 text-sm border border-gray-200 rounded-lg hover:border-woye hover:text-woye disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              下一页
            </button>
          </div>
        </div>
      )}
    </div>
  )
}