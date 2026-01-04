"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Mic, FileText, Download, Send, CheckCircle, AlertTriangle, Info } from "lucide-react";

/**
 * SOAP Note Builder
 *
 * Generate structured SOAP format clinical notes from voice or text.
 * Supports voice dictation, auto-fill from patient data, and real-time validation.
 */
export default function SOAPNotePage() {
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [soapNote, setSoapNote] = useState<any>(null);
  const [validation, setValidation] = useState<any>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleVoiceInput = () => {
    setIsRecording(!isRecording);
    // TODO: Integrate with voice module
    if (!isRecording) {
      // Start recording
      console.log("Started voice recording");
    } else {
      // Stop recording and transcribe
      console.log("Stopped voice recording");
    }
  };

  const handleGenerate = async () => {
    setIsGenerating(true);

    try {
      const response = await fetch("/api/docs/soap/voice", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          text: transcript,
          patient: {
            name: "Sample Patient",
            age: 45,
            gender: "Male",
            mrn: "PAT-2024-1234",
          },
          provider: {
            name: "Dr. Current User",
            qualification: "MD",
          },
        }),
      });

      const data = await response.json();
      setSoapNote(data);

      // Validate
      const validationResponse = await fetch("/api/docs/validate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          document: data,
          document_type: "soap",
        }),
      });

      const validationData = await validationResponse.json();
      setValidation(validationData);
    } catch (error) {
      console.error("Error generating SOAP note:", error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSign = async () => {
    if (!soapNote || !validation?.is_valid) {
      alert("Please fix validation errors before signing");
      return;
    }

    try {
      const response = await fetch("/api/docs/sign", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          document: soapNote,
          document_type: "soap",
        }),
      });

      const data = await response.json();
      if (data.success) {
        alert("Document signed successfully!");
        setSoapNote({ ...soapNote, status: "signed", signed_at: data.signed_at });
      }
    } catch (error) {
      console.error("Error signing document:", error);
    }
  };

  const handleExport = async (format: string) => {
    try {
      const response = await fetch("/api/docs/format", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          document: soapNote,
          document_type: "soap",
          format: format,
        }),
      });

      if (format === "pdf") {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "soap_note.pdf";
        a.click();
      } else {
        const data = await response.json();
        console.log("Exported:", data);
        // Handle text/json export
      }
    } catch (error) {
      console.error("Error exporting:", error);
    }
  };

  return (
    <div className="min-h-screen p-8 bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">SOAP Note Builder</h1>
            <p className="text-lg text-gray-600">
              Dictate your encounter, AI structures it into perfect SOAP format
            </p>
          </div>
          <Badge variant={soapNote?.status === "signed" ? "default" : "secondary"}>
            {soapNote?.status || "Draft"}
          </Badge>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Input Section */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Voice Input</CardTitle>
                <CardDescription>
                  Dictate your clinical encounter naturally
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Button
                  onClick={handleVoiceInput}
                  variant={isRecording ? "destructive" : "default"}
                  className="w-full"
                  size="lg"
                >
                  <Mic className="mr-2 h-5 w-5" />
                  {isRecording ? "Stop Recording" : "Start Voice Dictation"}
                </Button>

                <div className="relative">
                  <Label htmlFor="transcript">Transcript / Text Input</Label>
                  <Textarea
                    id="transcript"
                    placeholder="Patient presents with chest pain for 2 hours. Pain is substernal, pressure-like, 7/10 severity, radiating to left arm..."
                    value={transcript}
                    onChange={(e) => setTranscript(e.target.value)}
                    className="min-h-[200px] mt-2"
                  />
                </div>

                <Button
                  onClick={handleGenerate}
                  disabled={!transcript || isGenerating}
                  className="w-full"
                >
                  <FileText className="mr-2 h-4 w-4" />
                  {isGenerating ? "Generating..." : "Generate SOAP Note"}
                </Button>
              </CardContent>
            </Card>

            {/* Patient Context */}
            <Card>
              <CardHeader>
                <CardTitle>Patient Context</CardTitle>
                <CardDescription>Auto-filled from EMR</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label>Patient Name</Label>
                  <Input value="Sample Patient" disabled />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Age</Label>
                    <Input value="45" disabled />
                  </div>
                  <div>
                    <Label>Gender</Label>
                    <Input value="Male" disabled />
                  </div>
                </div>
                <div>
                  <Label>Active Diagnoses</Label>
                  <div className="flex flex-wrap gap-2 mt-2">
                    <Badge>HTN</Badge>
                    <Badge>Type 2 DM</Badge>
                    <Badge>Hyperlipidemia</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Output Section */}
          <div className="space-y-6">
            {/* Validation */}
            {validation && (
              <Card className={validation.has_errors ? "border-red-300" : validation.has_warnings ? "border-yellow-300" : "border-green-300"}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>Validation</span>
                    <span className="text-sm font-normal">
                      Completeness: {validation.completeness_score}%
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {validation.has_errors && (
                    <div className="space-y-1">
                      <div className="flex items-center text-red-600 font-semibold">
                        <AlertTriangle className="h-4 w-4 mr-2" />
                        Errors - Must Fix
                      </div>
                      {validation.issues
                        .filter((i: any) => i.level === "error")
                        .map((issue: any, idx: number) => (
                          <div key={idx} className="text-sm text-red-700 ml-6">
                            • {issue.field}: {issue.message}
                          </div>
                        ))}
                    </div>
                  )}

                  {validation.has_warnings && (
                    <div className="space-y-1 mt-2">
                      <div className="flex items-center text-yellow-600 font-semibold">
                        <AlertTriangle className="h-4 w-4 mr-2" />
                        Warnings - Should Review
                      </div>
                      {validation.issues
                        .filter((i: any) => i.level === "warning")
                        .map((issue: any, idx: number) => (
                          <div key={idx} className="text-sm text-yellow-700 ml-6">
                            • {issue.field}: {issue.message}
                          </div>
                        ))}
                    </div>
                  )}

                  {validation.is_valid && !validation.has_warnings && (
                    <div className="flex items-center text-green-600">
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Document is complete and ready to sign
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Generated SOAP Note */}
            {soapNote && (
              <Card>
                <CardHeader>
                  <CardTitle>Generated SOAP Note</CardTitle>
                  <CardDescription>Review and edit as needed</CardDescription>
                </CardHeader>
                <CardContent>
                  <Tabs defaultValue="structured">
                    <TabsList className="grid w-full grid-cols-2">
                      <TabsTrigger value="structured">Structured</TabsTrigger>
                      <TabsTrigger value="preview">Preview</TabsTrigger>
                    </TabsList>

                    <TabsContent value="structured" className="space-y-4 mt-4">
                      <div>
                        <Label>Chief Complaint</Label>
                        <Input value={soapNote.chief_complaint} />
                      </div>

                      <div>
                        <Label>History of Present Illness</Label>
                        <Textarea value={soapNote.history_present_illness} className="min-h-[100px]" />
                      </div>

                      <div>
                        <Label>Assessment</Label>
                        <div className="space-y-1 mt-2">
                          {soapNote.diagnoses?.map((diag: any, idx: number) => (
                            <div key={idx} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                              <span>{diag.description}</span>
                              {diag.icd10_code && <Badge variant="outline">{diag.icd10_code}</Badge>}
                            </div>
                          ))}
                        </div>
                      </div>
                    </TabsContent>

                    <TabsContent value="preview" className="mt-4">
                      <div className="bg-gray-50 p-4 rounded font-mono text-sm whitespace-pre-wrap max-h-[400px] overflow-y-auto">
                        {/* Format as text preview */}
                        CLINICAL NOTE - SOAP FORMAT{"\n"}
                        ============================================{"\n\n"}
                        Patient: {soapNote.patient?.name}{"\n"}
                        Date: {new Date().toLocaleDateString()}{"\n\n"}
                        SUBJECTIVE:{"\n"}
                        Chief Complaint: {soapNote.chief_complaint}{"\n"}
                        HPI: {soapNote.history_present_illness}{"\n\n"}
                        ASSESSMENT:{"\n"}
                        {soapNote.diagnoses?.map((d: any, i: number) =>
                          `${i + 1}. ${d.description}${d.icd10_code ? ` (${d.icd10_code})` : ""}\n`
                        )}
                      </div>
                    </TabsContent>
                  </Tabs>

                  {/* Actions */}
                  <div className="flex gap-2 mt-4">
                    <Button
                      onClick={handleSign}
                      disabled={!validation?.is_valid || soapNote.status === "signed"}
                      variant="default"
                    >
                      <CheckCircle className="mr-2 h-4 w-4" />
                      Sign Document
                    </Button>

                    <Button onClick={() => handleExport("pdf")} variant="outline">
                      <Download className="mr-2 h-4 w-4" />
                      Export PDF
                    </Button>

                    <Button variant="outline">
                      <Send className="mr-2 h-4 w-4" />
                      Push to EMR
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {!soapNote && (
              <Card className="border-dashed">
                <CardContent className="pt-6 text-center text-gray-500">
                  <FileText className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p>Your SOAP note will appear here after generation</p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
