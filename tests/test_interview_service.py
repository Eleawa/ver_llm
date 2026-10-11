"""Tests for question generation and candidate answer evaluation logic."""

import json
from unittest.mock import MagicMock
import pytest
from app.schemas.interview import (
    AnswerEvaluationRequest,
    DifficultyLevel,
    EvaluationCriterionRubric,
    QuestionGenerationRequest,
    SeniorityLevel,
)
from app.services.interview_service import InterviewLLMService


@pytest.fixture
def mock_service():
    service = InterviewLLMService(api_key="mock-api-key", model_name="gemini-2.5-flash")
    service._client = MagicMock()
    return service


def test_empty_or_silent_answer(mock_service):
    """Empty or near-empty answer should return score 0 without calling Gemini."""
    req = AnswerEvaluationRequest(
        question_id="Q-TEST-001",
        question="What is dependency injection?",
        candidate_answer="   ",
        rubric=[
            EvaluationCriterionRubric(name="Technical Accuracy", weight=1.0, description="Explains DI"),
        ],
        expected_answer_points=["Inversion of control", "Decoupling components"],
        max_score=5.0,
    )

    eval_result = mock_service.evaluate_answer(req)
    assert eval_result.overall_score == 0.0
    assert eval_result.needs_follow_up is True
    assert "No answer was provided" in eval_result.feedback
    assert len(eval_result.criterion_scores) == 1
    assert eval_result.criterion_scores[0].score == 0.0
    # Gemini client should not have been called
    mock_service.client.models.generate_content.assert_not_called()


def test_question_generation_mock(mock_service):
    mock_llm_json = json.dumps({
        "question": "Can you explain how Java garbage collection works, specifically marking and sweeping?",
        "competency": "Memory Management & JVM Internals",
        "question_type": "conceptual",
        "evaluation_criteria": [
            {"name": "Mark and Sweep Mechanism", "weight": 1.5, "description": "Explains phases accurately"},
            {"name": "Generational Heap", "weight": 1.0, "description": "Mentions Eden, Survivor, Tenured"},
        ],
        "expected_answer_points": [
            "Root objects traversal",
            "Marking live objects",
            "Sweeping dead objects",
            "Compaction to reduce fragmentation"
        ]
    })

    mock_response = MagicMock()
    mock_response.text = mock_llm_json
    mock_service.client.models.generate_content.return_value = mock_response

    req = QuestionGenerationRequest(
        role="Backend Engineer",
        level=SeniorityLevel.MID,
        topic="Java JVM Internals",
        difficulty=DifficultyLevel.MEDIUM,
    )

    result = mock_service.generate_question(req)
    assert result.question_id.startswith("Q-")
    assert "garbage collection" in result.question.lower()
    assert result.topic == "Java JVM Internals"
    assert len(result.evaluation_criteria) == 2
    assert len(result.expected_answer_points) == 4


def test_evaluate_strong_answer(mock_service):
    """Test 1: Strong, technically correct answer."""
    mock_llm_json = json.dumps({
        "criterion_scores": [
            {
                "criterion_name": "Technical Accuracy",
                "score": 5.0,
                "reasoning": "Candidate clearly explained optimistic locking using version numbers and pessimistic locking using database row locks."
            },
            {
                "criterion_name": "Trade-off Analysis",
                "score": 4.5,
                "reasoning": "Correctly identified that optimistic locking excels in low-contention environments, whereas pessimistic locking avoids retry storms in high write contention."
            }
        ],
        "strengths": [
            "Precise understanding of locking mechanisms",
            "Grounded understanding of concurrency bottlenecks"
        ],
        "improvements": [],
        "missing_concepts": [],
        "evidence_from_answer": [
            "Optimistic locking checks a version column on update",
            "Pessimistic locking issues a SELECT FOR UPDATE"
        ],
        "needs_follow_up": False,
        "feedback": "Outstanding answer. You clearly articulated both locking strategies and their respective trade-offs."
    })

    mock_response = MagicMock()
    mock_response.text = mock_llm_json
    mock_service.client.models.generate_content.return_value = mock_response

    req = AnswerEvaluationRequest(
        question_id="Q-BE-SENIOR-CONCURRENCY-001",
        question="Can you explain optimistic vs pessimistic locking?",
        candidate_answer="Optimistic locking checks a version column on update to ensure no collisions occurred, whereas pessimistic locking issues a SELECT FOR UPDATE to lock the row upfront.",
        rubric=[
            EvaluationCriterionRubric(name="Technical Accuracy", weight=1.5, description="Accurate definitions"),
            EvaluationCriterionRubric(name="Trade-off Analysis", weight=1.0, description="Contention trade-offs"),
        ],
        expected_answer_points=["Version check", "SELECT FOR UPDATE", "Contention impact"],
        max_score=5.0,
    )

    result = mock_service.evaluate_answer(req)
    # Expected weighted score: (5.0 * 1.5 + 4.5 * 1.0) / (2.5) = (7.5 + 4.5) / 2.5 = 12.0 / 2.5 = 4.8
    assert result.overall_score == 4.8
    assert result.needs_follow_up is False
    assert len(result.strengths) >= 1
    assert len(result.evidence_from_answer) == 2


def test_evaluate_partial_answer(mock_service):
    """Test 2: Partially correct answer with missing concepts and follow-up signal."""
    mock_llm_json = json.dumps({
        "criterion_scores": [
            {
                "criterion_name": "Technical Accuracy",
                "score": 3.0,
                "reasoning": "Candidate described pessimistic locking adequately but had a vague understanding of optimistic locking."
            },
            {
                "criterion_name": "Trade-off Analysis",
                "score": 2.0,
                "reasoning": "Did not explain performance trade-offs under high write contention."
            }
        ],
        "strengths": [
            "Understands that pessimistic locking holds a lock in the database"
        ],
        "improvements": [
            "Explain how optimistic locking detects conflicts using versioning or timestamps",
            "Discuss retry overhead during high contention"
        ],
        "missing_concepts": [
            "Version number check",
            "Retry storm trade-offs"
        ],
        "evidence_from_answer": [
            "Pessimistic locking locks the table so nobody else can touch it"
        ],
        "needs_follow_up": True,
        "feedback": "You understood the basic concept of pessimistic locking, but how does optimistic locking actually detect a collision when committing?"
    })

    mock_response = MagicMock()
    mock_response.text = mock_llm_json
    mock_service.client.models.generate_content.return_value = mock_response

    req = AnswerEvaluationRequest(
        question_id="Q-BE-SENIOR-CONCURRENCY-001",
        question="Can you explain optimistic vs pessimistic locking?",
        candidate_answer="Pessimistic locking locks the table so nobody else can touch it. Optimistic locking is when you just hope there's no conflict.",
        rubric=[
            EvaluationCriterionRubric(name="Technical Accuracy", weight=1.0, description="Accurate definitions"),
            EvaluationCriterionRubric(name="Trade-off Analysis", weight=1.0, description="Contention trade-offs"),
        ],
        expected_answer_points=["Version check", "SELECT FOR UPDATE", "Contention impact"],
        max_score=5.0,
    )

    result = mock_service.evaluate_answer(req)
    assert result.overall_score == 2.5
    assert result.needs_follow_up is True
    assert len(result.missing_concepts) == 2


def test_evaluate_incorrect_answer(mock_service):
    """Test 3: Incorrect answer."""
    mock_llm_json = json.dumps({
        "criterion_scores": [
            {
                "criterion_name": "Technical Accuracy",
                "score": 0.5,
                "reasoning": "Candidate confused database concurrency locking with thread synchronization mutexes in frontend UI."
            },
            {
                "criterion_name": "Trade-off Analysis",
                "score": 0.0,
                "reasoning": "Completely missed database transaction concepts."
            }
        ],
        "strengths": [],
        "improvements": [
            "Review ACID transactions and database concurrency control mechanisms."
        ],
        "missing_concepts": [
            "Optimistic concurrency control",
            "Pessimistic row locking",
            "Database transaction isolation"
        ],
        "evidence_from_answer": [
            "Optimistic locking is a CSS feature to prevent button clicks"
        ],
        "needs_follow_up": True,
        "feedback": "Your explanation confused database locking with UI state management."
    })

    mock_response = MagicMock()
    mock_response.text = mock_llm_json
    mock_service.client.models.generate_content.return_value = mock_response

    req = AnswerEvaluationRequest(
        question_id="Q-BE-SENIOR-CONCURRENCY-001",
        question="Can you explain optimistic vs pessimistic locking?",
        candidate_answer="Optimistic locking is a CSS feature to prevent button clicks twice on the frontend.",
        rubric=[
            EvaluationCriterionRubric(name="Technical Accuracy", weight=1.0, description="Accurate definitions"),
            EvaluationCriterionRubric(name="Trade-off Analysis", weight=1.0, description="Contention trade-offs"),
        ],
        expected_answer_points=["Version check", "SELECT FOR UPDATE", "Contention impact"],
        max_score=5.0,
    )

    result = mock_service.evaluate_answer(req)
    # Expected weighted score: (0.5 * 1.0 + 0.0 * 1.0) / 2.0 = 0.25
    assert result.overall_score == 0.25
    assert result.overall_score <= 1.0
    assert result.needs_follow_up is True
