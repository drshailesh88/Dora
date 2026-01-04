"use client";

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Bell, Mail, MessageSquare, Send } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotificationsManagement() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Notification Channels</CardTitle>
          <CardDescription>Configure notification delivery methods</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="p-6 border rounded-lg">
              <Mail className="h-12 w-12 text-primary mb-4" />
              <h3 className="font-semibold mb-2">Email</h3>
              <p className="text-sm text-gray-500 mb-4">Send notifications via email</p>
              <div className="text-xs text-green-600">Active</div>
            </div>

            <div className="p-6 border rounded-lg">
              <MessageSquare className="h-12 w-12 text-green-600 mb-4" />
              <h3 className="font-semibold mb-2">WhatsApp</h3>
              <p className="text-sm text-gray-500 mb-4">Send via WhatsApp Business API</p>
              <div className="text-xs text-green-600">Active</div>
            </div>

            <div className="p-6 border rounded-lg">
              <Send className="h-12 w-12 text-blue-600 mb-4" />
              <h3 className="font-semibold mb-2">SMS</h3>
              <p className="text-sm text-gray-500 mb-4">Send via SMS gateway</p>
              <div className="text-xs text-green-600">Active</div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Notification Templates</CardTitle>
          <CardDescription>Pre-configured message templates</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="p-4 border rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold">Welcome Email</h4>
                <Button size="sm" variant="outline">Edit</Button>
              </div>
              <p className="text-sm text-gray-500">Sent to new users after registration</p>
            </div>

            <div className="p-4 border rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold">Subscription Confirmation</h4>
                <Button size="sm" variant="outline">Edit</Button>
              </div>
              <p className="text-sm text-gray-500">Sent after successful subscription payment</p>
            </div>

            <div className="p-4 border rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold">Payment Failed</h4>
                <Button size="sm" variant="outline">Edit</Button>
              </div>
              <p className="text-sm text-gray-500">Sent when payment fails</p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Send Notification</CardTitle>
          <CardDescription>Broadcast message to users</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            Notification composer will appear here
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
