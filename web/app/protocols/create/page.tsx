/**
 * Create Protocol Page
 *
 * Create new protocol from scratch or from template.
 */

'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface Template {
  id: string;
  title: string;
  description: string;
  category: string;
  tags: string[];
}

export default function CreateProtocolPage() {
  const router = useRouter();
  const [mode, setMode] = useState<'blank' | 'template'>('blank');
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'general',
    content: '',
    tags: '',
    is_clinic_wide: false,
  });

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
    'general',
  ];

  useEffect(() => {
    if (mode === 'template') {
      fetchTemplates();
    }
  }, [mode]);

  const fetchTemplates = async () => {
    try {
      const response = await fetch('/api/v1/protocols/templates/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setTemplates(data.templates);
      }
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const response = await fetch('/api/v1/protocols/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          tags: formData.tags.split(',').map(t => t.trim()).filter(Boolean),
        }),
      });

      if (response.ok) {
        const protocol = await response.json();
        router.push(`/protocols/${protocol.id}`);
      } else {
        console.error('Failed to create protocol');
      }
    } catch (error) {
      console.error('Error creating protocol:', error);
    }
  };

  const handleCreateFromTemplate = async () => {
    if (!selectedTemplate) return;

    try {
      const response = await fetch(`/api/v1/protocols/templates/${selectedTemplate}/create`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          template_id: selectedTemplate,
        }),
      });

      if (response.ok) {
        const protocol = await response.json();
        router.push(`/protocols/${protocol.id}`);
      }
    } catch (error) {
      console.error('Failed to create from template:', error);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Create Protocol</h1>

        {/* Mode Selection */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={() => setMode('blank')}
              className={`p-6 border-2 rounded-lg transition-colors ${
                mode === 'blank'
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-4xl mb-3">📝</div>
              <h3 className="text-lg font-semibold mb-2">Start from Blank</h3>
              <p className="text-sm text-gray-600">Create a custom protocol from scratch</p>
            </button>

            <button
              onClick={() => setMode('template')}
              className={`p-6 border-2 rounded-lg transition-colors ${
                mode === 'template'
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="text-4xl mb-3">📋</div>
              <h3 className="text-lg font-semibold mb-2">Use Template</h3>
              <p className="text-sm text-gray-600">Start with a pre-built clinical protocol</p>
            </button>
          </div>
        </div>

        {/* Template Selection */}
        {mode === 'template' && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Choose a Template</h2>
            <div className="grid grid-cols-1 gap-4">
              {templates.map((template) => (
                <div
                  key={template.id}
                  onClick={() => setSelectedTemplate(template.id)}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-colors ${
                    selectedTemplate === template.id
                      ? 'border-blue-600 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <h3 className="font-semibold text-gray-900 mb-1">{template.title}</h3>
                  <p className="text-sm text-gray-600 mb-2">{template.description}</p>
                  <div className="flex gap-2">
                    <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                      {template.category}
                    </span>
                    {template.tags.slice(0, 3).map((tag) => (
                      <span key={tag} className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <button
              onClick={handleCreateFromTemplate}
              disabled={!selectedTemplate}
              className="mt-6 w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              Create from Template
            </button>
          </div>
        )}

        {/* Blank Protocol Form */}
        {mode === 'blank' && (
          <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6">
            <div className="space-y-6">
              {/* Title */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Protocol Title *
                </label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., Acute Myocardial Infarction Management"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Brief description of the protocol..."
                />
              </div>

              {/* Category */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Category *
                </label>
                <select
                  required
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  {categories.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat.replace(/_/g, ' ').toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              {/* Tags */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tags
                </label>
                <input
                  type="text"
                  value={formData.tags}
                  onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Comma-separated tags (e.g., cardiology, emergency, ACS)"
                />
              </div>

              {/* Content */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Protocol Content (Markdown)
                </label>
                <textarea
                  value={formData.content}
                  onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                  rows={20}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  placeholder="# Protocol Title&#10;&#10;## Section 1&#10;&#10;Content here..."
                />
              </div>

              {/* Clinic-wide */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="clinic_wide"
                  checked={formData.is_clinic_wide}
                  onChange={(e) => setFormData({ ...formData, is_clinic_wide: e.target.checked })}
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <label htmlFor="clinic_wide" className="ml-2 block text-sm text-gray-700">
                  Make this protocol clinic-wide (accessible to entire organization)
                </label>
              </div>

              {/* Submit */}
              <div className="flex gap-4">
                <button
                  type="button"
                  onClick={() => router.back()}
                  className="flex-1 px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Create Protocol
                </button>
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
