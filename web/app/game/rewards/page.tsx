'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

/**
 * Rewards Shop Page
 *
 * Browse and redeem rewards using XP points.
 */

export default function RewardsPage() {
  const [rewards, setRewards] = useState<any[]>([]);
  const [myRewards, setMyRewards] = useState<any[]>([]);
  const [userXP, setUserXP] = useState(0);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('shop');

  useEffect(() => {
    loadRewards();
  }, []);

  const loadRewards = async () => {
    try {
      const userId = 'current-user-id'; // TODO: Get from auth

      const [catalogRes, myRewardsRes, profileRes] = await Promise.all([
        fetch(`/api/game/rewards?user_id=${userId}`),
        fetch(`/api/game/rewards/my?user_id=${userId}`),
        fetch(`/api/game/profile?user_id=${userId}`),
      ]);

      const catalogData = await catalogRes.json();
      const myRewardsData = await myRewardsRes.json();
      const profileData = await profileRes.json();

      if (catalogData.success) setRewards(catalogData.rewards || []);
      if (myRewardsData.success) setMyRewards(myRewardsData.rewards || []);
      if (profileData.success) setUserXP(profileData.profile?.xp?.total || 0);
    } catch (error) {
      console.error('Failed to load rewards:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRedeem = async (rewardId: string) => {
    try {
      const userId = 'current-user-id';
      const response = await fetch(`/api/game/rewards/redeem`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, reward_id: rewardId }),
      });

      const data = await response.json();

      if (data.success) {
        alert(`Reward redeemed! Code: ${data.redemption_code}`);
        loadRewards(); // Reload
      } else {
        alert(data.message || 'Failed to redeem reward');
      }
    } catch (error) {
      alert('Error redeeming reward');
    }
  };

  if (loading) {
    return <div className="container mx-auto p-6">Loading rewards...</div>;
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      <div>
        <h1 className="text-4xl font-bold mb-2">Rewards Shop</h1>
        <p className="text-muted-foreground">
          Redeem your XP for exclusive rewards and benefits
        </p>
        <div className="mt-4 p-4 bg-secondary rounded-lg inline-block">
          <span className="text-2xl font-bold text-primary">
            {userXP.toLocaleString()} XP Available
          </span>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="shop">🛍️ Shop</TabsTrigger>
          <TabsTrigger value="my-rewards">🎁 My Rewards</TabsTrigger>
        </TabsList>

        <TabsContent value="shop" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {rewards.map((rewardData: any) => {
              const reward = rewardData.reward;
              const canAfford = rewardData.can_afford;
              const meetsLevel = rewardData.meets_level;
              const isAvailable = rewardData.status === 'available';

              return (
                <Card
                  key={reward.id}
                  className={`${
                    canAfford && meetsLevel
                      ? 'border-2 border-primary'
                      : 'opacity-60'
                  }`}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <span className="text-4xl">{reward.icon || '🎁'}</span>
                      <Badge variant={canAfford ? 'default' : 'secondary'}>
                        {reward.reward_type?.replace('_', ' ')}
                      </Badge>
                    </div>
                    <CardTitle className="mt-2">{reward.title}</CardTitle>
                    <CardDescription>{reward.description}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium">Cost:</span>
                        <span className={`text-lg font-bold ${
                          canAfford ? 'text-primary' : 'text-destructive'
                        }`}>
                          {reward.xp_cost.toLocaleString()} XP
                        </span>
                      </div>

                      {!meetsLevel && (
                        <Badge variant="destructive" className="w-full justify-center">
                          Requires Level {reward.level_required}
                        </Badge>
                      )}

                      {reward.monetary_value && (
                        <div className="text-sm text-muted-foreground text-center">
                          Value: ₹{reward.monetary_value.toLocaleString()}
                        </div>
                      )}

                      <Button
                        className="w-full"
                        disabled={!canAfford || !meetsLevel}
                        onClick={() => handleRedeem(reward.id)}
                      >
                        {canAfford && meetsLevel ? 'Redeem Now' : 'Locked'}
                      </Button>

                      {!canAfford && meetsLevel && (
                        <p className="text-xs text-center text-muted-foreground">
                          Need {rewardData.xp_needed.toLocaleString()} more XP
                        </p>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {rewards.length === 0 && (
            <Card>
              <CardContent className="text-center py-12 text-muted-foreground">
                <p>No rewards available at the moment!</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="my-rewards" className="mt-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {myRewards.map((userReward: any) => (
              <Card key={userReward.id}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span>🎁</span>
                    {userReward.reward_title}
                  </CardTitle>
                  <CardDescription>{userReward.reward_description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="p-4 bg-secondary rounded-lg">
                    <div className="text-sm font-medium mb-1">Redemption Code:</div>
                    <div className="text-xl font-bold font-mono text-primary">
                      {userReward.redemption_code}
                    </div>
                  </div>

                  {userReward.instructions && (
                    <div className="text-sm text-muted-foreground">
                      <strong>Instructions:</strong> {userReward.instructions}
                    </div>
                  )}

                  {userReward.expires_at && (
                    <div className="text-xs text-muted-foreground">
                      Expires: {new Date(userReward.expires_at).toLocaleDateString()}
                    </div>
                  )}

                  <Badge
                    variant={userReward.fulfilled ? 'default' : 'secondary'}
                    className="mt-2"
                  >
                    {userReward.fulfilled ? 'Fulfilled' : 'Pending'}
                  </Badge>
                </CardContent>
              </Card>
            ))}
          </div>

          {myRewards.length === 0 && (
            <Card>
              <CardContent className="text-center py-12 text-muted-foreground">
                <p>You haven't redeemed any rewards yet!</p>
                <p className="text-sm mt-2">Browse the shop to find great deals</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
