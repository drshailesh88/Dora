/**
 * Clinic Dashboard
 *
 * Main dashboard for clinic/tenant administrators showing:
 * - Team overview
 * - Usage statistics
 * - Recent activity
 * - Quick actions
 */

'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Users, Activity, FileText, Settings } from 'lucide-react';

interface TenantData {
  tenant: {
    id: string;
    name: string;
    plan_id: string;
    status: string;
  };
  members: any[];
  teams: any[];
}

interface UsageData {
  members: {
    total: number;
    by_role: Record<string, number>;
  };
  queries: {
    total: number;
  };
  costs: {
    total_price: number;
    currency: string;
  };
}

export default function ClinicDashboard() {
  const [tenantData, setTenantData] = useState<TenantData | null>(null);
  const [usageData, setUsageData] = useState<UsageData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Get tenant ID from localStorage or context
      const tenantId = localStorage.getItem('tenantId');
      if (!tenantId) {
        console.error('No tenant ID found');
        return;
      }

      // Fetch tenant details
      const tenantRes = await fetch(`/api/tenants/${tenantId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      const tenantResult = await tenantRes.json();

      // Fetch usage analytics
      const usageRes = await fetch(`/api/tenants/${tenantId}/usage`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      const usageResult = await usageRes.json();

      setTenantData(tenantResult);
      setUsageData(usageResult.analytics);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (!tenantData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-gray-600">No organization found</p>
          <Button className="mt-4" onClick={() => window.location.href = '/clinic/create'}>
            Create Organization
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">{tenantData.tenant.name}</h1>
        <p className="text-gray-600 mt-2">Organization Dashboard</p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Members</CardTitle>
            <Users className="h-4 w-4 text-gray-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {usageData?.members.total || 0}
            </div>
            <p className="text-xs text-gray-600 mt-1">
              Active team members
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Queries This Month</CardTitle>
            <Activity className="h-4 w-4 text-gray-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {usageData?.queries.total || 0}
            </div>
            <p className="text-xs text-gray-600 mt-1">
              Total queries across team
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Plan</CardTitle>
            <FileText className="h-4 w-4 text-gray-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">
              {tenantData.tenant.plan_id}
            </div>
            <p className="text-xs text-gray-600 mt-1">
              Current subscription
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Monthly Cost</CardTitle>
            <Settings className="h-4 w-4 text-gray-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ₹{usageData?.costs.total_price.toFixed(2) || '0.00'}
            </div>
            <p className="text-xs text-gray-600 mt-1">
              Current billing cycle
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common administrative tasks</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button
              variant="outline"
              className="h-24 flex flex-col items-center justify-center"
              onClick={() => window.location.href = '/clinic/members'}
            >
              <Users className="h-6 w-6 mb-2" />
              Manage Members
            </Button>
            <Button
              variant="outline"
              className="h-24 flex flex-col items-center justify-center"
              onClick={() => window.location.href = '/clinic/invite'}
            >
              <Users className="h-6 w-6 mb-2" />
              Invite Members
            </Button>
            <Button
              variant="outline"
              className="h-24 flex flex-col items-center justify-center"
              onClick={() => window.location.href = '/clinic/billing'}
            >
              <FileText className="h-6 w-6 mb-2" />
              Billing & Usage
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Team Members */}
      <Card>
        <CardHeader>
          <CardTitle>Team Members</CardTitle>
          <CardDescription>
            Recent members and activity
          </CardDescription>
        </CardHeader>
        <CardContent>
          {tenantData.members && tenantData.members.length > 0 ? (
            <div className="space-y-4">
              {tenantData.members.slice(0, 5).map((member: any) => (
                <div key={member.id} className="flex items-center justify-between py-2 border-b last:border-0">
                  <div>
                    <p className="font-medium">{member.user_id}</p>
                    <p className="text-sm text-gray-600 capitalize">{member.role}</p>
                  </div>
                  <div className="text-sm text-gray-600">
                    Joined {new Date(member.joined_at).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-600 text-center py-4">No members yet</p>
          )}

          <Button
            variant="link"
            className="w-full mt-4"
            onClick={() => window.location.href = '/clinic/members'}
          >
            View all members →
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
