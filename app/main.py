"""FastAPI Application exposing interview intelligence endpoints for VERNITA."""

import logging
from typing import Optional
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from google.genai.errors import APIError

from app.config import settings
from app.schemas.interview import (
    AnswerEvaluationRequest,
    AnswerEvaluationResponse,
    QuestionGenerationRequest,
    QuestionResponse,
)
from app.services.interview_service import InterviewLLMService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vernita_llm")

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="VERNITA LLM Module - Spoken Interview Question Generation and Evaluation API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service: Optional[InterviewLLMService] = None


def get_service() -> InterviewLLMService:
    global service
    if service is None:
        service = InterviewLLMService()
    return service


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.api_title,
        "model": settings.gemini_model,
        "has_api_key": bool(settings.gemini_api_key),
    }


@app.post(
    "/interview/questions",
    response_model=QuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate an interview question",
    description="Generates a role-specific interview question with rubric and expected answer concepts.",
)
def generate_interview_question(
    request: QuestionGenerationRequest,
    svc: InterviewLLMService = Depends(get_service),
):
    try:
        return svc.generate_question(request)
    except ValueError as e:
        logger.error(f"Configuration or validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "ConfigurationError", "message": str(e)},
        )
    except APIError as e:
        logger.error(f"Gemini API error during question generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": "GeminiAPIError", "message": str(e)},
        )
    except Exception as e:
        logger.exception("Unexpected error generating question")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalError", "message": str(e)},
        )


@app.post(
    "/interview/evaluate",
    response_model=AnswerEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate a candidate's answer",
    description="Evaluates a candidate's transcribed spoken answer against rubric criteria and expected points.",
)
def evaluate_interview_answer(
    request: AnswerEvaluationRequest,
    svc: InterviewLLMService = Depends(get_service),
):
    try:
        return svc.evaluate_answer(request)
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "ValidationError", "message": str(e)},
        )
    except APIError as e:
        logger.error(f"Gemini API error during answer evaluation: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": "GeminiAPIError", "message": str(e)},
        )
    except Exception as e:
        logger.exception("Unexpected error evaluating answer")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "InternalError", "message": str(e)},
        )
