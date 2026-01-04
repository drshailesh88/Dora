"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  FileText,
  ClipboardList,
  Send,
  Award,
  Scissors,
  BookOpen,
  Mic,
  Download,
  CheckCircle
} from "lucide-react";
import Link from "next/link";

/**
 * Clinical Documentation Hub
 *
 * Main page for accessing all clinical documentation features.
 * Doctors hate paperwork - let AI handle it!
 */
export default function DocumentationPage() {
  const documentTypes = [
    {
      title: "SOAP Note",
      description: "Generate structured SOAP format clinical notes from voice or text",
      icon: FileText,
      href: "/documentation/soap",
      color: "text-blue-600",
      bgColor: "bg-blue-50",
    },
    {
      title: "Discharge Summary",
      description: "Create comprehensive discharge summaries with AI assistance",
      icon: ClipboardList,
      href: "/documentation/discharge",
      color: "text-green-600",
      bgColor: "bg-green-50",
    },
    {
      title: "Referral Letter",
      description: "Generate professional referral letters to specialists",
      icon: Send,
      href: "/documentation/referral",
      color: "text-purple-600",
      bgColor: "bg-purple-50",
    },
    {
      title: "Medical Certificate",
      description: "Issue fitness, sick leave, and other certificates",
      icon: Award,
      href: "/documentation/certificate",
      color: "text-orange-600",
      bgColor: "bg-orange-50",
    },
    {
      title: "Operative Note",
      description: "Document surgical procedures from dictation",
      icon: Scissors,
      href: "/documentation/operative",
      color: "text-red-600",
      bgColor: "bg-red-50",
    },
    {
      title: "Templates",
      description: "Manage specialty-specific documentation templates",
      icon: BookOpen,
      href: "/documentation/templates",
      color: "text-indigo-600",
      bgColor: "bg-indigo-50",
    },
  ];

  const features = [
    {
      icon: Mic,
      title: "Voice Dictation",
      description: "Speak naturally, AI converts to structured documentation",
    },
    {
      icon: CheckCircle,
      title: "Auto-Validation",
      description: "Real-time validation ensures completeness and accuracy",
    },
    {
      icon: Download,
      title: "Multiple Formats",
      description: "Export as text, PDF, or push directly to EMR",
    },
  ];

  return (
    <div className="min-h-screen p-8 bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Clinical Documentation
          </h1>
          <p className="text-lg text-gray-600">
            AI-powered documentation. Save time, reduce errors, focus on patients.
          </p>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {features.map((feature, index) => (
            <Card key={index} className="border-2">
              <CardContent className="pt-6">
                <div className="flex items-start space-x-4">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <feature.icon className="h-6 w-6 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Document Types */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {documentTypes.map((docType, index) => (
            <Link key={index} href={docType.href}>
              <Card className="h-full hover:shadow-lg transition-shadow cursor-pointer border-2 hover:border-blue-300">
                <CardHeader>
                  <div className={`inline-flex p-3 rounded-lg ${docType.bgColor} mb-4`}>
                    <docType.icon className={`h-8 w-8 ${docType.color}`} />
                  </div>
                  <CardTitle className="text-xl">{docType.title}</CardTitle>
                  <CardDescription>{docType.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button variant="outline" className="w-full">
                    Create Document
                  </Button>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>

        {/* Quick Stats */}
        <Card className="mt-8 border-2">
          <CardHeader>
            <CardTitle>Documentation Statistics</CardTitle>
            <CardDescription>Your documentation activity</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600">24</div>
                <div className="text-sm text-gray-600">SOAP Notes (This Week)</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">8</div>
                <div className="text-sm text-gray-600">Discharge Summaries</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600">12</div>
                <div className="text-sm text-gray-600">Referral Letters</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-orange-600">15</div>
                <div className="text-sm text-gray-600">Certificates</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Help Section */}
        <Card className="mt-6 border-2 border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="flex items-start space-x-4">
              <div className="p-2 bg-blue-200 rounded-full">
                <BookOpen className="h-6 w-6 text-blue-700" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-1">
                  Need Help?
                </h3>
                <p className="text-sm text-gray-700 mb-3">
                  All documents are generated in draft mode and require your review before signing.
                  Use voice dictation for fastest documentation.
                </p>
                <Button variant="link" className="p-0 h-auto text-blue-700">
                  View Documentation Guide →
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
