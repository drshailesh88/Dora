"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Calendar,
  TrendingUp,
  Lightbulb,
  AlertTriangle,
  FileText,
  Users,
  ChevronRight,
} from "lucide-react";

interface BriefingItem {
  id: string;
  type: string;
  title: string;
  content: string;
  icon: string;
  priority: number;
  severity?: string;
  actionable: boolean;
  action_url?: string;
}

interface DailyBriefing {
  id: string;
  user_id: string;
  date: string;
  greeting: string;
  summary_line: string;
  items: BriefingItem[];
  specialty: string;
  patient_count_today: number;
}

export function MorningBriefing() {
  const [briefing, setBriefing] = useState<DailyBriefing | null>(null);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string[]>([]);

  useEffect(() => {
    fetchBriefing();
  }, []);

  const fetchBriefing = async () => {
    try {
      const response = await fetch("/api/v1/engagement/briefing", {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setBriefing(data);
      }
    } catch (error) {
      console.error("Failed to fetch briefing:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleItemClick = async (item: BriefingItem) => {
    // Track click
    await fetch("/api/v1/engagement/briefing/click", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${localStorage.getItem("token")}`,
      },
      body: JSON.stringify({
        briefing_id: briefing?.id,
        item_id: item.id,
      }),
    });

    // Navigate to action URL
    if (item.action_url) {
      window.location.href = item.action_url;
    }
  };

  const toggleExpand = (itemId: string) => {
    setExpanded((prev) =>
      prev.includes(itemId)
        ? prev.filter((id) => id !== itemId)
        : [...prev, itemId]
    );
  };

  const getItemIcon = (type: string) => {
    switch (type) {
      case "patient_preview":
        return <Users className="h-5 w-5" />;
      case "clinical_pearl":
        return <Lightbulb className="h-5 w-5" />;
      case "trending_query":
        return <TrendingUp className="h-5 w-5" />;
      case "research_alert":
        return <FileText className="h-5 w-5" />;
      case "guideline_update":
      case "drug_alert":
        return <AlertTriangle className="h-5 w-5" />;
      default:
        return <Calendar className="h-5 w-5" />;
    }
  };

  const getSeverityColor = (severity?: string) => {
    switch (severity) {
      case "critical":
        return "destructive";
      case "high":
        return "destructive";
      case "medium":
        return "warning";
      default:
        return "default";
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          <div className="space-y-3">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        </div>
      </Card>
    );
  }

  if (!briefing) {
    return (
      <Card className="p-6">
        <p className="text-gray-500">No briefing available</p>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2">{briefing.greeting}</h2>
        <p className="text-gray-600">{briefing.summary_line}</p>
      </div>

      {/* Briefing Items */}
      <div className="space-y-3">
        {briefing.items.map((item) => {
          const isExpanded = expanded.includes(item.id);

          return (
            <Card
              key={item.id}
              className={`p-4 cursor-pointer hover:shadow-md transition-shadow ${
                item.severity === "critical" || item.severity === "high"
                  ? "border-red-300"
                  : ""
              }`}
              onClick={() => item.actionable && handleItemClick(item)}
            >
              <div className="flex items-start gap-3">
                {/* Icon */}
                <div className="mt-1">{getItemIcon(item.type)}</div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-semibold">{item.title}</h3>
                    {item.severity && (
                      <Badge variant={getSeverityColor(item.severity)}>
                        {item.severity}
                      </Badge>
                    )}
                  </div>

                  <p
                    className={`text-sm text-gray-600 ${
                      isExpanded ? "" : "line-clamp-2"
                    }`}
                  >
                    {item.content}
                  </p>

                  {item.content.length > 100 && (
                    <Button
                      variant="link"
                      size="sm"
                      className="mt-1 p-0 h-auto"
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleExpand(item.id);
                      }}
                    >
                      {isExpanded ? "Show less" : "Show more"}
                    </Button>
                  )}
                </div>

                {/* Action arrow */}
                {item.actionable && (
                  <ChevronRight className="h-5 w-5 text-gray-400 flex-shrink-0" />
                )}
              </div>
            </Card>
          );
        })}
      </div>

      {briefing.items.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <Calendar className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p>No updates for today</p>
        </div>
      )}
    </Card>
  );
}
