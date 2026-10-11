"""Custom interview question dataset repository interface and synthetic fixture."""

import json
from pathlib import Path
from typing import List, Optional
from app.schemas.interview import (
    DifficultyLevel,
    EvaluationCriterionRubric,
    QuestionResponse,
    QuestionType,
    SeniorityLevel,
)


class QuestionRepository:
    """Interface and in-memory implementation for question dataset storage."""

    def __init__(self, data_path: Optional[str] = None):
        self._questions: List[QuestionResponse] = []
        if data_path and Path(data_path).exists():
            self.load_from_file(data_path)
        else:
            self._load_default_fixtures()

    def _load_default_fixtures(self):
        """Loads curated synthetic interview questions for testing and offline fallback."""
        fixtures = [
            QuestionResponse(
                question_id="Q-BE-SENIOR-CONCURRENCY-001",
                question="Can you explain how optimistic locking differs from pessimistic locking in database transactions, and how you would choose between them in a high-throughput microservice?",
                topic="Concurrency & Databases",
                competency="Distributed Systems & Data Consistency",
                difficulty=DifficultyLevel.HARD,
                question_type=QuestionType.SYSTEM_DESIGN,
                evaluation_criteria=[
                    EvaluationCriterionRubric(
                        name="Technical Accuracy",
                        weight=1.5,
                        description="Accurately defines optimistic (version/timestamp check at commit) vs pessimistic (row/table locking during read) locking.",
                    ),
                    EvaluationCriterionRubric(
                        name="Trade-off Analysis",
                        weight=1.2,
                        description="Analyzes contention, latency, lock contention overhead, and abort/retry storms under high write load.",
                    ),
                    EvaluationCriterionRubric(
                        name="Practical Application",
                        weight=1.0,
                        description="Provides realistic microservice architectural examples (e.g., inventory deduction vs reading user profile).",
                    ),
                ],
                expected_answer_points=[
                    "Pessimistic locking takes explicit lock on read (SELECT ... FOR UPDATE) preventing concurrent writes/reads.",
                    "Optimistic locking assumes low conflict, validates version/timestamp during UPDATE without blocking reads.",
                    "Optimistic locking is ideal for read-heavy or low-contention environments to maximize throughput.",
                    "Pessimistic locking avoids expensive rollback/retry loops when contention is very high on the same entity.",
                ],
            ),
            QuestionResponse(
                question_id="Q-BE-MID-SPRING-001",
                question="In Spring Boot, how does the @Transactional annotation work under the hood, and what common pitfalls might prevent it from applying rollback behavior?",
                topic="Spring Framework",
                competency="Framework Internals & Transaction Management",
                difficulty=DifficultyLevel.MEDIUM,
                question_type=QuestionType.CONCEPTUAL,
                evaluation_criteria=[
                    EvaluationCriterionRubric(
                        name="AOP Proxy Knowledge",
                        weight=1.5,
                        description="Understands dynamic proxies / CGLIB and self-invocation limitations.",
                    ),
                    EvaluationCriterionRubric(
                        name="Exception Rollback Rules",
                        weight=1.2,
                        description="Explains default rollback only on unchecked (RuntimeException/Error) vs checked exceptions.",
                    ),
                ],
                expected_answer_points=[
                    "Spring uses AOP proxies to intercept method calls and manage begin/commit/rollback.",
                    "Self-invocation (calling a transactional method from within the same class) bypasses the proxy.",
                    "By default, Spring only rolls back on unchecked (RuntimeException and Error), requiring rollbackFor for checked exceptions.",
                    "Transactional methods must usually be public to be proxied correctly.",
                ],
            ),
            QuestionResponse(
                question_id="Q-FE-JUNIOR-REACT-001",
                question="What is the difference between state and props in React, and when should you use each one?",
                topic="React",
                competency="Frontend Fundamentals",
                difficulty=DifficultyLevel.EASY,
                question_type=QuestionType.CONCEPTUAL,
                evaluation_criteria=[
                    EvaluationCriterionRubric(
                        name="Fundamental Concepts",
                        weight=1.5,
                        description="Accurately defines props as immutable inputs from parent and state as mutable component-managed data.",
                    ),
                    EvaluationCriterionRubric(
                        name="Clarity & Communication",
                        weight=1.0,
                        description="Clear, concise explanation suitable for spoken interview.",
                    ),
                ],
                expected_answer_points=[
                    "Props are passed into a component from its parent and are immutable to the component.",
                    "State is managed internally by the component and can change over time via setState or useState.",
                    "Changing state triggers a re-render of the component and its children.",
                ],
            ),
        ]
        self._questions = fixtures

    def load_from_file(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self._questions = [QuestionResponse(**item) for item in data]

    def save_to_file(self, file_path: str):
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump([q.model_dump() for q in self._questions], f, indent=2)

    def find_questions(
        self,
        topic: Optional[str] = None,
        difficulty: Optional[DifficultyLevel] = None,
    ) -> List[QuestionResponse]:
        results = []
        for q in self._questions:
            if topic and topic.lower() not in q.topic.lower() and topic.lower() not in q.competency.lower():
                continue
            if difficulty and q.difficulty != difficulty:
                continue
            results.append(q)
        return results

    def get_by_id(self, question_id: str) -> Optional[QuestionResponse]:
        for q in self._questions:
            if q.question_id == question_id:
                return q
        return None

    def add_question(self, question: QuestionResponse):
        self._questions.append(question)

    def count(self) -> int:
        return len(self._questions)
