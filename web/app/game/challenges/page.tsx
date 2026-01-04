'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

/**
 * Challenges Page
 *
 * Daily, weekly, and monthly challenges.
 */

export default function ChallengesPage() {
  const [challenges, setChallenges] = useState<any>({ daily: [], weekly: [], monthly: [] });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadChallenges();
  }, []);

  const loadChallenges = async () => {
    try {
      const userId = 'current-user-id'; // TODO: Get from auth
      const response = await fetch(`/api/game/challenges?user_id=${userId}`);
      const data = await response.json();

      if (data.success) {
        setChallenges(data.challenges);
      }
    } catch (error) {
      console.error('Failed to load challenges:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderChallenge = (challenge: any) => {
    const progress = (challenge.current_value / challenge.goal_value) * 100;
    const isCompleted = challenge.status === 'completed';

    return (
      <Card key={challenge.id} className={isCompleted ? 'border-2 border-green-500' : ''}>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <span className="text-3xl">{challenge.icon || '🎯'}</span>
              <div>
                <CardTitle>{challenge.challenge_title}</CardTitle>
                <CardDescription className="mt-1">
                  {challenge.goal_value} {challenge.goal_type}
                </CardDescription>
              </div>
            </div>
            {isCompleted && (
              <Badge variant="secondary" className="bg-green-500 text-white">
                ✓ Complete
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {!isCompleted && (
            <>
              <div className="flex justify-between text-sm mb-1">
                <span>Progress</span>
                <span>
                  {challenge.current_value} / {challenge.goal_value}
                </span>
              </div>
              <Progress value={progress} className="h-2 mb-2" />
            </>
          )}
          <div className="flex justify-between items-center mt-4">
            <span className="text-sm font-medium text-primary">
              Reward: +{challenge.xp_earned || 0} XP
            </span>
            {isCompleted && (
              <span className="text-xs text-muted-foreground">
                Completed {new Date(challenge.completed_at).toLocaleDateString()}
              </span>
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return <div className="container mx-auto p-6">Loading challenges...</div>;
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-4xl font-bold mb-2">Challenges</h1>
        <p className="text-muted-foreground">
          Complete challenges to earn bonus XP and unlock achievements
        </p>
      </div>

      {/* Daily Challenges */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <span className="text-2xl">📅</span>
          <h2 className="text-2xl font-bold">Daily Challenges</h2>
          <Badge variant="secondary">Resets in 12h</Badge>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {challenges.daily?.map(renderChallenge) || (
            <Card>
              <CardContent className="text-center py-12 text-muted-foreground">
                <p>No daily challenges available!</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Weekly Challenges */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <span className="text-2xl">📆</span>
          <h2 className="text-2xl font-bold">Weekly Challenges</h2>
          <Badge variant="secondary">Resets Monday</Badge>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {challenges.weekly?.map(renderChallenge) || (
            <Card>
              <CardContent className="text-center py-12 text-muted-foreground">
                <p>No weekly challenges available!</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Monthly Challenges */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <span className="text-2xl">📊</span>
          <h2 className="text-2xl font-bold">Monthly Challenges</h2>
          <Badge variant="secondary">Resets 1st</Badge>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {challenges.monthly?.map(renderChallenge) || (
            <Card>
              <CardContent className="text-center py-12 text-muted-foreground">
                <p>No monthly challenges available!</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
