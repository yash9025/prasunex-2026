import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { PlanProgressReport, SupportGroup, SupportPlan } from '../types';
import { useModalA11y } from '../hooks/useModalA11y';

interface ProgressReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  group: SupportGroup;
  plan: SupportPlan;
  onPlanClosed: () => void;
}

export const ProgressReviewModal: React.FC<ProgressReviewModalProps> = ({
  isOpen,
  onClose,
  group,
  plan,
  onPlanClosed,
}) => {
  const containerRef = useModalA11y({
    isOpen,
    onClose,
    closeOnEscape: true,
  });

  const [report, setReport] = useState<PlanProgressReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [rationale, setRationale] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadProgress();
    } else {
      setReport(null);
      setErrorMsg(null);
      setSuccessMsg(null);
      setRationale('');
    }
  }, [isOpen, plan.id]);

  const loadProgress = async () => {
    try {
      setIsLoading(true);
      setErrorMsg(null);
      const data = await api.getPlanProgress(plan.id);
      setReport(data);
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to load progress report');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDecision = async (action: 'close' | 'request_revision') => {
    if (!rationale.trim() || rationale.length < 10) {
      setErrorMsg('Please enter a descriptive teacher observation rationale (at least 10 characters).');
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMsg(null);
      await api.closePlan(plan.id, action, rationale);
      setSuccessMsg(
        action === 'close'
          ? 'Intervention cycle successfully closed. Evidence shows mastery achieved!'
          : 'Remedial revision requested for further practice.'
      );
      onPlanClosed();
      loadProgress();
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to submit teacher decision');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div
      onClick={(e) => {
        if (e.target === e.currentTarget && !isSubmitting) onClose();
      }}
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(11, 16, 32, 0.85)',
        backdropFilter: 'blur(6px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1100,
        padding: '20px',
      }}
    >
      <div
        ref={containerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="progress-modal-title"
        style={{
          backgroundColor: '#151B3A',
          border: '1px solid #27325E',
          borderRadius: '16px',
          width: '920px',
          maxWidth: '96vw',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6)',
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid #27325E',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{
                backgroundColor: '#34D399',
                color: '#0B1020',
                fontSize: '10px',
                fontWeight: 800,
                padding: '2px 8px',
                borderRadius: '4px',
                textTransform: 'uppercase',
              }}>
                Progress & Mastery Review
              </span>
              <span style={{ color: '#22D3EE', fontSize: '13px', fontWeight: 600 }}>
                {group.topic_name} ({group.topic_code})
              </span>
              <span style={{
                backgroundColor: '#27325E',
                color: '#F6F3EC',
                fontSize: '11px',
                padding: '2px 8px',
                borderRadius: '4px',
              }}>
                Status: {report?.plan_status || plan.status}
              </span>
            </div>
            <h3 id="progress-modal-title" style={{ fontSize: '18px', fontWeight: 700, color: '#F6F3EC', marginTop: '4px' }}>
              Intervention Progress Report: {group.name}
            </h3>
          </div>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            style={{
              background: 'none',
              border: 'none',
              color: '#94A3B8',
              fontSize: '22px',
              cursor: 'pointer',
              padding: '4px 8px',
            }}
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
          {errorMsg && (
            <div style={{
              backgroundColor: 'rgba(255, 107, 107, 0.15)',
              border: '1px solid #FF6B6B',
              color: '#FF6B6B',
              padding: '10px 14px',
              borderRadius: '6px',
              marginBottom: '16px',
              fontSize: '13px',
            }}>
              {errorMsg}
            </div>
          )}

          {successMsg && (
            <div style={{
              backgroundColor: 'rgba(52, 211, 153, 0.15)',
              border: '1px solid #34D399',
              color: '#34D399',
              padding: '10px 14px',
              borderRadius: '6px',
              marginBottom: '16px',
              fontSize: '13px',
            }}>
              ✓ {successMsg}
            </div>
          )}

          {isLoading ? (
            <div style={{ textAlign: 'center', padding: '40px', color: '#94A3B8' }}>
              Loading comparative trajectory...
            </div>
          ) : report ? (
            <>
              {/* Cohort Summary Cards */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '14px',
                marginBottom: '20px',
              }}>
                <div style={{
                  backgroundColor: '#0B1020',
                  border: '1px solid #27325E',
                  padding: '14px',
                  borderRadius: '8px',
                }}>
                  <div style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600 }}>Cohort Size</div>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: '#F6F3EC', marginTop: '4px' }}>
                    {report.total_learners} Learners
                  </div>
                </div>

                <div style={{
                  backgroundColor: '#0B1020',
                  border: '1px solid #27325E',
                  padding: '14px',
                  borderRadius: '8px',
                }}>
                  <div style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600 }}>Reassessment Completion</div>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: report.all_completed ? '#34D399' : '#FFB547', marginTop: '4px' }}>
                    {report.completed_count} / {report.total_learners} Completed
                  </div>
                </div>

                <div style={{
                  backgroundColor: '#0B1020',
                  border: '1px solid #27325E',
                  padding: '14px',
                  borderRadius: '8px',
                }}>
                  <div style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 600 }}>Assigned Content</div>
                  <div style={{ fontSize: '20px', fontWeight: 800, color: '#22D3EE', marginTop: '4px' }}>
                    Version {report.assigned_version_num} (Frozen)
                  </div>
                </div>
              </div>

              {/* Comparative Trajectory Table */}
              <div style={{
                backgroundColor: '#0B1020',
                border: '1px solid #27325E',
                borderRadius: '10px',
                overflow: 'hidden',
                marginBottom: '20px',
              }}>
                <div style={{ padding: '12px 16px', borderBottom: '1px solid #27325E', fontWeight: 700, fontSize: '13px', color: '#F6F3EC' }}>
                  Pre-Intervention vs. Post-Intervention Trajectory
                </div>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
                  <thead>
                    <tr style={{ backgroundColor: '#151B3A', borderBottom: '1px solid #27325E', color: '#94A3B8', fontSize: '11px' }}>
                      <th style={{ padding: '10px 14px' }}>Learner</th>
                      <th style={{ padding: '10px 14px', textAlign: 'center' }}>Baseline Score</th>
                      <th style={{ padding: '10px 14px', textAlign: 'center' }}>Fresh Reassessment</th>
                      <th style={{ padding: '10px 14px', textAlign: 'center' }}>Trajectory Delta</th>
                      <th style={{ padding: '10px 14px', textAlign: 'right' }}>Diagnostic Outcome</th>
                    </tr>
                  </thead>
                  <tbody>
                    {report.learners.map((l) => {
                      const delta = l.reassessment_percentage !== null && l.reassessment_percentage !== undefined
                        ? Math.round(l.reassessment_percentage - l.baseline_percentage)
                        : null;

                      return (
                        <tr key={l.learner_id} style={{ borderBottom: '1px solid #27325E' }}>
                          <td style={{ padding: '12px 14px' }}>
                            <strong style={{ color: '#F6F3EC', display: 'block' }}>{l.learner_name}</strong>
                            <span style={{ fontSize: '11px', color: '#22D3EE', fontFamily: 'Consolas, monospace' }}>
                              {l.learner_ref}
                            </span>
                          </td>

                          <td style={{ padding: '12px 14px', textAlign: 'center' }}>
                            <span style={{
                              backgroundColor: 'rgba(255, 107, 107, 0.15)',
                              color: '#FF6B6B',
                              padding: '2px 8px',
                              borderRadius: '4px',
                              fontWeight: 700,
                            }}>
                              {l.baseline_awarded}/{l.baseline_possible} ({Math.round(l.baseline_percentage)}%)
                            </span>
                          </td>

                          <td style={{ padding: '12px 14px', textAlign: 'center' }}>
                            {l.is_completed ? (
                              <span style={{
                                backgroundColor: 'rgba(52, 211, 153, 0.15)',
                                color: '#34D399',
                                padding: '2px 8px',
                                borderRadius: '4px',
                                fontWeight: 700,
                              }}>
                                {l.reassessment_awarded}/{l.reassessment_possible} ({Math.round(l.reassessment_percentage || 0)}%)
                              </span>
                            ) : (
                              <span style={{ color: '#94A3B8', fontSize: '12px' }}>Pending Sitting</span>
                            )}
                          </td>

                          <td style={{ padding: '12px 14px', textAlign: 'center' }}>
                            {delta !== null ? (
                              <span style={{
                                color: delta >= 0 ? '#34D399' : '#FF6B6B',
                                fontWeight: 800,
                              }}>
                                {delta >= 0 ? `+${delta}%` : `${delta}%`}
                              </span>
                            ) : (
                              <span style={{ color: '#64748B' }}>—</span>
                            )}
                          </td>

                          <td style={{ padding: '12px 14px', textAlign: 'right' }}>
                            {l.is_completed && (l.reassessment_percentage || 0) >= 60 ? (
                              <span style={{ color: '#34D399', fontWeight: 700, fontSize: '12px' }}>
                                ✓ Secure / Mastered
                              </span>
                            ) : l.is_completed ? (
                              <span style={{ color: '#FFB547', fontWeight: 700, fontSize: '12px' }}>
                                ⚠ Review Continued
                              </span>
                            ) : (
                              <span style={{ color: '#94A3B8', fontSize: '12px' }}>Awaiting Sitting</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Teacher Decision Box */}
              {report.plan_status !== 'closed' && (
                <div style={{
                  backgroundColor: '#0B1020',
                  border: '1px solid #27325E',
                  borderRadius: '10px',
                  padding: '16px',
                }}>
                  <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#F6F3EC', marginBottom: '4px' }}>
                    Teacher Observation & Intervention Closure
                  </h4>
                  <p style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '10px' }}>
                    Review the evidence above and record your final decision to conclude this intervention or schedule further practice.
                  </p>

                  <textarea
                    placeholder="Enter observation notes explaining the evidence (e.g. Learners demonstrated mastery of common denominators on fresh items)..."
                    value={rationale}
                    onChange={(e) => setRationale(e.target.value)}
                    rows={3}
                    style={{
                      width: '100%',
                      backgroundColor: '#151B3A',
                      border: '1px solid #27325E',
                      color: '#F6F3EC',
                      padding: '10px 12px',
                      borderRadius: '6px',
                      fontSize: '13px',
                      outline: 'none',
                      marginBottom: '12px',
                    }}
                  />

                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                    <button
                      onClick={() => handleDecision('request_revision')}
                      disabled={isSubmitting}
                      style={{
                        backgroundColor: '#FFB547',
                        color: '#0B1020',
                        border: 'none',
                        padding: '8px 16px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: 700,
                        cursor: isSubmitting ? 'not-allowed' : 'pointer',
                      }}
                    >
                      Request Remedial Revision
                    </button>
                    <button
                      onClick={() => handleDecision('close')}
                      disabled={isSubmitting}
                      style={{
                        backgroundColor: '#34D399',
                        color: '#0B1020',
                        border: 'none',
                        padding: '8px 20px',
                        borderRadius: '6px',
                        fontSize: '12px',
                        fontWeight: 800,
                        cursor: isSubmitting ? 'not-allowed' : 'pointer',
                        boxShadow: '0 2px 10px rgba(52, 211, 153, 0.4)',
                      }}
                    >
                      {isSubmitting ? 'Recording...' : 'Close Intervention (Mastery Achieved)'}
                    </button>
                  </div>
                </div>
              )}
            </>
          ) : null}
        </div>

        {/* Footer */}
        <div style={{
          padding: '14px 24px',
          borderTop: '1px solid #27325E',
          display: 'flex',
          justifyContent: 'flex-end',
          backgroundColor: '#0B1020',
        }}>
          <button
            onClick={onClose}
            style={{
              backgroundColor: 'transparent',
              color: '#94A3B8',
              border: '1px solid #27325E',
              padding: '8px 16px',
              borderRadius: '6px',
              fontSize: '13px',
              cursor: 'pointer',
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
