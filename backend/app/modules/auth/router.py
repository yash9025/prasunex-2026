"""Authentication routes: login, token issuance, demo identity switch, and GET /v1/me."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AuthenticationError
from app.core.request_context import RequestContext, get_current_request_context
from app.core.security import create_access_token, verify_password
from app.modules.auth.models import SchoolMembership, User, ClassMembership
from app.modules.auth.schemas import (
    LoginRequest,
    MeResponse,
    SchoolMembershipOut,
    TokenResponse,
    UserOut,
)
from app.modules.classrooms.models import School

router = APIRouter(prefix="", tags=["Authentication & Identity"])


@router.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticates credentials against persistent User table and returns signed JWT."""
    user = db.query(User).filter(User.email == request.email.lower(), User.is_active == True).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise AuthenticationError("Invalid email or password.")

    # Fetch memberships
    memberships = (
        db.query(SchoolMembership, School)
        .join(School, SchoolMembership.school_id == School.id)
        .filter(SchoolMembership.user_id == user.id, SchoolMembership.is_active == True)
        .all()
    )
    if not memberships:
        raise AuthenticationError("User account has no active school assignment.")

    first_membership, first_school = memberships[0]
    token = create_access_token(
        subject=user.id,
        claims={"school_id": first_school.id, "role": first_membership.role},
    )

    return TokenResponse(
        access_token=token,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=UserOut.model_validate(user),
        active_school=SchoolMembershipOut(
            school_id=first_school.id,
            school_name=first_school.name,
            school_code=first_school.code,
            role=first_membership.role,
        ),
    )


@router.get("/me", response_model=MeResponse)
def get_current_actor(
    ctx: RequestContext = Depends(get_current_request_context),
    db: Session = Depends(get_db),
):
    """Returns verified server-side identity, active school context, and authorized classes."""
    memberships = (
        db.query(SchoolMembership, School)
        .join(School, SchoolMembership.school_id == School.id)
        .filter(SchoolMembership.user_id == ctx.user_id, SchoolMembership.is_active == True)
        .all()
    )

    membership_list = [
        SchoolMembershipOut(
            school_id=m.School.id,
            school_name=m.School.name,
            school_code=m.School.code,
            role=m.SchoolMembership.role,
        )
        for m in memberships
    ]

    return MeResponse(
        id=ctx.user_id,
        email=ctx.email,
        full_name=ctx.full_name,
        active_school_id=ctx.school_id,
        active_school_name=ctx.school_name,
        role=ctx.role,
        memberships=membership_list,
        authorized_class_ids=ctx.authorized_class_ids,
    )
