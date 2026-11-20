/**
 * TypeScript contracts reflecting the LearningBridge API schemas.
 */

export interface SchoolMembership {
  school_id: string;
  school_name: string;
  school_code: string;
  role: string;
}

export interface UserMe {
  id: string;
  email: string;
  full_name: string;
  active_school_id: string;
  active_school_name: string;
  role: string;
  memberships: SchoolMembership[];
  authorized_class_ids: string[];
}

export interface Learner {
  id: string;
  school_id: string;
  classroom_id: string;
  external_ref: string;
  first_name: string;
  last_name: string;
  is_synthetic: boolean;
}

export interface Classroom {
  id: string;
  school_id: string;
  name: string;
  grade_level: number;
  section: string;
  academic_year: string;
  learner_count: number;
}

export interface ClassroomDetail extends Classroom {
  learners: Learner[];
}

export interface ClassOverviewMetrics {
  total_learners: number;
  synthetic_count: number;
  pending_actions_count: number;
  active_assessments_count: number;
  confirmed_count?: number;
  groups_count?: number;
}

export interface EvidenceAttempt {
  attempt_id: string;
  question_ref: string;
  question_text: string;
  answer_kind: string;
  expected_answer: string;
  raw_response: string;
  normalized_value?: string;
  outcome: 'correct' | 'incorrect' | 'unattempted' | 'invalid' | 'requires_review';
  awarded_marks: number;
  max_marks: number;
}

export interface TeacherDecision {
  id: string;
  gap_evidence_id: string;
  actor_id: string;
  actor_name: string;
  action: 'confirm' | 'correct' | 'dismiss';
  corrected_topic_id?: string;
  rationale: string;
  created_at: string;
}

export interface GapEvidence {
  id: string;
  learner_id: string;
  learner_ref: string;
  learner_name: string;
  topic_id: string;
  topic_code: string;
  topic_name: string;
  awarded_marks: number;
  possible_marks: number;
  assessed_items_count: number;
  unattempted_count: number;
  invalid_count: number;
  percentage?: number;
  rule_version: string;
  status: 'pending_review' | 'confirmed' | 'corrected' | 'dismissed' | 'insufficient_evidence';
  suspected_pattern?: string;
  supporting_attempts: EvidenceAttempt[];
  decisions: TeacherDecision[];
}

export interface Assessment {
  id: string;
  title: string;
  classroom_id: string;
  academic_year: string;
  status: string;
  created_at: string;
}

export interface AssessmentEvidencePage {
  assessment: Assessment;
  total_records: number;
  evidence: GapEvidence[];
}

export interface GroupMember {
  id: string;
  learner_id: string;
  learner_ref: string;
  learner_name: string;
  gap_evidence_id: string;
}

export interface SupportGroup {
  id: string;
  school_id: string;
  classroom_id: string;
  topic_id: string;
  topic_code: string;
  topic_name: string;
  name: string;
  created_by_id: string;
  created_by_name: string;
  members: GroupMember[];
  created_at: string;
}

export interface RowError {
  row_num: number;
  column?: string;
  message: string;
}

export interface JobStatus {
  id: string;
  kind: string;
  status: 'queued' | 'running' | 'succeeded' | 'failed' | 'retry_pending';
  attempt_count: number;
  max_attempts: number;
  failure_code?: string;
  failure_message?: string;
  result_summary?: {
    assessment_id?: string;
    assessment_title?: string;
    rows_processed?: number;
    questions_count?: number;
    learners_count?: number;
    pending_review_count?: number;
    secure_count?: number;
    insufficient_evidence_count?: number;
    row_errors?: RowError[];
  };
  created_at: string;
  updated_at: string;
}

export interface ApprovedSnippet {
  id: string;
  school_id: string;
  topic_id: string;
  title: string;
  content: string;
  grade_level: number;
  language: string;
  source_ref: string;
  is_approved: boolean;
}

export interface MathSpec {
  operation: 'add' | 'subtract' | 'multiply' | 'divide';
  operands: string[];
  answer_format: 'fraction' | 'decimal' | 'percentage' | 'integer';
}

export interface PracticeItem {
  item_num: number;
  question_text: string;
  math_spec: MathSpec;
  expected_answer: string;
  rationale: string;
  verified?: boolean;
  verification_error?: string | null;
}

export interface PlanVersion {
  id: string;
  support_plan_id: string;
  version_num: number;
  explanation: string;
  practice_items: PracticeItem[];
  content_hash: string;
  cited_snippets: ApprovedSnippet[];
  created_by_id: string;
  created_by_name: string;
  created_at: string;
}

export interface SupportPlan {
  id: string;
  school_id: string;
  support_group_id: string;
  support_group_name: string;
  topic_id: string;
  topic_code: string;
  topic_name: string;
  status: 'draft' | 'reviewed' | 'assigned' | 'reassessed' | 'closed' | 'needs_revision';
  revision: number;
  current_version_id?: string | null;
  current_version?: PlanVersion | null;
  generation_mode?: string | null;
  is_fallback?: boolean;
  fallback_reason?: string | null;
  created_at: string;
  updated_at: string;
}

export interface Approval {
  id: string;
  plan_version_id: string;
  approver_id: string;
  approver_name: string;
  approval_hash: string;
  approved_at: string;
}

export interface AssignmentRecipientInfo {
  id: string;
  learner_id: string;
  learner_ref: string;
  learner_name: string;
  status: 'pending' | 'completed';
}

export interface Assignment {
  id: string;
  school_id: string;
  support_plan_id: string;
  plan_version_id: string;
  plan_version_num: number;
  support_group_id: string;
  support_group_name: string;
  topic_code: string;
  topic_name: string;
  assigned_by_id: string;
  assigned_by_name: string;
  status: 'active' | 'completed' | 'cancelled';
  due_date?: string | null;
  recipients: AssignmentRecipientInfo[];
  created_at: string;
}

export interface QuizQuestion {
  question_ref: string;
  question_text: string;
  answer_kind: string;
  max_marks: number;
}

export interface QuizData {
  recipient_id: string;
  assignment_id: string;
  learner_ref: string;
  learner_name: string;
  topic_code: string;
  topic_name: string;
  quiz_version: string;
  status: string;
  questions: QuizQuestion[];
}

export interface ScoredResponseItem {
  question_ref: string;
  question_text: string;
  expected_answer: string;
  raw_response: string;
  normalized_value?: string | null;
  outcome: string;
  awarded_marks: number;
  max_marks: number;
  rationale: string;
}

export interface QuizSubmissionResult {
  reassessment_id: string;
  recipient_id: string;
  learner_ref: string;
  learner_name: string;
  awarded_marks: number;
  possible_marks: number;
  percentage: number;
  mastery_achieved: boolean;
  items: ScoredResponseItem[];
}

export interface LearnerProgressDetail {
  learner_id: string;
  learner_ref: string;
  learner_name: string;
  baseline_awarded: number;
  baseline_possible: number;
  baseline_percentage: number;
  reassessment_awarded?: number | null;
  reassessment_possible?: number | null;
  reassessment_percentage?: number | null;
  status: string;
  is_completed: boolean;
  reassessment_items: ScoredResponseItem[];
}

export interface PlanProgressReport {
  plan_id: string;
  plan_status: string;
  support_group_id: string;
  support_group_name: string;
  topic_code: string;
  topic_name: string;
  assigned_version_num: number;
  total_learners: number;
  completed_count: number;
  all_completed: boolean;
  learners: LearnerProgressDetail[];
}

export interface AuditEvent {
  id: string;
  school_id: string;
  actor_id: string;
  actor_name?: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  request_id?: string | null;
  metadata_json?: Record<string, any> | null;
  created_at: string;
}

export interface AuditLogPage {
  total_count: number;
  limit: number;
  offset: number;
  events: AuditEvent[];
}

export interface SystemHealth {
  status: string;
  environment: string;
  database: {
    status: string;
    ping_latency_ms: number;
  };
  job_queue: {
    queued: number;
    running: number;
    succeeded: number;
    failed: number;
    retry_pending: number;
  };
  outbox: {
    pending: number;
    dispatched: number;
  };
}
