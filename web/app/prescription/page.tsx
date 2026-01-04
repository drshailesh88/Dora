"use client"

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  FileText,
  AlertTriangle,
  CheckCircle,
  DollarSign,
  Send,
  Download,
  Save,
  Sparkles,
  Pill,
  User,
  Stethoscope,
} from 'lucide-react'

interface PrescriptionItem {
  drug_name: string
  strength: string
  dosage_form: string
  frequency: string
  duration_days: number
  quantity: number
  instructions?: string
  confidence_score?: number
}

interface ValidationWarning {
  type: 'error' | 'warning' | 'info'
  message: string
}

interface DrugAlternative {
  alternative_drug: string
  savings_per_month: number
  reason_for_suggestion: string
}

export default function PrescriptionPage() {
  const [doraAnswer, setDoraAnswer] = useState('')
  const [extractedItems, setExtractedItems] = useState<PrescriptionItem[]>([])
  const [validationWarnings, setValidationWarnings] = useState<ValidationWarning[]>([])
  const [alternatives, setAlternatives] = useState<DrugAlternative[]>([])
  const [preview, setPreview] = useState('')
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('extract')

  const handleExtractFromDora = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/prescription/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          answer_text: doraAnswer,
          dora_answer_id: `DORA-${Date.now()}`,
          patient: {
            patient_id: 'PAT-001',
            name: 'Sample Patient',
            age: 45,
            gender: 'M',
            known_allergies: [],
          },
          doctor: {
            doctor_id: 'DOC-001',
            name: 'Dr. Sample',
            qualifications: 'MD, MBBS',
            registration_number: 'REG-001',
          },
          use_llm: false,
        }),
      })

      const data = await response.json()

      if (data.success) {
        setExtractedItems(data.prescription?.items || [])
        setPreview(data.preview || '')

        // Set validation warnings
        const warnings: ValidationWarning[] = []
        if (data.validation?.errors) {
          data.validation.errors.forEach((err: string) => {
            warnings.push({ type: 'error', message: err })
          })
        }
        if (data.validation?.warnings) {
          data.validation.warnings.forEach((warn: string) => {
            warnings.push({ type: 'warning', message: warn })
          })
        }
        setValidationWarnings(warnings)

        setAlternatives(data.alternatives || [])
        setActiveTab('preview')
      }
    } catch (error) {
      console.error('Error extracting prescription:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleDownloadPDF = async () => {
    // PDF download logic
    console.log('Downloading PDF...')
  }

  const handleSendToPharmacy = async () => {
    // Send to pharmacy logic
    console.log('Sending to pharmacy...')
  }

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Prescription Builder</h1>
        <p className="text-muted-foreground">
          One-tap prescription from Dora answers with AI-powered validation
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="extract">
            <Sparkles className="mr-2 h-4 w-4" />
            Extract from Dora
          </TabsTrigger>
          <TabsTrigger value="manual">
            <Pill className="mr-2 h-4 w-4" />
            Manual Entry
          </TabsTrigger>
          <TabsTrigger value="preview">
            <FileText className="mr-2 h-4 w-4" />
            Preview
          </TabsTrigger>
          <TabsTrigger value="alternatives">
            <DollarSign className="mr-2 h-4 w-4" />
            Alternatives
          </TabsTrigger>
        </TabsList>

        {/* Extract from Dora Tab */}
        <TabsContent value="extract" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-purple-500" />
                AI-Powered Prescription Extraction
              </CardTitle>
              <CardDescription>
                Paste Dora's answer and we'll automatically extract prescription items
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="dora-answer">Dora AI Answer</Label>
                <Textarea
                  id="dora-answer"
                  placeholder="Paste Dora's medical recommendation here...&#10;&#10;Example:&#10;1. Tab. Metformin 500mg - 1-0-1 x 30 days (after food)&#10;2. Tab. Amlodipine 5mg - 0-0-1 x 30 days (at bedtime)"
                  rows={8}
                  value={doraAnswer}
                  onChange={(e) => setDoraAnswer(e.target.value)}
                  className="font-mono"
                />
              </div>

              <Button
                onClick={handleExtractFromDora}
                disabled={!doraAnswer || loading}
                className="w-full"
                size="lg"
              >
                {loading ? 'Extracting...' : 'Extract Prescription'}
              </Button>

              {extractedItems.length > 0 && (
                <div className="mt-6 space-y-3">
                  <h3 className="font-semibold text-lg">Extracted Medications ({extractedItems.length})</h3>
                  {extractedItems.map((item, idx) => (
                    <Card key={idx}>
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-semibold">{item.drug_name} {item.strength}</h4>
                            <p className="text-sm text-muted-foreground">
                              {item.frequency} × {item.duration_days} days
                            </p>
                            <p className="text-sm">Qty: {item.quantity} {item.dosage_form}s</p>
                          </div>
                          {item.confidence_score && (
                            <Badge variant={item.confidence_score > 0.8 ? 'default' : 'secondary'}>
                              {Math.round(item.confidence_score * 100)}% confidence
                            </Badge>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Manual Entry Tab */}
        <TabsContent value="manual" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Manual Prescription Entry</CardTitle>
              <CardDescription>Add medications manually or use templates</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-muted-foreground">Manual entry form coming soon...</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Preview Tab */}
        <TabsContent value="preview" className="space-y-4">
          {validationWarnings.length > 0 && (
            <div className="space-y-2">
              {validationWarnings.map((warning, idx) => (
                <Alert
                  key={idx}
                  variant={warning.type === 'error' ? 'destructive' : 'default'}
                >
                  {warning.type === 'error' ? (
                    <AlertTriangle className="h-4 w-4" />
                  ) : (
                    <CheckCircle className="h-4 w-4" />
                  )}
                  <AlertDescription>{warning.message}</AlertDescription>
                </Alert>
              ))}
            </div>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Prescription Preview</CardTitle>
              <CardDescription>Review before signing and sending</CardDescription>
            </CardHeader>
            <CardContent>
              {preview ? (
                <pre className="bg-muted p-4 rounded-lg overflow-x-auto text-sm font-mono">
                  {preview}
                </pre>
              ) : (
                <p className="text-muted-foreground">No prescription to preview. Extract from Dora answer first.</p>
              )}

              {preview && (
                <div className="flex gap-2 mt-4">
                  <Button onClick={handleDownloadPDF} variant="outline">
                    <Download className="mr-2 h-4 w-4" />
                    Download PDF
                  </Button>
                  <Button onClick={handleSendToPharmacy} variant="outline">
                    <Send className="mr-2 h-4 w-4" />
                    Send to Pharmacy
                  </Button>
                  <Button>
                    <Save className="mr-2 h-4 w-4" />
                    Sign & Save
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Alternatives Tab */}
        <TabsContent value="alternatives" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-green-500" />
                Cost-Saving Alternatives
              </CardTitle>
              <CardDescription>
                Generic equivalents and therapeutic alternatives
              </CardDescription>
            </CardHeader>
            <CardContent>
              {alternatives.length > 0 ? (
                <div className="space-y-3">
                  {alternatives.map((alt, idx) => (
                    <Card key={idx}>
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start">
                          <div>
                            <h4 className="font-semibold">{alt.alternative_drug}</h4>
                            <p className="text-sm text-muted-foreground">{alt.reason_for_suggestion}</p>
                          </div>
                          <Badge variant="outline" className="bg-green-50">
                            Save ₹{alt.savings_per_month}/month
                          </Badge>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              ) : (
                <p className="text-muted-foreground">No alternatives available. Extract prescription first.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
