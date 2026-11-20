"""Server-side identity and tenant request context resolution.

Resolves actor permissions, active school membership, and authorized classes.
Guarantees client-provided payload fields cannot forge identity or access.
"""

from contextvars import ContextVar
from typing import List, Optional
import uuid

from fastapi import Depends, Header, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db, set_tenant_context
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import decode_access_token

# Bearer token extractor
security_bearer = HTTPBearer(auto_error=False)

# ContextVar for logging and thread-local / task-local tracing
_current_context_var: ContextVar[Optional["RequestContext"]] = ContextVar(
    "current_request_context", default=None
)


class RequestContext(BaseModel):
    """Server-resolved identity and tenant context for the active request."""

    user_id: str = Field(..., description="Authenticated user ID")
    email: str = Field(..., description="User email address")
    full_name: str = Field(..., description="User display name")
    school_id: str = Field(..., description="Resolved authorized school ID")
    school_name: str = Field(..., description="Name of the active school")
    role: str = Field(..., description="Role in current school: teacher, coordinator, admin")
    authorized_school_ids: List[str] = Field(default_factory=list)
    authorized_class_ids: List[str] = Field(default_factory=list)
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    def assert_class_access(self, classroom_id: str) -> None:
        """Enforces that the current actor is assigned to teach or manage the requested class."""
        if self.role in ("admin", "coordinator"):
            return
        if classroom_id not in self.authorized_class_ids:
            raise AuthorizationError(
                f"You do not have teaching permissions for class '{classroom_id}' in this school."
            )


def get_current_request_context(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    x_school_id: Optional[str] = Header(None, alias="X-School-ID"),
    db: Session = Depends(get_db),
) -> RequestContext:
    """FastAPI dependency resolving server-side authorization and school context."""
    # Read or assign Request-ID
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())

    if not credentials or not credentials.credentials:
        raise AuthenticationError("Authorization header with Bearer token is required.")

    # Validate signed JWT
    token_claims = decode_access_token(credentials.credentials)
    user_id = token_claims.get("sub")
    if not user_id:
        raise AuthenticationError("Malformed token: missing subject claim.")

    # Lazy import to avoid circular dependencies with auth models
    from app.modules.auth.models import User, SchoolMembership, ClassMembership
    from app.modules.classrooms.models import School

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise AuthenticationError("User account not found or has been deactivated.")

    # Server-side resolution of memberships
    memberships = (
        db.query(SchoolMembership, School)
        .join(School, SchoolMembership.school_id == School.id)
        .filter(SchoolMembership.user_id == user_id, SchoolMembership.is_active == True)
        .all()
    )

    if not memberships:
        raise AuthorizationError("User is not assigned to any active school.")

    authorized_school_map = {m.School.id: (m.SchoolMembership, m.School) for m in memberships}
    authorized_school_ids = list(authorized_school_map.keys())

    # If client requests a specific school via X-School-ID header, verify membership
    selected_school_id = x_school_id or authorized_school_ids[0]
    if selected_school_id not in authorized_school_map:
        raise AuthorizationError(
            f"Access denied: You do not hold an active membership for school '{selected_school_id}'."
        )

    active_membership, active_school = authorized_school_map[selected_school_id]

    # Resolve authorized classes for this school
    class_memberships = (
        db.query(ClassMembership.classroom_id)
        .filter(
            ClassMembership.user_id == user_id,
            ClassMembership.school_id == selected_school_id,
        )
        .all()
    )
    authorized_class_ids = [cm[0] for cm in class_memberships]

    # Apply database session RLS tenant context
    set_tenant_context(db, selected_school_id)

    ctx = RequestContext(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        school_id=active_school.id,
        school_name=active_school.name,
        role=active_membership.role,
        authorized_school_ids=authorized_school_ids,
        authorized_class_ids=authorized_class_ids,
        request_id=req_id,
    )

    _current_context_var.set(ctx)
    return ctx
