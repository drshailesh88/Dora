/**
 * Quick References Page
 *
 * Display quick reference cards and pocket guides.
 */

'use client';

import { useState, useEffect } from 'react';

interface QuickReference {
  id: string;
  title: string;
  content: string;
  card_type: string;
}

export default function QuickReferencesPage() {
  const [references, setReferences] = useState<QuickReference[]>([]);
  const [defaultReferences, setDefaultReferences] = useState<any[]>([]);
  const [selectedRef, setSelectedRef] = useState<QuickReference | null>(null);

  useEffect(() => {
    fetchReferences();
  }, []);

  const fetchReferences = async () => {
    try {
      const response = await fetch('/api/v1/protocols/references/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setReferences(data.references || []);
        setDefaultReferences(data.default_references || []);
      }
    } catch (error) {
      console.error('Failed to fetch references:', error);
    }
  };

  const allReferences = [
    ...defaultReferences.map(r => ({ ...r, isDefault: true })),
    ...references.map(r => ({ ...r, isDefault: false })),
  ];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex gap-6">
        {/* Sidebar */}
        <div className="w-80 flex-shrink-0">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">Quick References</h1>

          <div className="space-y-2">
            {allReferences.map((ref) => (
              <button
                key={ref.id}
                onClick={() => setSelectedRef(ref)}
                className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                  selectedRef?.id === ref.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-white hover:bg-gray-50 border border-gray-200'
                }`}
              >
                <div className="font-medium">{ref.title}</div>
                <div className={`text-xs mt-1 ${
                  selectedRef?.id === ref.id ? 'text-blue-100' : 'text-gray-500'
                }`}>
                  {ref.card_type}
                  {ref.isDefault && ' • Default'}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1">
          {selectedRef ? (
            <div className="bg-white rounded-lg shadow p-8">
              <div className="flex justify-between items-start mb-6">
                <h2 className="text-2xl font-bold text-gray-900">{selectedRef.title}</h2>
                <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  🖨️ Print
                </button>
              </div>
              <pre className="font-mono text-sm whitespace-pre-wrap bg-gray-50 p-6 rounded-lg overflow-x-auto">
                {selectedRef.content}
              </pre>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <div className="text-6xl mb-4">📋</div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Select a Reference Card</h2>
              <p className="text-gray-600">
                Choose a quick reference from the sidebar to view it
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
