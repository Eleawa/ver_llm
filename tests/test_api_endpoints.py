"""FastAPI integration tests mocking the service layer."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.main import app, get_service
from app.schemas.interview import (
    AnswerEvaluationResponse,
    CriterionScore,
    DifficultyLevel,
    EvaluationCriterionRubric,
    QuestionResponse,
    QuestionType,
)

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


def test_api_generate_question(monkeypatch):
    mock_svc = MagicMock()
    mock_q = QuestionResponse(
        question_id="Q-TEST-1234",
        question="How does indexing improve SQL query performance?",
        topic="Databases",
        competency="Query Optimization",
        difficulty=DifficultyLevel.MEDIUM,
        question_type=QuestionType.CONCEPTUAL,
        evaluation_criteria=[
            EvaluationCriterionRubric(name="B-Tree Structure", weight=1.0, description="Explains B-Tree search")
        ],
        expected_answer_points=["Reduces full table scans to log(N) lookups"],
    )
    mock_svc.generate_question.return_value = mock_q
    app.dependency_overrides[get_service] = lambda: mock_svc

    response = client.post(
        "/interview/questions",
        json={
            "role": "Backend Engineer",
            "level": "mid",
            "topic": "Databases",
            "difficulty": "medium",
        },
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["question_id"] == "Q-TEST-1234"
    assert res_data["question"] == "How does indexing improve SQL query performance?"

    app.dependency_overrides.clear()


def test_api_evaluate_answer(monkeypatch):
    mock_svc = MagicMock()
    mock_eval = AnswerEvaluationResponse(
        question_id="Q-TEST-1234",
        overall_score=4.5,
        max_score=5.0,
        criterion_scores=[
            CriterionScore(criterion_name="B-Tree Structure", score=4.5, reasoning="Clear explanation.")
        ],
        strengths=["Understands search complexity."],
        improvements=[],
        missing_concepts=[],
        evidence_from_answer=["Indexes use B-trees"],
        needs_follow_up=False,
        feedback="Very good answer.",
    )
    mock_svc.evaluate_answer.return_value = mock_eval
    app.dependency_overrides[get_service] = lambda: mock_svc

    response = client.post(
        "/interview/evaluate",
        json={
            "question_id": "Q-TEST-1234",
            "question": "How does indexing improve SQL query performance?",
            "candidate_answer": "Indexes use B-trees to avoid full table scans, reducing disk I/O.",
            "rubric": [
                {"name": "B-Tree Structure", "weight": 1.0, "description": "Explains B-Tree search"}
            ],
            "expected_answer_points": ["Reduces full table scans"],
            "max_score": 5.0,
        },
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["overall_score"] == 4.5
    assert res_data["needs_follow_up"] is False

    app.dependency_overrides.clear()


def test_api_invalid_request_validation():
    # Missing required field 'role'
    response = client.post(
        "/interview/questions",
        json={
            "level": "mid",
            "topic": "Databases",
            "difficulty": "medium",
        },
    )
    assert response.status_code == 422
