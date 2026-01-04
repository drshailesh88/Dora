"use client";

import React, { useState } from "react";

/**
 * Specialist Directory
 *
 * Browse and search verified specialists by specialty, location, ratings.
 */
export default function SpecialistsPage() {
  const [selectedSpecialty, setSelectedSpecialty] = useState("all");
  const [searchCity, setSearchCity] = useState("");

  const specialties = [
    "All Specialties",
    "Cardiology",
    "Neurology",
    "Pulmonology",
    "Gastroenterology",
    "Endocrinology",
    "Nephrology",
    "Oncology",
    "Orthopedics",
    "Pediatrics",
  ];

  // Mock specialists data
  const specialists = [
    {
      id: "1",
      name: "Dr. Rajesh Kumar",
      specialty: "Cardiology",
      city: "Mumbai",
      rating: 4.8,
      consultations: 156,
      verificationLevel: "expert",
      fee: 500,
      responseTime: "12 hours",
    },
    {
      id: "2",
      name: "Dr. Priya Sharma",
      specialty: "Neurology",
      city: "Delhi",
      rating: 4.9,
      consultations: 203,
      verificationLevel: "certified",
      fee: 600,
      responseTime: "8 hours",
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Find Specialists</h1>
        <p className="text-gray-600">
          Browse verified specialists across all specialties
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Specialty</label>
            <select
              value={selectedSpecialty}
              onChange={(e) => setSelectedSpecialty(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg"
            >
              {specialties.map((s) => (
                <option key={s} value={s.toLowerCase().replace(" ", "_")}>
                  {s}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">City</label>
            <input
              type="text"
              placeholder="Search by city"
              value={searchCity}
              onChange={(e) => setSearchCity(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Rating</label>
            <select className="w-full px-3 py-2 border rounded-lg">
              <option value="0">All Ratings</option>
              <option value="4.5">4.5+ Stars</option>
              <option value="4.0">4.0+ Stars</option>
            </select>
          </div>
        </div>
      </div>

      {/* Specialists List */}
      <div className="space-y-4">
        {specialists.map((specialist) => (
          <div
            key={specialist.id}
            className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center mb-2">
                  <h3 className="text-xl font-semibold mr-3">
                    {specialist.name}
                  </h3>
                  {specialist.verificationLevel === "expert" && (
                    <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded">
                      ⭐⭐⭐ Expert
                    </span>
                  )}
                  {specialist.verificationLevel === "certified" && (
                    <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">
                      ⭐⭐ Certified
                    </span>
                  )}
                </div>
                <div className="text-gray-600 mb-4">
                  {specialist.specialty} • {specialist.city}
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div>
                    <div className="text-sm text-gray-500">Rating</div>
                    <div className="font-semibold">
                      {specialist.rating} ⭐
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Consultations</div>
                    <div className="font-semibold">
                      {specialist.consultations}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Fee</div>
                    <div className="font-semibold">₹{specialist.fee}</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Response Time</div>
                    <div className="font-semibold">
                      {specialist.responseTime}
                    </div>
                  </div>
                </div>
              </div>

              <div className="ml-4">
                <button className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition">
                  Request Consultation
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
