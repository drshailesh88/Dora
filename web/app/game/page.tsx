'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

/**
 * Gamification Dashboard Page
 *
 * Main hub for all gamification features:
 * - User level and XP progress
 * - Current streak status
 * - Active challenges
 * - Recent badges
 * - Leaderboard position
 * - Available rewards
 */

export default function GameDashboard() {
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      // TODO: Replace with actual user ID from auth
      const userId = 'current-user-id';

      const response = await fetch(`/api/game/profile?user_id=${userId}`);
      const data = await response.json();

      if (data.success) {
        setProfile(data.profile);
      }
    } catch (error) {
      console.error('Failed to load profile:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  const level = profile?.level || { current_level: 1, current_level_name: 'Level 1' };
  const xp = profile?.xp || { total: 0, current_level: 0, to_next_level: 100 };
  const streak = profile?.streak || { current_streak: 0, freeze_tokens: 0, is_at_risk: false };
  const badges = profile?.badges || { total: 0, rare: 0, showcased: [] };
  const rank = profile?.rank || { global: null, percentile: null };

  const xpProgress = xp.to_next_level > 0
    ? (xp.current_level / xp.to_next_level) * 100
    : 0;

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold mb-2">Gamification Dashboard</h1>
        <p className="text-muted-foreground">
          Track your progress, earn rewards, and compete with peers
        </p>
      </div>

      {/* Main Stats Card */}
      <Card className="border-2 border-primary">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span className="text-3xl">{level.tier_icon || '⭐'}</span>
            <span>Level {level.current_level} - {level.current_level_title}</span>
          </CardTitle>
          <CardDescription>
            {xp.current_level.toLocaleString()} / {xp.to_next_level.toLocaleString()} XP
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Progress value={xpProgress} className="h-3" />
            <p className="text-sm text-muted-foreground mt-2">
              {xp.to_next_level - xp.current_level} XP to Level {level.current_level + 1}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Total XP */}
            <div className="text-center p-4 bg-secondary rounded-lg">
              <div className="text-3xl font-bold text-primary">
                {xp.total.toLocaleString()}
              </div>
              <div className="text-sm text-muted-foreground">Total XP</div>
            </div>

            {/* Streak */}
            <div className="text-center p-4 bg-secondary rounded-lg">
              <div className="text-3xl font-bold text-orange-500">
                🔥 {streak.current_streak}
              </div>
              <div className="text-sm text-muted-foreground">
                Day Streak
                {streak.is_at_risk && (
                  <Badge variant="destructive" className="ml-2">At Risk!</Badge>
                )}
              </div>
            </div>

            {/* Global Rank */}
            <div className="text-center p-4 bg-secondary rounded-lg">
              <div className="text-3xl font-bold text-blue-500">
                #{rank.global || '—'}
              </div>
              <div className="text-sm text-muted-foreground">
                Global Rank
                {rank.percentile && ` (Top ${Math.round(100 - rank.percentile)}%)`}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Badges */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Badges Earned</CardTitle>
            <span className="text-2xl">🏆</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{badges.total}</div>
            <p className="text-xs text-muted-foreground">
              {badges.rare} rare badges
            </p>
            <Link href="/game/badges">
              <Button variant="link" className="px-0 mt-2">
                View All →
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* Challenges */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Active Challenges</CardTitle>
            <span className="text-2xl">🎯</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {profile?.challenges?.daily?.length || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Daily challenges active
            </p>
            <Link href="/game/challenges">
              <Button variant="link" className="px-0 mt-2">
                View Challenges →
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* Leaderboard */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Leaderboard</CardTitle>
            <span className="text-2xl">📊</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              #{rank.global || '—'}
            </div>
            <p className="text-xs text-muted-foreground">
              Your global position
            </p>
            <Link href="/game/leaderboard">
              <Button variant="link" className="px-0 mt-2">
                View Rankings →
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* Rewards */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Rewards</CardTitle>
            <span className="text-2xl">🎁</span>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">—</div>
            <p className="text-xs text-muted-foreground">
              Available to redeem
            </p>
            <Link href="/game/rewards">
              <Button variant="link" className="px-0 mt-2">
                Browse Rewards →
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      {/* Showcased Badges */}
      {badges.showcased && badges.showcased.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Showcased Badges</CardTitle>
            <CardDescription>Your proudest achievements</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              {badges.showcased.map((badge: any) => (
                <div
                  key={badge.id}
                  className="flex flex-col items-center p-4 bg-secondary rounded-lg"
                >
                  <span className="text-4xl mb-2">{badge.icon}</span>
                  <span className="text-sm font-medium text-center">
                    {badge.title}
                  </span>
                  <Badge variant="secondary" className="mt-1">
                    {badge.tier}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recent Activity (Placeholder) */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Your latest achievements and progress</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            <p>Start learning to see your recent activities here!</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
