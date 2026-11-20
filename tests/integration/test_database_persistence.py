"""Persistence test verifying data survival across session and connection restarts."""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.modules.classrooms.models import School, Classroom, Learner
from seeds.run_seed import OAKRIDGE_SCHOOL_ID, CLASS_6A_ID


def test_data_survives_session_restart():
    """Confirms persistent storage retains records across independent database connections."""
    db_file = Path("learningbridge.db")
    assert db_file.exists(), "Persistent database file learningbridge.db must exist."

    # Open completely new engine connection to test file persistence
    fresh_engine = create_engine(f"sqlite:///{db_file.name}")
    FreshSession = sessionmaker(bind=fresh_engine)

    with FreshSession() as session:
        # Verify School survives
        school = session.query(School).filter(School.id == OAKRIDGE_SCHOOL_ID).first()
        assert school is not None
        assert school.name == "Oakridge International Academy"

        # Verify Class 6-A survives
        classroom = session.query(Classroom).filter(Classroom.id == CLASS_6A_ID).first()
        assert classroom is not None
        assert classroom.name == "Grade 6 Mathematics"
        assert classroom.section == "A"

        # Verify 40 learners survive
        count = session.query(Learner).filter(Learner.classroom_id == CLASS_6A_ID).count()
        assert count == 40

    fresh_engine.dispose()
