import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Assignment, QuizData, QuizSubmissionResult } from '../types';
import { useModalA11y } from '../hooks/useModalA11y';

interface ReassessmentQuizModalProps {
  isOpen: boolean;
  onClose: () => void;
  assignment: Assignment;
  onQuizSubmitted: () => void;
}

export const ReassessmentQuizModal: React.FC<ReassessmentQuizModalProps> = ({
  isOpen,
  onClose,
  assignment,
  onQuizSubmitted,
}) => {
  const containerRef = useModalA11y({
    isOpen,
    onClose,
    closeOnEscape: true,
  });

  const [selectedRecipientId, setSelectedRecipientId] = useState<string>('');
  const [quizData, setQuizData] = useState<QuizData | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionResult, setSubmissionResult] = useState<QuizSubmissionResult | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && assignment.recipients.length > 0) {
      // Pick first pending recipient or first recipient
      const firstPending = assignment.recipients.find((r) => r.status === 'pending') || assignment.recipients[0];
      setSelectedRecipientId(firstPending.id);
      loadQuiz(firstPending.id);
    } else {
      setQuizData(null);
      setSubmissionResult(null);
      setErrorMsg(null);
    }
  }, [isOpen, assignment.id]);

  const loadQuiz = async (recipientId: string) => {
    try {
      setErrorMsg(null);
      setSubmissionResult(null);
      const data = await api.getReassessmentQuiz(recipientId);
      setQuizData(data);

      const initialAnswers: Record<string, string> = {};
      data.questions.forEach((q) => {
        initialAnswers[q.question_ref] = '';
      });
      setAnswers(initialAnswers);
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to load quiz');
    }
  };

  const fillMasteredAnswers = () => {
    setAnswers({
      'Q-RE-FRAC-01': '7/12',
      'Q-RE-FRAC-02': '5/6',
      'Q-RE-FRAC-03': '5/8',
      'Q-RE-DEC-01': '0.95',
      'Q-RE-DEC-02': '1.35',
      'Q-RE-DEC-03': '0.75',
      'Q-RE-PCT-01': '75%',
      'Q-RE-PCT-02': '50%',
      'Q-RE-PCT-03': '50%',
    });
  };

  const fillMisconceptionAnswers = () => {
    // Adding numerators and denominators error pattern
    setAnswers({
      'Q-RE-FRAC-01': '2/7',  // 1/4 + 1/3 = 2/7 (misconception)
      'Q-RE-FRAC-02': '3/9',  // 2/3 + 1/6 = 3/9 (misconception)
      'Q-RE-FRAC-03': '4/12', // 3/8 + 1/4 = 4/12 (misconception)
    });
  };

  const handleSubmit = async () => {
    if (!quizData) return;
    try {
      setIsSubmitting(true);
      setErrorMsg(null);

      const formattedAnswers = Object.entries(answers).map(([qRef, rawResp]) => ({
        question_ref: qRef,
        raw_response: rawResp,
      }));

      const submissionKey = `sub-${selectedRecipientId}-${Date.now()}`;
      const result = await api.submitReassessmentQuiz(selectedRecipientId, submissionKey, formattedAnswers);
      setSubmissionResult(result);
      onQuizSubmitted();
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to submit reassessment quiz');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  const currentRecipient = assignment.recipients.find((r) => r.id === selectedRecipientId);

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
        aria-labelledby="quiz-modal-title"
        style={{
          backgroundColor: '#151B3A',
          border: '1px solid #27325E',
          borderRadius: '16px',
          width: '840px',
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
                backgroundColor: '#22D3EE',
                color: '#0B1020',
                fontSize: '10px',
                fontWeight: 800,
                padding: '2px 8px',
                borderRadius: '4px',
                textTransform: 'uppercase',
              }}>
                Fresh Reassessment Quiz
              </span>
              <span style={{ color: '#F6F3EC', fontSize: '13px', fontWeight: 600 }}>
                {assignment.topic_name} ({assignment.topic_code})
              </span>
            </div>
            <h3 id="quiz-modal-title" style={{ fontSize: '18px', fontWeight: 700, color: '#F6F3EC', marginTop: '4px' }}>
              Student Quiz Sitting: {currentRecipient?.learner_name} ({currentRecipient?.learner_ref})
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

        {/* Recipient Picker Bar */}
        <div style={{
          padding: '12px 24px',
          backgroundColor: '#0B1020',
          borderBottom: '1px solid #27325E',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '12px', color: '#94A3B8' }}>Select Learner Sitting:</span>
            <select
              value={selectedRecipientId}
              onChange={(e) => {
                setSelectedRecipientId(e.target.value);
                loadQuiz(e.target.value);
              }}
              style={{
                backgroundColor: '#151B3A',
                border: '1px solid #27325E',
                color: '#F6F3EC',
                fontSize: '12px',
                padding: '6px 12px',
                borderRadius: '6px',
                outline: 'none',
              }}
            >
              {assignment.recipients.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.learner_name} ({r.learner_ref}) — {r.status === 'completed' ? '✓ Completed' : 'Pending'}
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={fillMasteredAnswers}
              style={{
                backgroundColor: 'rgba(52, 211, 153, 0.15)',
                color: '#34D399',
                border: '1px solid #34D399',
                borderRadius: '4px',
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              Demo: Fill Mastered Key (100%)
            </button>
            <button
              onClick={fillMisconceptionAnswers}
              style={{
                backgroundColor: 'rgba(255, 181, 71, 0.15)',
                color: '#FFB547',
                border: '1px solid #FFB547',
                borderRadius: '4px',
                padding: '4px 10px',
                fontSize: '11px',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              Demo: Fill Misconception
            </button>
          </div>
        </div>

        {/* Body */}
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

          {submissionResult ? (
            /* Results View */
            <div style={{
              backgroundColor: '#0B1020',
              border: '1px solid #27325E',
              borderRadius: '12px',
              padding: '20px',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <span style={{
                    backgroundColor: submissionResult.mastery_achieved ? '#34D399' : '#FFB547',
                    color: '#0B1020',
                    fontSize: '11px',
                    fontWeight: 800,
                    padding: '2px 8px',
                    borderRadius: '4px',
                    textTransform: 'uppercase',
                  }}>
                    {submissionResult.mastery_achieved ? '✓ Topic Mastered' : 'Remediation Needed'}
                  </span>
                  <h4 style={{ fontSize: '18px', fontWeight: 700, color: '#F6F3EC', marginTop: '6px' }}>
                    Reassessment Outcome: {submissionResult.awarded_marks} / {submissionResult.possible_marks} ({submissionResult.percentage}%)
                  </h4>
                </div>
                <div style={{ fontSize: '24px', fontWeight: 800, color: submissionResult.mastery_achieved ? '#34D399' : '#FFB547' }}>
                  {submissionResult.percentage}%
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {submissionResult.items.map((it) => (
                  <div
                    key={it.question_ref}
                    style={{
                      backgroundColor: '#151B3A',
                      border: it.outcome === 'correct' ? '1px solid rgba(52, 211, 153, 0.4)' : '1px solid rgba(255, 107, 107, 0.4)',
                      borderRadius: '8px',
                      padding: '14px',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <strong style={{ fontSize: '13px', color: '#F6F3EC' }}>{it.question_text}</strong>
                      <span style={{
                        color: it.outcome === 'correct' ? '#34D399' : '#FF6B6B',
                        fontWeight: 700,
                        fontSize: '12px',
                      }}>
                        {it.awarded_marks}/{it.max_marks} marks ({it.outcome})
                      </span>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '12px', marginTop: '8px' }}>
                      <div>
                        <span style={{ color: '#94A3B8' }}>Submitted Response: </span>
                        <strong style={{ color: '#F6F3EC', fontFamily: 'Consolas, monospace' }}>
                          {it.raw_response || '(Blank)'}
                        </strong>
                      </div>
                      <div>
                        <span style={{ color: '#94A3B8' }}>Verified Solution Key: </span>
                        <strong style={{ color: '#34D399', fontFamily: 'Consolas, monospace' }}>
                          {it.expected_answer}
                        </strong>
                      </div>
                    </div>
                    <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '6px' }}>
                      Explanation: {it.rationale}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : quizData ? (
            /* Quiz Form View */
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ fontSize: '12px', color: '#94A3B8' }}>
                Please enter responses for each question. Answers can be simplified fractions (e.g. <code style={{ color: '#22D3EE' }}>7/12</code>, <code style={{ color: '#22D3EE' }}>5/6</code>) or decimals.
              </div>

              {quizData.questions.map((q, idx) => (
                <div
                  key={q.question_ref}
                  style={{
                    backgroundColor: '#0B1020',
                    border: '1px solid #27325E',
                    borderRadius: '10px',
                    padding: '16px',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{
                      backgroundColor: '#27325E',
                      color: '#F6F3EC',
                      fontSize: '11px',
                      fontWeight: 700,
                      padding: '2px 8px',
                      borderRadius: '4px',
                    }}>
                      Question {idx + 1} ({q.question_ref})
                    </span>
                    <span style={{ fontSize: '12px', color: '#94A3B8' }}>
                      {q.max_marks} mark
                    </span>
                  </div>

                  <p style={{ fontSize: '14px', color: '#F6F3EC', fontWeight: 600, marginBottom: '12px' }}>
                    {q.question_text}
                  </p>

                  <div>
                    <label style={{ fontSize: '11px', color: '#94A3B8', display: 'block', marginBottom: '4px' }}>
                      Student Answer:
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. 7/12"
                      value={answers[q.question_ref] || ''}
                      onChange={(e) => {
                        setAnswers({ ...answers, [q.question_ref]: e.target.value });
                      }}
                      style={{
                        backgroundColor: '#151B3A',
                        border: '1px solid #27325E',
                        color: '#F6F3EC',
                        padding: '10px 14px',
                        borderRadius: '6px',
                        fontSize: '14px',
                        fontFamily: 'Consolas, monospace',
                        outline: 'none',
                        width: '240px',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px', color: '#94A3B8' }}>
              Loading quiz questions...
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid #27325E',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
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

          {!submissionResult && (
            <button
              onClick={handleSubmit}
              disabled={isSubmitting || !quizData}
              style={{
                backgroundColor: '#22D3EE',
                color: '#0B1020',
                border: 'none',
                padding: '10px 24px',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: 800,
                cursor: isSubmitting ? 'not-allowed' : 'pointer',
                boxShadow: '0 2px 10px rgba(34, 211, 238, 0.4)',
              }}
            >
              {isSubmitting ? 'Grading Answers...' : 'Submit Reassessment Answers'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
