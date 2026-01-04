'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge as BadgeUI } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';

/**
 * Badges Collection Page
 *
 * Displays all available badges and user's collection progress.
 */

export default function BadgesPage() {
  const [badges, setBadges] = useState<any[]>([]);
  const [earned, setEarned] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');

  useEffect(() => {
    loadBadges();
  }, []);

  const loadBadges = async () => {
    try {
      const userId = 'current-user-id'; // TODO: Get from auth

      const [availableRes, earnedRes] = await Promise.all([
        fetch(`/api/game/badges/available?user_id=${userId}`),
        fetch(`/api/game/badges?user_id=${userId}`),
      ]);

      const availableData = await availableRes.json();
      const earnedData = await earnedRes.json();

      if (availableData.success) setBadges(availableData.badges || []);
      if (earnedData.success) setEarned(earnedData.badges || []);
    } catch (error) {
      console.error('Failed to load badges:', error);
    } finally {
      setLoading(false);
    }
  };

  const categories = [
    { key: 'all', label: 'All Badges', icon: '🏆' },
    { key: 'streak', label: 'Streaks', icon: '🔥' },
    { key: 'query', label: 'Queries', icon: '🎯' },
    { key: 'learning', label: 'Learning', icon: '📚' },
    { key: 'competition', label: 'Competition', icon: '👑' },
    { key: 'community', label: 'Community', icon: '🤝' },
    { key: 'specialty', label: 'Specialty', icon: '💊' },
  ];

  const filteredBadges = selectedCategory === 'all'
    ? badges
    : badges.filter((b: any) => b.badge?.category === selectedCategory);

  const getTierColor = (tier: string) => {
    const colors = {
      bronze: 'bg-amber-700',
      silver: 'bg-gray-400',
      gold: 'bg-yellow-500',
      platinum: 'bg-cyan-500',
      legendary: 'bg-purple-600',
    };
    return colors[tier as keyof typeof colors] || 'bg-gray-500';
  };

  if (loading) {
    return <div className="container mx-auto p-6">Loading badges...</div>;
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold mb-2">Badge Collection</h1>
        <p className="text-muted-foreground">
          {earned.length} / {badges.length} badges earned
        </p>
        <Progress value={(earned.length / badges.length) * 100} className="mt-2" />
      </div>

      {/* Categories */}
      <Tabs value={selectedCategory} onValueChange={setSelectedCategory}>
        <TabsList className="grid grid-cols-7 w-full">
          {categories.map((cat) => (
            <TabsTrigger key={cat.key} value={cat.key}>
              <span className="mr-1">{cat.icon}</span>
              <span className="hidden md:inline">{cat.label}</span>
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {/* Badges Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {filteredBadges.map((badgeData: any) => {
          const badge = badgeData.badge;
          const isEarned = badgeData.is_earned;
          const progress = badgeData.progress_percentage || 0;

          return (
            <Card
              key={badge.id}
              className={`${
                isEarned ? 'border-2 border-primary' : 'opacity-60'
              }`}
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <span className="text-5xl">{badge.icon}</span>
                  <BadgeUI className={getTierColor(badge.tier)}>
                    {badge.tier}
                  </BadgeUI>
                </div>
                <CardTitle className="mt-2">{badge.title}</CardTitle>
                <CardDescription>{badge.description}</CardDescription>
              </CardHeader>
              <CardContent>
                {isEarned ? (
                  <div className="text-center py-2">
                    <BadgeUI variant="secondary" className="text-green-600">
                      ✓ Earned
                    </BadgeUI>
                    {badgeData.earned_at && (
                      <p className="text-xs text-muted-foreground mt-1">
                        {new Date(badgeData.earned_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                ) : (
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span>Progress</span>
                      <span>{Math.round(progress)}%</span>
                    </div>
                    <Progress value={progress} className="h-2" />
                    <p className="text-xs text-muted-foreground mt-1">
                      {badgeData.current_value} / {badge.criteria_value} {badge.criteria_type}
                    </p>
                  </div>
                )}
                <div className="mt-2 text-center">
                  <span className="text-xs font-medium text-primary">
                    +{badge.xp_reward} XP
                  </span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {filteredBadges.length === 0 && (
        <Card>
          <CardContent className="text-center py-12 text-muted-foreground">
            <p>No badges in this category yet!</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
