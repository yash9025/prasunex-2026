"""Classroom domain models: School, Classroom, and Learner.

Includes synthetic indicators, composite school uniqueness constraints,
and foreign key links adhering to Section 6 of the specification.
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base, TimestampMixin, generate_uuid


class School(Base, TimestampMixin):
    """Educational institution / tenant entity."""

    __tablename__ = "schools"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    classrooms = relationship("Classroom", back_populates="school", cascade="all, delete-orphan")
    memberships = relationship("SchoolMembership", back_populates="school", cascade="all, delete-orphan")
    learners = relationship("Learner", back_populates="school", cascade="all, delete-orphan")


class Classroom(Base, TimestampMixin):
    """Class section / cohort within a school (e.g., Grade 6 - Section A)."""

    __tablename__ = "classrooms"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    grade_level = Column(Integer, nullable=False)
    section = Column(String(20), nullable=False)
    academic_year = Column(String(20), nullable=False, default="2026-2027")

    __table_args__ = (
        UniqueConstraint("school_id", "name", "academic_year", name="uq_classroom_school_name_year"),
    )

    # Relationships
    school = relationship("School", back_populates="classrooms")
    learners = relationship("Learner", back_populates="classroom", cascade="all, delete-orphan")
    teacher_memberships = relationship("ClassMembership", back_populates="classroom", cascade="all, delete-orphan")


class Learner(Base, TimestampMixin):
    """Enrolled student within a classroom. Explicitly flagged when synthetic."""

    __tablename__ = "learners"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    classroom_id = Column(String(36), ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False, index=True)
    external_ref = Column(String(50), nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    is_synthetic = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("school_id", "external_ref", name="uq_learner_school_external_ref"),
    )

    # Relationships
    school = relationship("School", back_populates="learners")
    classroom = relationship("Classroom", back_populates="learners")
