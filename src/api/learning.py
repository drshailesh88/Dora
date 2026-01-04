"""
Learning and CME API Endpoints
"""

from datetime import date, datetime
from typing import Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel, Field

from src.learning import (
    get_learning_service,
    LearningService,
    DifficultyLevel,
    QuestionType,
)

router = APIRouter(prefix="/api/learning", tags=["learning"])


# === Request/Response Models ===

class TrackQueryRequest(BaseModel):
    """Request to track a query"""
    query_id: str
    query_text: str
    specialty: Optional[str] = None
    topics: Optional[list[str]] = None
    duration_seconds: int = 0
    confidence_score: Optional[float] = None
    has_follow_up: bool = False


class QuizAnswerRequest(BaseModel):
    """Request to submit quiz answer"""
    question_id: str
    answer: str


class PathRatingRequest(BaseModel):
    """Request to rate a learning path"""
    rating: int = Field(..., ge=1, le=5)
    feedback: Optional[str] = None


class CreateGoalRequest(BaseModel):
    """Request to create learning goal"""
    goal_type: str
    target_value: int
    period_type: str


# === Dependencies ===

def get_service() -> LearningService:
    """Get learning service instance"""
    return get_learning_service()


def get_current_user_id() -> str:
    """
    Get current user ID (stub - would use JWT auth in production)

    In production, this would:
    1. Extract JWT from Authorization header
    2. Validate token
    3. Return user_id from token
    """
    # For now, return a test user ID
    return "test_user_123"


# === Learning Dashboard ===

@router.get("/dashboard")
async def get_dashboard(
    user_id: str = Depends(get_current_user_id),
    service: LearningService = Depends(get_service),
):
    """Get comprehensive learning dashboard"""
    try:
        dashboard = service.get_learning_dashboard(user_id)
        return dashboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === CME Credits ===

@router.get("/credits")
async def get_cme_credits(
    year: Optional[int] = None,
    user_id: str = Depends(get_current_user_id),
    service: LearningService = Depends(get_service),
):
    """Get CME credits summary"""
    try:
        annual_credits = service.cme_system.get_annual_credits(user_id, year)

        # Get credits by specialty
        credits_by_specialty = service.cme_system.get_credits_by_specialty(user_id)

        # Get expiring credits
        expiring = service.cme_system.get_expiring_credits(user_id, days_until_expiry=90)

        return {
            "annual_summary": annual_credits,
            "by_specialty": credits_by_specialty,
            "expiring_soon": [
                {
                    "id": c.id,
                    "credits": c.credits,
                    "activity_title": c.activity_title,
                    "expires_date": c.expires_date.isoformat(),
                }
                for c in expiring
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/credits/history")
async def get_credit_history(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    user_id: str = Depends(get_current_user_id),
    service: LearningService = Depends(get_service),
):
    """Get detailed credit history"""
    try:
        credits = service.cme_system.get_user_credits(
            user_id,
            start_date=start_date,
            end_date=end_date,
        )

        return {
            "credits": [
                {
                    "id": c.id,
                    "credits": c.credits,
                    "category": c.category,
                    "activity_title": c.activity_title,
                    "activity_type": c.activity_type,
                    "specialty": c.specialty,
                    "earned_date": c.earned_date.isoformat(),
                    "expires_date": c.expires_date.isoformat(),
                    "verification_code": c.verification_code,
                }
                for c in credits
            ],
            "total": sum(c.credits for c in credits),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === Certificates ===

@router.get("/certificates")
async def list_certificates(
    user_id: str = Depends(get_current_user_id),
    service: LearningService = Depends(get_service),
):
    """List user's certificates"""
    # In production, would query database for certificates
    return {
        "certificates": [],
        "total_certificates": 0,
    }


@router.post("/certificates/generate")
async def generate_certificate(
    period_start: date,
    period_end: date,
    doctor_name: str,
    registration_number: Optional[str] = None,
    specialty: Optional[str] = None,
    institution: Optional[str] = None,
    user_id: str = Depends(get_current_user_id),
    service: LearningService = Depends(get_service),
):
    """Generate CME certificate for a period"""
    try:
        certificate = service.generate_certificate(
            user_id=user_id,
            doctor_name=doctor_name,
            period_start=period_start,
            period_end=period_end,
            registration_number=registration_number,
            specialty=specialty,
            institution=institution,
        )

        return {
            "certificate_id": certificate.id,
            "certificate_number": certificate.certificate_number,
            "total_credits": certificate.total_credits,
            "verification_url": certificate.verification_url,
            "pdf_path": certificate.pdf_path,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/certificates/{certificate_id}/download")
async def download_certificate(
    certificate_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Download certificate PDF"""
    # In production, would:
    # 1. Verify certificate belongs to user
    # 2. Return PDF file
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/certificates/verify/{certificate_number}")
async def verify_certificate(
    certificate_number: str,
    service: LearningService = Depends(get_service),
):
    """Verify a certificate (public endpoint)"""
    # In production, would look up certificate in database
    return {
        "valid": False,
        "message": "Certificate verification not yet implemented",
    }


# === Streaks ===

@router.get("/streaks")
async def get_streak(
    user_id: str = Depends(get_current_user_id),
    service: LearningService = Depends(get_service),
):
    """Get streak status"""
    try:
        status = service.streak_manager.check_streak_status(user_id)
        leaderboard = service.streak_manager.get_leaderboard(limit=10)
        user_rank = service.streak_manager.get_user_rank(user_id)

        return {
            "status": status,
            "leaderboard": leaderboard,
            "your_rank": user_rank,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/streaks/freeze")
async def use_freeze_token(
    user_id: str = Depends(get_current_user_id),
    service: LearningService = Depends(get_service),
):
    """Use a freeze token to protect streak"""
    try:
        success = service.streak_manager.use_freeze_token(user_id)

        if not success:
            raise HTTPException(
                status_code=400,
                detail="No freeze tokens available or streak cannot be protected"
            )

        status = service.streak_manager.check_streak_status(user_id)
        return {"success": True, "status": status}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === Achievements ===

@router.get("/achievements")
async def get_achievements(
    user_id: str = Depends(get_current_user_id),
    service: LearningService = Depends(get_service),
):
    """Get user's achievements"""
    try:
        earned = service.achievement_system.get_user_achievements(user_id)
        available = service.achievement_system.get_available_achievements(user_id)
        level_progress = service.achievement_system.get_progress_to_next_level(user_id)

        return {
            "earned": [
                {
                    "id": a.id,
                    "key": a.achievement_key,
                    "title": a.title,
                    "icon": a.icon,
                    "points": a.points_earned,
                    "earned_at": a.earned_at.isoformat(),
                    "is_showcased": a.is_showcased,
                }
                for a in earned
            ],
            "available": [
                {
                    "id": a["achievement"].id,
                    "key": a["achievement"].key,
                    "title": a["achievement"].title,
                    "description": a["achievement"].description,
                    "icon": a["achievement"].icon,
                    "points": a["achievement"].points,
                    "criteria_value": a["achievement"].criteria_value,
                    "progress": a["progress"],
                    "progress_percentage": a["progress_percentage"],
                }
                for a in available
            ],
            "level_progress": level_progress,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/achievements/{achievement_id}/showcase")
async def showcase_achievement(
    achievement_id: str,
    user_id: str = Depends(get_current_user_id),
    service: LearningService = Depends(get_service),
):
    """Showcase an achievement on profile"""
    try:
        success = service.achievement_system.showcase_achievement(user_id, achievement_id)

        if not success:
            raise HTTPException(status_code=404, detail="Achievement not found")

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === Quizzes ===

@router.get("/quizzes")
async def list_quizzes(
    specialty: Optional[str] = None,
    difficulty: Optional[DifficultyLevel] = None,
    service: LearningService = Depends(get_service),
):
    """List available quizzes"""
    try:
        # In production, would have database query
        all_quizzes = list(service.quiz_system.quizzes.values())

        # Filter
        if specialty:
            all_quizzes = [q for q in all_quizzes if q.specialty == specialty]

        if difficulty:
            all_quizzes = [q for q in all_quizzes if q.difficulty == difficulty]

        return {
            "quizzes": [
                {
                    "id": q.id,
                    "title": q.title,
                    "description": q.description,
                    "specialty": q.specialty,
                    "difficulty": q.difficulty,
                    "total_questions": q.total_questions,
                    "estimated_time_minutes": q.estimated_time_minutes,
                    "cme_credits": q.cme_credits,
                    "average_score": q.average_score,
                    "attempt_count": q.attempt_count,
                }
                for q in all_quizzes
                if q.is_active
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quizzes/start")
async def start_quiz(
    quiz_id: str,
    user_id: str = Depends(get_current_user_id),
    service: LearningService = Depends(get_service),
):
    """Start a quiz attempt"""
    try:
        attempt = service.quiz_system.start_quiz(user_id, quiz_id)
        quiz = service.quiz_system.get_quiz(quiz_id)

        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found")

        # Return quiz with questions (without answers)
        return {
            "attempt_id": attempt.id,
            "quiz": {
                "id": quiz.id,
                "title": quiz.title,
                "description": quiz.description,
                "total_questions": quiz.total_questions,
                "questions": [
                    {
                        "id": q.id,
                        "question_type": q.question_type,
                        "question_text": q.question_text,
                        "question_context": q.question_context,
                        "image_url": q.image_url,
                        "options": [
                            {"text": opt["text"]}
                            for opt in q.options
                        ] if q.question_type == QuestionType.MULTIPLE_CHOICE else None,
                        "points": q.points,
                    }
                    for q in quiz.questions
                ],
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quizzes/submit-answer")
async def submit_quiz_answer(
    attempt_id: str,
    request: QuizAnswerRequest,
    user_id: str = Depends(get_current_user_id),
    service: LearningService = Depends(get_service),
):
    """Submit answer to a quiz question"""
    try:
        result = service.quiz_system.submit_answer(
            attempt_id=attempt_id,
            question_id=request.question_id,
            answer=request.answer,
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/quizzes/complete")
async def complete_quiz(
    attempt_id: str,
    user_id: str = Depends(get_current_user_id),
    service: LearningService = Depends(get_service),
):
    """Complete quiz and get results"""
    try:
        attempt = service.quiz_system.complete_quiz(attempt_id)

        # Track completion and award credits
        result = service.track_quiz_completion(user_id, attempt.quiz_id, attempt)

        return {
            "attempt": {
                "id": attempt.id,
                "score": attempt.score,
                "passed": attempt.passed,
                "correct_count": attempt.correct_count,
                "incorrect_count": attempt.incorrect_count,
                "time_taken_seconds": attempt.time_taken_seconds,
                "cme_credits_earned": attempt.cme_credits_earned,
                "points_earned": attempt.points_earned,
            },
            "cme_credit": result.get("cme_credit"),
            "new_achievements": [
                {"title": a.title, "icon": a.icon, "points": a.points_earned}
                for a in result.get("new_achievements", [])
            ],
            "streak": result.get("streak"),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quizzes/history")
async def get_quiz_history(
    user_id: str = Depends(get_current_user_id),
    service: LearningService = Depends(get_service),
):
    """Get user's quiz history"""
    try:
        attempts = service.quiz_system.get_user_attempts(user_id)
        performance = service.quiz_system.get_quiz_performance(user_id)

        return {
            "history": [
                {
                    "id": a.id,
                    "quiz_id": a.quiz_id,
                    "score": a.score,
                    "passed": a.passed,
                    "time_taken_seconds": a.time_taken_seconds,
                    "completed_at": a.completed_at.isoformat() if a.completed_at else None,
                }
                for a in attempts[:20]  # Last 20 attempts
            ],
            "performance": performance,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === Learning Paths ===

@router.get("/paths")
async def list_learning_paths(
    specialty: Optional[str] = None,
    difficulty: Optional[DifficultyLevel] = None,
    featured: Optional[bool] = None,
    service: LearningService = Depends(get_service),
):
    """List available learning paths"""
    try:
        paths = service.path_manager.get_all_paths(
            specialty=specialty,
            difficulty=difficulty,
            is_featured=featured,
        )

        return {
            "paths": [
                {
                    "id": p.id,
                    "title": p.title,
                    "description": p.description,
                    "specialty": p.specialty,
                    "difficulty": p.difficulty,
                    "total_modules": p.total_modules,
                    "estimated_hours": p.estimated_hours,
                    "total_cme_credits": p.total_cme_credits,
                    "enrollment_count": p.enrollment_count,
                    "average_rating": p.average_rating,
                    "is_featured": p.is_featured,
                }
                for p in paths
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/paths/recommended")
async def get_recommended_paths(
    specialty: Optional[str] = None,
    limit: int = 5,
    user_id: str = Depends(get_current_user_id),
    service: LearningService = Depends(get_service),
):
    """Get recommended learning paths"""
    try:
        paths = service.get_recommended_paths(user_id, specialty, limit)

        return {
            "paths": [
                {
                    "id": p.id,
                    "title": p.title,
                    "description": p.description,
                    "specialty": p.specialty,
                    "difficulty": p.difficulty,
                    "estimated_hours": p.estimated_hours,
                    "total_cme_credits": p.total_cme_credits,
                }
                for p in paths
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/paths/{path_id}/enroll")
async def enroll_in_path(
    path_id: str,
    user_id: str = Depends(get_current_user_id),
    service: LearningService = Depends(get_service),
):
    """Enroll in a learning path"""
    try:
        enrollment = service.enroll_in_path(user_id, path_id)

        return {
            "enrollment_id": enrollment.id,
            "path_id": enrollment.path_id,
            "status": enrollment.status,
            "progress_percentage": enrollment.progress_percentage,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/paths/my-paths")
async def get_my_paths(
    user_id: str = Depends(get_current_user_id),
    service: LearningService = Depends(get_service),
):
    """Get user's enrolled paths"""
    try:
        active = service.path_manager.get_active_enrollments(user_id)
        completed = service.path_manager.get_completed_paths(user_id)

        return {
            "active": [
                {
                    "enrollment_id": e.id,
                    "path_id": e.path_id,
                    "status": e.status,
                    "progress_percentage": e.progress_percentage,
                    "current_module_id": e.current_module_id,
                    "enrolled_at": e.enrolled_at.isoformat(),
                }
                for e in active
            ],
            "completed": [
                {
                    "enrollment_id": e.id,
                    "path_id": e.path_id,
                    "progress_percentage": e.progress_percentage,
                    "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                    "cme_credits_earned": e.cme_credits_earned,
                    "rating": e.rating,
                }
                for e in completed
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/paths/{path_id}/modules/{module_id}/complete")
async def complete_module(
    path_id: str,
    module_id: str,
    time_spent_seconds: int = 0,
    user_id: str = Depends(get_current_user_id),
    service: LearningService = Depends(get_service),
):
    """Mark a module as completed"""
    try:
        result = service.complete_path_module(
            user_id=user_id,
            path_id=path_id,
            module_id=module_id,
            time_spent_seconds=time_spent_seconds,
        )

        return {
            "enrollment": {
                "status": result["enrollment"].status,
                "progress_percentage": result["enrollment"].progress_percentage,
                "current_module_id": result["enrollment"].current_module_id,
            },
            "cme_credits_earned": result.get("cme_credit").credits if result.get("cme_credit") else 0,
            "path_completed": result["enrollment"].status == "completed",
            "certificate": result.get("certificate"),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/paths/{path_id}/rate")
async def rate_path(
    path_id: str,
    request: PathRatingRequest,
    user_id: str = Depends(get_current_user_id),
    service: LearningService = Depends(get_service),
):
    """Rate a completed learning path"""
    try:
        enrollment = service.path_manager.rate_path(
            user_id=user_id,
            path_id=path_id,
            rating=request.rating,
            feedback=request.feedback,
        )

        return {"success": True, "rating": enrollment.rating}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === Analytics ===

@router.get("/analytics")
async def get_analytics(
    days: int = 30,
    user_id: str = Depends(get_current_user_id),
    service: LearningService = Depends(get_service),
):
    """Get learning analytics"""
    try:
        analytics = service.get_analytics(user_id, days=days)

        return {
            "period": {
                "start": analytics.period_start.isoformat(),
                "end": analytics.period_end.isoformat(),
            },
            "summary": {
                "total_activities": analytics.total_activities,
                "total_time_spent_seconds": analytics.total_time_spent_seconds,
                "total_time_spent_hours": analytics.total_time_spent_seconds / 3600,
                "total_cme_credits": analytics.total_cme_credits,
            },
            "streaks": {
                "current_streak": analytics.current_streak,
                "longest_streak": analytics.longest_streak,
            },
            "activities_by_type": analytics.activities_by_type,
            "credits_by_specialty": analytics.credits_by_specialty,
            "quiz_performance": {
                "total_quizzes": analytics.total_quizzes,
                "quizzes_passed": analytics.quizzes_passed,
                "average_score": analytics.average_quiz_score,
            },
            "top_topics": analytics.top_topics,
            "weak_areas": analytics.weak_areas,
            "achievements": {
                "earned": analytics.achievements_earned,
                "total_points": analytics.total_points,
                "current_level": analytics.current_level,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === Activity Tracking ===

@router.post("/track/query")
async def track_query(
    request: TrackQueryRequest,
    user_id: str = Depends(get_current_user_id),
    service: LearningService = Depends(get_service),
):
    """Track a medical query"""
    try:
        result = service.track_query(
            user_id=user_id,
            query_id=request.query_id,
            query_text=request.query_text,
            specialty=request.specialty,
            topics=request.topics,
            duration_seconds=request.duration_seconds,
            confidence_score=request.confidence_score,
            has_follow_up=request.has_follow_up,
        )

        return {
            "success": True,
            "cme_credits_earned": result["cme_credit"].credits if result["cme_credit"] else 0,
            "points_earned": result["activity"].points_earned,
            "new_achievements": [
                {"title": a.title, "icon": a.icon}
                for a in result["new_achievements"]
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
