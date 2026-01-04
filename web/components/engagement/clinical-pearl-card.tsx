"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Lightbulb, RefreshCw, BookOpen } from "lucide-react";

interface ClinicalPearl {
  id: string;
  title: string;
  content: string;
  explanation?: string;
  specialty: string;
  category: string;
  evidence_level: string;
  citations: string[];
  question?: string;
  answer?: string;
  distractors?: string[];
}

export function ClinicalPearlCard() {
  const [pearl, setPearl] = useState<ClinicalPearl | null>(null);
  const [loading, setLoading] = useState(true);
  const [showExplanation, setShowExplanation] = useState(false);
  const [isQuizMode, setIsQuizMode] = useState(false);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);

  useEffect(() => {
    fetchPearl();
  }, []);

  const fetchPearl = async (quiz: boolean = false) => {
    setLoading(true);
    setSelectedAnswer(null);
    setShowExplanation(false);

    try {
      const endpoint = quiz
        ? "/api/v1/engagement/pearls/quiz"
        : "/api/v1/engagement/pearls/daily";

      const response = await fetch(endpoint, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setPearl(data);
        setIsQuizMode(quiz && !!data.question);
      }
    } catch (error) {
      console.error("Failed to fetch pearl:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSelect = (answer: string) => {
    setSelectedAnswer(answer);
  };

  const checkAnswer = () => {
    if (selectedAnswer === pearl?.answer) {
      return true;
    }
    return false;
  };

  if (loading) {
    return (
      <Card className="p-6">
        <div className="animate-pulse space-y-3">
          <div className="h-6 bg-gray-200 rounded w-1/2"></div>
          <div className="h-4 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        </div>
      </Card>
    );
  }

  if (!pearl) {
    return (
      <Card className="p-6">
        <div className="text-center text-gray-500">
          <Lightbulb className="h-12 w-12 mx-auto mb-2 opacity-50" />
          <p>No pearl available</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-6 bg-gradient-to-br from-amber-50 to-yellow-50 border-amber-200">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Lightbulb className="h-6 w-6 text-amber-600" />
          <h3 className="font-semibold text-lg">Clinical Pearl</h3>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="outline">{pearl.specialty}</Badge>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => fetchPearl(isQuizMode)}
          >
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Quiz Mode */}
      {isQuizMode && pearl.question ? (
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-lg border border-amber-200">
            <p className="font-medium mb-3">{pearl.question}</p>

            <div className="space-y-2">
              {/* Correct answer + distractors */}
              {[pearl.answer, ...(pearl.distractors || [])]
                .sort(() => Math.random() - 0.5)
                .map((option, index) => {
                  const isSelected = selectedAnswer === option;
                  const isCorrect = option === pearl.answer;
                  const showResult = selectedAnswer !== null;

                  return (
                    <button
                      key={index}
                      onClick={() => handleAnswerSelect(option)}
                      disabled={selectedAnswer !== null}
                      className={`w-full text-left p-3 rounded border transition-colors ${
                        isSelected && showResult && isCorrect
                          ? "bg-green-100 border-green-500"
                          : isSelected && showResult && !isCorrect
                          ? "bg-red-100 border-red-500"
                          : showResult && isCorrect
                          ? "bg-green-50 border-green-300"
                          : isSelected
                          ? "bg-amber-100 border-amber-300"
                          : "hover:bg-gray-50 border-gray-200"
                      }`}
                    >
                      {option}
                    </button>
                  );
                })}
            </div>

            {selectedAnswer && (
              <div className="mt-4">
                {checkAnswer() ? (
                  <div className="bg-green-50 p-3 rounded border border-green-200">
                    <p className="text-green-800 font-medium">Correct!</p>
                  </div>
                ) : (
                  <div className="bg-red-50 p-3 rounded border border-red-200">
                    <p className="text-red-800 font-medium">
                      Incorrect. The correct answer is: {pearl.answer}
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Regular Pearl Mode */
        <div>
          <h4 className="font-bold text-xl mb-3 text-gray-900">
            {pearl.title}
          </h4>

          <p className="text-gray-800 text-lg mb-4">{pearl.content}</p>

          {pearl.explanation && (
            <div>
              <Button
                variant="link"
                className="p-0 h-auto mb-2"
                onClick={() => setShowExplanation(!showExplanation)}
              >
                {showExplanation ? "Hide" : "Show"} explanation
              </Button>

              {showExplanation && (
                <div className="bg-white p-4 rounded-lg border border-amber-200 mb-4">
                  <p className="text-gray-700">{pearl.explanation}</p>
                </div>
              )}
            </div>
          )}

          {pearl.citations.length > 0 && (
            <div className="mt-4 pt-3 border-t border-amber-200">
              <div className="flex items-start gap-2 text-sm text-gray-600">
                <BookOpen className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium mb-1">Sources:</p>
                  {pearl.citations.map((citation, index) => (
                    <p key={index} className="text-xs">
                      {citation}
                    </p>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Toggle Mode Button */}
      <div className="mt-4 pt-3 border-t border-amber-200">
        <Button
          variant="outline"
          size="sm"
          className="w-full"
          onClick={() => fetchPearl(!isQuizMode)}
        >
          Switch to {isQuizMode ? "Pearl" : "Quiz"} Mode
        </Button>
      </div>
    </Card>
  );
}
