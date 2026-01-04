/**
 * Checklists Page
 *
 * Display and interact with procedural checklists.
 */

'use client';

import { useState, useEffect } from 'react';

interface ChecklistItem {
  id: string;
  text: string;
  required: boolean;
  order: number;
  section?: string;
}

interface Checklist {
  id: string;
  title: string;
  description: string;
  items: ChecklistItem[];
}

export default function ChecklistsPage() {
  const [checklists, setChecklists] = useState<Checklist[]>([]);
  const [selectedChecklist, setSelectedChecklist] = useState<Checklist | null>(null);
  const [execution, setExecution] = useState<any>(null);
  const [itemStatuses, setItemStatuses] = useState<Record<string, string>>({});

  useEffect(() => {
    fetchChecklists();
  }, []);

  const fetchChecklists = async () => {
    try {
      const response = await fetch('/api/v1/protocols/checklists/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        const all = [...(data.default_checklists || []), ...(data.checklists || [])];
        setChecklists(all);
      }
    } catch (error) {
      console.error('Failed to fetch checklists:', error);
    }
  };

  const startChecklist = async (checklistId: string) => {
    try {
      const response = await fetch(`/api/v1/protocols/checklists/${checklistId}/start`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const exec = await response.json();
        setExecution(exec);
        setItemStatuses({});
      }
    } catch (error) {
      console.error('Failed to start checklist:', error);
    }
  };

  const toggleItem = (itemId: string) => {
    const newStatus = itemStatuses[itemId] === 'completed' ? 'pending' : 'completed';
    setItemStatuses({ ...itemStatuses, [itemId]: newStatus });
  };

  const groupBySection = (items: ChecklistItem[]) => {
    const groups: Record<string, ChecklistItem[]> = {};
    items.forEach(item => {
      const section = item.section || 'General';
      if (!groups[section]) groups[section] = [];
      groups[section].push(item);
    });
    return groups;
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex gap-6">
        {/* Sidebar */}
        <div className="w-80 flex-shrink-0">
          <h1 className="text-2xl font-bold text-gray-900 mb-6">Procedural Checklists</h1>

          <div className="space-y-3">
            {checklists.map((checklist) => (
              <button
                key={checklist.id}
                onClick={() => setSelectedChecklist(checklist)}
                className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                  selectedChecklist?.id === checklist.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-white hover:bg-gray-50 border border-gray-200'
                }`}
              >
                <div className="font-medium">{checklist.title}</div>
                <div className={`text-xs mt-1 ${
                  selectedChecklist?.id === checklist.id ? 'text-blue-100' : 'text-gray-500'
                }`}>
                  {checklist.items.length} items
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1">
          {selectedChecklist ? (
            <div className="bg-white rounded-lg shadow">
              <div className="p-6 border-b">
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  {selectedChecklist.title}
                </h2>
                <p className="text-gray-600 mb-4">{selectedChecklist.description}</p>
                {!execution && (
                  <button
                    onClick={() => startChecklist(selectedChecklist.id)}
                    className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                  >
                    ▶️ Start Checklist
                  </button>
                )}
              </div>

              <div className="p-6">
                {Object.entries(groupBySection(selectedChecklist.items)).map(([section, items]) => (
                  <div key={section} className="mb-8 last:mb-0">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 pb-2 border-b">
                      {section}
                    </h3>
                    <div className="space-y-3">
                      {items.map((item) => (
                        <div
                          key={item.id}
                          className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50"
                        >
                          <input
                            type="checkbox"
                            checked={itemStatuses[item.id] === 'completed'}
                            onChange={() => toggleItem(item.id)}
                            disabled={!execution}
                            className="mt-1 h-5 w-5 text-green-600 focus:ring-green-500 border-gray-300 rounded disabled:opacity-50"
                          />
                          <div className="flex-1">
                            <label
                              className={`cursor-pointer ${
                                itemStatuses[item.id] === 'completed'
                                  ? 'line-through text-gray-400'
                                  : 'text-gray-900'
                              }`}
                            >
                              {item.text}
                              {item.required && (
                                <span className="ml-2 text-red-500 text-sm">*</span>
                              )}
                            </label>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {execution && (
                <div className="p-6 border-t bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm text-gray-600">Completion</div>
                      <div className="text-2xl font-bold text-gray-900">
                        {Math.round((Object.values(itemStatuses).filter(s => s === 'completed').length / selectedChecklist.items.length) * 100)}%
                      </div>
                    </div>
                    <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                      Complete Checklist
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-12 text-center">
              <div className="text-6xl mb-4">✅</div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Select a Checklist</h2>
              <p className="text-gray-600">
                Choose a procedural checklist from the sidebar
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
