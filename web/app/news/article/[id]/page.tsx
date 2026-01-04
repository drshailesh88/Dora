"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";

interface Article {
  id: string;
  title: string;
  subtitle?: string;
  url: string;
  source: string;
  category: string;
  authors: string[];
  journal?: string;
  publication_date: string;
  summary: string;
  key_findings: string[];
  clinical_implications?: string;
  full_text?: string;
  specialty: string[];
  keywords: string[];
  priority: string;
  reading_time_minutes: number;
  pubmed_id?: string;
  doi?: string;
}

export default function ArticlePage() {
  const params = useParams();
  const router = useRouter();
  const articleId = params.id as string;

  const [article, setArticle] = useState<Article | null>(null);
  const [similar, setSimilar] = useState<Article[]>([]);
  const [loading, setLoading] = useState(true);
  const [bookmarked, setBookmarked] = useState(false);
  const [showBookmarkModal, setShowBookmarkModal] = useState(false);

  useEffect(() => {
    fetchArticle();
  }, [articleId]);

  const fetchArticle = async () => {
    try {
      const response = await fetch(`/api/v1/news/article/${articleId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      const data = await response.json();
      if (data.success) {
        setArticle(data.article);
        setSimilar(data.similar || []);
      }
    } catch (error) {
      console.error("Failed to fetch article:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleBookmark = async () => {
    try {
      const response = await fetch("/api/v1/news/bookmark", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          article_id: articleId,
          tags: [],
          notes: "",
        }),
      });

      const data = await response.json();
      if (data.success) {
        setBookmarked(true);
        setShowBookmarkModal(false);
      }
    } catch (error) {
      console.error("Failed to bookmark:", error);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <p className="mt-4 text-gray-600">Loading article...</p>
        </div>
      </div>
    );
  }

  if (!article) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Article not found</p>
          <button
            onClick={() => router.push("/news")}
            className="mt-4 text-indigo-600 hover:text-indigo-800"
          >
            Back to News Feed
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <button
            onClick={() => router.push("/news")}
            className="text-gray-600 hover:text-gray-900 flex items-center"
          >
            ← Back to News Feed
          </button>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Article */}
        <article className="bg-white rounded-lg shadow-lg">
          <div className="p-8">
            {/* Category & Source */}
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <span className="font-medium text-indigo-600">
                {article.category.replace("_", " ").toUpperCase()}
              </span>
              <span>•</span>
              <span>{article.source.toUpperCase()}</span>
              <span>•</span>
              <span>{new Date(article.publication_date).toLocaleDateString()}</span>
              <span>•</span>
              <span>{article.reading_time_minutes} min read</span>
            </div>

            {/* Title */}
            <h1 className="mt-4 text-4xl font-bold text-gray-900">
              {article.title}
            </h1>

            {article.subtitle && (
              <h2 className="mt-4 text-xl text-gray-600">{article.subtitle}</h2>
            )}

            {/* Authors */}
            {article.authors && article.authors.length > 0 && (
              <p className="mt-4 text-gray-700">
                <span className="font-medium">Authors: </span>
                {article.authors.join(", ")}
              </p>
            )}

            {/* Journal */}
            {article.journal && (
              <p className="mt-2 text-gray-700">
                <span className="font-medium">Published in: </span>
                {article.journal}
              </p>
            )}

            {/* Actions */}
            <div className="mt-6 flex space-x-4">
              <button
                onClick={() => setShowBookmarkModal(true)}
                className={`px-4 py-2 rounded-md ${
                  bookmarked
                    ? "bg-gray-100 text-gray-700"
                    : "bg-indigo-600 text-white hover:bg-indigo-700"
                }`}
              >
                {bookmarked ? "✓ Bookmarked" : "🔖 Bookmark"}
              </button>
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 rounded-md border border-gray-300 text-gray-700 hover:bg-gray-50"
              >
                View Original →
              </a>
            </div>

            {/* Summary */}
            <div className="mt-8">
              <h3 className="text-lg font-semibold text-gray-900">Summary</h3>
              <p className="mt-2 text-gray-700 leading-relaxed">{article.summary}</p>
            </div>

            {/* Key Findings */}
            {article.key_findings && article.key_findings.length > 0 && (
              <div className="mt-8">
                <h3 className="text-lg font-semibold text-gray-900">
                  Key Findings
                </h3>
                <ul className="mt-4 space-y-3">
                  {article.key_findings.map((finding, idx) => (
                    <li key={idx} className="flex items-start">
                      <span className="flex-shrink-0 h-6 w-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center text-sm font-medium mr-3">
                        {idx + 1}
                      </span>
                      <span className="text-gray-700">{finding}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Clinical Implications */}
            {article.clinical_implications && (
              <div className="mt-8 bg-blue-50 border-l-4 border-blue-500 p-6">
                <h3 className="text-lg font-semibold text-blue-900 flex items-center">
                  ⚕️ Clinical Implications
                </h3>
                <p className="mt-2 text-blue-800 leading-relaxed">
                  {article.clinical_implications}
                </p>
              </div>
            )}

            {/* Full Text */}
            {article.full_text && (
              <div className="mt-8">
                <h3 className="text-lg font-semibold text-gray-900">Abstract</h3>
                <div className="mt-2 prose max-w-none text-gray-700">
                  {article.full_text}
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="mt-8 pt-8 border-t">
              <div className="grid grid-cols-2 gap-6">
                {/* Specialties */}
                {article.specialty && article.specialty.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">
                      Specialties
                    </h4>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {article.specialty.map((spec) => (
                        <span
                          key={spec}
                          className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-gray-100 text-gray-800"
                        >
                          {spec}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Keywords */}
                {article.keywords && article.keywords.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">Keywords</h4>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {article.keywords.slice(0, 8).map((keyword) => (
                        <span
                          key={keyword}
                          className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-50 text-gray-700"
                        >
                          {keyword}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* External Links */}
              <div className="mt-6">
                <h4 className="text-sm font-medium text-gray-900">External Links</h4>
                <div className="mt-2 flex space-x-4">
                  {article.pubmed_id && (
                    <a
                      href={`https://pubmed.ncbi.nlm.nih.gov/${article.pubmed_id}/`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-600 hover:text-indigo-800 text-sm"
                    >
                      PubMed: {article.pubmed_id}
                    </a>
                  )}
                  {article.doi && (
                    <a
                      href={`https://doi.org/${article.doi}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-600 hover:text-indigo-800 text-sm"
                    >
                      DOI: {article.doi}
                    </a>
                  )}
                </div>
              </div>
            </div>
          </div>
        </article>

        {/* Similar Articles */}
        {similar.length > 0 && (
          <div className="mt-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              Related Articles
            </h2>
            <div className="space-y-4">
              {similar.map((sim) => (
                <div
                  key={sim.id}
                  className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => router.push(`/news/article/${sim.id}`)}
                >
                  <h3 className="text-lg font-semibold text-gray-900 hover:text-indigo-600">
                    {sim.title}
                  </h3>
                  <div className="mt-2 text-sm text-gray-500 flex items-center space-x-4">
                    <span>{sim.source.toUpperCase()}</span>
                    <span>
                      {new Date(sim.publication_date).toLocaleDateString()}
                    </span>
                    <span>{sim.reading_time_minutes} min read</span>
                  </div>
                  <p className="mt-3 text-gray-600 line-clamp-2">{sim.summary}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
