"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { TrendingUp, Users, Activity, Award } from "lucide-react";

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await fetch("/api/v1/admin/analytics", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (error) {
      console.error("Error fetching analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64">Loading analytics...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Top Queries */}
      <Card>
        <CardHeader>
          <CardTitle>Top Queries</CardTitle>
          <CardDescription>Most popular searches on the platform</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {analytics?.top_queries?.slice(0, 10).map((query: any, index: number) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="font-medium">{query.query}</div>
                  <div className="text-sm text-gray-500">
                    {query.count} queries • {query.avg_response_time_ms.toFixed(0)}ms avg
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
                    {(query.success_rate * 100).toFixed(0)}% success
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Specialty Stats */}
      <Card>
        <CardHeader>
          <CardTitle>Usage by Specialty</CardTitle>
          <CardDescription>Medical specialties using the platform</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {analytics?.specialty_stats?.slice(0, 10).map((spec: any, index: number) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Award className="h-5 w-5 text-primary" />
                  <div>
                    <div className="font-medium">{spec.specialty}</div>
                    <div className="text-sm text-gray-500">
                      {spec.user_count} users • {spec.query_count} total queries
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-medium">{spec.avg_queries_per_user.toFixed(1)}</div>
                  <div className="text-xs text-gray-500">avg queries/user</div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* System Health */}
      <Card>
        <CardHeader>
          <CardTitle>System Health</CardTitle>
          <CardDescription>Platform performance metrics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold mb-4">Services Status</h4>
              <div className="space-y-3">
                {Object.entries({
                  API: analytics?.system_health?.api_status,
                  Database: analytics?.system_health?.database_status,
                  "Vector DB": analytics?.system_health?.vector_db_status,
                  LLM: analytics?.system_health?.llm_status,
                  Payment: analytics?.system_health?.payment_status,
                }).map(([service, status]: any) => (
                  <div key={service} className="flex items-center justify-between">
                    <span>{service}</span>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      status === "healthy"
                        ? "bg-green-100 text-green-800"
                        : "bg-red-100 text-red-800"
                    }`}>
                      {status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <h4 className="font-semibold mb-4">Performance</h4>
              <div className="space-y-3">
                <div>
                  <div className="text-sm text-gray-500">Avg Query Latency</div>
                  <div className="text-2xl font-bold">
                    {analytics?.system_health?.avg_query_latency_ms?.toFixed(0)}ms
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">P95 Latency</div>
                  <div className="text-2xl font-bold">
                    {analytics?.system_health?.p95_query_latency_ms?.toFixed(0)}ms
                  </div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">Error Rate</div>
                  <div className="text-2xl font-bold">
                    {analytics?.system_health?.error_rate_percent?.toFixed(2)}%
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Usage Timeline Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>Usage Trends</CardTitle>
          <CardDescription>Daily active users and query volume over time</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            Charts will be rendered here using recharts library
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
