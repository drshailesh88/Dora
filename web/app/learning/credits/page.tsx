"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Award, Download, TrendingUp, AlertCircle } from "lucide-react";
import { Progress } from "@/components/ui/progress";

interface CMECredit {
  id: string;
  credits: number;
  category: string;
  activity_title: string;
  activity_type: string;
  specialty: string | null;
  earned_date: string;
  expires_date: string;
  verification_code: string;
}

interface CMECreditsData {
  annual_summary: {
    year: number;
    total_credits: number;
    category_1_credits: number;
    category_2_credits: number;
    category_3_credits: number;
    annual_requirement: number;
    progress_percentage: number;
    credits_remaining: number;
    requirement_met: boolean;
  };
  by_specialty: Record<string, number>;
  expiring_soon: Array<{
    id: string;
    credits: number;
    activity_title: string;
    expires_date: string;
  }>;
}

export default function CMECreditsPage() {
  const [data, setData] = useState<CMECreditsData | null>(null);
  const [history, setHistory] = useState<CMECredit[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCredits();
    fetchHistory();
  }, []);

  const fetchCredits = async () => {
    try {
      const response = await fetch("/api/learning/credits");
      const data = await response.json();
      setData(data);
    } catch (error) {
      console.error("Failed to fetch credits:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async () => {
    try {
      const response = await fetch("/api/learning/credits/history");
      const data = await response.json();
      setHistory(data.credits || []);
    } catch (error) {
      console.error("Failed to fetch history:", error);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
    </div>;
  }

  if (!data) {
    return <div>Failed to load credits</div>;
  }

  const { annual_summary } = data;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">CME Credits</h1>
        <p className="text-muted-foreground">
          Track your Continuing Medical Education credits and meet annual requirements
        </p>
      </div>

      {/* Annual Progress */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Annual Progress ({annual_summary.year})</CardTitle>
              <CardDescription>
                MCI requires {annual_summary.annual_requirement} CME credits per year
              </CardDescription>
            </div>
            {annual_summary.requirement_met && (
              <Badge variant="default" className="bg-green-500">
                <Award className="h-4 w-4 mr-1" />
                Requirement Met
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <div className="flex justify-between mb-2">
              <span className="text-sm font-medium">
                {annual_summary.total_credits.toFixed(1)} / {annual_summary.annual_requirement} credits
              </span>
              <span className="text-sm text-muted-foreground">
                {annual_summary.progress_percentage.toFixed(0)}%
              </span>
            </div>
            <Progress value={annual_summary.progress_percentage} className="h-3" />
            <p className="text-sm text-muted-foreground mt-2">
              {annual_summary.requirement_met
                ? `Congratulations! You've exceeded the requirement by ${(annual_summary.total_credits - annual_summary.annual_requirement).toFixed(1)} credits.`
                : `${annual_summary.credits_remaining.toFixed(1)} credits remaining to meet annual requirement`
              }
            </p>
          </div>

          {/* Category Breakdown */}
          <div className="grid gap-4 md:grid-cols-3 pt-4 border-t">
            <div>
              <div className="text-sm font-medium text-muted-foreground">Category 1</div>
              <div className="text-2xl font-bold mt-1">
                {annual_summary.category_1_credits.toFixed(1)}
              </div>
              <p className="text-xs text-muted-foreground">Formal CME</p>
            </div>
            <div>
              <div className="text-sm font-medium text-muted-foreground">Category 2</div>
              <div className="text-2xl font-bold mt-1">
                {annual_summary.category_2_credits.toFixed(1)}
              </div>
              <p className="text-xs text-muted-foreground">Self-Study</p>
            </div>
            <div>
              <div className="text-sm font-medium text-muted-foreground">Category 3</div>
              <div className="text-2xl font-bold mt-1">
                {annual_summary.category_3_credits.toFixed(1)}
              </div>
              <p className="text-xs text-muted-foreground">Teaching</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Expiring Soon */}
      {data.expiring_soon.length > 0 && (
        <Card className="border-yellow-500">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-yellow-500" />
              <CardTitle>Credits Expiring Soon</CardTitle>
            </div>
            <CardDescription>
              These credits will expire within 90 days
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data.expiring_soon.map((credit) => (
                <div key={credit.id} className="flex justify-between items-center p-3 bg-yellow-50 rounded-lg">
                  <div>
                    <div className="font-medium">{credit.activity_title}</div>
                    <div className="text-sm text-muted-foreground">
                      Expires: {new Date(credit.expires_date).toLocaleDateString()}
                    </div>
                  </div>
                  <Badge variant="outline">{credit.credits} credits</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Credits by Specialty */}
      {Object.keys(data.by_specialty).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Credits by Specialty</CardTitle>
            <CardDescription>Distribution of your CME credits across specialties</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(data.by_specialty)
                .sort(([, a], [, b]) => b - a)
                .map(([specialty, credits]) => (
                  <div key={specialty} className="flex justify-between items-center">
                    <span className="text-sm font-medium capitalize">
                      {specialty.replace(/_/g, " ")}
                    </span>
                    <Badge variant="secondary">{credits.toFixed(1)} credits</Badge>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Credit History */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Credit History</CardTitle>
              <CardDescription>All your earned CME credits</CardDescription>
            </div>
            <Button variant="outline">
              <Download className="h-4 w-4 mr-2" />
              Export Report
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {history.map((credit) => (
              <div key={credit.id} className="border rounded-lg p-4">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <div className="font-medium">{credit.activity_title}</div>
                    <div className="text-sm text-muted-foreground mt-1">
                      {new Date(credit.earned_date).toLocaleDateString()} •{" "}
                      {credit.activity_type.replace(/_/g, " ")}
                      {credit.specialty && ` • ${credit.specialty}`}
                    </div>
                  </div>
                  <Badge variant="default">{credit.credits} credits</Badge>
                </div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>Category: {credit.category.replace(/_/g, " ").toUpperCase()}</span>
                  <span>•</span>
                  <span>Verification: {credit.verification_code}</span>
                  <span>•</span>
                  <span>Expires: {new Date(credit.expires_date).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
