import React, { useState } from 'react';
import { api } from '../services/api';
import { GapEvidence } from '../types';
import { useModalA11y } from '../hooks/useModalA11y';

interface EvidenceModalProps {
  evidence: GapEvidence | null;
  onClose: () => void;
  onDecisionRecorded: (updated: GapEvidence) => void;
}

export const EvidenceModal: React.FC<EvidenceModalProps> = ({
  evidence,
  onClose,
  onDecisionRecorded,
}) => {
  const containerRef = useModalA11y({
    isOpen: Boolean(evidence),
    onClose,
  });

  if (!evidence) return null;

  const [action, setAction] = useState<'confirm' | 'correct' | 'dismiss'>('confirm');
  const [rationale, setRationale] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleDecisionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rationale.trim() || rationale.trim().length < 3) {
      setErrorMsg('Please provide a pedagogical rationale for your decision (minimum 3 characters).');
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const updated = await api.recordTeacherDecision(evidence.id, action, rationale);
      onDecisionRecorded(updated);
      setRationale('');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to submit decision.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'confirmed':
        return '#FFB547';
      case 'pending_review':
        return '#FFB547';
      case 'secure':
        return '#34D399';
      case 'dismissed':
        return '#94A3B8';
      case 'corrected':
        return '#22D3EE';
      default:
        return '#94A3B8';
    }
  };

  return (
    <div
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(11, 16, 32, 0.85)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 50,
        padding: '20px',
      }}
    >
      <div
        ref={containerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="evidence-modal-title"
        style={{
          backgroundColor: '#151B3A',
          border: '1px solid #27325E',
          borderRadius: '12px',
          width: '100%',
          maxWidth: '740px',
          padding: '28px',
          boxShadow: '0 24px 48px rgba(0, 0, 0, 0.6)',
          maxHeight: '92vh',
          overflowY: 'auto',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span style={{
                backgroundColor: getStatusBadgeColor(evidence.status),
                color: '#0B1020',
                fontSize: '11px',
                fontWeight: 800,
                padding: '2px 8px',
                borderRadius: '4px',
                textTransform: 'uppercase',
              }}>
                {evidence.status === 'confirmed' ? '★ Confirmed Need' : evidence.status === 'pending_review' ? 'Review Signal' : evidence.status}
              </span>
              <span style={{ color: '#22D3EE', fontSize: '13px', fontWeight: 600 }}>
                {evidence.topic_name} ({evidence.topic_code})
              </span>
            </div>
            <h3 id="evidence-modal-title" style={{ fontSize: '20px', fontWeight: 700, color: '#F6F3EC' }}>
              {evidence.learner_name} · <span style={{ fontFamily: 'Consolas, monospace', color: '#22D3EE' }}>{evidence.learner_ref}</span>
            </h3>
          </div>
          <button
            onClick={onClose}
            aria-label="Close evidence detail modal"
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94A3B8',
              fontSize: '20px',
              cursor: 'pointer',
              padding: '4px 8px',
            }}
          >
            ✕
          </button>
        </div>

        {/* Diagnostic Score Metrics */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '12px',
          backgroundColor: '#0B1020',
          padding: '16px',
          borderRadius: '8px',
          border: '1px solid #27325E',
          marginBottom: '20px',
        }}>
          <div>
            <div style={{ fontSize: '11px', color: '#94A3B8' }}>Awarded Marks</div>
            <div style={{ fontSize: '18px', fontWeight: 700, color: '#F6F3EC' }}>
              {evidence.awarded_marks} / {evidence.possible_marks}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '11px', color: '#94A3B8' }}>Topic Percentage</div>
            <div style={{
              fontSize: '18px',
              fontWeight: 700,
              color: evidence.percentage !== null && evidence.percentage !== undefined && evidence.percentage < 60 ? '#FFB547' : '#34D399',
            }}>
              {evidence.percentage !== null && evidence.percentage !== undefined ? `${evidence.percentage}%` : 'N/A (Blanks)'}
            </div>
          </div>
          <div>
            <div style={{ fontSize: '11px', color: '#94A3B8' }}>Assessed Items</div>
            <div style={{ fontSize: '18px', fontWeight: 700, color: '#22D3EE' }}>
              {evidence.assessed_items_count} <span style={{ fontSize: '12px', color: '#94A3B8' }}>valid</span>
            </div>
          </div>
          <div>
            <div style={{ fontSize: '11px', color: '#94A3B8' }}>Rule Version</div>
            <div style={{ fontSize: '18px', fontWeight: 700, color: '#94A3B8' }}>
              {evidence.rule_version}
            </div>
          </div>
        </div>

        {/* Misconception Tag Callout */}
        {evidence.suspected_pattern && (
          <div style={{
            backgroundColor: 'rgba(34, 211, 238, 0.1)',
            border: '1px solid #22D3EE',
            borderRadius: '8px',
            padding: '14px 18px',
            marginBottom: '20px',
          }}>
            <div style={{ color: '#22D3EE', fontWeight: 700, fontSize: '13px', marginBottom: '4px' }}>
              ★ Suspected Pedagogical Misconception Tagged
            </div>
            <div style={{ color: '#F6F3EC', fontSize: '12px', lineHeight: 1.5 }}>
              Pattern: <code>{evidence.suspected_pattern}</code>. Learner exhibits repeated numerator-and-denominator addition without finding common multiples ($1/2 + 1/3 = 2/5$ and $1/4 + 1/2 = 1/3$).
            </div>
          </div>
        )}

        {/* Question Responses Breakdown */}
        <h4 style={{ fontSize: '14px', fontWeight: 700, color: '#F6F3EC', marginBottom: '12px' }}>
          Question-Level Evidence ({evidence.supporting_attempts.length} attempts)
        </h4>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '24px' }}>
          {evidence.supporting_attempts.map((att) => {
            const isCorrect = att.outcome === 'correct';
            const isUnattempted = att.outcome === 'unattempted';

            return (
              <div
                key={att.attempt_id}
                style={{
                  backgroundColor: '#0B1020',
                  border: '1px solid #27325E',
                  borderRadius: '8px',
                  padding: '12px 16px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{ color: '#22D3EE', fontWeight: 700, fontSize: '12px' }}>
                      {att.question_ref}
                    </span>
                    <span style={{ color: '#F6F3EC', fontSize: '13px', fontWeight: 500 }}>
                      {att.question_text}
                    </span>
                  </div>
                  <div style={{ fontSize: '12px', color: '#94A3B8' }}>
                    Key: <strong style={{ color: '#34D399' }}>{att.expected_answer}</strong> ·
                    Submitted: <strong style={{ color: isCorrect ? '#34D399' : isUnattempted ? '#94A3B8' : '#FF6B6B' }}>
                      {isUnattempted ? '(Blank / Unattempted)' : att.raw_response}
                    </strong>
                    {att.normalized_value && att.normalized_value !== att.raw_response && (
                      <span style={{ color: '#64748B', marginLeft: '6px' }}>
                        (Normalized: {att.normalized_value})
                      </span>
                    )}
                  </div>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <span style={{
                    backgroundColor: isCorrect ? 'rgba(52, 211, 153, 0.15)' : isUnattempted ? 'rgba(148, 163, 184, 0.15)' : 'rgba(255, 107, 107, 0.15)',
                    color: isCorrect ? '#34D399' : isUnattempted ? '#94A3B8' : '#FF6B6B',
                    padding: '3px 8px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                  }}>
                    {att.outcome} (+{att.awarded_marks} / {att.max_marks})
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Teacher Decision Recording Form (Phase 3 Core Feature) */}
        <div style={{
          backgroundColor: '#0B1020',
          border: '1px solid #27325E',
          borderRadius: '10px',
          padding: '20px',
          marginBottom: '20px',
        }}>
          <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#FFB547', marginBottom: '6px' }}>
            Teacher Judgment &amp; Action (Section 10.2)
          </h4>
          <p style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '14px' }}>
            System flags are diagnostic suggestions. Teachers hold final authority to confirm, reassign, or dismiss support needs.
          </p>

          {errorMsg && (
            <div style={{
              backgroundColor: 'rgba(255, 107, 107, 0.15)',
              border: '1px solid #FF6B6B',
              color: '#FF6B6B',
              padding: '8px 12px',
              borderRadius: '6px',
              fontSize: '12px',
              marginBottom: '14px',
            }}>
              {errorMsg}
            </div>
          )}

          <form onSubmit={handleDecisionSubmit}>
            <div style={{ display: 'flex', gap: '10px', marginBottom: '14px' }}>
              <button
                type="button"
                onClick={() => setAction('confirm')}
                style={{
                  flex: 1,
                  padding: '8px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  fontWeight: 700,
                  border: action === 'confirm' ? '2px solid #FFB547' : '1px solid #27325E',
                  backgroundColor: action === 'confirm' ? 'rgba(255, 181, 71, 0.2)' : 'transparent',
                  color: action === 'confirm' ? '#FFB547' : '#94A3B8',
                }}
              >
                ✓ Confirm Learning Need
              </button>

              <button
                type="button"
                onClick={() => setAction('correct')}
                style={{
                  flex: 1,
                  padding: '8px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  fontWeight: 700,
                  border: action === 'correct' ? '2px solid #22D3EE' : '1px solid #27325E',
                  backgroundColor: action === 'correct' ? 'rgba(34, 211, 238, 0.2)' : 'transparent',
                  color: action === 'correct' ? '#22D3EE' : '#94A3B8',
                }}
              >
                ✎ Correct / Reassign
              </button>

              <button
                type="button"
                onClick={() => setAction('dismiss')}
                style={{
                  flex: 1,
                  padding: '8px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  fontWeight: 700,
                  border: action === 'dismiss' ? '2px solid #94A3B8' : '1px solid #27325E',
                  backgroundColor: action === 'dismiss' ? 'rgba(148, 163, 184, 0.2)' : 'transparent',
                  color: action === 'dismiss' ? '#F6F3EC' : '#94A3B8',
                }}
              >
                ✕ Dismiss Flag
              </button>
            </div>

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '11px', color: '#94A3B8', marginBottom: '6px', fontWeight: 600 }}>
                Teacher Rationale &amp; Instructional Notes (Persisted to Audit Trail)
              </label>
              <textarea
                value={rationale}
                onChange={(e) => setRationale(e.target.value)}
                placeholder="Explain observation (e.g. Learner adds across numerators and denominators without common denominator)..."
                rows={3}
                style={{
                  width: '100%',
                  backgroundColor: '#151B3A',
                  border: '1px solid #27325E',
                  color: '#F6F3EC',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  fontSize: '12px',
                  outline: 'none',
                  resize: 'vertical',
                }}
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              style={{
                backgroundColor: action === 'confirm' ? '#FFB547' : action === 'correct' ? '#22D3EE' : '#94A3B8',
                color: '#0B1020',
                fontWeight: 700,
                fontSize: '13px',
                padding: '10px 18px',
                borderRadius: '6px',
                border: 'none',
                cursor: isSubmitting ? 'not-allowed' : 'pointer',
              }}
            >
              {isSubmitting ? 'Recording Decision...' : `Record ${action.toUpperCase()} Decision`}
            </button>
          </form>
        </div>

        {/* Decision History Log */}
        {evidence.decisions && evidence.decisions.length > 0 && (
          <div style={{ marginBottom: '20px' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 700, color: '#94A3B8', marginBottom: '8px' }}>
              Decision History Log ({evidence.decisions.length})
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {evidence.decisions.map((dec) => (
                <div
                  key={dec.id}
                  style={{
                    backgroundColor: '#0B1020',
                    border: '1px solid #27325E',
                    padding: '10px 14px',
                    borderRadius: '6px',
                    fontSize: '12px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2px' }}>
                    <span style={{ fontWeight: 700, color: getStatusBadgeColor(dec.action), textTransform: 'uppercase' }}>
                      {dec.action}
                    </span>
                    <span style={{ color: '#64748B' }}>
                      {new Date(dec.created_at).toLocaleString()}
                    </span>
                  </div>
                  <div style={{ color: '#F6F3EC' }}>{dec.rationale}</div>
                  <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '2px' }}>
                    Recorded by: {dec.actor_name}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div style={{ textAlign: 'right' }}>
          <button
            onClick={onClose}
            style={{
              backgroundColor: 'transparent',
              border: '1px solid #27325E',
              color: '#94A3B8',
              padding: '8px 16px',
              borderRadius: '6px',
              fontWeight: 600,
              fontSize: '12px',
              cursor: 'pointer',
            }}
          >
            Close Window
          </button>
        </div>
      </div>
    </div>
  );
};
