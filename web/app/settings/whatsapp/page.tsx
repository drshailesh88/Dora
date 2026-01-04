"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { QrCode, Link, MessageSquare, Settings, Smartphone } from "lucide-react";

interface WhatsAppSettings {
  linked: boolean;
  whatsapp_id?: string;
  preferences: {
    language: string;
    preferred_format: string;
    voice_responses: boolean;
    notifications_enabled: boolean;
  };
}

export default function WhatsAppSettingsPage() {
  const [settings, setSettings] = useState<WhatsAppSettings | null>(null);
  const [linkCode, setLinkCode] = useState("");
  const [isLinking, setIsLinking] = useState(false);
  const [showQR, setShowQR] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const response = await fetch("/api/whatsapp/status", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      }
    } catch (error) {
      console.error("Failed to load WhatsApp settings:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleLinkAccount = async () => {
    if (!linkCode || linkCode.length !== 6) {
      alert("Please enter a valid 6-digit code");
      return;
    }

    setIsLinking(true);

    try {
      const response = await fetch("/api/whatsapp/link", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ code: linkCode }),
      });

      const data = await response.json();

      if (data.success) {
        alert("WhatsApp account linked successfully!");
        setLinkCode("");
        loadSettings();
      } else {
        alert(data.message || "Failed to link account");
      }
    } catch (error) {
      console.error("Failed to link account:", error);
      alert("An error occurred. Please try again.");
    } finally {
      setIsLinking(false);
    }
  };

  const handleUnlinkAccount = async () => {
    if (!confirm("Are you sure you want to unlink your WhatsApp account?")) {
      return;
    }

    try {
      const response = await fetch("/api/whatsapp/unlink", {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (response.ok) {
        alert("WhatsApp account unlinked successfully!");
        loadSettings();
      }
    } catch (error) {
      console.error("Failed to unlink account:", error);
      alert("An error occurred. Please try again.");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading WhatsApp settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container max-w-4xl mx-auto py-8 px-4">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">WhatsApp Integration</h1>
        <p className="text-gray-600">
          Connect your WhatsApp to access Dora on the go
        </p>
      </div>

      {/* Link Status Card */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Connection Status
              </CardTitle>
              <CardDescription>
                {settings?.linked
                  ? "Your WhatsApp is connected"
                  : "Link your WhatsApp to use Dora via messaging"}
              </CardDescription>
            </div>
            {settings?.linked ? (
              <Badge variant="default" className="bg-green-500">
                Connected
              </Badge>
            ) : (
              <Badge variant="secondary">Not Connected</Badge>
            )}
          </div>
        </CardHeader>

        <CardContent>
          {settings?.linked ? (
            <div className="space-y-4">
              <div>
                <Label>WhatsApp Number</Label>
                <p className="text-sm text-gray-600 mt-1">
                  {settings.whatsapp_id || "Not available"}
                </p>
              </div>

              <Button
                variant="destructive"
                onClick={handleUnlinkAccount}
                className="w-full sm:w-auto"
              >
                Unlink WhatsApp
              </Button>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="font-semibold mb-2">How to Link:</h3>
                <ol className="list-decimal list-inside space-y-1 text-sm text-gray-700">
                  <li>Open WhatsApp and message: <strong>+1234567890</strong></li>
                  <li>Send: <strong>link</strong></li>
                  <li>You'll receive a 6-digit code</li>
                  <li>Enter the code below</li>
                </ol>
              </div>

              <div className="space-y-4">
                <div>
                  <Label htmlFor="link-code">6-Digit Link Code</Label>
                  <div className="flex gap-2 mt-2">
                    <Input
                      id="link-code"
                      placeholder="000000"
                      value={linkCode}
                      onChange={(e) => setLinkCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                      maxLength={6}
                      className="text-center text-2xl tracking-widest font-mono"
                    />
                    <Button
                      onClick={handleLinkAccount}
                      disabled={isLinking || linkCode.length !== 6}
                      className="whitespace-nowrap"
                    >
                      <Link className="h-4 w-4 mr-2" />
                      {isLinking ? "Linking..." : "Link Account"}
                    </Button>
                  </div>
                </div>

                <Button
                  variant="outline"
                  onClick={() => setShowQR(!showQR)}
                  className="w-full"
                >
                  <QrCode className="h-4 w-4 mr-2" />
                  {showQR ? "Hide" : "Show"} QR Code
                </Button>

                {showQR && (
                  <div className="bg-white p-6 rounded-lg border text-center">
                    <div className="bg-gray-200 h-64 w-64 mx-auto flex items-center justify-center rounded-lg">
                      <p className="text-gray-500">QR Code Placeholder</p>
                      {/* In production, generate actual QR code here */}
                    </div>
                    <p className="text-sm text-gray-600 mt-4">
                      Scan this QR code with your WhatsApp to get started
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Features Card */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Smartphone className="h-5 w-5" />
            WhatsApp Features
          </CardTitle>
          <CardDescription>
            What you can do with WhatsApp
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="flex gap-3">
              <div className="bg-blue-100 p-2 rounded-lg h-fit">
                <MessageSquare className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <h4 className="font-semibold">Medical Queries</h4>
                <p className="text-sm text-gray-600">
                  Ask medical questions via text or voice notes
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <div className="bg-green-100 p-2 rounded-lg h-fit">
                <Settings className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <h4 className="font-semibold">Drug Interactions</h4>
                <p className="text-sm text-gray-600">
                  Quick drug interaction checks
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <div className="bg-purple-100 p-2 rounded-lg h-fit">
                <QrCode className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <h4 className="font-semibold">Share with Patients</h4>
                <p className="text-sm text-gray-600">
                  Send medical information to patients
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <div className="bg-orange-100 p-2 rounded-lg h-fit">
                <Smartphone className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <h4 className="font-semibold">Notifications</h4>
                <p className="text-sm text-gray-600">
                  Get important updates and alerts
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Preferences Card (only shown when linked) */}
      {settings?.linked && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              Preferences
            </CardTitle>
            <CardDescription>
              Customize your WhatsApp experience
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <Label>Voice Responses</Label>
                <p className="text-sm text-gray-600">
                  Receive audio responses to voice notes
                </p>
              </div>
              <Switch
                checked={settings.preferences.voice_responses}
                onCheckedChange={(checked) => {
                  // TODO: Update preference via API
                  console.log("Voice responses:", checked);
                }}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label>Notifications</Label>
                <p className="text-sm text-gray-600">
                  Receive important updates via WhatsApp
                </p>
              </div>
              <Switch
                checked={settings.preferences.notifications_enabled}
                onCheckedChange={(checked) => {
                  // TODO: Update preference via API
                  console.log("Notifications:", checked);
                }}
              />
            </div>

            <div>
              <Label>Response Format</Label>
              <select
                className="mt-2 w-full border rounded-lg px-3 py-2"
                value={settings.preferences.preferred_format}
                onChange={(e) => {
                  // TODO: Update preference via API
                  console.log("Format:", e.target.value);
                }}
              >
                <option value="concise">Concise</option>
                <option value="detailed">Detailed</option>
                <option value="patient_friendly">Patient Friendly</option>
              </select>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
