"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { FileText, Upload, Database, BookOpen } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ContentManagement() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Knowledge Base Content</CardTitle>
          <CardDescription>Manage medical documents and knowledge sources</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 border rounded-lg">
              <FileText className="h-12 w-12 text-primary mb-4" />
              <h3 className="font-semibold mb-2">Documents</h3>
              <p className="text-3xl font-bold mb-2">1,247</p>
              <p className="text-sm text-gray-500">Indexed documents</p>
            </div>

            <div className="p-6 border rounded-lg">
              <Database className="h-12 w-12 text-green-600 mb-4" />
              <h3 className="font-semibold mb-2">Chunks</h3>
              <p className="text-3xl font-bold mb-2">23,456</p>
              <p className="text-sm text-gray-500">Vector embeddings</p>
            </div>

            <div className="p-6 border rounded-lg">
              <BookOpen className="h-12 w-12 text-blue-600 mb-4" />
              <h3 className="font-semibold mb-2">Sources</h3>
              <p className="text-3xl font-bold mb-2">42</p>
              <p className="text-sm text-gray-500">Unique sources</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Content Management</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Button className="w-full md:w-auto">
              <Upload className="h-4 w-4 mr-2" />
              Upload Documents
            </Button>
            <div className="text-sm text-gray-500">
              Upload medical textbooks, guidelines, and research papers to expand the knowledge base
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent Documents</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            Document list will appear here
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
