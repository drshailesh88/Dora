"use client";

import { useAuth } from "@/lib/auth-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/navigation";
import { Search, Pill, BookOpen, TrendingUp, Clock } from "lucide-react";

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Dashboard
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          Welcome to your medical knowledge platform
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => router.push("/query")}>
          <CardHeader>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-primary-100 rounded-lg">
                <Search className="h-6 w-6 text-primary" />
              </div>
              <div>
                <CardTitle>Ask a Question</CardTitle>
                <CardDescription>
                  Get instant evidence-based answers
                </CardDescription>
              </div>
            </div>
          </CardHeader>
        </Card>

        <Card className="cursor-pointer hover:shadow-lg transition-shadow" onClick={() => router.push("/drugs")}>
          <CardHeader>
            <div className="flex items-center gap-4">
              <div className="p-3 bg-green-100 rounded-lg">
                <Pill className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <CardTitle>Check Drug Interactions</CardTitle>
                <CardDescription>
                  Verify medication safety
                </CardDescription>
              </div>
            </div>
          </CardHeader>
        </Card>
      </div>

      {/* Stats */}
      <div className="grid md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-500">
              Queries This Week
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">24</div>
            <p className="text-sm text-green-600 flex items-center gap-1 mt-2">
              <TrendingUp className="h-4 w-4" />
              12% from last week
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-500">
              Drug Checks
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">8</div>
            <p className="text-sm text-gray-500 flex items-center gap-1 mt-2">
              <Clock className="h-4 w-4" />
              Last check: 2h ago
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-500">
              Knowledge Base
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">1,247</div>
            <p className="text-sm text-gray-500 flex items-center gap-1 mt-2">
              <BookOpen className="h-4 w-4" />
              Documents indexed
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Your latest queries and checks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-start gap-4 p-3 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg">
              <div className="p-2 bg-primary-100 rounded">
                <Search className="h-4 w-4 text-primary" />
              </div>
              <div className="flex-1">
                <p className="font-medium">Treatment options for Type 2 Diabetes</p>
                <p className="text-sm text-gray-500">2 hours ago</p>
              </div>
            </div>
            <div className="flex items-start gap-4 p-3 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg">
              <div className="p-2 bg-green-100 rounded">
                <Pill className="h-4 w-4 text-green-600" />
              </div>
              <div className="flex-1">
                <p className="font-medium">Drug interaction check: Metformin + Aspirin</p>
                <p className="text-sm text-gray-500">5 hours ago</p>
              </div>
            </div>
            <div className="flex items-start gap-4 p-3 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg">
              <div className="p-2 bg-primary-100 rounded">
                <Search className="h-4 w-4 text-primary" />
              </div>
              <div className="flex-1">
                <p className="font-medium">Hypertension management guidelines</p>
                <p className="text-sm text-gray-500">1 day ago</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Subscription Banner */}
      {user?.license_tier === "free" && (
        <Card className="bg-gradient-to-r from-primary to-primary-600 text-white">
          <CardHeader>
            <CardTitle>Upgrade to Premium</CardTitle>
            <CardDescription className="text-white/80">
              Get unlimited queries, offline access, and advanced features
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button variant="secondary" onClick={() => router.push("/pricing")}>
              View Plans
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
