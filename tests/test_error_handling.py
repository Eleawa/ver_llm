"""Tests for error handling (API timeouts, quota errors, invalid responses)."""

import pytest
from unittest.mock import MagicMock
from google.genai.errors import APIError
from app.schemas.interview import (
    AnswerEvaluationRequest,
    DifficultyLevel,
    EvaluationCriterionRubric,
    QuestionGenerationRequest,
    SeniorityLevel,
)
from app.services.interview_service import InterviewLLMService


def test_gemini_api_error_raised():
    svc = InterviewLLMService(api_key="mock-key")
    mock_client = MagicMock()
    # Simulate an API error (quota / timeout)
    mock_client.models.generate_content.side_effect = APIError(
        code=429,
        response_json={"error": {"message": "Resource has been exhausted (e.g. check quota)."}},
    )
    svc._client = mock_client

    req = QuestionGenerationRequest(
        role="DevOps Engineer",
        level=SeniorityLevel.SENIOR,
        topic="Kubernetes Ingress",
        difficulty=DifficultyLevel.HARD,
    )

    with pytest.raises(APIError) as exc_info:
        svc.generate_question(req)

    assert "Resource has been exhausted" in str(exc_info.value)


def test_missing_api_key_raises_value_error():
    svc = InterviewLLMService(api_key="")
    req = QuestionGenerationRequest(
        role="DevOps Engineer",
        level=SeniorityLevel.SENIOR,
        topic="Kubernetes",
        difficulty=DifficultyLevel.MEDIUM,
    )
    with pytest.raises(ValueError) as exc_info:
        svc.generate_question(req)
    assert "GEMINI_API_KEY is not configured" in str(exc_info.value)
