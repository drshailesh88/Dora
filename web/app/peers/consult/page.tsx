"use client";

import React, { useState } from "react";

/**
 * Request Consultation
 *
 * Form to request a consultation with a specialist.
 */
export default function RequestConsultPage() {
  const [formData, setFormData] = useState({
    specialty: "",
    priority: "routine",
    chiefComplaint: "",
    caseSummary: "",
    specificQuestion: "",
    patientAge: "",
    patientGender: "",
    medications: "",
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Consultation requested:", formData);
    // API call would go here
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Request Consultation</h1>
        <p className="text-gray-600">
          Get expert opinion from a verified specialist
        </p>
      </div>

      <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow p-6 space-y-6">
        {/* Specialty */}
        <div>
          <label className="block font-medium mb-2">
            Specialty Needed *
          </label>
          <select
            required
            value={formData.specialty}
            onChange={(e) => setFormData({ ...formData, specialty: e.target.value })}
            className="w-full px-3 py-2 border rounded-lg"
          >
            <option value="">Select specialty</option>
            <option value="cardiology">Cardiology</option>
            <option value="neurology">Neurology</option>
            <option value="pulmonology">Pulmonology</option>
            <option value="gastroenterology">Gastroenterology</option>
            <option value="endocrinology">Endocrinology</option>
          </select>
        </div>

        {/* Priority */}
        <div>
          <label className="block font-medium mb-2">Priority *</label>
          <div className="flex gap-4">
            <label className="flex items-center">
              <input
                type="radio"
                value="routine"
                checked={formData.priority === "routine"}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="mr-2"
              />
              Routine (24-48h)
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="urgent"
                checked={formData.priority === "urgent"}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="mr-2"
              />
              Urgent (4-6h)
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                value="emergency"
                checked={formData.priority === "emergency"}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="mr-2"
              />
              Emergency (&lt;1h)
            </label>
          </div>
        </div>

        {/* Chief Complaint */}
        <div>
          <label className="block font-medium mb-2">
            Chief Complaint * <span className="text-sm text-gray-500">(max 200 chars)</span>
          </label>
          <input
            type="text"
            required
            maxLength={200}
            value={formData.chiefComplaint}
            onChange={(e) => setFormData({ ...formData, chiefComplaint: e.target.value })}
            placeholder="Brief description of the main issue"
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>

        {/* Case Summary */}
        <div>
          <label className="block font-medium mb-2">
            Case Summary * <span className="text-sm text-gray-500">(anonymized)</span>
          </label>
          <textarea
            required
            rows={6}
            value={formData.caseSummary}
            onChange={(e) => setFormData({ ...formData, caseSummary: e.target.value })}
            placeholder="Detailed case presentation with history, examination, investigations..."
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>

        {/* Specific Question */}
        <div>
          <label className="block font-medium mb-2">
            Specific Question *
          </label>
          <textarea
            required
            rows={3}
            value={formData.specificQuestion}
            onChange={(e) => setFormData({ ...formData, specificQuestion: e.target.value })}
            placeholder="What specifically do you need help with?"
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>

        {/* Patient Context */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block font-medium mb-2">Patient Age</label>
            <input
              type="number"
              min="0"
              max="150"
              value={formData.patientAge}
              onChange={(e) => setFormData({ ...formData, patientAge: e.target.value })}
              placeholder="Years"
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="block font-medium mb-2">Patient Gender</label>
            <select
              value={formData.patientGender}
              onChange={(e) => setFormData({ ...formData, patientGender: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg"
            >
              <option value="">Select</option>
              <option value="male">Male</option>
              <option value="female">Female</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>

        {/* Current Medications */}
        <div>
          <label className="block font-medium mb-2">
            Current Medications
          </label>
          <textarea
            rows={3}
            value={formData.medications}
            onChange={(e) => setFormData({ ...formData, medications: e.target.value })}
            placeholder="List of current medications (one per line)"
            className="w-full px-3 py-2 border rounded-lg"
          />
        </div>

        {/* Submit */}
        <div className="flex justify-end gap-4">
          <button
            type="button"
            className="px-6 py-2 border rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Request Consultation
          </button>
        </div>
      </form>
    </div>
  );
}
