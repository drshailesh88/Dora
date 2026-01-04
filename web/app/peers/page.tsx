"use client";

import React from "react";
import Link from "next/link";

/**
 * Peer Network Hub
 *
 * Main landing page for the specialist peer network.
 * Doctors can connect with specialist peers for consultations and case discussions.
 */
export default function PeersPage() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Peer Network</h1>
        <p className="text-gray-600">
          Connect with specialist peers for consultations and case discussions
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
        <Link href="/peers/consult">
          <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-6 hover:shadow-lg transition cursor-pointer">
            <div className="text-3xl mb-3">💬</div>
            <h3 className="font-semibold text-lg mb-2">Ask a Specialist</h3>
            <p className="text-sm text-gray-600">
              Get expert consultation on your case
            </p>
          </div>
        </Link>

        <Link href="/peers/specialists">
          <div className="bg-green-50 border-2 border-green-200 rounded-lg p-6 hover:shadow-lg transition cursor-pointer">
            <div className="text-3xl mb-3">👨‍⚕️</div>
            <h3 className="font-semibold text-lg mb-2">Find Specialists</h3>
            <p className="text-sm text-gray-600">
              Browse verified specialists by specialty
            </p>
          </div>
        </Link>

        <Link href="/peers/cases">
          <div className="bg-purple-50 border-2 border-purple-200 rounded-lg p-6 hover:shadow-lg transition cursor-pointer">
            <div className="text-3xl mb-3">📚</div>
            <h3 className="font-semibold text-lg mb-2">Case Library</h3>
            <p className="text-sm text-gray-600">
              Browse interesting cases and discussions
            </p>
          </div>
        </Link>

        <Link href="/peers/profile">
          <div className="bg-orange-50 border-2 border-orange-200 rounded-lg p-6 hover:shadow-lg transition cursor-pointer">
            <div className="text-3xl mb-3">⭐</div>
            <h3 className="font-semibold text-lg mb-2">My Profile</h3>
            <p className="text-sm text-gray-600">
              Manage specialist profile and consultations
            </p>
          </div>
        </Link>
      </div>

      {/* Stats */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Network Stats</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <div className="text-3xl font-bold text-blue-600">1,234</div>
            <div className="text-sm text-gray-600">Verified Specialists</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-green-600">5,678</div>
            <div className="text-sm text-gray-600">Consultations</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-purple-600">892</div>
            <div className="text-sm text-gray-600">Case Discussions</div>
          </div>
          <div>
            <div className="text-3xl font-bold text-orange-600">4.8</div>
            <div className="text-sm text-gray-600">Avg. Rating</div>
          </div>
        </div>
      </div>

      {/* How It Works */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">How It Works</h2>
        <div className="space-y-4">
          <div className="flex items-start">
            <div className="bg-blue-100 rounded-full w-8 h-8 flex items-center justify-center mr-4 flex-shrink-0">
              1
            </div>
            <div>
              <h4 className="font-semibold mb-1">Submit Your Case</h4>
              <p className="text-sm text-gray-600">
                Describe your case with anonymized patient details
              </p>
            </div>
          </div>
          <div className="flex items-start">
            <div className="bg-blue-100 rounded-full w-8 h-8 flex items-center justify-center mr-4 flex-shrink-0">
              2
            </div>
            <div>
              <h4 className="font-semibold mb-1">Get Matched</h4>
              <p className="text-sm text-gray-600">
                We match you with the best specialist for your case
              </p>
            </div>
          </div>
          <div className="flex items-start">
            <div className="bg-blue-100 rounded-full w-8 h-8 flex items-center justify-center mr-4 flex-shrink-0">
              3
            </div>
            <div>
              <h4 className="font-semibold mb-1">Receive Expert Opinion</h4>
              <p className="text-sm text-gray-600">
                Get detailed recommendations from verified specialists
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
