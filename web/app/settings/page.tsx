"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { User, Bell, Shield, CreditCard, Trash2 } from "lucide-react";

export default function SettingsPage() {
  const { user } = useAuth();
  const [formData, setFormData] = useState({
    name: user?.name || "",
    email: user?.email || "",
    specialty: user?.specialty || "",
    institution: user?.institution || "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.id]: e.target.value,
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // In production, call API to update profile
    console.log("Update profile:", formData);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Settings
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          Manage your account and preferences
        </p>
      </div>

      {/* Profile Settings */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <User className="h-5 w-5" />
            <CardTitle>Profile Information</CardTitle>
          </div>
          <CardDescription>
            Update your personal information and preferences
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={handleChange}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                />
              </div>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="specialty">Specialty</Label>
                <Input
                  id="specialty"
                  value={formData.specialty}
                  onChange={handleChange}
                  placeholder="e.g., Cardiology"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="institution">Institution</Label>
                <Input
                  id="institution"
                  value={formData.institution}
                  onChange={handleChange}
                  placeholder="e.g., City Hospital"
                />
              </div>
            </div>
            <div className="flex justify-end">
              <Button type="submit">Save Changes</Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Subscription */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <CreditCard className="h-5 w-5" />
            <CardTitle>Subscription</CardTitle>
          </div>
          <CardDescription>Manage your subscription and billing</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div>
              <p className="font-semibold text-gray-900 dark:text-white">
                {user?.license_tier === "free" ? "Free Tier" : "Premium Plan"}
              </p>
              <p className="text-sm text-gray-500">
                {user?.license_tier === "free"
                  ? "Upgrade to unlock all features"
                  : "Access to all premium features"}
              </p>
            </div>
            <Button variant={user?.license_tier === "free" ? "default" : "outline"}>
              {user?.license_tier === "free" ? "Upgrade" : "Manage"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            <CardTitle>Notifications</CardTitle>
          </div>
          <CardDescription>
            Configure how you receive notifications
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Email Notifications</p>
              <p className="text-sm text-gray-500">
                Receive updates via email
              </p>
            </div>
            <input type="checkbox" className="toggle" defaultChecked />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Query Summaries</p>
              <p className="text-sm text-gray-500">
                Daily summary of your queries
              </p>
            </div>
            <input type="checkbox" className="toggle" />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Feature Updates</p>
              <p className="text-sm text-gray-500">
                Announcements about new features
              </p>
            </div>
            <input type="checkbox" className="toggle" defaultChecked />
          </div>
        </CardContent>
      </Card>

      {/* Security */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            <CardTitle>Security</CardTitle>
          </div>
          <CardDescription>Manage your password and security settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Password</p>
              <p className="text-sm text-gray-500">
                Last changed 30 days ago
              </p>
            </div>
            <Button variant="outline">Change Password</Button>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Two-Factor Authentication</p>
              <p className="text-sm text-gray-500">
                Add an extra layer of security
              </p>
            </div>
            <Button variant="outline">Enable 2FA</Button>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Active Sessions</p>
              <p className="text-sm text-gray-500">
                Manage your active sessions
              </p>
            </div>
            <Button variant="outline">View Sessions</Button>
          </div>
        </CardContent>
      </Card>

      {/* Danger Zone */}
      <Card className="border-red-200">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Trash2 className="h-5 w-5 text-red-600" />
            <CardTitle className="text-red-600">Danger Zone</CardTitle>
          </div>
          <CardDescription>
            Irreversible actions for your account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium text-red-900 dark:text-red-100">
                Delete Account
              </p>
              <p className="text-sm text-gray-500">
                Permanently delete your account and all data
              </p>
            </div>
            <Button variant="destructive">Delete Account</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
