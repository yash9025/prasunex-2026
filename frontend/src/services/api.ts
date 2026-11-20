import {
  Approval,
  ApprovedSnippet,
  Assessment,
  AssessmentEvidencePage,
  Assignment,
  AuditLogPage,
  Classroom,
  ClassroomDetail,
  ClassOverviewMetrics,
  GapEvidence,
  JobStatus,
  PlanProgressReport,
  QuizData,
  QuizSubmissionResult,
  SupportGroup,
  SupportPlan,
  SystemHealth,
  UserMe,
} from '../types';

const API_BASE = '/v1';

class ApiClient {
  private token: string | null = null;
  private schoolId: string | null = null;

  constructor() {
    this.token = localStorage.getItem('learningbridge_token');
    this.schoolId = localStorage.getItem('learningbridge_school_id');
  }

  setToken(token: string, schoolId?: string) {
    this.token = token;
    localStorage.setItem('learningbridge_token', token);
    if (schoolId) {
      this.schoolId = schoolId;
      localStorage.setItem('learningbridge_school_id', schoolId);
    }
  }

  clearToken() {
    this.token = null;
    this.schoolId = null;
    localStorage.removeItem('learningbridge_token');
    localStorage.removeItem('learningbridge_school_id');
  }

  getToken(): string | null {
    return this.token;
  }

  private getHeaders(): HeadersInit {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    if (this.schoolId) {
      headers['X-School-ID'] = this.schoolId;
    }
    return headers;
  }

  async checkHealth(): Promise<{ status: string; database?: string }> {
    const res = await fetch('/health/ready');
    return res.json();
  }

  async login(email: string, password: string): Promise<{ access_token: string; user: any; active_school: any }> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Authentication failed');
    }
    const data = await res.json();
    this.setToken(data.access_token, data.active_school.school_id);
    return data;
  }

  async getMe(): Promise<UserMe> {
    const res = await fetch(`${API_BASE}/me`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to fetch current user profile');
    }
    return res.json();
  }

  async getClasses(): Promise<Classroom[]> {
    const res = await fetch(`${API_BASE}/classes`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to fetch classes');
    }
    return res.json();
  }

  async getClassDetail(classId: string): Promise<ClassroomDetail> {
    const res = await fetch(`${API_BASE}/classes/${classId}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to fetch class detail');
    }
    return res.json();
  }

  async getClassOverview(classId: string): Promise<ClassOverviewMetrics> {
    const res = await fetch(`${API_BASE}/classes/${classId}/overview`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to fetch class overview metrics');
    }
    return res.json();
  }

  // --- Phase 2: Assessment Import & Evidence Services ---

  getTemplateDownloadUrl(): string {
    return `${API_BASE}/imports/template`;
  }

  async uploadAssessmentCsv(
    classroomId: string,
    assessmentTitle: string,
    file: File,
    idempotencyKey?: string,
  ): Promise<{ job_id: string; status: string; message: string }> {
    const formData = new FormData();
    formData.append('classroom_id', classroomId);
    formData.append('assessment_title', assessmentTitle);
    formData.append('file', file);

    const headers: Record<string, string> = {};
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    if (this.schoolId) {
      headers['X-School-ID'] = this.schoolId;
    }
    if (idempotencyKey) {
      headers['Idempotency-Key'] = idempotencyKey;
    }

    const res = await fetch(`${API_BASE}/imports`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'CSV assessment upload failed');
    }

    return res.json();
  }

  async getJobStatus(jobId: string): Promise<JobStatus> {
    const res = await fetch(`${API_BASE}/jobs/${jobId}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to poll job status');
    }
    return res.json();
  }

  async getClassAssessments(classroomId: string): Promise<Assessment[]> {
    const res = await fetch(`${API_BASE}/classes/${classroomId}/assessments`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to load classroom assessments');
    }
    return res.json();
  }

  async getAssessmentEvidence(
    assessmentId: string,
    topicFilter?: string,
    statusFilter?: string,
  ): Promise<AssessmentEvidencePage> {
    const params = new URLSearchParams();
    if (topicFilter && topicFilter !== 'ALL') params.append('topic_filter', topicFilter);
    if (statusFilter && statusFilter !== 'ALL') params.append('status_filter', statusFilter);

    const qs = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_BASE}/assessments/${assessmentId}/evidence${qs}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to load assessment evidence');
    }
    return res.json();
  }

  // --- Phase 3: Teacher Decisions & Support Groups ---

  async recordTeacherDecision(
    evidenceId: string,
    action: 'confirm' | 'correct' | 'dismiss',
    rationale: string,
    correctedTopicId?: string,
  ): Promise<GapEvidence> {
    const res = await fetch(`${API_BASE}/evidence/${evidenceId}/decisions`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        action,
        rationale,
        corrected_topic_id: correctedTopicId || null,
      }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to record teacher decision');
    }
    return res.json();
  }

  async createSupportGroup(
    classroomId: string,
    topicId: string,
    name: string,
    members: Array<{ learner_id: string; gap_evidence_id: string }>,
  ): Promise<SupportGroup> {
    const res = await fetch(`${API_BASE}/groups`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        classroom_id: classroomId,
        topic_id: topicId,
        name,
        members,
      }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to create support group');
    }
    return res.json();
  }

  async getSupportGroups(classroomId: string): Promise<SupportGroup[]> {
    const res = await fetch(`${API_BASE}/classes/${classroomId}/groups`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to load support groups');
    }
    return res.json();
  }

  // --- Phase 4: Grounded Support Drafting & Approvals ---

  async getApprovedSnippets(topicId?: string): Promise<ApprovedSnippet[]> {
    const url = topicId ? `${API_BASE}/snippets?topic_id=${topicId}` : `${API_BASE}/snippets`;
    const res = await fetch(url, {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to load approved snippets');
    }
    return res.json();
  }

  async generateSupportDraft(data: {
    support_group_id: string;
    source_snippet_ids: string[];
    generation_mode?: string;
  }): Promise<SupportPlan> {
    const res = await fetch(`${API_BASE}/plans/drafts`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to generate support draft');
    }
    return res.json();
  }

  async getSupportPlan(planId: string): Promise<SupportPlan> {
    const res = await fetch(`${API_BASE}/plans/${planId}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to load support plan');
    }
    return res.json();
  }

  async updateSupportDraft(
    planId: string,
    data: { revision: number; explanation?: string; practice_items?: any[] },
  ): Promise<SupportPlan> {
    const res = await fetch(`${API_BASE}/plans/${planId}/draft`, {
      method: 'PATCH',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to update support draft');
    }
    return res.json();
  }

  async approveSupportPlan(
    planId: string,
    data: { revision: number; sign_off_responsibility: boolean },
  ): Promise<Approval> {
    const res = await fetch(`${API_BASE}/plans/${planId}/approve`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to approve support plan');
    }
    return res.json();
  }

  async getPlanAssignment(planId: string): Promise<Assignment | null> {
    const res = await fetch(`${API_BASE}/plans/${planId}/assignment`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      return null;
    }
    return res.json();
  }

  async getGroupPlan(groupId: string): Promise<SupportPlan | null> {
    const res = await fetch(`${API_BASE}/groups/${groupId}/plan`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      return null;
    }
    return res.json();
  }

  // --- Phase 5: Assignment, Reassessment, and Progress Review ---

  async createAssignment(
    planId: string,
    planVersionId: string,
    dueDate?: string,
  ): Promise<Assignment> {
    const res = await fetch(`${API_BASE}/plans/${planId}/assign`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        plan_version_id: planVersionId,
        due_date: dueDate || null,
      }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to create assignment');
    }
    return res.json();
  }

  async getAssignment(assignmentId: string): Promise<Assignment> {
    const res = await fetch(`${API_BASE}/assignments/${assignmentId}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to load assignment');
    }
    return res.json();
  }

  async getReassessmentQuiz(recipientId: string): Promise<QuizData> {
    const res = await fetch(`${API_BASE}/reassessments/quiz/${recipientId}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to load reassessment quiz');
    }
    return res.json();
  }

  async submitReassessmentQuiz(
    recipientId: string,
    submissionKey: string,
    answers: Array<{ question_ref: string; raw_response: string }>,
  ): Promise<QuizSubmissionResult> {
    const res = await fetch(`${API_BASE}/reassessments/quiz/${recipientId}/submit`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        submission_key: submissionKey,
        answers,
      }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to submit reassessment quiz');
    }
    return res.json();
  }

  async getPlanProgress(planId: string): Promise<PlanProgressReport> {
    const res = await fetch(`${API_BASE}/plans/${planId}/progress`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to load plan progress report');
    }
    return res.json();
  }

  async closePlan(
    planId: string,
    action: 'close' | 'request_revision',
    rationale: string,
  ): Promise<any> {
    const res = await fetch(`${API_BASE}/plans/${planId}/close`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        action,
        rationale,
      }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to conclude support plan');
    }
    return res.json();
  }

  async getAuditEvents(limit = 50, offset = 0): Promise<AuditLogPage> {
    const res = await fetch(`${API_BASE}/audit/events?limit=${limit}&offset=${offset}`, {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to fetch audit log events');
    }
    return res.json();
  }

  async getSystemDiagnostics(): Promise<SystemHealth> {
    const res = await fetch('/health/system', {
      headers: this.getHeaders(),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to fetch system diagnostics');
    }
    return res.json();
  }

  async resetDemoTenant(preloadBaseline = false): Promise<any> {
    const res = await fetch(`${API_BASE}/demo/reset`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ preload_baseline: preloadBaseline }),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Failed to reset demonstration environment');
    }
    return res.json();
  }
}

export const api = new ApiClient();
