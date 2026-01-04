"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { ClipboardList, Download, Send, CheckCircle, AlertCircle } from "lucide-react";

/**
 * Discharge Summary Builder
 *
 * Generate comprehensive hospital discharge summaries with AI assistance.
 * Auto-fills from admission data, generates patient-friendly instructions.
 */
export default function DischargeSummaryPage() {
  const [dischargeSummary, setDischargeSummary] = useState<any>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const [formData, setFormData] = useState({
    admission_date: "2026-01-01",
    discharge_date: "2026-01-04",
    chief_complaint: "Chest pain",
    admitting_diagnosis: "Acute coronary syndrome",
    hospital_course: "",
    procedures_performed: [] as string[],
    discharge_medications: [] as any[],
  });

  const handleGenerate = async () => {
    setIsGenerating(true);

    try {
      const response = await fetch("/api/docs/discharge", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          patient: {
            name: "Sample Patient",
            age: 65,
            gender: "Male",
            mrn: "PAT-2024-5678",
          },
          provider: {
            name: "Dr. Current User",
            qualification: "MD",
          },
          admission_data: {
            ...formData,
            final_diagnosis: [
              {
                description: "STEMI - Anterior wall",
                icd10_code: "I21.0",
                is_primary: true,
              },
              {
                description: "Type 2 Diabetes Mellitus",
                icd10_code: "E11.9",
                is_primary: false,
              },
            ],
            admission_department: "Emergency",
            discharge_department: "Cardiology",
            condition_at_discharge: "Improved",
            followup_instructions: "Follow up with cardiologist in 1 week",
          },
          enhance: true,
        }),
      });

      const data = await response.json();
      setDischargeSummary(data);
    } catch (error) {
      console.error("Error generating discharge summary:", error);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen p-8 bg-gradient-to-br from-green-50 via-white to-blue-50">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Discharge Summary Builder
          </h1>
          <p className="text-lg text-gray-600">
            Comprehensive discharge documentation with AI-enhanced instructions
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Form */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Admission Details</CardTitle>
                <CardDescription>Basic admission information</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Admission Date</Label>
                    <Input
                      type="date"
                      value={formData.admission_date}
                      onChange={(e) =>
                        setFormData({ ...formData, admission_date: e.target.value })
                      }
                    />
                  </div>
                  <div>
                    <Label>Discharge Date</Label>
                    <Input
                      type="date"
                      value={formData.discharge_date}
                      onChange={(e) =>
                        setFormData({ ...formData, discharge_date: e.target.value })
                      }
                    />
                  </div>
                </div>

                <div>
                  <Label>Chief Complaint</Label>
                  <Input
                    value={formData.chief_complaint}
                    onChange={(e) =>
                      setFormData({ ...formData, chief_complaint: e.target.value })
                    }
                    placeholder="Why was patient admitted?"
                  />
                </div>

                <div>
                  <Label>Admitting Diagnosis</Label>
                  <Input
                    value={formData.admitting_diagnosis}
                    onChange={(e) =>
                      setFormData({ ...formData, admitting_diagnosis: e.target.value })
                    }
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Hospital Course</CardTitle>
                <CardDescription>
                  Describe what happened during hospital stay
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Textarea
                  value={formData.hospital_course}
                  onChange={(e) =>
                    setFormData({ ...formData, hospital_course: e.target.value })
                  }
                  placeholder="Patient admitted with chest pain, troponin elevated at 0.8 ng/mL. ECG showed ST elevation in V2-V4. Emergent PCI performed with stent placement to LAD..."
                  className="min-h-[200px]"
                />
              </CardContent>
            </Card>

            <Button
              onClick={handleGenerate}
              disabled={isGenerating || !formData.hospital_course}
              className="w-full"
              size="lg"
            >
              <ClipboardList className="mr-2 h-5 w-5" />
              {isGenerating ? "Generating..." : "Generate Discharge Summary"}
            </Button>
          </div>

          {/* Output */}
          <div className="space-y-6">
            {dischargeSummary ? (
              <>
                <Card>
                  <CardHeader>
                    <CardTitle>Discharge Summary</CardTitle>
                    <CardDescription>
                      Review and edit before signing
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="bg-gray-50 p-4 rounded max-h-[500px] overflow-y-auto">
                      <div className="space-y-4">
                        {/* Header */}
                        <div className="border-b pb-2">
                          <h3 className="font-bold text-lg">DISCHARGE SUMMARY</h3>
                          <div className="text-sm mt-2">
                            <p><strong>Patient:</strong> {dischargeSummary.patient.name} ({dischargeSummary.patient.age}/{dischargeSummary.patient.gender[0]})</p>
                            <p><strong>MRN:</strong> {dischargeSummary.patient.mrn}</p>
                            <p><strong>Admission:</strong> {new Date(dischargeSummary.admission_date).toLocaleDateString()}</p>
                            <p><strong>Discharge:</strong> {new Date(dischargeSummary.discharge_date).toLocaleDateString()}</p>
                            <p><strong>Length of Stay:</strong> {dischargeSummary.length_of_stay} days</p>
                          </div>
                        </div>

                        {/* Diagnoses */}
                        <div>
                          <h4 className="font-semibold mb-2">Final Diagnosis:</h4>
                          {dischargeSummary.final_diagnosis?.map((diag: any, idx: number) => (
                            <div key={idx} className="flex items-center justify-between mb-1">
                              <span className="text-sm">
                                {idx + 1}. {diag.description}
                              </span>
                              {diag.icd10_code && (
                                <Badge variant="outline" className="text-xs">
                                  {diag.icd10_code}
                                </Badge>
                              )}
                            </div>
                          ))}
                        </div>

                        {/* Hospital Course */}
                        <div>
                          <h4 className="font-semibold mb-2">Hospital Course:</h4>
                          <p className="text-sm text-gray-700">
                            {dischargeSummary.hospital_course}
                          </p>
                        </div>

                        {/* Discharge Instructions */}
                        {dischargeSummary.discharge_instructions && (
                          <div className="bg-blue-50 p-3 rounded">
                            <h4 className="font-semibold mb-2 flex items-center">
                              <CheckCircle className="h-4 w-4 mr-2 text-blue-600" />
                              Discharge Instructions (AI-Enhanced):
                            </h4>
                            <p className="text-sm text-gray-700">
                              {dischargeSummary.discharge_instructions}
                            </p>
                          </div>
                        )}

                        {/* Warning Signs */}
                        {dischargeSummary.warning_signs && dischargeSummary.warning_signs.length > 0 && (
                          <div className="bg-red-50 p-3 rounded">
                            <h4 className="font-semibold mb-2 flex items-center text-red-700">
                              <AlertCircle className="h-4 w-4 mr-2" />
                              Return to ER if you experience:
                            </h4>
                            <ul className="text-sm space-y-1">
                              {dischargeSummary.warning_signs.map((sign: string, idx: number) => (
                                <li key={idx} className="text-red-700">• {sign}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Follow-up */}
                        <div>
                          <h4 className="font-semibold mb-2">Follow-up:</h4>
                          <p className="text-sm">{dischargeSummary.followup_instructions}</p>
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2">
                      <Button variant="default">
                        <CheckCircle className="mr-2 h-4 w-4" />
                        Sign & Complete
                      </Button>
                      <Button variant="outline">
                        <Download className="mr-2 h-4 w-4" />
                        Export PDF
                      </Button>
                      <Button variant="outline">
                        <Send className="mr-2 h-4 w-4" />
                        Send to Patient
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card className="border-dashed">
                <CardContent className="pt-6 text-center text-gray-500">
                  <ClipboardList className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p>Your discharge summary will appear here</p>
                  <p className="text-sm mt-2">
                    AI will enhance with patient-friendly instructions and warning signs
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
