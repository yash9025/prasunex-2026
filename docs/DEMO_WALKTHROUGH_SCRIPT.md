# LearningBridge — 5-Minute Live Demonstration Script & Presenter Guide

> **PRASUNEX INNOVATHON 2026 · Round 3: Prototype Demonstration**  
> **Presenter Persona:** Senior Software Engineer / Lead Presenter  
> **Target Audience:** Technical Jury, Academic Evaluators, School System Administrators  
> **Demo Scenario:** Oakridge International Academy (`sch-oakridge-001`), Class 6-A Maths, Teacher Priya Sharma (`usr-priya-001`)  
> **Primary Target Learner:** Aarav Patel (`SYN-L6-014`)  
> **Curriculum Topics:** Fractions (`MATH-G6-FRAC`), Decimals (`MATH-G6-DEC`), Percentages (`MATH-G6-PCT`)

---

## Executive Presenter Overview

This script provides an exact second-by-second execution plan for the live 5-minute presentation defined in **Section 15.2 of the Implementation Plan**. Every click, spoken narration point, and screen transition is synchronized with automated system behaviors.

```
0:00 ──── 0:40 ──── 1:30 ──── 2:15 ──── 3:15 ──── 4:15 ──── 5:00
 │          │          │          │          │          │
 ▼          ▼          ▼          ▼          ▼          ▼
The 7/10   CSV Import  Underlying Grounded   Reassessment Reliability,
Dilemma    & Matrix    Evidence   Support    & Mastery    Idempotency
           View        Review     Studio     Review       & Audit
```

---

## Segment 1: The Classroom Dilemma & The 7/10 Assessment (0:00 – 0:40)

### Visual State
- Screen shows the **LearningBridge Home Dashboard**.
- Header displays: `Oakridge International Academy`, `Class 6-A`, `Teacher: Priya Sharma`.
- The top synthetic notice banner is visible: `Demo Environment: Oakridge International Academy (Synthetic Data Only)`.

### Presenter Narration
> *"Good morning, members of the jury. In conventional school management systems, an assessment score is recorded as an aggregate number. Consider Aarav Patel, a Class 6 learner in Oakridge International Academy. On paper, Aarav achieved 7 out of 10 on his Term 1 Mathematics Assessment.*
>
> *To an administrator or a busy teacher reviewing a spreadsheet, a 70% score looks completely satisfactory—safe, passing, unremarkable. But underneath that aggregate score lies a serious, hidden foundational misconception that will derail Aarav when he reaches algebra next year.*
>
> *LearningBridge is built specifically to bridge this blind spot: connecting raw response-level evidence to teacher-controlled support, grounded intervention drafting, and verifiable reassessment—all within a secure, multi-tenant architecture."*

### UI Actions
1. Point to Aarav Patel's row on the learner list: Score `7/10` (70%).
2. Highlight the three topics: Decimals (100%), Percentages (100%), but Fractions (33.3%).

---

## Segment 2: Ingestion & The Explainable Diagnostic Learning Map (0:40 – 1:30)

### Visual State
- Teacher clicks **"Import Assessment CSV"** (or demonstrates clean reset via **"↺ Reset Demo State"** -> **"Preload Baseline"**).
- The Ingestion dialog shows file validation, SHA-256 payload checksum, and deterministic rational parsing.

### Presenter Narration
> *"Let's see how this works in practice. Rather than requiring teachers to manually enter grades, LearningBridge ingests raw, question-level CSV responses. We don't do brittle float comparisons or opaque AI grading. Our custom Python rational answer engine parses inputs like '1/2', '2/4', or '0.5' using exact mathematical fractions.*
>
> *Within 400 milliseconds, all 400 student question responses across Class 6-A are scored, validated, and mapped against curriculum topics. Notice the Diagnostic Learning Matrix: it displays topic mastery across Fractions, Decimals, and Percentages.*
>
> *Here, Aarav's aggregate 7/10 is unpacked. He scored 3 out of 3 on Decimals and 3 out of 3 on Percentages, but only 1 out of 3 on Fractions. The system surfaces a cyan 'Review Suggested' flag."*

### UI Actions
1. Open the **Learning Map / Class Overview** matrix.
2. Filter the table to show `Review Suggested` status.
3. Observe the flagged learners: Aarav Patel (`SYN-L6-014`) and Diya Sen (`SYN-L6-015`).

---

## Segment 3: Deep Inspection & Teacher-in-the-Loop Confirmation (1:30 – 2:15)

### Visual State
- Teacher clicks **"Inspect Evidence"** next to Aarav Patel's Fractions score.
- The **Diagnostic Evidence Inspector** modal opens, displaying exact student inputs vs expected keys.

### Presenter Narration
> *"Critically, LearningBridge never diagnoses a student autonomously. An algorithm cannot know if a child was distracted, rushed, or genuinely confused. The system provides explainable evidence to empower teacher judgment.*
>
> *When Priya clicks 'Inspect Evidence', she sees Aarav's exact responses:*
> *On Question 1: '1/2 + 1/3', Aarav wrote '2/5' (expected: '5/6').*
> *On Question 2: '1/4 + 1/2', Aarav wrote '1/3' (expected: '3/4').*
>
> *Our deterministic pattern engine flags the underlying rule: Aarav is adding numerators and adding denominators together: (1+1)/(2+3) = 2/5. This is a classic fraction addition misconception.*
>
> *Priya confirms this diagnostic flag, recording her clinical rationale: 'Confirmed denominator addition error. Requires concrete fraction bar scaffolding.'*
> *She forms a targeted Support Group pairing Aarav with Diya Sen, who exhibits the exact same error pattern."*

### UI Actions
1. Click Aarav Patel's **"Inspect Evidence"** button.
2. Review the raw attempt table (showing `2/5` and `1/3`).
3. Click **"Confirm Evidence"**, type rationale: *"Confirmed denominator addition error"*, submit.
4. Click **"Create Support Group"**, select Aarav Patel and Diya Sen, name group: *"Class 6 Fractions Intensive - Unlike Denominators"*.

---

## Segment 4: Grounded Support Studio & Mathematical Verification (2:15 – 3:15)

### Visual State
- Priya opens the **Support Studio** for the newly created group.
- Curated NCTM reference snippets are visible in the left rail.
- Support plan draft is generated, edited, and approved.

### Presenter Narration
> *"Now Priya needs an intervention plan. In typical AI implementations, large language models hallucinate math questions with impossible answers or inappropriate pedagogy.*
>
> *LearningBridge enforces strict mathematical grounding. Intervention plans can only be drafted using verified, teacher-approved curriculum snippets—in this case, NCTM Fraction Equivalence Standards. Furthermore, every practice question generated by the LLM is passed through our deterministic `DraftMathVerifier`.*
>
> *If an LLM invents a question where the arithmetic does not balance, the system rejects it before the teacher ever sees it.*
>
> *Priya reviews the 3-step intervention:*
> *1. Visualizing unlike denominators with fraction strips.*
> *2. Finding common multiples through LCM grids.*
> *3. Guided practice with exact rational verification.*
>
> *Priya modifies the scaffolding notes. The system tracks optimistic locking revision numbers to prevent stale overwrite conflicts. When satisfied, she clicks 'Approve Plan'.*
> *The approved plan is permanently frozen with a SHA-256 content hash, guaranteeing legal and pedagogical immutability."*

### UI Actions
1. Click **"Generate Grounded Draft"** (or observe pre-loaded verified draft).
2. Point out the verified curriculum snippet badge (`NCTM-FRAC-01: Fraction Bar Modeling`).
3. Make a minor edit in the teacher rationale box (showing real-time revision increment from 2 to 3).
4. Click **"Approve Plan"**. Point out the generated SHA-256 fingerprint badge (`Hash: 7a8f...`).
5. Click **"Assign to Group"**, creating durable student assignment records.

---

## Segment 5: Fresh Reassessment & Verifiable Mastery Trajectory (3:15 – 4:15)

### Visual State
- The assignment is dispatched. Learner reassessment mode is opened.
- Aarav Patel sits the **Fresh Diagnostic Reassessment Quiz**.
- Progress Review table displays comparative before-and-after scores.

### Presenter Narration
> *"An intervention without reassessment is just wishful thinking. LearningBridge attaches a fresh diagnostic quiz to every assigned support plan.*
>
> *These questions do not duplicate the baseline or the practice exercises; they are fresh, teacher-approved diagnostic items drawn from our secure question bank.*
>
> *Crucially, our API protects the answer key: inspecting the learner's network traffic reveals zero expected answers or scoring rationales. Scoring occurs exclusively on the backend.*
>
> *Aarav completes the reassessment:*
> *- Question 1: 1/4 + 1/3 = 7/12.*
> *- Question 2: 2/3 + 1/6 = 5/6.*
> *- Question 3: 3/8 + 1/4 = 5/8.*
>
> *The system evaluates the answers rational-by-rational: 3 out of 3 marks awarded (100% mastery).*
>
> *Priya opens the Progress Review dashboard: Aarav's Fractions performance has advanced from 33.3% on baseline to 100% on reassessment. With verified evidence in hand, Priya formally closes the intervention cycle with closing rationale."*

### UI Actions
1. Open Aarav's reassessment quiz view.
2. Submit answers: `7/12`, `5/6`, `5/8`.
3. View instant evaluation: `3.0 / 3.0 (100%) - Mastery Achieved`.
4. Switch to **"Intervention Progress Review"** modal.
5. Click **"Close Support Cycle"**, enter closing comment: *"Mastery demonstrated on fresh unlike denominator items. Misconception resolved."*

---

## Segment 6: Reliability, Security, & System Health (4:15 – 5:00)

### Visual State
- Teacher clicks **"Audit Log & System Health"** in the top navigation.
- Audit history timeline and operational diagnostics panels appear.

### Presenter Narration
> *"Finally, let us look under the hood at enterprise-grade reliability and security.*
>
> *Every single action taken during this cycle—from CSV ingestion to evidence confirmation, plan draft edits, SHA-256 approval, learner submission, and cycle closure—is recorded in an append-only, tenant-isolated audit log.*
>
> *Our multi-tenant architecture strictly enforces tenant isolation at both the JWT request context level and the database query level. Teacher David Chen at Pinegrove Public School cannot read or alter a single record belonging to Oakridge.*
>
> *If network drops occur, our outbox pattern and lease reconciler automatically recover in-flight jobs. If the LLM service experiences rate limits, the system seamlessly transitions to teacher-authored template fallbacks with zero user downtime.*
>
> *LearningBridge turns fragmented classroom data into an accountable, transparent, and pedagogically grounded journey for every learner. Thank you, and we welcome your questions."*

### UI Actions
1. Open the **Audit Log Viewer**: point out chronological event entries (`demo_environment_reset`, `EVIDENCE_DECISION_RECORDED`, `PLAN_APPROVED`, `ASSIGNMENT_CREATED`, `REASSESSMENT_SUBMITTED`, `PLAN_CLOSE`).
2. Point out the **System Health Diagnostics** card: Database connected (<5ms ping), Redis queue ready, 0 stale leases.
3. Conclude presentation.

---

## Contingency & Failure Disclosure Guide

| Potential Incident | Immediate Presenter Action | Technical Explanation to Jury |
|---|---|---|
| **External LLM Provider Rate Limit / Timeout** | Click "Generate Draft". If Gemini API key is absent or exhausts quota, the template provider activates instantly. | *"As designed, LearningBridge uses an offline-first architectural pattern. If the LLM provider is unavailable, our deterministic pedagogical template engine generates verified drafts without delay."* |
| **Accidental State Corruption During Rehearsal** | Click **"↺ Reset Demo State"** -> **"Reset & Preload Baseline"**. Clean state returns in <50ms. | *"Our demo reset service atomically purges dynamic transactions for tenant `sch-oakridge-001` while preserving baseline fixtures and cross-tenant data."* |
| **Network Disconnection / Offline Presentation** | The prototype runs 100% locally on localhost (`localhost:5173` / `localhost:8000`) with SQLite/Postgres. | *"Zero internet dependencies are required for the core workflow. All rational scoring, evidence rules, and question banks execute locally."* |
| **Jury asks about floating-point rounding errors** | Open `backend/app/modules/scoring/exact_checker.py`. | *"We strictly reject floating-point comparisons. All numbers are parsed into Python's `fractions.Fraction` with exact integer numerator/denominator arithmetic."* |
