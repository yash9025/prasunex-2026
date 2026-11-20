"""Classroom and learner response schemas."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class SchoolOut(BaseModel):
    """Educational institution / school summary."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    code: str
    is_active: bool


class LearnerOut(BaseModel):
    """Enrolled student details with synthetic safety indicator."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    classroom_id: str
    external_ref: str
    first_name: str
    last_name: str
    is_synthetic: bool = True


class ClassroomOut(BaseModel):
    """Class section / cohort summary."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    school_id: str
    name: str
    grade_level: int
    section: str
    academic_year: str
    learner_count: int = 0


class ClassroomDetailOut(ClassroomOut):
    """Classroom overview including enrolled learners."""

    learners: List[LearnerOut] = Field(default_factory=list)


class ClassOverviewMetric(BaseModel):
    """Aggregate statistics for class overview per Section 7.1 & Phase 3."""

    total_learners: int
    synthetic_count: int
    pending_actions_count: int = 0
    active_assessments_count: int = 0
    confirmed_count: int = 0
    groups_count: int = 0
