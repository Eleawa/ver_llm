"""Tests for data repository and schema validation."""

import pytest
from pydantic import ValidationError
from app.data.repository import QuestionRepository
from app.schemas.interview import (
    AnswerEvaluationRequest,
    AnswerEvaluationResponse,
    CriterionScore,
    DifficultyLevel,
    EvaluationCriterionRubric,
    QuestionGenerationRequest,
    QuestionResponse,
    QuestionType,
    SeniorityLevel,
)


def test_question_repository_lookup():
    repo = QuestionRepository()
    assert repo.count() >= 3

    # Lookup by topic
    results = repo.find_questions(topic="concurrency")
    assert len(results) >= 1
    assert "locking" in results[0].question.lower()

    # Lookup by difficulty
    results_hard = repo.find_questions(difficulty=DifficultyLevel.HARD)
    assert len(results_hard) >= 1

    # Lookup by ID
    q = repo.get_by_id("Q-FE-JUNIOR-REACT-001")
    assert q is not None
    assert q.topic == "React"

    # Missing ID returns None
    assert repo.get_by_id("NON_EXISTENT_ID") is None


def test_question_generation_request_validation():
    # Valid request
    valid_req = QuestionGenerationRequest(
        role="Backend Engineer",
        level=SeniorityLevel.SENIOR,
        topic="Database Indexing",
        difficulty=DifficultyLevel.HARD,
    )
    assert valid_req.role == "Backend Engineer"
    assert valid_req.level == SeniorityLevel.SENIOR

    # Invalid enum
    with pytest.raises(ValidationError):
        QuestionGenerationRequest(
            role="Backend Engineer",
            level="super_ninja",  # invalid
            topic="Database Indexing",
            difficulty=DifficultyLevel.HARD,
        )


def test_answer_evaluation_response_score_boundary():
    # overall_score > max_score should fail validation
    with pytest.raises(ValidationError):
        AnswerEvaluationResponse(
            question_id="Q-1",
            overall_score=6.0,
            max_score=5.0,
            criterion_scores=[
                CriterionScore(criterion_name="Accuracy", score=6.0, reasoning="Over boundary")
            ],
            strengths=[],
            improvements=[],
            missing_concepts=[],
            evidence_from_answer=[],
            needs_follow_up=False,
            feedback="Good",
        )
