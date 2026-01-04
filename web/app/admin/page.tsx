"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Users,
  DollarSign,
  TrendingUp,
  Activity,
  UserCheck,
  UserX,
  CreditCard,
  AlertCircle,
} from "lucide-react";

interface PlatformStats {
  total_users: number;
  active_users: number;
  inactive_users: number;
  trial_users: number;
  paid_users: number;
  new_users_today: number;
  new_users_this_week: number;
  new_users_this_month: number;
  total_revenue: number;
  revenue_today: number;
  revenue_this_week: number;
  revenue_this_month: number;
  mrr: number;
  arr: number;
  active_subscriptions: number;
  trial_subscriptions: number;
  cancelled_subscriptions: number;
  failed_payments: number;
  queries_today: number;
  queries_this_week: number;
  queries_this_month: number;
  total_queries: number;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<PlatformStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const response = await fetch("/api/v1/admin/stats", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error("Error fetching stats:", error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 0,
    }).format(amount / 100); // Convert from paise to rupees
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading statistics...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Users</CardTitle>
            <Users className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_users || 0}</div>
            <p className="text-xs text-muted-foreground">
              +{stats?.new_users_this_month || 0} this month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Users</CardTitle>
            <UserCheck className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.active_users || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.inactive_users || 0} inactive
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">MRR</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{formatCurrency(stats?.mrr || 0)}</div>
            <p className="text-xs text-muted-foreground">
              ARR: {formatCurrency(stats?.arr || 0)}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Queries Today</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.queries_today || 0}</div>
            <p className="text-xs text-muted-foreground">
              {stats?.queries_this_month || 0} this month
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Revenue Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-500">
              Revenue Today
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {formatCurrency(stats?.revenue_today || 0)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-500">
              Revenue This Week
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {formatCurrency(stats?.revenue_this_week || 0)}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium text-gray-500">
              Revenue This Month
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {formatCurrency(stats?.revenue_this_month || 0)}
            </div>
            <p className="text-sm text-green-600 flex items-center gap-1 mt-2">
              <TrendingUp className="h-4 w-4" />
              Total: {formatCurrency(stats?.total_revenue || 0)}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Subscription & User Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Subscriptions</CardTitle>
            <CardDescription>Active subscription breakdown</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CreditCard className="h-5 w-5 text-green-600" />
                <span className="font-medium">Active Subscriptions</span>
              </div>
              <span className="text-2xl font-bold">{stats?.active_subscriptions || 0}</span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CreditCard className="h-5 w-5 text-blue-600" />
                <span className="font-medium">Trial Subscriptions</span>
              </div>
              <span className="text-2xl font-bold">{stats?.trial_subscriptions || 0}</span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <UserX className="h-5 w-5 text-gray-600" />
                <span className="font-medium">Cancelled</span>
              </div>
              <span className="text-2xl font-bold">{stats?.cancelled_subscriptions || 0}</span>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5 text-red-600" />
                <span className="font-medium">Failed Payments</span>
              </div>
              <span className="text-2xl font-bold text-red-600">
                {stats?.failed_payments || 0}
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>User Growth</CardTitle>
            <CardDescription>New user registrations</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="font-medium">Today</span>
              <span className="text-2xl font-bold text-green-600">
                +{stats?.new_users_today || 0}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="font-medium">This Week</span>
              <span className="text-2xl font-bold text-green-600">
                +{stats?.new_users_this_week || 0}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="font-medium">This Month</span>
              <span className="text-2xl font-bold text-green-600">
                +{stats?.new_users_this_month || 0}
              </span>
            </div>

            <div className="pt-4 border-t">
              <div className="flex items-center justify-between">
                <span className="font-medium">Paid Users</span>
                <span className="text-2xl font-bold">{stats?.paid_users || 0}</span>
              </div>
              <div className="flex items-center justify-between mt-2">
                <span className="font-medium">Free/Trial Users</span>
                <span className="text-2xl font-bold">{stats?.trial_users || 0}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Usage Stats */}
      <Card>
        <CardHeader>
          <CardTitle>Platform Usage</CardTitle>
          <CardDescription>Query and activity statistics</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Today</p>
              <p className="text-3xl font-bold">{stats?.queries_today || 0}</p>
              <p className="text-sm text-gray-500">queries</p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">This Week</p>
              <p className="text-3xl font-bold">{stats?.queries_this_week || 0}</p>
              <p className="text-sm text-gray-500">queries</p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">This Month</p>
              <p className="text-3xl font-bold">{stats?.queries_this_month || 0}</p>
              <p className="text-sm text-gray-500">queries</p>
            </div>
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">All Time</p>
              <p className="text-3xl font-bold">{stats?.total_queries || 0}</p>
              <p className="text-sm text-gray-500">queries</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
