"""Unit tests for RequestContext assertion methods."""

import pytest
from app.core.exceptions import AuthorizationError
from app.core.request_context import RequestContext


def test_request_context_class_access():
    ctx = RequestContext(
        user_id="usr-1",
        email="test@school.edu",
        full_name="Test Teacher",
        school_id="sch-1",
        school_name="Test School",
        role="teacher",
        authorized_class_ids=["cls-6a", "cls-6b"],
    )

    # Authorized class should pass silently
    ctx.assert_class_access("cls-6a")
    ctx.assert_class_access("cls-6b")

    # Unauthorized class should raise AuthorizationError (403)
    with pytest.raises(AuthorizationError) as exc_info:
        ctx.assert_class_access("cls-foreign-7c")
    assert "do not have teaching permissions" in str(exc_info.value.message)


def test_coordinator_bypasses_specific_class_assignment():
    ctx = RequestContext(
        user_id="usr-coord",
        email="coord@school.edu",
        full_name="Coordinator User",
        school_id="sch-1",
        school_name="Test School",
        role="coordinator",
        authorized_class_ids=[],
    )

    # Coordinator can inspect any class in their school
    ctx.assert_class_access("cls-any-class")
