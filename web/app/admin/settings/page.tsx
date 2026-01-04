"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Settings, Shield, Key, Database, Globe } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Platform Configuration</CardTitle>
          <CardDescription>Core system settings and configuration</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div className="flex items-start gap-4 p-4 border rounded-lg">
              <Settings className="h-6 w-6 text-primary mt-1" />
              <div className="flex-1">
                <h3 className="font-semibold mb-2">General Settings</h3>
                <p className="text-sm text-gray-500 mb-4">
                  Platform name, branding, and basic configuration
                </p>
                <Button size="sm" variant="outline">Configure</Button>
              </div>
            </div>

            <div className="flex items-start gap-4 p-4 border rounded-lg">
              <Shield className="h-6 w-6 text-green-600 mt-1" />
              <div className="flex-1">
                <h3 className="font-semibold mb-2">Security Settings</h3>
                <p className="text-sm text-gray-500 mb-4">
                  Authentication, MFA, and security policies
                </p>
                <Button size="sm" variant="outline">Configure</Button>
              </div>
            </div>

            <div className="flex items-start gap-4 p-4 border rounded-lg">
              <Key className="h-6 w-6 text-blue-600 mt-1" />
              <div className="flex-1">
                <h3 className="font-semibold mb-2">API Keys</h3>
                <p className="text-sm text-gray-500 mb-4">
                  Manage API keys for external services (LLM, payments, etc.)
                </p>
                <Button size="sm" variant="outline">Manage Keys</Button>
              </div>
            </div>

            <div className="flex items-start gap-4 p-4 border rounded-lg">
              <Database className="h-6 w-6 text-purple-600 mt-1" />
              <div className="flex-1">
                <h3 className="font-semibold mb-2">Database Settings</h3>
                <p className="text-sm text-gray-500 mb-4">
                  Database connections and backup configuration
                </p>
                <Button size="sm" variant="outline">Configure</Button>
              </div>
            </div>

            <div className="flex items-start gap-4 p-4 border rounded-lg">
              <Globe className="h-6 w-6 text-orange-600 mt-1" />
              <div className="flex-1">
                <h3 className="font-semibold mb-2">Localization</h3>
                <p className="text-sm text-gray-500 mb-4">
                  Languages, regions, and currency settings
                </p>
                <Button size="sm" variant="outline">Configure</Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Feature Flags</CardTitle>
          <CardDescription>Enable or disable platform features</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 border rounded">
              <div>
                <div className="font-medium">Voice Assistant</div>
                <div className="text-sm text-gray-500">Enable "Hey DocAssist" voice commands</div>
              </div>
              <div className="text-green-600 font-medium">Enabled</div>
            </div>

            <div className="flex items-center justify-between p-3 border rounded">
              <div>
                <div className="font-medium">SSO Authentication</div>
                <div className="text-sm text-gray-500">Allow Google/Microsoft login</div>
              </div>
              <div className="text-green-600 font-medium">Enabled</div>
            </div>

            <div className="flex items-center justify-between p-3 border rounded">
              <div>
                <div className="font-medium">Offline Mode</div>
                <div className="text-sm text-gray-500">Enable offline document access</div>
              </div>
              <div className="text-green-600 font-medium">Enabled</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
