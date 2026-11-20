"""Identity and membership models: User, SchoolMembership, ClassMembership.

Separates global user identity from tenant-specific permissions and class assignments.
"""

from sqlalchemy import Boolean, Column, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base, TimestampMixin, generate_uuid


class User(Base, TimestampMixin):
    """Global user identity."""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(200), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Relationships
    school_memberships = relationship("SchoolMembership", back_populates="user", cascade="all, delete-orphan")
    class_memberships = relationship("ClassMembership", back_populates="user", cascade="all, delete-orphan")


class SchoolMembership(Base, TimestampMixin):
    """Associates a User with a specific School tenant under a designated role."""

    __tablename__ = "school_memberships"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="teacher")  # teacher, coordinator, admin
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("school_id", "user_id", name="uq_school_user_membership"),
    )

    # Relationships
    school = relationship("School", back_populates="memberships")
    user = relationship("User", back_populates="school_memberships")


class ClassMembership(Base, TimestampMixin):
    """Authorizes a teacher to inspect, grade, and create interventions for a classroom."""

    __tablename__ = "class_memberships"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    school_id = Column(String(36), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    classroom_id = Column(String(36), ForeignKey("classrooms.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    is_primary = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("classroom_id", "user_id", name="uq_class_user_membership"),
    )

    # Relationships
    classroom = relationship("Classroom", back_populates="teacher_memberships")
    user = relationship("User", back_populates="class_memberships")
