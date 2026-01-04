"use client";

import React, { useState } from "react";

/**
 * Specialist Profile
 *
 * Manage specialist profile and view consultation history.
 */
export default function ProfilePage() {
  const [activeTab, setActiveTab] = useState("overview");

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold mb-2">Dr. Rajesh Kumar</h1>
            <p className="text-gray-600 mb-4">Cardiology • Mumbai, Maharashtra</p>
            <div className="flex gap-4">
              <span className="bg-yellow-100 text-yellow-800 text-sm px-3 py-1 rounded">
                ⭐⭐⭐ Expert Verified
              </span>
              <span className="bg-green-100 text-green-800 text-sm px-3 py-1 rounded">
                ✓ Accepting Consultations
              </span>
            </div>
          </div>
          <button className="px-6 py-2 border rounded-lg hover:bg-gray-50">
            Edit Profile
          </button>
        </div>

        <div className="grid grid-cols-4 gap-4 mt-6 pt-6 border-t">
          <div>
            <div className="text-2xl font-bold text-blue-600">156</div>
            <div className="text-sm text-gray-600">Consultations</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-600">4.8</div>
            <div className="text-sm text-gray-600">Avg. Rating</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-purple-600">12h</div>
            <div className="text-sm text-gray-600">Avg. Response</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-orange-600">₹78,000</div>
            <div className="text-sm text-gray-600">This Month</div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="border-b">
          <div className="flex gap-6 px-6">
            <button
              onClick={() => setActiveTab("overview")}
              className={`py-4 border-b-2 transition ${
                activeTab === "overview"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-600"
              }`}
            >
              Overview
            </button>
            <button
              onClick={() => setActiveTab("consultations")}
              className={`py-4 border-b-2 transition ${
                activeTab === "consultations"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-600"
              }`}
            >
              Consultations
            </button>
            <button
              onClick={() => setActiveTab("earnings")}
              className={`py-4 border-b-2 transition ${
                activeTab === "earnings"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-600"
              }`}
            >
              Earnings
            </button>
            <button
              onClick={() => setActiveTab("reviews")}
              className={`py-4 border-b-2 transition ${
                activeTab === "reviews"
                  ? "border-blue-600 text-blue-600"
                  : "border-transparent text-gray-600"
              }`}
            >
              Reviews
            </button>
          </div>
        </div>

        <div className="p-6">
          {activeTab === "overview" && (
            <div>
              <h3 className="font-semibold mb-4">Recent Activity</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div>
                    <div className="font-medium">New consultation request</div>
                    <div className="text-sm text-gray-600">
                      Chest pain case • Urgent
                    </div>
                  </div>
                  <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                    View
                  </button>
                </div>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div>
                    <div className="font-medium">Payment received</div>
                    <div className="text-sm text-gray-600">₹500 from consultation #1234</div>
                  </div>
                  <span className="text-green-600 font-semibold">+₹500</span>
                </div>
              </div>
            </div>
          )}

          {activeTab === "consultations" && (
            <div>
              <h3 className="font-semibold mb-4">Active Consultations</h3>
              <p className="text-gray-600">No active consultations</p>
            </div>
          )}

          {activeTab === "earnings" && (
            <div>
              <h3 className="font-semibold mb-4">Earnings Overview</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Pending (in escrow)</span>
                  <span className="font-semibold">₹12,000</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Available for payout</span>
                  <span className="font-semibold text-green-600">₹66,000</span>
                </div>
                <button className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
                  Request Payout
                </button>
              </div>
            </div>
          )}

          {activeTab === "reviews" && (
            <div>
              <h3 className="font-semibold mb-4">Recent Reviews</h3>
              <p className="text-gray-600">No reviews yet</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
