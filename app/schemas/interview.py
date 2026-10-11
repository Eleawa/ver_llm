"""Pydantic schemas for interview question generation and candidate answer evaluation."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class SeniorityLevel(str, Enum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionType(str, Enum):
    CONCEPTUAL = "conceptual"
    BEHAVIORAL = "behavioral"
    SYSTEM_DESIGN = "system_design"
    SCENARIO = "scenario"
    PROBLEM_SOLVING = "problem_solving"


class QuestionGenerationRequest(BaseModel):
    role: str = Field(..., description="Target job role, e.g. 'Backend Engineer'")
    level: SeniorityLevel = Field(..., description="Seniority level, e.g. 'senior'")
    topic: str = Field(..., description="Technical or behavioral topic/competency domain, e.g. 'Concurrency & Locking'")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level, e.g. 'medium'")
    context: Optional[str] = Field(None, description="Optional job description, CV excerpt, or prior context")


class EvaluationCriterionRubric(BaseModel):
    name: str = Field(..., description="Criterion name, e.g. 'Technical Accuracy'")
    weight: float = Field(default=1.0, ge=0.1, le=5.0, description="Criterion weight multiplier")
    description: str = Field(..., description="Guideline for scoring this criterion from 0 to 5")


class QuestionResponse(BaseModel):
    question_id: str = Field(..., description="Unique question identifier")
    question: str = Field(..., description="Verbal interview question text")
    topic: str = Field(..., description="Interview topic")
    competency: str = Field(..., description="Primary competency being evaluated")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level")
    question_type: QuestionType = Field(..., description="Category of the question")
    evaluation_criteria: List[EvaluationCriterionRubric] = Field(
        ..., min_length=1, description="Rubric criteria for evaluating candidate responses"
    )
    expected_answer_points: List[str] = Field(
        ..., min_length=1, description="Key concepts or points expected in a solid answer"
    )


class AnswerEvaluationRequest(BaseModel):
    question_id: str = Field(..., description="Question identifier being answered")
    question: str = Field(..., description="Original interview question text")
    candidate_answer: str = Field(..., description="Candidate transcript or answer text")
    rubric: List[EvaluationCriterionRubric] = Field(..., min_length=1, description="Evaluation rubric criteria")
    expected_answer_points: List[str] = Field(
        default_factory=list, description="Key concepts or reference answer points"
    )
    max_score: float = Field(default=5.0, gt=0, description="Maximum scale score, default 5.0")


class CriterionScore(BaseModel):
    criterion_name: str = Field(..., description="Name matching the rubric criterion")
    score: float = Field(..., ge=0.0, le=5.0, description="Score on 0.0 to 5.0 scale")
    reasoning: str = Field(..., description="Justification grounded in candidate answer")


class AnswerEvaluationResponse(BaseModel):
    question_id: str = Field(..., description="Question identifier")
    overall_score: float = Field(..., ge=0.0, description="Calculated overall score")
    max_score: float = Field(default=5.0, gt=0, description="Maximum possible score")
    criterion_scores: List[CriterionScore] = Field(..., min_length=1, description="Scores per rubric criterion")
    strengths: List[str] = Field(default_factory=list, description="Candidate strengths observed")
    improvements: List[str] = Field(default_factory=list, description="Specific areas for candidate improvement")
    missing_concepts: List[str] = Field(default_factory=list, description="Key expected concepts omitted")
    evidence_from_answer: List[str] = Field(
        default_factory=list, description="Direct quotes or grounded evidence from candidate response"
    )
    needs_follow_up: bool = Field(..., description="Flag indicating if a clarifying or follow-up question is needed")
    feedback: str = Field(..., description="Constructive spoken/verbal feedback for candidate")

    @model_validator(mode="after")
    def validate_scores(self) -> "AnswerEvaluationResponse":
        if self.overall_score > self.max_score:
            raise ValueError(f"overall_score ({self.overall_score}) cannot exceed max_score ({self.max_score})")
        return self


# Internal schemas used for Gemini Structured Output
class LLMQuestionGenerationOutput(BaseModel):
    question: str = Field(..., description="Interview question text suitable for a spoken interview")
    competency: str = Field(..., description="Competency evaluated")
    question_type: QuestionType = Field(..., description="Category of the question")
    evaluation_criteria: List[EvaluationCriterionRubric] = Field(..., min_length=1)
    expected_answer_points: List[str] = Field(..., min_length=1)


class LLMCriterionScoreOutput(BaseModel):
    criterion_name: str
    score: float = Field(..., ge=0.0, le=5.0)
    reasoning: str


class LLMAnswerEvaluationOutput(BaseModel):
    criterion_scores: List[LLMCriterionScoreOutput] = Field(..., min_length=1)
    strengths: List[str]
    improvements: List[str]
    missing_concepts: List[str]
    evidence_from_answer: List[str]
    needs_follow_up: bool
    feedback: str
