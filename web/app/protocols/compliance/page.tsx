/**
 * Compliance Dashboard Page
 *
 * View compliance metrics and reports.
 */

'use client';

import { useState, useEffect } from 'react';

export default function ComplianceDashboardPage() {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [viewType, setViewType] = useState<'user' | 'organization'>('user');

  useEffect(() => {
    fetchReport();
  }, [viewType]);

  const fetchReport = async () => {
    setLoading(true);
    try {
      const endpoint = viewType === 'user'
        ? '/api/v1/protocols/compliance/user'
        : '/api/v1/protocols/compliance/organization';

      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setReport(data);
      }
    } catch (error) {
      console.error('Failed to fetch report:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Compliance Dashboard</h1>
        <p className="text-gray-600">Protocol usage and adherence metrics</p>
      </div>

      {/* View Selector */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex gap-2">
          <button
            onClick={() => setViewType('user')}
            className={`px-6 py-2 rounded-lg font-medium ${
              viewType === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            My Compliance
          </button>
          <button
            onClick={() => setViewType('organization')}
            className={`px-6 py-2 rounded-lg font-medium ${
              viewType === 'organization'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Organization Compliance
          </button>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
        </div>
      ) : report ? (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 mb-1">Total Uses</div>
              <div className="text-3xl font-bold text-gray-900">{report.total_uses || 0}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 mb-1">Compliant Uses</div>
              <div className="text-3xl font-bold text-green-600">{report.compliant_uses || 0}</div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 mb-1">Compliance Rate</div>
              <div className="text-3xl font-bold text-blue-600">
                {Math.round(report.compliance_rate || 0)}%
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <div className="text-sm text-gray-600 mb-1">Protocols Used</div>
              <div className="text-3xl font-bold text-purple-600">
                {report.protocols_used || report.active_protocols || 0}
              </div>
            </div>
          </div>

          {/* Most Used Protocols */}
          {report.most_used_protocols && report.most_used_protocols.length > 0 && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Most Used Protocols</h2>
              <div className="space-y-3">
                {report.most_used_protocols.map((protocol: any, index: number) => (
                  <div key={protocol.protocol_id || index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{protocol.title}</div>
                      <div className="text-sm text-gray-600">
                        {protocol.usage_count} uses
                        {protocol.compliance_rate !== undefined && (
                          <span className="ml-2">
                            • {Math.round(protocol.compliance_rate)}% compliance
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-600">No compliance data available</p>
        </div>
      )}
    </div>
  );
}
