"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Flame, Award, BookOpen, TrendingUp, Calendar, Target } from "lucide-react";

interface DashboardData {
  streak: {
    current_streak: number;
    longest_streak: number;
    status: string;
    next_milestone: number;
    freeze_tokens: number;
  };
  cme_credits: {
    total_credits: number;
    annual_requirement: number;
    progress_percentage: number;
    credits_remaining: number;
  };
  achievements: {
    earned: number;
    level: {
      current_level: number;
      total_points: number;
      progress_percentage: number;
      points_needed_for_next: number;
    };
  };
  quiz_performance: {
    total_attempts: number;
    quizzes_passed: number;
    average_score: number;
  };
  analytics: {
    summary: {
      total_activities: number;
      total_time_spent_hours: number;
      total_cme_credits: number;
    };
  };
}

export default function LearningDashboard() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await fetch("/api/learning/dashboard");
      const data = await response.json();
      setDashboard(data);
    } catch (error) {
      console.error("Failed to fetch dashboard:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading your learning dashboard...</p>
        </div>
      </div>
    );
  }

  if (!dashboard) {
    return <div>Failed to load dashboard</div>;
  }

  const streakStatus = dashboard.streak.status;
  const streakColor =
    streakStatus === "active" ? "text-green-500" :
    streakStatus === "at_risk" ? "text-yellow-500" :
    "text-gray-400";

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Learning Dashboard</h1>
        <p className="text-muted-foreground">
          Track your CME credits, streaks, and learning progress
        </p>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {/* Streak Card */}
        <Card className="border-l-4 border-l-orange-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Learning Streak</CardTitle>
            <Flame className={`h-4 w-4 ${streakColor}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboard.streak.current_streak} days</div>
            <p className="text-xs text-muted-foreground">
              Longest: {dashboard.streak.longest_streak} days
            </p>
            <div className="mt-2 flex items-center gap-2">
              <Badge variant={streakStatus === "active" ? "default" : "destructive"}>
                {streakStatus}
              </Badge>
              {dashboard.streak.freeze_tokens > 0 && (
                <Badge variant="outline">
                  {dashboard.streak.freeze_tokens} freeze tokens
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>

        {/* CME Credits Card */}
        <Card className="border-l-4 border-l-blue-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CME Credits</CardTitle>
            <Award className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboard.cme_credits.total_credits.toFixed(1)}</div>
            <p className="text-xs text-muted-foreground">
              of {dashboard.cme_credits.annual_requirement} required
            </p>
            <Progress
              value={dashboard.cme_credits.progress_percentage}
              className="mt-2"
            />
            <p className="text-xs text-muted-foreground mt-1">
              {dashboard.cme_credits.credits_remaining.toFixed(1)} credits remaining
            </p>
          </CardContent>
        </Card>

        {/* Achievements Card */}
        <Card className="border-l-4 border-l-purple-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Achievements</CardTitle>
            <Target className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboard.achievements.earned}</div>
            <p className="text-xs text-muted-foreground">
              Level {dashboard.achievements.level.current_level} • {dashboard.achievements.level.total_points} points
            </p>
            <Progress
              value={dashboard.achievements.level.progress_percentage}
              className="mt-2"
            />
            <p className="text-xs text-muted-foreground mt-1">
              {dashboard.achievements.level.points_needed_for_next} points to next level
            </p>
          </CardContent>
        </Card>

        {/* Quiz Performance Card */}
        <Card className="border-l-4 border-l-green-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Quiz Performance</CardTitle>
            <BookOpen className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {(dashboard.quiz_performance.average_score * 100).toFixed(0)}%
            </div>
            <p className="text-xs text-muted-foreground">
              {dashboard.quiz_performance.quizzes_passed} quizzes passed
            </p>
            <div className="mt-2 text-xs">
              <span className="text-muted-foreground">Total attempts: </span>
              <span className="font-medium">{dashboard.quiz_performance.total_attempts}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Activity Summary */}
      <Card>
        <CardHeader>
          <CardTitle>30-Day Activity Summary</CardTitle>
          <CardDescription>Your learning activity over the past month</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <div className="text-sm font-medium text-muted-foreground">Total Activities</div>
              <div className="text-2xl font-bold mt-1">
                {dashboard.analytics.summary.total_activities}
              </div>
            </div>
            <div>
              <div className="text-sm font-medium text-muted-foreground">Learning Time</div>
              <div className="text-2xl font-bold mt-1">
                {dashboard.analytics.summary.total_time_spent_hours.toFixed(1)}h
              </div>
            </div>
            <div>
              <div className="text-sm font-medium text-muted-foreground">Credits Earned</div>
              <div className="text-2xl font-bold mt-1">
                {dashboard.analytics.summary.total_cme_credits.toFixed(1)}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Button className="h-24" variant="outline" asChild>
          <a href="/learning/quiz" className="flex flex-col items-center justify-center">
            <BookOpen className="h-6 w-6 mb-2" />
            <span>Take a Quiz</span>
          </a>
        </Button>
        <Button className="h-24" variant="outline" asChild>
          <a href="/learning/paths" className="flex flex-col items-center justify-center">
            <TrendingUp className="h-6 w-6 mb-2" />
            <span>Learning Paths</span>
          </a>
        </Button>
        <Button className="h-24" variant="outline" asChild>
          <a href="/learning/certificates" className="flex flex-col items-center justify-center">
            <Award className="h-6 w-6 mb-2" />
            <span>Certificates</span>
          </a>
        </Button>
        <Button className="h-24" variant="outline" asChild>
          <a href="/learning/achievements" className="flex flex-col items-center justify-center">
            <Target className="h-6 w-6 mb-2" />
            <span>Achievements</span>
          </a>
        </Button>
      </div>
    </div>
  );
}
