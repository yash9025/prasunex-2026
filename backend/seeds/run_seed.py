"""Database seeding script for reproducible local and demo environments.

Seeds:
1. School 1: Oakridge International Academy with Teacher Priya Sharma, Class 6-A, 40 synthetic learners, 3 topics.
2. School 2: Pinegrove Public School with Teacher David Chen, Class 6-B, 10 synthetic learners.
"""

import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal, Base, engine
from app.core.security import hash_password
from app.modules.classrooms.models import School, Classroom, Learner
from app.modules.auth.models import User, SchoolMembership, ClassMembership
from app.modules.evidence.models import Topic
from app.modules.plans.models import ApprovedSnippet

# Deterministic IDs for reproducible testing and fixtures
OAKRIDGE_SCHOOL_ID = "sch-oakridge-001"
PINEGROVE_SCHOOL_ID = "sch-pinegrove-002"

TEACHER_PRIYA_ID = "usr-priya-001"
TEACHER_DAVID_ID = "usr-david-002"

CLASS_6A_ID = "cls-oak-6a-001"
CLASS_6B_ID = "cls-png-6b-002"

TOPIC_FRAC_ID = "top-frac-001"
TOPIC_DEC_ID = "top-dec-001"
TOPIC_PCT_ID = "top-pct-001"

SYNTHETIC_LEARNER_NAMES = [
    ("SYN-L6-001", "Ananya", "Sharma"),
    ("SYN-L6-002", "Aditya", "Verma"),
    ("SYN-L6-003", "Bhavya", "Reddy"),
    ("SYN-L6-004", "Chirag", "Mehta"),
    ("SYN-L6-005", "Dev", "Iyer"),
    ("SYN-L6-006", "Esha", "Nambiar"),
    ("SYN-L6-007", "Farhan", "Khan"),
    ("SYN-L6-008", "Gauri", "Kulkarni"),
    ("SYN-L6-009", "Harsh", "Bansal"),
    ("SYN-L6-010", "Ishita", "Menon"),
    ("SYN-L6-011", "Jay", "Deshmukh"),
    ("SYN-L6-012", "Kavya", "Pillai"),
    ("SYN-L6-013", "Laksh", "Singhania"),
    ("SYN-L6-014", "Aarav", "Patel"),     # Primary 7/10 demo learner (1/3 in fractions)
    ("SYN-L6-015", "Diya", "Sen"),        # Matching fraction error pattern
    ("SYN-L6-016", "Kabir", "Nair"),      # 0/3 fractions
    ("SYN-L6-017", "Manav", "Chopra"),
    ("SYN-L6-018", "Neha", "Kapoor"),
    ("SYN-L6-019", "Om", "Pandey"),
    ("SYN-L6-020", "Rhea", "Varma"),      # Boundary 2/3 (66.7% - no flag)
    ("SYN-L6-021", "Ishaan", "Joshi"),    # Blanks / Unattempted (completion concern)
    ("SYN-L6-022", "Pranav", "Mishra"),
    ("SYN-L6-023", "Rohan", "Bhatia"),
    ("SYN-L6-024", "Sanya", "Dutta"),
    ("SYN-L6-025", "Tanvi", "Aggarwal"),
    ("SYN-L6-026", "Utkarsh", "Trivedi"),
    ("SYN-L6-027", "Vidhi", "Jain"),
    ("SYN-L6-028", "Yash", "Chauhan"),
    ("SYN-L6-029", "Zara", "Siddiqui"),
    ("SYN-L6-030", "Aryan", "Saxena"),
    ("SYN-L6-031", "Avani", "Rao"),
    ("SYN-L6-032", "Dhruv", "Gupta"),
    ("SYN-L6-033", "Gautam", "Malhotra"),
    ("SYN-L6-034", "Hridhaan", "Bose"),
    ("SYN-L6-035", "Kiran", "Natarajan"),
    ("SYN-L6-036", "Mira", "Soni"),
    ("SYN-L6-037", "Naveen", "Shekhar"),
    ("SYN-L6-038", "Pooja", "Bhardwaj"),
    ("SYN-L6-039", "Rishi", "Srivastava"),
    ("SYN-L6-040", "Siddharth", "Ghosh"),
]

PINEGROVE_LEARNER_NAMES = [
    ("SYN-PG-001", "Lucas", "Zhang"),
    ("SYN-PG-002", "Maya", "Lin"),
    ("SYN-PG-003", "Ethan", "Wang"),
    ("SYN-PG-004", "Chloe", "Tan"),
    ("SYN-PG-005", "Noah", "Kim"),
    ("SYN-PG-006", "Olivia", "Park"),
    ("SYN-PG-007", "Liam", "Lee"),
    ("SYN-PG-008", "Emma", "Chen"),
    ("SYN-PG-009", "Mason", "Wu"),
    ("SYN-PG-010", "Sophia", "Huang"),
]


def seed_database(session: SessionLocal = None) -> None:
    """Populates persistent seed data into the database."""
    # Ensure tables exist
    target_engine = session.bind if session and session.bind else engine
    Base.metadata.create_all(bind=target_engine)

    db = session if session else SessionLocal()
    try:
        print("🌱 Seeding LearningBridge database...")

        # 1. School 1: Oakridge International Academy
        oakridge = db.query(School).filter(School.id == OAKRIDGE_SCHOOL_ID).first()
        if not oakridge:
            oakridge = School(
                id=OAKRIDGE_SCHOOL_ID,
                name="Oakridge International Academy",
                slug="oakridge-academy",
                code="OAK-01",
                is_active=True,
            )
            db.add(oakridge)

        # 2. School 2: Pinegrove Public School (Isolation test tenant)
        pinegrove = db.query(School).filter(School.id == PINEGROVE_SCHOOL_ID).first()
        if not pinegrove:
            pinegrove = School(
                id=PINEGROVE_SCHOOL_ID,
                name="Pinegrove Public School",
                slug="pinegrove-school",
                code="PNG-02",
                is_active=True,
            )
            db.add(pinegrove)
        db.commit()

        # 3. Users: Teacher Priya (Oakridge) and Teacher David (Pinegrove)
        hashed_pw = hash_password("TeacherPass123!")

        priya = db.query(User).filter(User.id == TEACHER_PRIYA_ID).first()
        if not priya:
            priya = User(
                id=TEACHER_PRIYA_ID,
                email="priya.sharma@demo.learningbridge.internal",
                full_name="Priya Sharma",
                hashed_password=hashed_pw,
                is_active=True,
            )
            db.add(priya)

        david = db.query(User).filter(User.id == TEACHER_DAVID_ID).first()
        if not david:
            david = User(
                id=TEACHER_DAVID_ID,
                email="david.chen@demo.learningbridge.internal",
                full_name="David Chen",
                hashed_password=hashed_pw,
                is_active=True,
            )
            db.add(david)
        db.commit()

        # 4. School Memberships
        m_priya = db.query(SchoolMembership).filter(
            SchoolMembership.school_id == OAKRIDGE_SCHOOL_ID,
            SchoolMembership.user_id == TEACHER_PRIYA_ID,
        ).first()
        if not m_priya:
            db.add(SchoolMembership(
                school_id=OAKRIDGE_SCHOOL_ID,
                user_id=TEACHER_PRIYA_ID,
                role="teacher",
                is_active=True,
            ))

        m_david = db.query(SchoolMembership).filter(
            SchoolMembership.school_id == PINEGROVE_SCHOOL_ID,
            SchoolMembership.user_id == TEACHER_DAVID_ID,
        ).first()
        if not m_david:
            db.add(SchoolMembership(
                school_id=PINEGROVE_SCHOOL_ID,
                user_id=TEACHER_DAVID_ID,
                role="teacher",
                is_active=True,
            ))
        db.commit()

        # 5. Classrooms
        class_6a = db.query(Classroom).filter(Classroom.id == CLASS_6A_ID).first()
        if not class_6a:
            class_6a = Classroom(
                id=CLASS_6A_ID,
                school_id=OAKRIDGE_SCHOOL_ID,
                name="Grade 6 Mathematics",
                grade_level=6,
                section="A",
                academic_year="2026-2027",
            )
            db.add(class_6a)

        class_6b = db.query(Classroom).filter(Classroom.id == CLASS_6B_ID).first()
        if not class_6b:
            class_6b = Classroom(
                id=CLASS_6B_ID,
                school_id=PINEGROVE_SCHOOL_ID,
                name="Grade 6 Mathematics",
                grade_level=6,
                section="B",
                academic_year="2026-2027",
            )
            db.add(class_6b)
        db.commit()

        # 6. Class Memberships (Authorizing Priya to 6-A and David to 6-B)
        cm_priya = db.query(ClassMembership).filter(
            ClassMembership.classroom_id == CLASS_6A_ID,
            ClassMembership.user_id == TEACHER_PRIYA_ID,
        ).first()
        if not cm_priya:
            db.add(ClassMembership(
                school_id=OAKRIDGE_SCHOOL_ID,
                classroom_id=CLASS_6A_ID,
                user_id=TEACHER_PRIYA_ID,
                is_primary=True,
            ))

        cm_david = db.query(ClassMembership).filter(
            ClassMembership.classroom_id == CLASS_6B_ID,
            ClassMembership.user_id == TEACHER_DAVID_ID,
        ).first()
        if not cm_david:
            db.add(ClassMembership(
                school_id=PINEGROVE_SCHOOL_ID,
                classroom_id=CLASS_6B_ID,
                user_id=TEACHER_DAVID_ID,
                is_primary=True,
            ))
        db.commit()

        # 7. 40 Synthetic Learners in Class 6-A
        for ref, fname, lname in SYNTHETIC_LEARNER_NAMES:
            learner = db.query(Learner).filter(
                Learner.school_id == OAKRIDGE_SCHOOL_ID,
                Learner.external_ref == ref,
            ).first()
            if not learner:
                db.add(Learner(
                    school_id=OAKRIDGE_SCHOOL_ID,
                    classroom_id=CLASS_6A_ID,
                    external_ref=ref,
                    first_name=fname,
                    last_name=lname,
                    is_synthetic=True,
                ))

        # 8. 10 Synthetic Learners in Class 6-B (Pinegrove)
        for ref, fname, lname in PINEGROVE_LEARNER_NAMES:
            learner = db.query(Learner).filter(
                Learner.school_id == PINEGROVE_SCHOOL_ID,
                Learner.external_ref == ref,
            ).first()
            if not learner:
                db.add(Learner(
                    school_id=PINEGROVE_SCHOOL_ID,
                    classroom_id=CLASS_6B_ID,
                    external_ref=ref,
                    first_name=fname,
                    last_name=lname,
                    is_synthetic=True,
                ))
        db.commit()

        # 9. Topics for Oakridge
        topics = [
            (TOPIC_FRAC_ID, "MATH-G6-FRAC", "Fractions", "Fraction addition, subtraction, common denominators"),
            (TOPIC_DEC_ID, "MATH-G6-DEC", "Decimals", "Decimal addition, subtraction, place-value multiplication"),
            (TOPIC_PCT_ID, "MATH-G6-PCT", "Percentages", "Percentage rates, conversions between fractions and decimals"),
        ]
        for tid, code, name, desc in topics:
            t = db.query(Topic).filter(Topic.id == tid).first()
            if not t:
                db.add(Topic(
                    id=tid,
                    school_id=OAKRIDGE_SCHOOL_ID,
                    code=code,
                    name=name,
                    description=desc,
                    grade_level=6,
                ))
        db.commit()

        # 10. Approved Lesson Snippets Library for Oakridge & Pinegrove
        curated_snippets = [
            (
                "snip-frac-001",
                OAKRIDGE_SCHOOL_ID,
                TOPIC_FRAC_ID,
                "Finding Common Denominators for Fraction Addition",
                "To add fractions with unlike denominators, you must first rewrite each fraction using a common denominator (the least common multiple of the denominators). Never add denominators together: 1/a + 1/b is not 2/(a+b). For example, 1/2 + 1/3 = 3/6 + 2/6 = 5/6.",
                6,
                "en",
                "Oakridge Mathematics Department Curriculum Guide 2026, Section 4.2",
                True,
                TEACHER_PRIYA_ID,
            ),
            (
                "snip-frac-002",
                OAKRIDGE_SCHOOL_ID,
                TOPIC_FRAC_ID,
                "Visualizing Fractions: Area Models and Parts of a Whole",
                "Fractions represent equal parts of a whole. When combining halves and thirds, partition each into sixths. Adding 1/2 and 1/4 gives 2/4 + 1/4 = 3/4. Denominators count the size of parts; numerators count how many parts.",
                6,
                "en",
                "National Council of Teachers of Mathematics (NCTM) Grade 6 Units, Unit 3",
                True,
                TEACHER_PRIYA_ID,
            ),
            (
                "snip-dec-001",
                OAKRIDGE_SCHOOL_ID,
                TOPIC_DEC_ID,
                "Aligning Decimal Places in Addition and Subtraction",
                "When adding or subtracting decimals, line up the decimal points vertically so place values correspond (tenths with tenths, hundredths with hundredths). Append trailing zeros if needed: 0.75 + 0.5 = 0.75 + 0.50 = 1.25.",
                6,
                "en",
                "Oakridge Mathematics Department Curriculum Guide 2026, Section 5.1",
                True,
                TEACHER_PRIYA_ID,
            ),
            (
                "snip-pct-001",
                OAKRIDGE_SCHOOL_ID,
                TOPIC_PCT_ID,
                "Percentages as Fractions out of 100",
                "A percentage expresses a ratio per hundred. To convert a percentage to a fraction, place the value over 100 and simplify: 50% = 50/100 = 1/2. To find a percentage of a quantity, multiply the quantity by the decimal or fraction equivalent.",
                6,
                "en",
                "Oakridge Mathematics Department Curriculum Guide 2026, Section 6.3",
                True,
                TEACHER_PRIYA_ID,
            ),
        ]

        for sid, sch_id, top_id, title, content, gr, lang, sref, is_appr, appr_by in curated_snippets:
            snip = db.query(ApprovedSnippet).filter(ApprovedSnippet.id == sid).first()
            if not snip:
                db.add(ApprovedSnippet(
                    id=sid,
                    school_id=sch_id,
                    topic_id=top_id,
                    title=title,
                    content=content,
                    grade_level=gr,
                    language=lang,
                    source_ref=sref,
                    is_approved=is_appr,
                    approved_by_id=appr_by,
                ))
        db.commit()

        print("✅ Database seeding completed successfully!")
        print(f"   • School 1: Oakridge ({OAKRIDGE_SCHOOL_ID}) - 40 Synthetic Learners in Class 6-A")
        print(f"   • Teacher 1: Priya Sharma (priya.sharma@demo.learningbridge.internal)")
        print(f"   • School 2: Pinegrove ({PINEGROVE_SCHOOL_ID}) - 10 Synthetic Learners in Class 6-B")
        print(f"   • Teacher 2: David Chen (david.chen@demo.learningbridge.internal)")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
