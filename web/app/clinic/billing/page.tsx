/**
 * Clinic Billing Page
 *
 * Displays billing information and usage analytics
 */

'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CreditCard, Users, TrendingUp, AlertCircle } from 'lucide-react';

interface BillingInfo {
  plan: any;
  current_members: number;
  max_members: number;
  overage_members: number;
  base_price: number;
  overage_price: number;
  total_price: number;
  currency: string;
}

export default function BillingPage() {
  const [billing, setBilling] = useState<BillingInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBillingInfo();
  }, []);

  const fetchBillingInfo = async () => {
    try {
      const tenantId = localStorage.getItem('tenantId');
      const token = localStorage.getItem('token');

      const response = await fetch(`/api/tenants/${tenantId}/billing`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      const result = await response.json();
      if (result.success) {
        setBilling(result.billing);
      }
    } catch (error) {
      console.error('Failed to fetch billing info:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (!billing) {
    return <div>Error loading billing information</div>;
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Billing & Usage</h1>
        <p className="text-gray-600 mt-2">Manage your subscription and view usage</p>
      </div>

      {/* Current Plan */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Current Plan</CardTitle>
          <CardDescription>Your active subscription</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-2xl font-bold capitalize">{billing.plan.name || 'Clinic Plan'}</h3>
                <p className="text-gray-600">Monthly subscription</p>
              </div>
              <Badge variant="default">Active</Badge>
            </div>

            <div className="border-t pt-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Base Price</p>
                  <p className="text-2xl font-bold">₹{billing.base_price.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Overage Charges</p>
                  <p className="text-2xl font-bold">₹{billing.overage_price.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Total</p>
                  <p className="text-2xl font-bold text-green-600">₹{billing.total_price.toFixed(2)}</p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Usage Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <Card>
          <CardHeader>
            <CardTitle>Team Members</CardTitle>
            <CardDescription>Current usage and limits</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Users className="h-5 w-5 text-gray-600" />
                  <span>Active Members</span>
                </div>
                <span className="font-bold">{billing.current_members}</span>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-gray-600">Plan Limit</span>
                <span>{billing.max_members === -1 ? 'Unlimited' : billing.max_members}</span>
              </div>

              {billing.overage_members > 0 && (
                <div className="flex items-center justify-between text-orange-600">
                  <div className="flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" />
                    <span>Overage Members</span>
                  </div>
                  <span className="font-bold">{billing.overage_members}</span>
                </div>
              )}

              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-blue-600 h-2.5 rounded-full"
                  style={{
                    width: `${Math.min((billing.current_members / billing.max_members) * 100, 100)}%`
                  }}
                ></div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Payment Method</CardTitle>
            <CardDescription>Manage your payment details</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-4 border rounded-lg">
                <CreditCard className="h-8 w-8 text-gray-600" />
                <div>
                  <p className="font-medium">•••• •••• •••• 4242</p>
                  <p className="text-sm text-gray-600">Expires 12/2025</p>
                </div>
              </div>
              <Button variant="outline" className="w-full">
                Update Payment Method
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Upgrade Options */}
      {billing.overage_members > 0 && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-orange-600" />
              <CardTitle className="text-orange-900">Overage Alert</CardTitle>
            </div>
            <CardDescription className="text-orange-700">
              You have {billing.overage_members} members over your plan limit
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="mb-4 text-orange-900">
              Consider upgrading your plan to avoid overage charges of ₹{billing.overage_price.toFixed(2)}/month.
            </p>
            <Button>Upgrade Plan</Button>
          </CardContent>
        </Card>
      )}

      {/* Invoice History */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle>Invoice History</CardTitle>
          <CardDescription>Past invoices and payments</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-600">
            No invoices yet
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
