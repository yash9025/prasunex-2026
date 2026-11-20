# LearningBridge — Synthetic Classroom Demonstration Scenario

## Overview & Synthetic Data Safety Notice

In strict accordance with the project specification and competition guidelines:
- **All student names, identifiers, and responses are explicitly synthetic**.
- No real student records or personal identifiable information (PII) are stored or processed.
- The platform is explicitly marked with synthetic demo banners across all screens.

---

## Classroom Setup

- **School**: Oakridge International Academy (`sch-oakridge-001`, Code `OAK-01`)
- **Teacher**: Priya Sharma (`priya.sharma@demo.learningbridge.internal`)
- **Classroom**: Grade 6 Mathematics — Section 6-A (`cls-oak-6a-001`)
- **Cohort Size**: 40 Synthetic Learners (`SYN-L6-001` through `SYN-L6-040`)
- **Topics**:
  1. `MATH-G6-FRAC` — Fractions (3 questions: Q1, Q2, Q3)
  2. `MATH-G6-DEC` — Decimals (3 questions: Q4, Q5, Q6)
  3. `MATH-G6-PCT` — Percentages (4 questions: Q7, Q8, Q9, Q10)

---

## Target Learner Profiles

### 1. Primary Demo Learner: Aarav Patel (`SYN-L6-014`)

- **Overall Score**: **7/10 (70.0%)** — appears satisfactory on aggregate report cards.
- **Fractions Topic Breakdown**:
  * Q1 (`1/2 + 1/3`): Submitted `2/5` (Wrong. Misconception: added numerators $1+1=2$ and denominators $2+3=5$). Correct is $5/6$.
  * Q2 (`1/4 + 1/2`): Submitted `1/3` (Wrong. Misconception: added numerators $1+1=2$ and denominators $4+2=6 \rightarrow 2/6 = 1/3$). Correct is $3/4$.
  * Q3 (`3/5 - 1/5`): Submitted `2/5` (Correct: common denominator subtraction).
  * **Awarded**: 1/3 marks (33.33%).
  * **Heuristic Signal**: Assessed items $\ge 3$ and percentage $< 60.0\%$ $\rightarrow$ **Pending Review Flagged**.
- **Decimals Topic Breakdown**: 3/3 marks (100.0%) — Secure.
- **Percentages Topic Breakdown**: 3/4 marks (75.0%) — Secure.

### 2. Grouping Candidate: Diya Sen (`SYN-L6-015`)

- Exhibits the identical fraction addition error pattern ($1/2 + 1/3 = 2/5$ and $1/4 + 1/2 = 1/3$).
- Awarded 1/3 in fractions.
- Demonstrates how the teacher can group learners with confirmed matching needs into a single focused support cohort.

### 3. Boundary Case: Rhea Varma (`SYN-L6-020`)

- Scores 2/3 on fractions ($66.67\% \ge 60.0\%$).
- Assessed items $\ge 3$.
- **Rule Verification**: Does NOT trigger the review flag.

### 4. Completion Concern: Ishaan Joshi (`SYN-L6-021`)

- Leaves Q1, Q2, and Q3 blank (unattempted).
- Assessed items count is 0.
- **Rule Verification**: Flagged as **Insufficient Evidence** with completion concern, rather than a misleading $0\%$ or $100\%$ score.

---

## Isolation Tenant: Pinegrove Public School (`sch-pinegrove-002`)

- **Teacher**: David Chen (`david.chen@demo.learningbridge.internal`)
- **Classroom**: Grade 6 Mathematics — Section 6-B (10 synthetic learners `SYN-PG-001` through `SYN-PG-010`)
- **Security Check**: Automated tests guarantee Teacher David Chen and Teacher Priya Sharma cannot access each other's classes or student records.
