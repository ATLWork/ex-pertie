'use client'

import { useState, useMemo, useCallback } from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { useToast, Toaster } from '@/components/ui/use-toast'
import PageLayout from '@/components/Layout/PageLayout'
import { useTranslate, useBatchTranslate, useGlossary, useEvaluateQuality } from '@/hooks/useTranslation'
import apiClient from '@/api/client'

interface QualityScores {
  accuracy: number
  professionalism: number
  localization: number
  completeness: number
  booking_match_rate: number
  overall: number
}

interface TranslationResponse {
  translated_text: string
  source: 'cache' | 'booking_reference' | 'machine' | 'ai_enhanced'
  confidence?: number
  booking_reference?: string
  ctrip_reference?: string
}

export default function TranslatePage() {
  const [sourceText, setSourceText] = useState('')
  const [translatedText, setTranslatedText] = useState('')
  const [sourceLang, setSourceLang] = useState('zh')
  const [targetLang, setTargetLang] = useState('en')
  const [batchTexts, setBatchTexts] = useState<string[]>([])
  const [batchResults, setBatchResults] = useState<string[]>([])
  const [useAiEnhance, setUseAiEnhance] = useState(true)
  const [showQuality, setShowQuality] = useState(false)
  const [qualityScores, setQualityScores] = useState<QualityScores | null>(null)
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [translationSource, setTranslationSource] = useState<string>('')
  const [referenceInfo, setReferenceInfo] = useState<{booking?: string; ctrip?: string} | null>(null)
  const { toast } = useToast()

  const translateMutation = useTranslate()
  const batchTranslateMutation = useBatchTranslate()
  const evaluateQualityMutation = useEvaluateQuality()
  const { data: glossaryTerms = [] } = useGlossary()

  const handleTranslate = async () => {
    if (!sourceText.trim()) {
      toast({ title: '请输入要翻译的文本', variant: 'error' })
      return
    }
    try {
      const result = await translateMutation.mutateAsync({
        text: sourceText,
        sourceLang,
        targetLang,
        useAiEnhance,
      })
      setTranslatedText(result.translated_text || result.text || '')
      setShowQuality(false)
      setQualityScores(null)
      // 显示翻译来源
      setTranslationSource(getSourceLabel(result.source))
      // 显示参考信息
      if (result.booking_reference || result.ctrip_reference) {
        setReferenceInfo({
          booking: result.booking_reference,
          ctrip: result.ctrip_reference,
        })
      } else {
        setReferenceInfo(null)
      }
    } catch {
      toast({ title: '翻译失败', variant: 'error' })
    }
  }

  const getSourceLabel = (source: string) => {
    const labels: Record<string, string> = {
      cache: '缓存',
      booking_reference: 'Booking 参考',
      machine: '机器翻译',
      ai_enhanced: 'AI 增强',
    }
    return labels[source] || source
  }

  const handleEvaluateQuality = async () => {
    if (!sourceText.trim() || !translatedText.trim()) {
      toast({ title: '请先进行翻译', variant: 'error' })
      return
    }
    setIsEvaluating(true)
    try {
      const result = await evaluateQualityMutation.mutateAsync({
        sourceText,
        translatedText,
        sourceLang,
        targetLang,
      })
      // result contains {scores, issues, suggestions, reference_matches}
      setQualityScores(result.scores)
      setShowQuality(true)
    } catch {
      toast({ title: '质量评估失败', variant: 'error' })
    } finally {
      setIsEvaluating(false)
    }
  }

  const highlightedSourceText = useMemo(() => {
    if (!sourceText || glossaryTerms.length === 0) return sourceText
    let text = sourceText
    glossaryTerms.forEach((term: { term: string; translation: string }) => {
      const regex = new RegExp(term.term, 'gi')
      text = text.replace(regex, `**${term.term}**`)
    })
    return text
  }, [sourceText, glossaryTerms])

  const handleBatchTranslate = async () => {
    const texts = batchTexts.filter((t) => t.trim())
    if (texts.length === 0) {
      toast({ title: '请输入要翻译的文本', variant: 'error' })
      return
    }
    try {
      const result = await batchTranslateMutation.mutateAsync({
        texts,
        sourceLang,
        targetLang,
      })
      setBatchResults(result.translations || result.results || [])
    } catch {
      toast({ title: '批量翻译失败', variant: 'error' })
    }
  }

  const handleSwap = () => {
    setSourceLang(targetLang)
    setTargetLang(sourceLang)
    setSourceText(translatedText)
    setTranslatedText(sourceText)
  }

  const langOptions = [
    { label: '简体中文', value: 'zh' },
    { label: '繁体中文', value: 'zh-TW' },
    { label: '英语', value: 'en' },
    { label: '日语', value: 'ja' },
    { label: '韩语', value: 'ko' },
  ]

  return (
    <PageLayout>
      <Toaster />
      <Card title="翻译工具" style={{ marginBottom: 24 }}>
        <div className="flex flex-col gap-4">
          <div className="flex flex-wrap gap-4 items-center">
            <select
              value={sourceLang}
              onChange={(e) => setSourceLang(e.target.value)}
              className="h-10 w-44 rounded-md border border-gray-200 px-3 text-sm"
            >
              {langOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            <Button variant="outline" onClick={handleSwap}>交换</Button>
            <select
              value={targetLang}
              onChange={(e) => setTargetLang(e.target.value)}
              className="h-10 w-44 rounded-md border border-gray-200 px-3 text-sm"
            >
              {langOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            <div className="flex items-center gap-2 ml-auto">
              <span className="text-sm text-gray-600">AI 增强</span>
              <Switch checked={useAiEnhance} onCheckedChange={setUseAiEnhance} />
            </div>
          </div>
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="text-sm font-medium text-woye mb-2 block">源文本</label>
              <div className="relative">
                <textarea
                  value={sourceText}
                  onChange={(e) => setSourceText(e.target.value)}
                  rows={6}
                  placeholder="输入要翻译的文本..."
                  className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm resize-none"
                />
                {glossaryTerms.length > 0 && sourceText && (
                  <div className="mt-2 p-2 bg-amber-50 rounded border border-amber-200 text-xs">
                    <span className="text-amber-800 font-medium">术语高亮:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {glossaryTerms
                        .filter((t: { term: string }) => sourceText.toLowerCase().includes(t.term.toLowerCase()))
                        .slice(0, 5)
                        .map((term: { id: number; term: string; translation: string }) => (
                          <Badge key={term.id} variant="outline" className="text-xs bg-amber-100">
                            {term.term} → {term.translation}
                          </Badge>
                        ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
            <div className="flex-1">
              <label className="text-sm font-medium text-woye mb-2 block">翻译结果</label>
              <textarea
                value={translatedText}
                onChange={(e) => setTranslatedText(e.target.value)}
                rows={6}
                placeholder="翻译结果将显示在这里..."
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm resize-none"
              />
            </div>
          </div>
          <div className="flex gap-3">
            <Button
              onClick={handleTranslate}
              loading={translateMutation.isPending}
              size="lg"
            >
              翻译
            </Button>
            <Button
              variant="outline"
              onClick={handleEvaluateQuality}
              loading={isEvaluating}
              disabled={!translatedText.trim()}
            >
              质量评估
            </Button>
          </div>
          {/* 翻译来源和参考信息 */}
          {(translationSource || referenceInfo) && (
            <div className="flex flex-wrap gap-4 items-start text-sm text-gray-600 p-3 bg-gray-50 rounded">
              {translationSource && (
                <div className="flex items-center gap-2">
                  <span className="text-gray-500">翻译来源:</span>
                  <Badge variant="outline">{translationSource}</Badge>
                </div>
              )}
              {referenceInfo?.booking && (
                <div className="flex items-center gap-2">
                  <span className="text-gray-500">Booking:</span>
                  <span className="text-blue-600">{referenceInfo.booking}</span>
                </div>
              )}
              {referenceInfo?.ctrip && (
                <div className="flex items-center gap-2">
                  <span className="text-gray-500">携程:</span>
                  <span className="text-green-600">{referenceInfo.ctrip}</span>
                </div>
              )}
            </div>
          )}
          {showQuality && qualityScores && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
              <h4 className="text-sm font-medium text-woye mb-3">翻译质量评估</h4>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">{qualityScores.accuracy.toFixed(2)}%</div>
                  <div className="text-xs text-gray-500">准确度</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">{qualityScores.professionalism.toFixed(2)}%</div>
                  <div className="text-xs text-gray-500">专业性</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">{qualityScores.localization.toFixed(2)}%</div>
                  <div className="text-xs text-gray-500">本地化</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">{qualityScores.completeness.toFixed(2)}%</div>
                  <div className="text-xs text-gray-500">完整性</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">{qualityScores.booking_match_rate.toFixed(2)}%</div>
                  <div className="text-xs text-gray-500">Booking 匹配率</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-woye">{qualityScores.overall.toFixed(2)}%</div>
                  <div className="text-xs text-gray-500">综合评分</div>
                </div>
              </div>
            </div>
          )}
        </div>
      </Card>

      <Card title="批量翻译">
        <div className="flex flex-col gap-4">
          <div>
            <label className="text-sm font-medium text-woye mb-2 block">源文本 (每行一条)</label>
            <textarea
              value={batchTexts.join('\n')}
              onChange={(e) => setBatchTexts(e.target.value.split('\n'))}
              rows={8}
              placeholder="输入多行文本进行翻译..."
              className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm resize-none"
            />
          </div>
          <Button
            onClick={handleBatchTranslate}
            loading={batchTranslateMutation.isPending}
          >
            全部翻译
          </Button>
          {batchResults.length > 0 && (
            <>
              <hr className="border-gray-200" />
              <div>
                <label className="text-sm font-medium text-woye mb-2 block">翻译结果</label>
                <textarea
                  value={batchResults.join('\n')}
                  rows={8}
                  readOnly
                  className="w-full rounded-md border border-gray-200 bg-gray-50 px-3 py-2 text-sm resize-none"
                />
              </div>
            </>
          )}
        </div>
      </Card>
    </PageLayout>
  )
}