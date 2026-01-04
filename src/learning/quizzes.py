"""
Quiz System

Generates and manages medical quizzes for assessment and learning.
"""

from datetime import datetime, date, timedelta
from typing import Optional
import logging
import random

from .models import (
    Quiz,
    QuizQuestion,
    QuizAttempt,
    QuestionType,
    DifficultyLevel,
)

logger = logging.getLogger(__name__)


class QuizSystem:
    """Manages medical quizzes"""

    def __init__(self):
        self.quizzes: dict[str, Quiz] = {}
        self.questions: dict[str, QuizQuestion] = {}
        self.attempts: list[QuizAttempt] = []

    def create_quiz(
        self,
        title: str,
        description: str,
        questions: list[QuizQuestion],
        specialty: Optional[str] = None,
        topics: Optional[list[str]] = None,
        difficulty: DifficultyLevel = DifficultyLevel.INTERMEDIATE,
        cme_credits: float = 0.5,
        passing_score: float = 0.7,
        created_by: Optional[str] = None,
    ) -> Quiz:
        """
        Create a new quiz

        Args:
            title: Quiz title
            description: Quiz description
            questions: List of questions
            specialty: Medical specialty
            topics: Topics covered
            difficulty: Difficulty level
            cme_credits: CME credits for completion
            passing_score: Minimum passing score (0-1)
            created_by: Creator user ID

        Returns:
            Quiz
        """
        # Calculate estimated time (2 min per question)
        estimated_time = len(questions) * 2

        quiz = Quiz(
            title=title,
            description=description,
            specialty=specialty,
            topics=topics or [],
            difficulty=difficulty,
            estimated_time_minutes=estimated_time,
            questions=questions,
            total_questions=len(questions),
            cme_credits=cme_credits,
            passing_score=passing_score,
            created_by=created_by,
        )

        # Store questions
        for question in questions:
            question.quiz_id = quiz.id
            self.questions[question.id] = question

        self.quizzes[quiz.id] = quiz

        logger.info(f"Created quiz: {title} with {len(questions)} questions")

        return quiz

    def generate_quiz_from_query(
        self,
        query_text: str,
        query_answer: str,
        citations: list[str],
        num_questions: int = 5,
        specialty: Optional[str] = None,
        topics: Optional[list[str]] = None,
    ) -> Quiz:
        """
        Generate a quiz from a medical query (using LLM)

        Args:
            query_text: Original query
            query_answer: Answer to query
            citations: Supporting citations
            num_questions: Number of questions to generate
            specialty: Medical specialty
            topics: Topics

        Returns:
            Quiz
        """
        # In production, this would use an LLM to generate questions
        # For now, creating sample questions

        questions = []

        # Sample question 1: Basic recall
        questions.append(QuizQuestion(
            quiz_id="",
            question_type=QuestionType.MULTIPLE_CHOICE,
            question_text=f"Based on: {query_text[:100]}...\n\nWhat is the most appropriate approach?",
            options=[
                {"text": "Option A (sample)", "is_correct": False},
                {"text": "Option B (sample)", "is_correct": True},
                {"text": "Option C (sample)", "is_correct": False},
                {"text": "Option D (sample)", "is_correct": False},
            ],
            correct_answer="Option B",
            explanation="This is the correct approach based on current guidelines.",
            citations=citations[:2] if citations else [],
            difficulty=DifficultyLevel.BEGINNER,
        ))

        # Add more questions up to num_questions
        for i in range(1, min(num_questions, 5)):
            questions.append(QuizQuestion(
                quiz_id="",
                question_type=QuestionType.MULTIPLE_CHOICE,
                question_text=f"Question {i+1} related to: {query_text[:50]}...",
                options=[
                    {"text": f"Option A{i}", "is_correct": i % 4 == 0},
                    {"text": f"Option B{i}", "is_correct": i % 4 == 1},
                    {"text": f"Option C{i}", "is_correct": i % 4 == 2},
                    {"text": f"Option D{i}", "is_correct": i % 4 == 3},
                ],
                correct_answer=f"Option {chr(65 + (i % 4))}{i}",
                explanation=f"Explanation for question {i+1}",
                citations=citations[:2] if citations else [],
                difficulty=DifficultyLevel.INTERMEDIATE,
            ))

        quiz = self.create_quiz(
            title=f"Quiz: {query_text[:50]}...",
            description="Auto-generated quiz based on your query",
            questions=questions,
            specialty=specialty,
            topics=topics,
            difficulty=DifficultyLevel.INTERMEDIATE,
        )

        quiz.source_query_id = "query_" + str(random.randint(1000, 9999))

        return quiz

    def start_quiz(self, user_id: str, quiz_id: str) -> QuizAttempt:
        """
        Start a quiz attempt

        Args:
            user_id: User ID
            quiz_id: Quiz ID

        Returns:
            QuizAttempt
        """
        quiz = self.quizzes.get(quiz_id)
        if not quiz:
            raise ValueError(f"Quiz not found: {quiz_id}")

        attempt = QuizAttempt(
            user_id=user_id,
            quiz_id=quiz_id,
            total_questions=quiz.total_questions,
            score=0.0,
        )

        self.attempts.append(attempt)

        logger.info(f"User {user_id} started quiz: {quiz.title}")

        return attempt

    def submit_answer(
        self,
        attempt_id: str,
        question_id: str,
        answer: str,
    ) -> dict:
        """
        Submit an answer to a quiz question

        Args:
            attempt_id: Attempt ID
            question_id: Question ID
            answer: User's answer

        Returns:
            Dict with result info
        """
        # Find attempt
        attempt = None
        for a in self.attempts:
            if a.id == attempt_id:
                attempt = a
                break

        if not attempt:
            raise ValueError(f"Attempt not found: {attempt_id}")

        # Find question
        question = self.questions.get(question_id)
        if not question:
            raise ValueError(f"Question not found: {question_id}")

        # Check answer
        is_correct = self._check_answer(question, answer)

        # Store answer
        attempt.answers[question_id] = {
            "answer": answer,
            "is_correct": is_correct,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Update question analytics
        question.times_shown += 1
        if is_correct:
            question.times_correct += 1
        else:
            question.times_incorrect += 1

        return {
            "is_correct": is_correct,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "citations": question.citations,
        }

    def complete_quiz(self, attempt_id: str) -> QuizAttempt:
        """
        Complete a quiz attempt and calculate score

        Args:
            attempt_id: Attempt ID

        Returns:
            Completed QuizAttempt
        """
        # Find attempt
        attempt = None
        for a in self.attempts:
            if a.id == attempt_id:
                attempt = a
                break

        if not attempt:
            raise ValueError(f"Attempt not found: {attempt_id}")

        # Calculate score
        correct_count = sum(
            1 for ans in attempt.answers.values()
            if ans.get("is_correct")
        )

        attempt.correct_count = correct_count
        attempt.incorrect_count = attempt.total_questions - correct_count
        attempt.score = correct_count / attempt.total_questions if attempt.total_questions > 0 else 0.0

        # Calculate time taken
        time_taken = (datetime.utcnow() - attempt.started_at).total_seconds()
        attempt.time_taken_seconds = int(time_taken)

        # Mark as completed
        attempt.completed_at = datetime.utcnow()

        # Get quiz
        quiz = self.quizzes.get(attempt.quiz_id)
        if quiz:
            # Check if passed
            attempt.passed = attempt.score >= quiz.passing_score

            if attempt.passed:
                attempt.cme_credits_earned = quiz.cme_credits
                attempt.points_earned = 100

            # Update quiz analytics
            quiz.attempt_count += 1
            quiz.average_score = (
                (quiz.average_score * (quiz.attempt_count - 1) + attempt.score)
                / quiz.attempt_count
            )

            # Calculate spaced repetition
            if attempt.passed:
                attempt.next_review_date = date.today() + timedelta(days=1)
                attempt.interval_days = 1
            else:
                # Review tomorrow if failed
                attempt.next_review_date = date.today() + timedelta(days=1)
                attempt.interval_days = 0

        logger.info(
            f"User {attempt.user_id} completed quiz {attempt.quiz_id}: "
            f"Score {attempt.score*100:.0f}% ({'Passed' if attempt.passed else 'Failed'})"
        )

        return attempt

    def get_quiz(self, quiz_id: str) -> Optional[Quiz]:
        """Get quiz by ID"""
        return self.quizzes.get(quiz_id)

    def get_user_attempts(
        self,
        user_id: str,
        quiz_id: Optional[str] = None,
    ) -> list[QuizAttempt]:
        """
        Get user's quiz attempts

        Args:
            user_id: User ID
            quiz_id: Optional quiz ID filter

        Returns:
            List of attempts
        """
        attempts = [a for a in self.attempts if a.user_id == user_id]

        if quiz_id:
            attempts = [a for a in attempts if a.quiz_id == quiz_id]

        return sorted(attempts, key=lambda x: x.started_at, reverse=True)

    def get_quiz_performance(self, user_id: str) -> dict:
        """
        Get overall quiz performance for user

        Args:
            user_id: User ID

        Returns:
            Performance summary
        """
        attempts = self.get_user_attempts(user_id)
        completed = [a for a in attempts if a.completed_at is not None]

        if not completed:
            return {
                "total_attempts": 0,
                "quizzes_passed": 0,
                "average_score": 0.0,
                "total_credits_earned": 0.0,
            }

        passed = [a for a in completed if a.passed]
        average_score = sum(a.score for a in completed) / len(completed)
        total_credits = sum(a.cme_credits_earned for a in completed)

        return {
            "total_attempts": len(completed),
            "quizzes_passed": len(passed),
            "pass_rate": len(passed) / len(completed) if completed else 0.0,
            "average_score": average_score,
            "total_credits_earned": total_credits,
            "perfect_scores": sum(1 for a in completed if a.score == 1.0),
        }

    def get_due_reviews(self, user_id: str) -> list[QuizAttempt]:
        """
        Get quizzes due for spaced repetition review

        Args:
            user_id: User ID

        Returns:
            List of attempts due for review
        """
        attempts = self.get_user_attempts(user_id)
        today = date.today()

        due = [
            a for a in attempts
            if a.next_review_date and a.next_review_date <= today
        ]

        return sorted(due, key=lambda x: x.next_review_date)

    def update_spaced_repetition(
        self,
        attempt_id: str,
        quality: int,  # 0-5 (SM-2 algorithm)
    ) -> None:
        """
        Update spaced repetition schedule based on recall quality

        Args:
            attempt_id: Attempt ID
            quality: Quality of recall (0=complete failure, 5=perfect)
        """
        # Find attempt
        attempt = None
        for a in self.attempts:
            if a.id == attempt_id:
                attempt = a
                break

        if not attempt:
            return

        # SM-2 algorithm
        if quality >= 3:
            if attempt.interval_days == 0:
                attempt.interval_days = 1
            elif attempt.interval_days == 1:
                attempt.interval_days = 6
            else:
                attempt.interval_days = int(attempt.interval_days * attempt.ease_factor)

            attempt.ease_factor = max(
                1.3,
                attempt.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            )
        else:
            attempt.interval_days = 1
            attempt.ease_factor = max(1.3, attempt.ease_factor - 0.2)

        attempt.next_review_date = date.today() + timedelta(days=attempt.interval_days)

        logger.info(
            f"Updated spaced repetition for attempt {attempt_id}: "
            f"Next review in {attempt.interval_days} days"
        )

    def _check_answer(self, question: QuizQuestion, answer: str) -> bool:
        """
        Check if answer is correct

        Args:
            question: Quiz question
            answer: User's answer

        Returns:
            True if correct
        """
        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            # Find correct option
            for option in question.options:
                if option.get("is_correct") and option.get("text") == answer:
                    return True
            return False

        elif question.question_type == QuestionType.TRUE_FALSE:
            return answer.lower() == question.correct_answer.lower()

        else:
            # For other types, simple string match
            return answer.strip().lower() == question.correct_answer.strip().lower()


# Global quiz system instance
_quiz_system = QuizSystem()


def get_quiz_system() -> QuizSystem:
    """Get the global quiz system instance"""
    return _quiz_system
