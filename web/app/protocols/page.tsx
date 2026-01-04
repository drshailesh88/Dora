/**
 * Protocol Library Page
 *
 * Main protocol library interface with search, filters, and protocol list.
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

interface Protocol {
  id: string;
  title: string;
  description: string;
  category: string;
  status: string;
  tags: string[];
  created_by: string;
  created_at: string;
  updated_at: string;
  usage_count: number;
  is_clinic_wide: boolean;
}

export default function ProtocolLibraryPage() {
  const router = useRouter();
  const [protocols, setProtocols] = useState<Protocol[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');

  const categories = [
    'emergency',
    'chronic_care',
    'procedures',
    'medications',
    'diagnostics',
    'post_op',
    'pediatrics',
    'cardiology',
    'neurology',
    'respiratory',
  ];

  const statuses = ['draft', 'review', 'published', 'archived'];

  useEffect(() => {
    fetchProtocols();
  }, [searchTerm, selectedCategory, selectedStatus]);

  const fetchProtocols = async () => {
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (selectedCategory) params.append('category', selectedCategory);
      if (selectedStatus) params.append('status', selectedStatus);

      const response = await fetch(`/api/v1/protocols?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setProtocols(data.protocols);
      }
    } catch (error) {
      console.error('Failed to fetch protocols:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryBadgeColor = (category: string) => {
    const colors: Record<string, string> = {
      emergency: 'bg-red-100 text-red-800',
      chronic_care: 'bg-blue-100 text-blue-800',
      procedures: 'bg-purple-100 text-purple-800',
      medications: 'bg-green-100 text-green-800',
      cardiology: 'bg-pink-100 text-pink-800',
      neurology: 'bg-indigo-100 text-indigo-800',
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  const getStatusBadgeColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: 'bg-gray-100 text-gray-800',
      review: 'bg-yellow-100 text-yellow-800',
      published: 'bg-green-100 text-green-800',
      archived: 'bg-red-100 text-red-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Clinical Protocols</h1>
          <p className="text-gray-600 mt-2">Team-based best practices and clinical guidelines</p>
        </div>
        <div className="flex gap-3">
          <Link
            href="/protocols/references"
            className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            📋 Quick References
          </Link>
          <Link
            href="/protocols/checklists"
            className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            ✅ Checklists
          </Link>
          <Link
            href="/protocols/create"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            + New Protocol
          </Link>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="md:col-span-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search
            </label>
            <input
              type="text"
              placeholder="Search protocols..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Category Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Categories</option>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat.replace(/_/g, ' ').toUpperCase()}
                </option>
              ))}
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Status
            </label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              {statuses.map((stat) => (
                <option key={stat} value={stat}>
                  {stat.toUpperCase()}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Protocol List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading protocols...</p>
        </div>
      ) : protocols.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow">
          <p className="text-gray-600">No protocols found</p>
          <Link
            href="/protocols/create"
            className="mt-4 inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Create Your First Protocol
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {protocols.map((protocol) => (
            <div
              key={protocol.id}
              className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => router.push(`/protocols/${protocol.id}`)}
            >
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 flex-1">
                    {protocol.title}
                  </h3>
                  {protocol.is_clinic_wide && (
                    <span className="ml-2 text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded">
                      CLINIC-WIDE
                    </span>
                  )}
                </div>

                <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                  {protocol.description}
                </p>

                <div className="flex flex-wrap gap-2 mb-4">
                  <span className={`text-xs px-2 py-1 rounded ${getCategoryBadgeColor(protocol.category)}`}>
                    {protocol.category.replace(/_/g, ' ')}
                  </span>
                  <span className={`text-xs px-2 py-1 rounded ${getStatusBadgeColor(protocol.status)}`}>
                    {protocol.status}
                  </span>
                </div>

                {protocol.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mb-4">
                    {protocol.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded"
                      >
                        #{tag}
                      </span>
                    ))}
                    {protocol.tags.length > 3 && (
                      <span className="text-xs text-gray-500">
                        +{protocol.tags.length - 3} more
                      </span>
                    )}
                  </div>
                )}

                <div className="flex items-center justify-between text-sm text-gray-500 pt-4 border-t">
                  <span>📊 {protocol.usage_count} uses</span>
                  <span>{new Date(protocol.updated_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Quick Access Section */}
      <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link
          href="/protocols/references"
          className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-lg hover:shadow-lg transition-shadow"
        >
          <div className="text-3xl mb-3">📋</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Quick References</h3>
          <p className="text-sm text-gray-600">
            One-page reference cards for rapid clinical decision-making
          </p>
        </Link>

        <Link
          href="/protocols/checklists"
          className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-lg hover:shadow-lg transition-shadow"
        >
          <div className="text-3xl mb-3">✅</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Checklists</h3>
          <p className="text-sm text-gray-600">
            Interactive procedural checklists with completion tracking
          </p>
        </Link>

        <Link
          href="/protocols/compliance"
          className="bg-gradient-to-br from-purple-50 to-purple-100 p-6 rounded-lg hover:shadow-lg transition-shadow"
        >
          <div className="text-3xl mb-3">📊</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Compliance Reports</h3>
          <p className="text-sm text-gray-600">
            Track protocol adherence and quality improvement
          </p>
        </Link>
      </div>
    </div>
  );
}
