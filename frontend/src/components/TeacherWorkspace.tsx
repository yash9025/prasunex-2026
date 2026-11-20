import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Assessment, Classroom, ClassroomDetail, GapEvidence, SupportGroup } from '../types';
import { ImportModal } from './ImportModal';
import { EvidenceModal } from './EvidenceModal';
import { SupportGroupModal } from './SupportGroupModal';
import { SupportStudioModal } from './SupportStudioModal';

interface TeacherWorkspaceProps {
  classroom: Classroom | null;
  detail: ClassroomDetail | null;
  isLoading: boolean;
}

export const TeacherWorkspace: React.FC<TeacherWorkspaceProps> = ({
  classroom,
  detail,
  isLoading,
}) => {
  const [activeTab, setActiveTab] = useState<'map' | 'groups'>('map');
  const [search, setSearch] = useState('');
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [activeAssessmentId, setActiveAssessmentId] = useState<string | null>(null);
  const [evidenceList, setEvidenceList] = useState<GapEvidence[]>([]);
  const [supportGroups, setSupportGroups] = useState<SupportGroup[]>([]);
  const [selectedEvidence, setSelectedEvidence] = useState<GapEvidence | null>(null);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [isGroupModalOpen, setIsGroupModalOpen] = useState(false);
  const [selectedStudioGroup, setSelectedStudioGroup] = useState<SupportGroup | null>(null);
  const [topicFilter, setTopicFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const loadAssessments = async (preferredId?: string) => {
    if (!classroom) return;
    try {
      const list = await api.getClassAssessments(classroom.id);
      setAssessments(list);

      const targetId = preferredId || (list.length > 0 ? list[0].id : null);
      if (targetId) {
        setActiveAssessmentId(targetId);
        loadEvidence(targetId);
      }
    } catch (e) {
      console.error('Failed to load assessments:', e);
    }
  };

  const loadEvidence = async (assessmentId: string) => {
    try {
      const res = await api.getAssessmentEvidence(assessmentId);
      setEvidenceList(res.evidence);
    } catch (e) {
      console.error('Failed to load assessment evidence:', e);
    }
  };

  const loadSupportGroups = async () => {
    if (!classroom) return;
    try {
      const groups = await api.getSupportGroups(classroom.id);
      setSupportGroups(groups);
    } catch (e) {
      console.error('Failed to load support groups:', e);
    }
  };

  useEffect(() => {
    if (classroom) {
      loadAssessments();
      loadSupportGroups();
    }
  }, [classroom?.id]);

  if (isLoading) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: '#94A3B8' }}>
        Loading classroom records...
      </div>
    );
  }

  if (!classroom || !detail) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: '#FF6B6B' }}>
        No classroom access or records found.
      </div>
    );
  }

  // Group evidence by learner_id -> { topic_code: GapEvidence }
  const learnerEvidenceMap: Record<string, Record<string, GapEvidence>> = {};
  for (const ev of evidenceList) {
    if (!learnerEvidenceMap[ev.learner_id]) {
      learnerEvidenceMap[ev.learner_id] = {};
    }
    learnerEvidenceMap[ev.learner_id][ev.topic_code] = ev;
  }

  const confirmedCount = evidenceList.filter((e) => e.status === 'confirmed').length;
  const pendingReviewCount = evidenceList.filter((e) => e.status === 'pending_review').length;

  // Filtered learners
  const filteredLearners = detail.learners.filter((l) => {
    const matchesSearch = `${l.first_name} ${l.last_name} ${l.external_ref}`
      .toLowerCase()
      .includes(search.toLowerCase());

    if (!matchesSearch) return false;

    if (topicFilter !== 'ALL' && statusFilter !== 'ALL') {
      const ev = learnerEvidenceMap[l.id]?.[topicFilter];
      if (!ev || ev.status !== statusFilter) return false;
    } else if (statusFilter !== 'ALL') {
      const statuses = Object.values(learnerEvidenceMap[l.id] || {}).map((e) => e.status);
      if (!statuses.includes(statusFilter as any)) return false;
    }

    return true;
  });

  return (
    <div style={{ maxWidth: '1240px', margin: '0 auto', padding: '28px 24px' }}>
      {/* Cohort Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '24px',
        backgroundColor: '#151B3A',
        padding: '24px 28px',
        borderRadius: '12px',
        border: '1px solid #27325E',
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
            <span style={{
              backgroundColor: '#7C5CFF',
              color: '#FFFFFF',
              fontSize: '11px',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '4px',
              textTransform: 'uppercase',
            }}>
              Assigned Cohort
            </span>
            <span style={{ color: '#22D3EE', fontSize: '13px', fontWeight: 600 }}>
              Academic Year {classroom.academic_year}
            </span>
          </div>
          <h2 style={{ fontSize: '24px', fontWeight: 700, color: '#F6F3EC' }}>
            {classroom.name} · Section {classroom.section}
          </h2>
          <p style={{ color: '#94A3B8', fontSize: '14px', marginTop: '4px' }}>
            Curriculum Topics: <strong>Fractions</strong>, <strong>Decimals</strong>, and <strong>Percentages</strong>
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <button
            onClick={() => setIsImportModalOpen(true)}
            style={{
              backgroundColor: '#7C5CFF',
              color: '#FFFFFF',
              fontWeight: 700,
              fontSize: '13px',
              padding: '12px 18px',
              borderRadius: '8px',
              border: 'none',
              boxShadow: '0 4px 14px rgba(124, 92, 255, 0.4)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>↑</span> Upload Assessment CSV
          </button>

          <button
            onClick={() => setIsGroupModalOpen(true)}
            disabled={confirmedCount === 0}
            style={{
              backgroundColor: confirmedCount > 0 ? '#FFB547' : '#334155',
              color: confirmedCount > 0 ? '#0B1020' : '#64748B',
              fontWeight: 700,
              fontSize: '13px',
              padding: '12px 18px',
              borderRadius: '8px',
              border: 'none',
              cursor: confirmedCount > 0 ? 'pointer' : 'not-allowed',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span>+</span> Form Support Group ({confirmedCount} Confirmed)
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '16px',
        marginBottom: '24px',
      }}>
        <div style={{
          backgroundColor: '#151B3A',
          border: '1px solid #27325E',
          padding: '18px 20px',
          borderRadius: '10px',
        }}>
          <div style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600 }}>Total Enrollment</div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: '#F6F3EC', marginTop: '4px' }}>
            {detail.learners.length} <span style={{ fontSize: '13px', color: '#34D399', fontWeight: 500 }}>(Synthetic)</span>
          </div>
        </div>

        <div style={{
          backgroundColor: '#151B3A',
          border: '1px solid #27325E',
          padding: '18px 20px',
          borderRadius: '10px',
        }}>
          <div style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600 }}>Pending Review Flags (&lt;60%)</div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: pendingReviewCount > 0 ? '#FFB547' : '#94A3B8', marginTop: '4px' }}>
            {pendingReviewCount} <span style={{ fontSize: '12px', color: '#94A3B8', fontWeight: 500 }}>signals</span>
          </div>
        </div>

        <div style={{
          backgroundColor: '#151B3A',
          border: '1px solid #27325E',
          padding: '18px 20px',
          borderRadius: '10px',
        }}>
          <div style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600 }}>Teacher-Confirmed Needs</div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: confirmedCount > 0 ? '#34D399' : '#94A3B8', marginTop: '4px' }}>
            {confirmedCount} <span style={{ fontSize: '12px', color: '#94A3B8', fontWeight: 500 }}>ready to group</span>
          </div>
        </div>

        <div style={{
          backgroundColor: '#151B3A',
          border: '1px solid #27325E',
          padding: '18px 20px',
          borderRadius: '10px',
        }}>
          <div style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600 }}>Active Support Groups</div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: supportGroups.length > 0 ? '#22D3EE' : '#94A3B8', marginTop: '4px' }}>
            {supportGroups.length} <span style={{ fontSize: '12px', color: '#94A3B8', fontWeight: 500 }}>cohorts</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid #27325E',
        marginBottom: '20px',
        gap: '24px',
      }}>
        <button
          onClick={() => setActiveTab('map')}
          style={{
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'map' ? '2px solid #7C5CFF' : '2px solid transparent',
            color: activeTab === 'map' ? '#F6F3EC' : '#94A3B8',
            fontWeight: 700,
            fontSize: '14px',
            padding: '10px 4px',
            cursor: 'pointer',
          }}
        >
          Classroom Learning Map ({detail.learners.length})
        </button>

        <button
          onClick={() => setActiveTab('groups')}
          style={{
            background: 'none',
            border: 'none',
            borderBottom: activeTab === 'groups' ? '2px solid #7C5CFF' : '2px solid transparent',
            color: activeTab === 'groups' ? '#F6F3EC' : '#94A3B8',
            fontWeight: 700,
            fontSize: '14px',
            padding: '10px 4px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}
        >
          <span>Intervention Support Groups</span>
          <span style={{
            backgroundColor: supportGroups.length > 0 ? '#22D3EE' : '#27325E',
            color: supportGroups.length > 0 ? '#0B1020' : '#94A3B8',
            fontSize: '10px',
            fontWeight: 800,
            padding: '1px 6px',
            borderRadius: '10px',
          }}>
            {supportGroups.length}
          </span>
        </button>
      </div>

      {activeTab === 'map' ? (
        <>
          {/* Controls Bar */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '16px',
            gap: '14px',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              {assessments.length > 0 && (
                <select
                  value={activeAssessmentId || ''}
                  onChange={(e) => {
                    const id = e.target.value;
                    setActiveAssessmentId(id);
                    loadEvidence(id);
                  }}
                  style={{
                    backgroundColor: '#151B3A',
                    border: '1px solid #7C5CFF',
                    color: '#F6F3EC',
                    padding: '6px 12px',
                    borderRadius: '6px',
                    fontSize: '12px',
                    outline: 'none',
                    fontWeight: 600,
                  }}
                >
                  {assessments.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.title} ({a.created_at ? a.created_at.slice(0, 10) : a.status})
                    </option>
                  ))}
                </select>
              )}

              <select
                value={topicFilter}
                onChange={(e) => setTopicFilter(e.target.value)}
                style={{
                  backgroundColor: '#151B3A',
                  border: '1px solid #27325E',
                  color: '#F6F3EC',
                  padding: '6px 12px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  outline: 'none',
                }}
              >
                <option value="ALL">All Curriculum Topics</option>
                <option value="MATH-G6-FRAC">Fractions (3 items)</option>
                <option value="MATH-G6-DEC">Decimals (3 items)</option>
                <option value="MATH-G6-PCT">Percentages (4 items)</option>
              </select>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{
                  backgroundColor: '#151B3A',
                  border: '1px solid #27325E',
                  color: '#F6F3EC',
                  padding: '6px 12px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  outline: 'none',
                }}
              >
                <option value="ALL">All Diagnostic Statuses</option>
                <option value="pending_review">Pending Review (&lt;60%)</option>
                <option value="confirmed">Teacher-Confirmed Needs</option>
                <option value="secure">Secure (≥60%)</option>
                <option value="insufficient_evidence">Insufficient Evidence</option>
              </select>
            </div>

            <input
              type="text"
              placeholder="Search student or ref (e.g. SYN-L6-014)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                backgroundColor: '#151B3A',
                border: '1px solid #27325E',
                color: '#F6F3EC',
                padding: '8px 16px',
                borderRadius: '6px',
                fontSize: '13px',
                width: '300px',
                outline: 'none',
              }}
            />
          </div>

          {/* Table */}
          <div style={{
            backgroundColor: '#151B3A',
            borderRadius: '10px',
            border: '1px solid #27325E',
            overflow: 'hidden',
          }}>
            <table>
              <thead>
                <tr style={{ backgroundColor: '#0B1020', borderBottom: '1px solid #27325E' }}>
                  <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', color: '#94A3B8', fontWeight: 600 }}>Ref</th>
                  <th style={{ padding: '12px 16px', textAlign: 'left', fontSize: '12px', color: '#94A3B8', fontWeight: 600 }}>Student Name</th>
                  <th style={{ padding: '12px 16px', textAlign: 'center', fontSize: '12px', color: '#94A3B8', fontWeight: 600 }}>Fractions (3Q)</th>
                  <th style={{ padding: '12px 16px', textAlign: 'center', fontSize: '12px', color: '#94A3B8', fontWeight: 600 }}>Decimals (3Q)</th>
                  <th style={{ padding: '12px 16px', textAlign: 'center', fontSize: '12px', color: '#94A3B8', fontWeight: 600 }}>Percentages (4Q)</th>
                  <th style={{ padding: '12px 16px', textAlign: 'center', fontSize: '12px', color: '#94A3B8', fontWeight: 600 }}>Overall</th>
                  <th style={{ padding: '12px 16px', textAlign: 'right', fontSize: '12px', color: '#94A3B8', fontWeight: 600 }}>Evidence Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredLearners.map((learner) => {
                  const isTargetDemo = learner.external_ref === 'SYN-L6-014';
                  const lEvidence = learnerEvidenceMap[learner.id] || {};

                  const fracEv = lEvidence['MATH-G6-FRAC'];
                  const decEv = lEvidence['MATH-G6-DEC'];
                  const pctEv = lEvidence['MATH-G6-PCT'];

                  const totalAwarded = (fracEv ? Number(fracEv.awarded_marks) : 0) + (decEv ? Number(decEv.awarded_marks) : 0) + (pctEv ? Number(pctEv.awarded_marks) : 0);
                  const totalPossible = (fracEv ? Number(fracEv.possible_marks) : 0) + (decEv ? Number(decEv.possible_marks) : 0) + (pctEv ? Number(pctEv.possible_marks) : 0);

                  return (
                    <tr
                      key={learner.id}
                      style={{
                        borderBottom: '1px solid #1E2752',
                        backgroundColor: isTargetDemo
                          ? 'rgba(124, 92, 255, 0.12)'
                          : 'transparent',
                      }}
                    >
                      <td style={{ padding: '12px 16px', fontSize: '13px', fontFamily: 'Consolas, monospace', color: '#22D3EE', fontWeight: 600 }}>
                        {learner.external_ref}
                      </td>
                      <td style={{ padding: '12px 16px', fontSize: '14px', fontWeight: 600, color: '#F6F3EC' }}>
                        {learner.first_name} {learner.last_name}
                        {isTargetDemo && (
                          <span style={{
                            marginLeft: '8px',
                            backgroundColor: '#7C5CFF',
                            color: '#FFFFFF',
                            padding: '1px 6px',
                            borderRadius: '3px',
                            fontSize: '10px',
                            fontWeight: 700,
                          }}>
                            Target 7/10 Demo
                          </span>
                        )}
                      </td>

                      {/* Fractions Cell */}
                      <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                        {fracEv ? (
                          <button
                            onClick={() => setSelectedEvidence(fracEv)}
                            style={{
                              backgroundColor: fracEv.status === 'confirmed' ? '#FFB547' : fracEv.status === 'pending_review' ? 'rgba(255, 181, 71, 0.2)' : 'rgba(52, 211, 153, 0.15)',
                              color: fracEv.status === 'confirmed' ? '#0B1020' : fracEv.status === 'pending_review' ? '#FFB547' : '#34D399',
                              border: fracEv.status === 'pending_review' ? '1px solid #FFB547' : '1px solid transparent',
                              padding: '4px 10px',
                              borderRadius: '6px',
                              fontSize: '12px',
                              fontWeight: 700,
                            }}
                          >
                            {fracEv.status === 'confirmed' ? '★ Confirmed Need' : `${fracEv.awarded_marks}/${fracEv.possible_marks} (${fracEv.percentage !== null && fracEv.percentage !== undefined ? `${fracEv.percentage}%` : 'Blanks'}) ⚠`}
                          </button>
                        ) : (
                          <span style={{ color: '#64748B', fontSize: '12px' }}>—</span>
                        )}
                      </td>

                      {/* Decimals Cell */}
                      <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                        {decEv ? (
                          <button
                            onClick={() => setSelectedEvidence(decEv)}
                            style={{
                              backgroundColor: 'rgba(52, 211, 153, 0.15)',
                              color: '#34D399',
                              border: 'none',
                              padding: '4px 10px',
                              borderRadius: '6px',
                              fontSize: '12px',
                              fontWeight: 600,
                            }}
                          >
                            {decEv.awarded_marks}/{decEv.possible_marks} ({decEv.percentage}%)
                          </button>
                        ) : (
                          <span style={{ color: '#64748B', fontSize: '12px' }}>—</span>
                        )}
                      </td>

                      {/* Percentages Cell */}
                      <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                        {pctEv ? (
                          <button
                            onClick={() => setSelectedEvidence(pctEv)}
                            style={{
                              backgroundColor: 'rgba(52, 211, 153, 0.15)',
                              color: '#34D399',
                              border: 'none',
                              padding: '4px 10px',
                              borderRadius: '6px',
                              fontSize: '12px',
                              fontWeight: 600,
                            }}
                          >
                            {pctEv.awarded_marks}/{pctEv.possible_marks} ({pctEv.percentage}%)
                          </button>
                        ) : (
                          <span style={{ color: '#64748B', fontSize: '12px' }}>—</span>
                        )}
                      </td>

                      {/* Overall Mark */}
                      <td style={{ padding: '12px 16px', textAlign: 'center', fontSize: '13px', fontWeight: 700, color: '#F6F3EC' }}>
                        {totalPossible > 0 ? (
                          <span>
                            {totalAwarded}/{totalPossible} ({Math.round((totalAwarded / totalPossible) * 100)}%)
                          </span>
                        ) : (
                          <span style={{ color: '#64748B' }}>Unassessed</span>
                        )}
                      </td>

                      {/* Action */}
                      <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                        {fracEv ? (
                          <button
                            onClick={() => setSelectedEvidence(fracEv)}
                            style={{
                              backgroundColor: fracEv.status === 'confirmed' ? 'rgba(52, 211, 153, 0.2)' : 'rgba(255, 181, 71, 0.15)',
                              color: fracEv.status === 'confirmed' ? '#34D399' : '#FFB547',
                              border: fracEv.status === 'confirmed' ? '1px solid #34D399' : '1px solid #FFB547',
                              padding: '4px 10px',
                              borderRadius: '4px',
                              fontSize: '11px',
                              fontWeight: 700,
                            }}
                          >
                            {fracEv.status === 'confirmed' ? 'View Decision' : 'Inspect Evidence'}
                          </button>
                        ) : (
                          <span style={{ color: '#64748B', fontSize: '12px' }}>Secure</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        /* Support Groups Tab */
        <div>
          {supportGroups.length === 0 ? (
            <div style={{
              backgroundColor: '#151B3A',
              border: '1px dashed #27325E',
              borderRadius: '10px',
              padding: '40px',
              textAlign: 'center',
            }}>
              <h4 style={{ fontSize: '16px', fontWeight: 700, color: '#F6F3EC', marginBottom: '6px' }}>
                No Support Groups Formed Yet
              </h4>
              <p style={{ color: '#94A3B8', fontSize: '13px', maxWidth: '480px', margin: '0 auto 18px auto' }}>
                Per Section 10.3, teachers group learners with confirmed diagnostic needs to prepare focused practice.
              </p>
              <button
                onClick={() => setIsGroupModalOpen(true)}
                disabled={confirmedCount === 0}
                style={{
                  backgroundColor: confirmedCount > 0 ? '#FFB547' : '#334155',
                  color: confirmedCount > 0 ? '#0B1020' : '#64748B',
                  fontWeight: 700,
                  fontSize: '13px',
                  padding: '10px 18px',
                  borderRadius: '6px',
                  border: 'none',
                }}
              >
                {confirmedCount > 0 ? `Form Group with ${confirmedCount} Confirmed Learners` : 'Confirm a Learning Need First'}
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {supportGroups.map((grp) => (
                <div
                  key={grp.id}
                  style={{
                    backgroundColor: '#151B3A',
                    border: '1px solid #27325E',
                    borderRadius: '10px',
                    padding: '20px 24px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '14px' }}>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                        <span style={{
                          backgroundColor: '#7C5CFF',
                          color: '#FFFFFF',
                          fontSize: '10px',
                          fontWeight: 700,
                          padding: '2px 6px',
                          borderRadius: '4px',
                          textTransform: 'uppercase',
                        }}>
                          Active Support Cohort
                        </span>
                        <span style={{ color: '#22D3EE', fontSize: '12px', fontWeight: 600 }}>
                          Topic: {grp.topic_name} ({grp.topic_code})
                        </span>
                      </div>
                      <h4 style={{ fontSize: '18px', fontWeight: 700, color: '#F6F3EC' }}>
                        {grp.name}
                      </h4>
                      <p style={{ fontSize: '12px', color: '#94A3B8', marginTop: '2px' }}>
                        Formed by {grp.created_by_name} · {new Date(grp.created_at).toLocaleDateString()}
                      </p>
                    </div>

                    <span style={{
                      backgroundColor: 'rgba(34, 211, 238, 0.15)',
                      color: '#22D3EE',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      fontSize: '12px',
                      fontWeight: 700,
                    }}>
                      {grp.members.length} Enrolled Learners
                    </span>
                  </div>

                  <div style={{
                    backgroundColor: '#0B1020',
                    border: '1px solid #27325E',
                    borderRadius: '8px',
                    padding: '12px 16px',
                  }}>
                    <div style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600, marginBottom: '8px' }}>
                      Enrolled Learners (Confirmed Evidence Snapshots)
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px' }}>
                      {grp.members.map((m) => (
                        <div
                          key={m.id}
                          style={{
                            backgroundColor: '#151B3A',
                            border: '1px solid #27325E',
                            padding: '4px 10px',
                            borderRadius: '6px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '6px',
                          }}
                        >
                          <span style={{ fontSize: '12px', fontWeight: 600, color: '#F6F3EC' }}>
                            {m.learner_name}
                          </span>
                          <span style={{ fontSize: '11px', fontFamily: 'Consolas, monospace', color: '#22D3EE' }}>
                            {m.learner_ref}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '14px' }}>
                    <button
                      onClick={() => setSelectedStudioGroup(grp)}
                      style={{
                        backgroundColor: '#7C5CFF',
                        color: '#FFFFFF',
                        border: 'none',
                        borderRadius: '6px',
                        padding: '8px 16px',
                        fontSize: '12px',
                        fontWeight: 700,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        boxShadow: '0 2px 8px rgba(124, 92, 255, 0.4)',
                      }}
                    >
                      <span>✦</span> Open Support Studio (Intervention Drafting)
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Modals */}
      {isImportModalOpen && (
        <ImportModal
          classroomId={classroom.id}
          onClose={() => setIsImportModalOpen(false)}
          onImportSuccess={(newAssmtId) => {
            setIsImportModalOpen(false);
            loadAssessments(newAssmtId);
          }}
        />
      )}

      {selectedEvidence && (
        <EvidenceModal
          evidence={selectedEvidence}
          onClose={() => setSelectedEvidence(null)}
          onDecisionRecorded={(updated) => {
            setSelectedEvidence(updated);
            if (activeAssessmentId) {
              loadEvidence(activeAssessmentId);
            }
          }}
        />
      )}

      {isGroupModalOpen && (
        <SupportGroupModal
          classroomId={classroom.id}
          evidenceList={evidenceList}
          onClose={() => setIsGroupModalOpen(false)}
          onGroupCreated={(newGroup) => {
            setIsGroupModalOpen(false);
            setSupportGroups((prev) => [newGroup, ...prev]);
            setActiveTab('groups');
          }}
        />
      )}

      {selectedStudioGroup && (
        <SupportStudioModal
          isOpen={!!selectedStudioGroup}
          group={selectedStudioGroup}
          onClose={() => setSelectedStudioGroup(null)}
          onPlanUpdated={loadSupportGroups}
        />
      )}
    </div>
  );
};
