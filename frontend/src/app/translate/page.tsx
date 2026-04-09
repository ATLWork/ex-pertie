'use client'

import { useState } from 'react'
import { Card, Input, Button, Space, Select, message, Spin, Divider } from 'antd'
import { TranslationOutlined, SwapOutlined } from '@ant-design/icons'
import PageLayout from '@/components/Layout/PageLayout'
import { useTranslate, useBatchTranslate } from '@/hooks/useTranslation'

const { TextArea } = Input

export default function TranslatePage() {
  const [sourceText, setSourceText] = useState('')
  const [translatedText, setTranslatedText] = useState('')
  const [sourceLang, setSourceLang] = useState('zh')
  const [targetLang, setTargetLang] = useState('en')
  const [batchTexts, setBatchTexts] = useState<string[]>([])
  const [batchResults, setBatchResults] = useState<string[]>([])

  const translateMutation = useTranslate()
  const batchTranslateMutation = useBatchTranslate()

  const handleTranslate = async () => {
    if (!sourceText.trim()) {
      message.warning('Please enter text to translate')
      return
    }
    try {
      const result = await translateMutation.mutateAsync({
        text: sourceText,
        sourceLang,
        targetLang,
      })
      setTranslatedText(result.translated_text || result.text || '')
    } catch {
      message.error('Translation failed')
    }
  }

  const handleBatchTranslate = async () => {
    const texts = batchTexts.filter((t) => t.trim())
    if (texts.length === 0) {
      message.warning('Please enter texts to translate')
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
      message.error('Batch translation failed')
    }
  }

  const handleSwap = () => {
    setSourceLang(targetLang)
    setTargetLang(sourceLang)
    setSourceText(translatedText)
    setTranslatedText(sourceText)
  }

  const langOptions = [
    { label: 'Chinese (Simplified)', value: 'zh' },
    { label: 'Chinese (Traditional)', value: 'zh-TW' },
    { label: 'English', value: 'en' },
    { label: 'Japanese', value: 'ja' },
    { label: 'Korean', value: 'ko' },
  ]

  return (
    <PageLayout>
      <Card title="Translation Workbench" style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <Space wrap align="start">
            <Select
              value={sourceLang}
              onChange={setSourceLang}
              options={langOptions}
              style={{ width: 180 }}
            />
            <Button icon={<SwapOutlined />} onClick={handleSwap} />
            <Select
              value={targetLang}
              onChange={setTargetLang}
              options={langOptions}
              style={{ width: 180 }}
            />
          </Space>
          <Space align="start" style={{ width: '100%' }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
                Source Text
              </label>
              <TextArea
                value={sourceText}
                onChange={(e) => setSourceText(e.target.value)}
                rows={6}
                placeholder="Enter text to translate..."
              />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
                Translated Text
              </label>
              <TextArea
                value={translatedText}
                onChange={(e) => setTranslatedText(e.target.value)}
                rows={6}
                placeholder="Translation will appear here..."
              />
            </div>
          </Space>
          <Button
            type="primary"
            icon={<TranslationOutlined />}
            onClick={handleTranslate}
            loading={translateMutation.isPending}
            size="large"
          >
            Translate
          </Button>
        </Space>
      </Card>

      <Card title="Batch Translation">
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
              Source Texts (one per line)
            </label>
            <TextArea
              value={batchTexts.join('\n')}
              onChange={(e) => setBatchTexts(e.target.value.split('\n'))}
              rows={8}
              placeholder="Enter multiple lines of text to translate..."
            />
          </div>
          <Button
            type="primary"
            onClick={handleBatchTranslate}
            loading={batchTranslateMutation.isPending}
          >
            Translate All
          </Button>
          {batchResults.length > 0 && (
            <>
              <Divider />
              <div>
                <label style={{ display: 'block', marginBottom: 8, fontWeight: 500 }}>
                  Results
                </label>
                <TextArea value={batchResults.join('\n')} rows={8} readOnly />
              </div>
            </>
          )}
        </Space>
      </Card>
    </PageLayout>
  )
}
