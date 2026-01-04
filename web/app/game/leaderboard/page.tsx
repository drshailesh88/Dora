'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

/**
 * Leaderboard Page
 *
 * Global, specialty, and regional rankings.
 */

export default function LeaderboardPage() {
  const [leaderboard, setLeaderboard] = useState<any>(null);
  const [period, setPeriod] = useState('weekly');
  const [type, setType] = useState('global');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLeaderboard();
  }, [period, type]);

  const loadLeaderboard = async () => {
    try {
      const response = await fetch(
        `/api/game/leaderboard?leaderboard_type=${type}&period=${period}`
      );
      const data = await response.json();

      if (data.success) {
        setLeaderboard(data.leaderboard);
      }
    } catch (error) {
      console.error('Failed to load leaderboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRankMedal = (rank: number) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return rank;
  };

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-4xl font-bold mb-2">Leaderboard</h1>
        <p className="text-muted-foreground">
          Compete with doctors from around the world
        </p>
      </div>

      {/* Period Tabs */}
      <Tabs value={period} onValueChange={setPeriod}>
        <TabsList className="grid grid-cols-4 w-full max-w-md">
          <TabsTrigger value="daily">Daily</TabsTrigger>
          <TabsTrigger value="weekly">Weekly</TabsTrigger>
          <TabsTrigger value="monthly">Monthly</TabsTrigger>
          <TabsTrigger value="all_time">All Time</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Type Tabs */}
      <Tabs value={type} onValueChange={setType}>
        <TabsList className="grid grid-cols-4 w-full max-w-md">
          <TabsTrigger value="global">🌍 Global</TabsTrigger>
          <TabsTrigger value="specialty">🩺 Specialty</TabsTrigger>
          <TabsTrigger value="regional">📍 Regional</TabsTrigger>
          <TabsTrigger value="friends">👥 Friends</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Rankings */}
      <Card>
        <CardHeader>
          <CardTitle>
            {type === 'global' && 'Global'}
            {type === 'specialty' && 'Specialty'}
            {type === 'regional' && 'Regional'}
            {type === 'friends' && 'Friends'} Rankings
          </CardTitle>
          <CardDescription>
            {period === 'daily' && "Today's"}
            {period === 'weekly' && 'This Week\'s'}
            {period === 'monthly' && 'This Month\'s'}
            {period === 'all_time' && 'All-Time'} top performers
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-12">Loading rankings...</div>
          ) : (
            <div className="space-y-2">
              {leaderboard?.rankings?.map((entry: any, index: number) => (
                <div
                  key={entry.user_id}
                  className={`flex items-center justify-between p-4 rounded-lg ${
                    index < 3 ? 'bg-secondary border-2 border-primary' : 'bg-secondary/50'
                  }`}
                >
                  <div className="flex items-center gap-4 flex-1">
                    <div className="text-2xl font-bold w-12 text-center">
                      {getRankMedal(entry.rank)}
                    </div>
                    <Avatar>
                      <AvatarFallback>
                        {entry.display_name?.charAt(0) || 'U'}
                      </AvatarFallback>
                    </Avatar>
                    <div>
                      <div className="font-medium">{entry.display_name || 'Anonymous'}</div>
                      <div className="text-sm text-muted-foreground">
                        Level {entry.level}
                        {entry.specialty && ` • ${entry.specialty}`}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xl font-bold text-primary">
                      {entry.xp?.toLocaleString() || 0} XP
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {entry.badges_count || 0} badges
                    </div>
                  </div>
                </div>
              )) || (
                <div className="text-center py-12 text-muted-foreground">
                  <p>No rankings available yet!</p>
                  <p className="text-sm mt-2">Start learning to appear on the leaderboard</p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
