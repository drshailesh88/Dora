"use client";

import React, { useState } from "react";

/**
 * Case Library
 *
 * Browse and discuss interesting clinical cases.
 */
export default function CasesPage() {
  const [selectedSpecialty, setSelectedSpecialty] = useState("all");

  // Mock cases data
  const cases = [
    {
      id: "1",
      title: "Takotsubo Cardiomyopathy Mimicking STEMI",
      specialty: "Cardiology",
      category: "Diagnosis",
      author: "Dr. Sharma",
      upvotes: 45,
      comments: 12,
      views: 234,
      isFeatured: true,
    },
    {
      id: "2",
      title: "Atypical Presentation of Guillain-Barré Syndrome",
      specialty: "Neurology",
      category: "Diagnosis",
      author: "Dr. Mehta",
      upvotes: 32,
      comments: 8,
      views: 189,
      isFeatured: false,
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Case Library</h1>
        <p className="text-gray-600">
          Learn from interesting cases shared by the community
        </p>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex gap-4">
          <select
            value={selectedSpecialty}
            onChange={(e) => setSelectedSpecialty(e.target.value)}
            className="px-3 py-2 border rounded-lg"
          >
            <option value="all">All Specialties</option>
            <option value="cardiology">Cardiology</option>
            <option value="neurology">Neurology</option>
            <option value="pulmonology">Pulmonology</option>
          </select>
          <button className="px-4 py-2 border rounded-lg hover:bg-gray-50">
            Featured Only
          </button>
        </div>
        <button className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          Submit Case
        </button>
      </div>

      {/* Cases List */}
      <div className="space-y-4">
        {cases.map((caseItem) => (
          <div
            key={caseItem.id}
            className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition cursor-pointer"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  {caseItem.isFeatured && (
                    <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded">
                      ⭐ Featured
                    </span>
                  )}
                  <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                    {caseItem.specialty}
                  </span>
                  <span className="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded">
                    {caseItem.category}
                  </span>
                </div>

                <h3 className="text-xl font-semibold mb-2">
                  {caseItem.title}
                </h3>

                <div className="text-sm text-gray-600 mb-4">
                  Submitted by {caseItem.author}
                </div>

                <div className="flex gap-6 text-sm text-gray-500">
                  <span>👍 {caseItem.upvotes} upvotes</span>
                  <span>💬 {caseItem.comments} comments</span>
                  <span>👁️ {caseItem.views} views</span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
