/**
 * Protocol Detail/Viewer Page
 *
 * View protocol content with versioning, annotations, and collaboration features.
 */

'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import ReactMarkdown from 'react-markdown';

interface Protocol {
  id: string;
  title: string;
  description: string;
  category: string;
  status: string;
  content: string;
  tags: string[];
  version_number: string;
  evidence_grade?: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  published_at?: string;
  reviewed_by?: string;
  usage_count: number;
}

export default function ProtocolDetailPage() {
  const params = useParams();
  const router = useRouter();
  const protocolId = params.id as string;

  const [protocol, setProtocol] = useState<Protocol | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'content' | 'versions' | 'annotations' | 'compliance'>('content');
  const [showShareModal, setShowShareModal] = useState(false);

  useEffect(() => {
    if (protocolId) {
      fetchProtocol();
    }
  }, [protocolId]);

  const fetchProtocol = async () => {
    try {
      const response = await fetch(`/api/v1/protocols/${protocolId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setProtocol(data);
      } else {
        console.error('Failed to fetch protocol');
      }
    } catch (error) {
      console.error('Error fetching protocol:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRecordUsage = async (followed: boolean) => {
    try {
      await fetch(`/api/v1/protocols/${protocolId}/use`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ followed }),
      });

      // Refresh protocol to update usage count
      fetchProtocol();
    } catch (error) {
      console.error('Failed to record usage:', error);
    }
  };

  const handlePublish = async () => {
    try {
      const response = await fetch(`/api/v1/protocols/${protocolId}/publish`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (response.ok) {
        fetchProtocol();
      }
    } catch (error) {
      console.error('Failed to publish protocol:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!protocol) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center">
          <p className="text-red-600">Protocol not found or access denied</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold text-gray-900">{protocol.title}</h1>
              <span className={`px-3 py-1 rounded text-sm ${
                protocol.status === 'published' ? 'bg-green-100 text-green-800' :
                protocol.status === 'review' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {protocol.status.toUpperCase()}
              </span>
              {protocol.evidence_grade && (
                <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded text-sm font-semibold">
                  Evidence Grade: {protocol.evidence_grade}
                </span>
              )}
            </div>
            <p className="text-gray-600 mb-4">{protocol.description}</p>
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span>Version {protocol.version_number}</span>
              <span>•</span>
              <span>📊 {protocol.usage_count} uses</span>
              <span>•</span>
              <span>Updated {new Date(protocol.updated_at).toLocaleDateString()}</span>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => handleRecordUsage(true)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              ✓ Used Protocol
            </button>
            {protocol.status === 'draft' && (
              <button
                onClick={handlePublish}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Publish
              </button>
            )}
            <button
              onClick={() => setShowShareModal(true)}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Share
            </button>
            <button
              onClick={() => router.push(`/protocols/${protocolId}/edit`)}
              className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Edit
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="border-b">
          <nav className="flex gap-8 px-6">
            {[
              { id: 'content', label: 'Protocol Content' },
              { id: 'versions', label: 'Version History' },
              { id: 'annotations', label: 'Team Comments' },
              { id: 'compliance', label: 'Compliance Metrics' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-4 px-2 border-b-2 font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'border-blue-600 text-blue-600'
                    : 'border-transparent text-gray-600 hover:text-gray-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="p-6">
          {activeTab === 'content' && (
            <div className="prose prose-slate max-w-none">
              <ReactMarkdown>{protocol.content}</ReactMarkdown>
            </div>
          )}

          {activeTab === 'versions' && (
            <div>
              <h3 className="text-lg font-semibold mb-4">Version History</h3>
              <p className="text-gray-600">Version history will be displayed here</p>
            </div>
          )}

          {activeTab === 'annotations' && (
            <div>
              <h3 className="text-lg font-semibold mb-4">Team Comments</h3>
              <p className="text-gray-600">Team annotations will be displayed here</p>
            </div>
          )}

          {activeTab === 'compliance' && (
            <div>
              <h3 className="text-lg font-semibold mb-4">Compliance Metrics</h3>
              <p className="text-gray-600">Compliance data will be displayed here</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
