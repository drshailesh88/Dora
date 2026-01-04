"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Search, Pill, Clock, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";

// Mock data - in production, this would come from the API
const mockHistory = [
  {
    id: 1,
    type: "query",
    question: "What are the first-line treatments for Type 2 Diabetes?",
    timestamp: "2 hours ago",
    confidence: 0.95,
  },
  {
    id: 2,
    type: "drug",
    question: "Drug interaction check: Metformin + Aspirin",
    timestamp: "5 hours ago",
    interactions: 0,
  },
  {
    id: 3,
    type: "query",
    question: "Hypertension management guidelines in elderly patients",
    timestamp: "1 day ago",
    confidence: 0.92,
  },
  {
    id: 4,
    type: "drug",
    question: "Drug interaction check: Warfarin + Ibuprofen",
    timestamp: "1 day ago",
    interactions: 1,
  },
  {
    id: 5,
    type: "query",
    question: "Side effects of ACE inhibitors",
    timestamp: "2 days ago",
    confidence: 0.98,
  },
];

export default function HistoryPage() {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Query History
          </h1>
          <p className="text-gray-500 dark:text-gray-400">
            View your past queries and drug checks
          </p>
        </div>
        <Button variant="outline">Export History</Button>
      </div>

      {/* Stats */}
      <div className="grid md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500">
              Total Queries
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">124</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500">
              Drug Checks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">38</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500">
              This Month
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">24</div>
          </CardContent>
        </Card>
      </div>

      {/* History List */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>
            Your queries and checks from the past 7 days
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {mockHistory.map((item) => (
              <div
                key={item.id}
                className="flex items-start gap-4 p-4 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg border cursor-pointer"
              >
                <div
                  className={`p-2 rounded ${
                    item.type === "query"
                      ? "bg-primary-100"
                      : "bg-green-100"
                  }`}
                >
                  {item.type === "query" ? (
                    <Search className="h-5 w-5 text-primary" />
                  ) : (
                    <Pill className="h-5 w-5 text-green-600" />
                  )}
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-900 dark:text-gray-100">
                    {item.question}
                  </p>
                  <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {item.timestamp}
                    </span>
                    {"confidence" in item && (
                      <span>
                        Confidence: {(item.confidence * 100).toFixed(0)}%
                      </span>
                    )}
                    {"interactions" in item && (
                      <span
                        className={
                          item.interactions > 0
                            ? "text-orange-600"
                            : "text-green-600"
                        }
                      >
                        {item.interactions > 0
                          ? `${item.interactions} interaction(s) found`
                          : "No interactions"}
                      </span>
                    )}
                  </div>
                </div>
                <Button variant="ghost" size="icon">
                  <ExternalLink className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Empty State (shown when no history) */}
      {/* <Card>
        <CardContent className="py-12 text-center">
          <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            No History Yet
          </h3>
          <p className="text-gray-500 mb-4">
            Your query history will appear here once you start using Dora
          </p>
          <Button>Ask Your First Question</Button>
        </CardContent>
      </Card> */}
    </div>
  );
}
