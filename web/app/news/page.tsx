"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

interface NewsArticle {
  id: string;
  title: string;
  subtitle?: string;
  url: string;
  source: string;
  category: string;
  publication_date: string;
  summary: string;
  key_findings: string[];
  clinical_implications?: string;
  specialty: string[];
  priority: string;
  relevance_score: number;
  reading_time_minutes: number;
  image_url?: string;
}

export default function NewsPage() {
  const router = useRouter();
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [view, setView] = useState<"feed" | "trending" | "breaking">("feed");

  const categories = [
    { id: "all", name: "All" },
    { id: "research", name: "Research" },
    { id: "guidelines", name: "Guidelines" },
    { id: "drug_approvals", name: "Drug Approvals" },
    { id: "conferences", name: "Conferences" },
    { id: "clinical_practice", name: "Clinical Practice" },
  ];

  useEffect(() => {
    fetchArticles();
  }, [view, selectedCategory]);

  const fetchArticles = async () => {
    setLoading(true);
    try {
      let endpoint = "/api/v1/news/feed";

      if (view === "trending") {
        endpoint = "/api/v1/news/trending";
      } else if (view === "breaking") {
        endpoint = "/api/v1/news/breaking";
      }

      const params = new URLSearchParams();
      if (selectedCategory !== "all") {
        params.append("category", selectedCategory);
      }

      const response = await fetch(`${endpoint}?${params}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      const data = await response.json();
      if (data.success) {
        setArticles(data.articles || []);
      }
    } catch (error) {
      console.error("Failed to fetch articles:", error);
    } finally {
      setLoading(false);
    }
  };

  const getPriorityBadge = (priority: string) => {
    const badges = {
      critical: "bg-red-100 text-red-800 border-red-200",
      high: "bg-orange-100 text-orange-800 border-orange-200",
      medium: "bg-blue-100 text-blue-800 border-blue-200",
      low: "bg-gray-100 text-gray-800 border-gray-200",
    };
    return badges[priority as keyof typeof badges] || badges.medium;
  };

  const getCategoryIcon = (category: string) => {
    const icons = {
      research: "🔬",
      guidelines: "📋",
      drug_approvals: "💊",
      conferences: "🎓",
      clinical_practice: "⚕️",
      drug_safety: "⚠️",
    };
    return icons[category as keyof typeof icons] || "📰";
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold text-gray-900">Medical News</h1>
          <p className="mt-2 text-gray-600">
            Stay current with the latest medical research, guidelines, and approvals
          </p>
        </div>
      </div>

      {/* View Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            <button
              onClick={() => setView("feed")}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                view === "feed"
                  ? "border-indigo-500 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              Personalized Feed
            </button>
            <button
              onClick={() => setView("trending")}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                view === "trending"
                  ? "border-indigo-500 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              🔥 Trending
            </button>
            <button
              onClick={() => setView("breaking")}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                view === "breaking"
                  ? "border-indigo-500 text-indigo-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              ⚡ Breaking News
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-12 gap-8">
          {/* Sidebar */}
          <div className="col-span-3">
            <div className="bg-white rounded-lg shadow p-6 sticky top-8">
              <h3 className="font-semibold text-gray-900 mb-4">Categories</h3>
              <div className="space-y-2">
                {categories.map((cat) => (
                  <button
                    key={cat.id}
                    onClick={() => setSelectedCategory(cat.id)}
                    className={`w-full text-left px-3 py-2 rounded-md text-sm ${
                      selectedCategory === cat.id
                        ? "bg-indigo-50 text-indigo-700 font-medium"
                        : "text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    {cat.name}
                  </button>
                ))}
              </div>

              <div className="mt-8 pt-8 border-t">
                <h3 className="font-semibold text-gray-900 mb-4">Quick Links</h3>
                <div className="space-y-2">
                  <button
                    onClick={() => router.push("/news/conferences")}
                    className="w-full text-left px-3 py-2 rounded-md text-sm text-gray-700 hover:bg-gray-50"
                  >
                    🎓 Conferences
                  </button>
                  <button
                    onClick={() => router.push("/news/guidelines")}
                    className="w-full text-left px-3 py-2 rounded-md text-sm text-gray-700 hover:bg-gray-50"
                  >
                    📋 Guidelines
                  </button>
                  <button
                    onClick={() => router.push("/news/bookmarks")}
                    className="w-full text-left px-3 py-2 rounded-md text-sm text-gray-700 hover:bg-gray-50"
                  >
                    🔖 Bookmarks
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="col-span-9">
            {loading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                <p className="mt-4 text-gray-600">Loading articles...</p>
              </div>
            ) : articles.length === 0 ? (
              <div className="text-center py-12 bg-white rounded-lg shadow">
                <p className="text-gray-600">No articles found</p>
              </div>
            ) : (
              <div className="space-y-6">
                {articles.map((article) => (
                  <div
                    key={article.id}
                    className="bg-white rounded-lg shadow hover:shadow-md transition-shadow cursor-pointer"
                    onClick={() => router.push(`/news/article/${article.id}`)}
                  >
                    <div className="p-6">
                      {/* Priority Badge */}
                      {article.priority !== "low" && (
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getPriorityBadge(
                            article.priority
                          )}`}
                        >
                          {article.priority.toUpperCase()}
                        </span>
                      )}

                      {/* Title */}
                      <h2 className="mt-2 text-xl font-semibold text-gray-900 hover:text-indigo-600">
                        {article.title}
                      </h2>

                      {/* Metadata */}
                      <div className="mt-2 flex items-center text-sm text-gray-500 space-x-4">
                        <span className="flex items-center">
                          {getCategoryIcon(article.category)}
                          <span className="ml-1">{article.category.replace("_", " ")}</span>
                        </span>
                        <span>{article.source.toUpperCase()}</span>
                        <span>
                          {new Date(article.publication_date).toLocaleDateString()}
                        </span>
                        <span>{article.reading_time_minutes} min read</span>
                      </div>

                      {/* Summary */}
                      <p className="mt-4 text-gray-600 line-clamp-3">
                        {article.summary}
                      </p>

                      {/* Key Findings */}
                      {article.key_findings && article.key_findings.length > 0 && (
                        <div className="mt-4">
                          <p className="text-sm font-medium text-gray-900 mb-2">
                            Key Findings:
                          </p>
                          <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
                            {article.key_findings.slice(0, 2).map((finding, idx) => (
                              <li key={idx}>{finding}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Specialties */}
                      {article.specialty && article.specialty.length > 0 && (
                        <div className="mt-4 flex flex-wrap gap-2">
                          {article.specialty.map((spec) => (
                            <span
                              key={spec}
                              className="inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-medium bg-gray-100 text-gray-800"
                            >
                              {spec}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
