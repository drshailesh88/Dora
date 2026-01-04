"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiClient } from "@/lib/api";
import { Send, Mic, Loader2, BookOpen, AlertTriangle } from "lucide-react";
import type { MedicalAnswer } from "@/types/api";

export default function QueryPage() {
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [answer, setAnswer] = useState<MedicalAnswer | null>(null);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setIsLoading(true);
    setError("");
    setAnswer(null);

    try {
      const response = await apiClient.query({
        question: question.trim(),
        top_k: 10,
        use_multi_query: true,
        use_hyde: true,
      });

      if (response.success && response.answer) {
        setAnswer(response.answer);
      } else {
        setError(response.error || "Failed to get answer");
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to process query");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Medical Query
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          Ask evidence-based medical questions
        </p>
      </div>

      {/* Query Input */}
      <Card>
        <CardHeader>
          <CardTitle>Ask a Question</CardTitle>
          <CardDescription>
            Get instant answers backed by medical literature
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="e.g., What are the first-line treatments for hypertension?"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                disabled={isLoading}
                className="flex-1"
              />
              <Button
                type="button"
                variant="outline"
                size="icon"
                disabled={isLoading}
              >
                <Mic className="h-4 w-4" />
              </Button>
            </div>
            <Button type="submit" disabled={isLoading} className="w-full">
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Send className="mr-2 h-4 w-4" />
                  Ask Question
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Card className="border-red-200 bg-red-50 dark:bg-red-900/20">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
              <div>
                <h3 className="font-semibold text-red-900 dark:text-red-100">
                  Error
                </h3>
                <p className="text-sm text-red-700 dark:text-red-200">{error}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Answer Display */}
      {answer && (
        <Card>
          <CardHeader>
            <CardTitle>Answer</CardTitle>
            <div className="flex items-center gap-4 text-sm text-gray-500">
              <span>Confidence: {(answer.confidence_score * 100).toFixed(1)}%</span>
              <span>Retrieved: {answer.retrieved_chunks} sources</span>
              <span>Time: {answer.query_time_ms}ms</span>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Main Answer */}
            <div className="prose dark:prose-invert max-w-none">
              <p className="text-gray-900 dark:text-gray-100 leading-relaxed">
                {answer.answer}
              </p>
            </div>

            {/* Warnings */}
            {answer.warnings && answer.warnings.length > 0 && (
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <h4 className="font-semibold text-yellow-900 dark:text-yellow-100 mb-2 flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  Important Notes
                </h4>
                <ul className="list-disc list-inside space-y-1 text-sm text-yellow-800 dark:text-yellow-200">
                  {answer.warnings.map((warning, idx) => (
                    <li key={idx}>{warning}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Citations */}
            {answer.citations && answer.citations.length > 0 && (
              <div>
                <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center gap-2">
                  <BookOpen className="h-4 w-4" />
                  Citations & References
                </h4>
                <div className="space-y-3">
                  {answer.citations.map((citation, idx) => (
                    <div
                      key={idx}
                      className="border-l-4 border-primary pl-4 py-2 bg-gray-50 dark:bg-gray-800 rounded-r"
                    >
                      <p className="text-sm text-gray-700 dark:text-gray-300 mb-1">
                        {citation.text}
                      </p>
                      <div className="flex items-center gap-3 text-xs text-gray-500">
                        <span className="font-medium">{citation.source}</span>
                        {citation.page && <span>Page {citation.page}</span>}
                        <span className="ml-auto">
                          Relevance: {(citation.score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Disclaimer */}
            <div className="text-xs text-gray-500 border-t pt-4">
              <p>
                This information is for educational purposes only and should not
                replace professional medical judgment. Always verify critical
                decisions with current clinical guidelines and patient-specific
                factors.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Example Questions */}
      {!answer && !isLoading && (
        <Card>
          <CardHeader>
            <CardTitle>Example Questions</CardTitle>
            <CardDescription>Try asking about:</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2">
              {[
                "What are the first-line treatments for Type 2 Diabetes?",
                "Latest guidelines for hypertension management",
                "Side effects of metformin",
                "Differential diagnosis for chest pain",
                "When to refer a patient with suspected heart failure?",
              ].map((example, idx) => (
                <button
                  key={idx}
                  onClick={() => setQuestion(example)}
                  className="text-left p-3 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg border text-sm"
                >
                  {example}
                </button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
