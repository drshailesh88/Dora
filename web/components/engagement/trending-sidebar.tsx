"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { TrendingUp, TrendingDown, Minus, ArrowRight } from "lucide-react";

interface TrendingQuery {
  query: string;
  count: number;
  unique_users: number;
  rank: number;
  trend: string;
  related: string[];
}

export function TrendingSidebar() {
  const [trending, setTrending] = useState<TrendingQuery[]>([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState("last_7d");

  useEffect(() => {
    fetchTrending();
  }, [period]);

  const fetchTrending = async () => {
    try {
      const response = await fetch(
        `/api/v1/engagement/trending?period=${period}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setTrending(data.queries || []);
      }
    } catch (error) {
      console.error("Failed to fetch trending:", error);
    } finally {
      setLoading(false);
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case "rising":
        return <TrendingUp className="h-4 w-4 text-green-600" />;
      case "falling":
        return <TrendingDown className="h-4 w-4 text-red-600" />;
      case "new":
        return <span className="text-xs font-bold text-blue-600">NEW</span>;
      default:
        return <Minus className="h-4 w-4 text-gray-400" />;
    }
  };

  if (loading) {
    return (
      <Card className="p-4">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="h-12 bg-gray-200 rounded"></div>
          <div className="h-12 bg-gray-200 rounded"></div>
          <div className="h-12 bg-gray-200 rounded"></div>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          Trending
        </h3>

        <select
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          className="text-xs border rounded px-2 py-1"
        >
          <option value="last_24h">24h</option>
          <option value="last_7d">7d</option>
          <option value="last_30d">30d</option>
        </select>
      </div>

      <div className="space-y-3">
        {trending.slice(0, 5).map((item, index) => (
          <div
            key={index}
            className="group cursor-pointer hover:bg-gray-50 p-2 rounded-lg transition-colors"
            onClick={() =>
              (window.location.href = `/app/query?q=${encodeURIComponent(
                item.query
              )}`)
            }
          >
            <div className="flex items-start gap-2">
              <span className="text-sm font-bold text-gray-400 w-6">
                {item.rank}
              </span>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 line-clamp-2 group-hover:text-blue-600">
                  {item.query}
                </p>

                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-gray-500">
                    {item.count} queries
                  </span>
                  <span className="text-xs text-gray-400">·</span>
                  <span className="text-xs text-gray-500">
                    {item.unique_users} doctors
                  </span>
                  {getTrendIcon(item.trend)}
                </div>
              </div>

              <ArrowRight className="h-4 w-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
            </div>
          </div>
        ))}
      </div>

      {trending.length === 0 && (
        <div className="text-center py-4 text-gray-500 text-sm">
          No trending queries yet
        </div>
      )}

      <div className="mt-4 pt-3 border-t">
        <a
          href="/app/trending"
          className="text-sm text-blue-600 hover:underline flex items-center gap-1"
        >
          View all trending
          <ArrowRight className="h-3 w-3" />
        </a>
      </div>
    </Card>
  );
}
