import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { ApprovedSnippet, Assignment, PracticeItem, SupportGroup, SupportPlan } from '../types';
import { AssignmentModal } from './AssignmentModal';
import { ReassessmentQuizModal } from './ReassessmentQuizModal';
import { ProgressReviewModal } from './ProgressReviewModal';
import { useModalA11y } from '../hooks/useModalA11y';

interface SupportStudioModalProps {
  isOpen: boolean;
  onClose: () => void;
  group: SupportGroup | null;
  onPlanUpdated?: () => void;
}

export const SupportStudioModal: React.FC<SupportStudioModalProps> = ({
  isOpen,
  onClose,
  group,
  onPlanUpdated,
}) => {
  const containerRef = useModalA11y({
    isOpen,
    onClose,
    closeOnEscape: true,
  });

  const [snippets, setSnippets] = useState<ApprovedSnippet[]>([]);
  const [selectedSnippetIds, setSelectedSnippetIds] = useState<string[]>([]);
  const [plan, setPlan] = useState<SupportPlan | null>(null);
  const [assignment, setAssignment] = useState<Assignment | null>(null);
  const [explanation, setExplanation] = useState('');
  const [practiceItems, setPracticeItems] = useState<PracticeItem[]>([]);
  const [genMode, setGenMode] = useState<'auto' | 'template'>('auto');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [signOffChecked, setSignOffChecked] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Phase 5 Modals
  const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
  const [isQuizModalOpen, setIsQuizModalOpen] = useState(false);
  const [isProgressModalOpen, setIsProgressModalOpen] = useState(false);

  useEffect(() => {
    if (isOpen && group) {
      loadSnippetsAndPlan();
    } else {
      setPlan(null);
      setAssignment(null);
      setErrorMsg(null);
      setSuccessMsg(null);
      setSignOffChecked(false);
    }
  }, [isOpen, group?.id]);

  const loadSnippetsAndPlan = async () => {
    if (!group) return;
    try {
      setErrorMsg(null);
      const snips = await api.getApprovedSnippets(group.topic_id);
      setSnippets(snips);
      if (snips.length > 0) {
        setSelectedSnippetIds(snips.map((s) => s.id));
      }

      // Check if plan already exists for this group
      const existingPlan = await api.getGroupPlan(group.id);
      if (existingPlan) {
        setPlan(existingPlan);
        if (existingPlan.current_version) {
          setExplanation(existingPlan.current_version.explanation);
          setPracticeItems(existingPlan.current_version.practice_items);
        }
        const existingAssign = await api.getPlanAssignment(existingPlan.id);
        setAssignment(existingAssign);
      }
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to initialize Support Studio');
    }
  };

  const handleGenerate = async () => {
    if (!group) return;
    if (selectedSnippetIds.length === 0) {
      setErrorMsg('Please select at least one approved curriculum source snippet.');
      return;
    }

    try {
      setIsGenerating(true);
      setErrorMsg(null);
      setSuccessMsg(null);

      const generatedPlan = await api.generateSupportDraft({
        support_group_id: group.id,
        source_snippet_ids: selectedSnippetIds,
        generation_mode: genMode,
      });

      setPlan(generatedPlan);
      if (generatedPlan.current_version) {
        setExplanation(generatedPlan.current_version.explanation);
        setPracticeItems(generatedPlan.current_version.practice_items);
      }
      setSuccessMsg(
        `Grounded draft generated successfully via ${generatedPlan.generation_mode === 'ai' ? 'Gemini AI' : 'curriculum template'}${generatedPlan.is_fallback ? ' (template fallback)' : ''}!`
      );
      if (onPlanUpdated) onPlanUpdated();
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to generate grounded support draft');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveDraft = async () => {
    if (!plan) return;
    try {
      setIsSaving(true);
      setErrorMsg(null);
      setSuccessMsg(null);

      const updated = await api.updateSupportDraft(plan.id, {
        revision: plan.revision,
        explanation,
        practice_items: practiceItems,
      });

      setPlan(updated);
      if (updated.current_version) {
        setExplanation(updated.current_version.explanation);
        setPracticeItems(updated.current_version.practice_items);
      }
      setSuccessMsg('Draft modifications saved and mathematically re-verified.');
      if (onPlanUpdated) onPlanUpdated();
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to save draft edits');
    } finally {
      setIsSaving(false);
    }
  };

  const handleApprove = async () => {
    if (!plan) return;
    if (!signOffChecked) {
      setErrorMsg('You must check the pedagogical responsibility box before approving.');
      return;
    }

    try {
      setIsApproving(true);
      setErrorMsg(null);
      setSuccessMsg(null);

      const approval = await api.approveSupportPlan(plan.id, {
        revision: plan.revision,
        sign_off_responsibility: true,
      });

      const reloaded = await api.getSupportPlan(plan.id);
      setPlan(reloaded);
      setSuccessMsg(`Plan version frozen and approved! Cryptographic audit hash: ${approval.approval_hash.slice(0, 16)}...`);
      if (onPlanUpdated) onPlanUpdated();
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to approve support plan');
    } finally {
      setIsApproving(false);
    }
  };

  const handleAssignmentCompleted = async () => {
    if (!group) return;
    await loadSnippetsAndPlan();
    if (onPlanUpdated) onPlanUpdated();
  };

  if (!isOpen || !group) return null;

  return (
    <div
      onClick={(e) => {
        if (e.target === e.currentTarget && !isSaving && !isApproving && !isGenerating) onClose();
      }}
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(11, 16, 32, 0.85)',
        backdropFilter: 'blur(6px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '20px',
      }}
    >
      <div
        ref={containerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="support-studio-title"
        style={{
          backgroundColor: '#151B3A',
          border: '1px solid #27325E',
          borderRadius: '16px',
          width: '1020px',
          maxWidth: '96vw',
          maxHeight: '92vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6)',
          overflow: 'hidden',
        }}
      >
        {/* Header */}
        <div style={{
          padding: '20px 28px',
          borderBottom: '1px solid #27325E',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{
                backgroundColor: '#7C5CFF',
                color: '#FFFFFF',
                fontSize: '11px',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: '4px',
                textTransform: 'uppercase',
              }}>
                Support Studio
              </span>
              <span style={{ color: '#22D3EE', fontSize: '13px', fontWeight: 600 }}>
                {group.topic_name} ({group.topic_code})
              </span>
              {plan && (
                <span style={{
                  backgroundColor: plan.status === 'closed' ? '#34D399' : plan.status === 'assigned' || plan.status === 'reassessed' ? '#22D3EE' : plan.status === 'reviewed' ? '#34D399' : '#FFB547',
                  color: '#0B1020',
                  fontSize: '11px',
                  fontWeight: 800,
                  padding: '2px 8px',
                  borderRadius: '4px',
                  textTransform: 'uppercase',
                }}>
                  Status: {plan.status}
                </span>
              )}
            </div>
            <h2 id="support-studio-title" style={{ fontSize: '20px', fontWeight: 700, color: '#F6F3EC', marginTop: '6px' }}>
              Intervention Workspace: {group.name}
            </h2>
            <p style={{ color: '#94A3B8', fontSize: '13px', marginTop: '2px' }}>
              Enrolled cohort: {group.members.map((m) => m.learner_name).join(', ')} ({group.members.length} confirmed)
            </p>
          </div>
          <button
            onClick={onClose}
            aria-label="Close Support Studio"
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

        {/* Body Content */}
        <div style={{ padding: '24px 28px', overflowY: 'auto', flex: 1 }}>
          {errorMsg && (
            <div style={{
              backgroundColor: 'rgba(255, 107, 107, 0.15)',
              border: '1px solid #FF6B6B',
              color: '#FF6B6B',
              padding: '12px 16px',
              borderRadius: '8px',
              marginBottom: '20px',
              fontSize: '13px',
            }}>
              <strong>Error:</strong> {errorMsg}
            </div>
          )}

          {successMsg && (
            <div style={{
              backgroundColor: 'rgba(52, 211, 153, 0.15)',
              border: '1px solid #34D399',
              color: '#34D399',
              padding: '12px 16px',
              borderRadius: '8px',
              marginBottom: '20px',
              fontSize: '13px',
            }}>
              ✓ {successMsg}
            </div>
          )}

          {/* Section 1: Approved Curriculum Grounding Sources */}
          <div style={{
            backgroundColor: '#0B1020',
            border: '1px solid #27325E',
            borderRadius: '12px',
            padding: '18px 20px',
            marginBottom: '24px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div>
                <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#F6F3EC' }}>
                  1. Approved Curriculum Grounding Sources
                </h3>
                <p style={{ fontSize: '12px', color: '#94A3B8', marginTop: '2px' }}>
                  Select teacher-verified snippets to ground the conceptual explanation and practice items.
                </p>
              </div>

              {(!plan || plan.status === 'draft') && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <select
                    value={genMode}
                    onChange={(e) => setGenMode(e.target.value as any)}
                    style={{
                      backgroundColor: '#151B3A',
                      border: '1px solid #27325E',
                      color: '#F6F3EC',
                      fontSize: '12px',
                      padding: '6px 10px',
                      borderRadius: '6px',
                      outline: 'none',
                    }}
                  >
                    <option value="auto">Auto (Gemini AI with Fallback)</option>
                    <option value="template">Deterministic Curriculum Template</option>
                  </select>

                  <button
                    onClick={handleGenerate}
                    disabled={isGenerating || selectedSnippetIds.length === 0}
                    style={{
                      backgroundColor: '#7C5CFF',
                      color: '#FFFFFF',
                      border: 'none',
                      borderRadius: '6px',
                      padding: '8px 16px',
                      fontSize: '13px',
                      fontWeight: 700,
                      cursor: isGenerating ? 'not-allowed' : 'pointer',
                      boxShadow: '0 2px 8px rgba(124, 92, 255, 0.4)',
                    }}
                  >
                    {isGenerating ? 'Generating Grounded Draft...' : 'Generate Intervention Draft'}
                  </button>
                </div>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginTop: '12px' }}>
              {snippets.map((snip) => {
                const isChecked = selectedSnippetIds.includes(snip.id);
                return (
                  <div
                    key={snip.id}
                    onClick={() => {
                      if (!plan || plan.status === 'draft') {
                        if (isChecked) {
                          setSelectedSnippetIds(selectedSnippetIds.filter((id) => id !== snip.id));
                        } else {
                          setSelectedSnippetIds([...selectedSnippetIds, snip.id]);
                        }
                      }
                    }}
                    style={{
                      border: isChecked ? '1px solid #7C5CFF' : '1px solid #27325E',
                      backgroundColor: isChecked ? 'rgba(124, 92, 255, 0.08)' : '#151B3A',
                      padding: '12px 14px',
                      borderRadius: '8px',
                      cursor: (!plan || plan.status === 'draft') ? 'pointer' : 'default',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <input
                        type="checkbox"
                        checked={isChecked}
                        disabled={Boolean(plan && plan.status !== 'draft')}
                        onChange={() => {}}
                        style={{ accentColor: '#7C5CFF' }}
                      />
                      <strong style={{ fontSize: '13px', color: '#F6F3EC' }}>{snip.title}</strong>
                    </div>
                    <p style={{ fontSize: '12px', color: '#94A3B8', marginTop: '6px', lineHeight: '1.4' }}>
                      {snip.content}
                    </p>
                    <div style={{ fontSize: '11px', color: '#22D3EE', marginTop: '6px' }}>
                      Source: {snip.source_ref}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Section 2: Conceptual Explanation Editor */}
          {plan && (
            <>
              <div style={{
                backgroundColor: '#0B1020',
                border: '1px solid #27325E',
                borderRadius: '12px',
                padding: '18px 20px',
                marginBottom: '24px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#F6F3EC' }}>
                    2. Conceptual Explanation
                  </h3>
                  <span style={{ fontSize: '11px', color: '#94A3B8' }}>
                    Revision {plan.revision} · Content Hash: {plan.current_version?.content_hash.slice(0, 12)}...
                  </span>
                </div>
                <p style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '10px' }}>
                  Teacher-reviewed pedagogical guidance tailored to address the identified misconception.
                </p>
                <textarea
                  value={explanation}
                  onChange={(e) => setExplanation(e.target.value)}
                  disabled={plan.status !== 'draft'}
                  rows={4}
                  style={{
                    width: '100%',
                    backgroundColor: '#151B3A',
                    border: '1px solid #27325E',
                    color: '#F6F3EC',
                    padding: '12px',
                    borderRadius: '8px',
                    fontSize: '13px',
                    lineHeight: '1.5',
                    outline: 'none',
                    resize: 'vertical',
                  }}
                />
              </div>

              {/* Section 3: Verified Practice Items */}
              <div style={{
                backgroundColor: '#0B1020',
                border: '1px solid #27325E',
                borderRadius: '12px',
                padding: '18px 20px',
                marginBottom: '24px',
              }}>
                <h3 style={{ fontSize: '15px', fontWeight: 700, color: '#F6F3EC', marginBottom: '4px' }}>
                  3. Deterministically Verified Practice Items (3 Items)
                </h3>
                <p style={{ fontSize: '12px', color: '#94A3B8', marginBottom: '16px' }}>
                  Each item is verified against its structured mathematical specification using exact rational arithmetic.
                </p>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {practiceItems.map((item, idx) => (
                    <div
                      key={item.item_num}
                      style={{
                        backgroundColor: '#151B3A',
                        border: '1px solid #27325E',
                        borderRadius: '8px',
                        padding: '16px',
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{
                            backgroundColor: '#27325E',
                            color: '#F6F3EC',
                            fontSize: '11px',
                            fontWeight: 700,
                            padding: '2px 8px',
                            borderRadius: '4px',
                          }}>
                            Item {item.item_num}
                          </span>
                          <span style={{
                            backgroundColor: 'rgba(52, 211, 153, 0.15)',
                            color: '#34D399',
                            fontSize: '11px',
                            fontWeight: 700,
                            padding: '2px 8px',
                            borderRadius: '4px',
                          }}>
                            ✓ Mathematically Verified
                          </span>
                        </div>
                        <span style={{ color: '#22D3EE', fontSize: '12px' }}>
                          Spec: {item.math_spec.operation.toUpperCase()}({item.math_spec.operands.join(', ')}) → {item.math_spec.answer_format}
                        </span>
                      </div>

                      <div style={{ marginBottom: '10px' }}>
                        <label style={{ fontSize: '11px', color: '#94A3B8', display: 'block', marginBottom: '4px' }}>
                          Question Text:
                        </label>
                        <input
                          type="text"
                          value={item.question_text}
                          disabled={plan.status !== 'draft'}
                          onChange={(e) => {
                            const updated = [...practiceItems];
                            updated[idx] = { ...updated[idx], question_text: e.target.value };
                            setPracticeItems(updated);
                          }}
                          style={{
                            width: '100%',
                            backgroundColor: '#0B1020',
                            border: '1px solid #27325E',
                            color: '#F6F3EC',
                            padding: '8px 12px',
                            borderRadius: '6px',
                            fontSize: '13px',
                            outline: 'none',
                          }}
                        />
                      </div>

                      <div style={{ display: 'grid', gridTemplateColumns: '150px 1fr', gap: '12px' }}>
                        <div>
                          <label style={{ fontSize: '11px', color: '#94A3B8', display: 'block', marginBottom: '4px' }}>
                            Expected Answer:
                          </label>
                          <input
                            type="text"
                            value={item.expected_answer}
                            disabled={plan.status !== 'draft'}
                            onChange={(e) => {
                              const updated = [...practiceItems];
                              updated[idx] = { ...updated[idx], expected_answer: e.target.value };
                              setPracticeItems(updated);
                            }}
                            style={{
                              width: '100%',
                              backgroundColor: '#0B1020',
                              border: '1px solid #27325E',
                              color: '#34D399',
                              fontWeight: 700,
                              padding: '8px 12px',
                              borderRadius: '6px',
                              fontSize: '13px',
                              outline: 'none',
                            }}
                          />
                        </div>

                        <div>
                          <label style={{ fontSize: '11px', color: '#94A3B8', display: 'block', marginBottom: '4px' }}>
                            Pedagogical Rationale:
                          </label>
                          <input
                            type="text"
                            value={item.rationale}
                            disabled={plan.status !== 'draft'}
                            onChange={(e) => {
                              const updated = [...practiceItems];
                              updated[idx] = { ...updated[idx], rationale: e.target.value };
                              setPracticeItems(updated);
                            }}
                            style={{
                              width: '100%',
                              backgroundColor: '#0B1020',
                              border: '1px solid #27325E',
                              color: '#F6F3EC',
                              padding: '8px 12px',
                              borderRadius: '6px',
                              fontSize: '13px',
                              outline: 'none',
                            }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Section 4: Actions, Approval & Phase 5 Lifecycle */}
              <div style={{
                backgroundColor: '#0B1020',
                border: '1px solid #27325E',
                borderRadius: '12px',
                padding: '20px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
              }}>
                <div>
                  {plan.status === 'draft' ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <input
                        type="checkbox"
                        id="signoff-check"
                        checked={signOffChecked}
                        onChange={(e) => setSignOffChecked(e.target.checked)}
                        style={{ accentColor: '#34D399', width: '16px', height: '16px' }}
                      />
                      <label htmlFor="signoff-check" style={{ fontSize: '12px', color: '#F6F3EC', cursor: 'pointer' }}>
                        I verify instructional alignment and take responsibility for this intervention content.
                      </label>
                    </div>
                  ) : plan.status === 'reviewed' ? (
                    <div>
                      <span style={{ color: '#34D399', fontSize: '13px', fontWeight: 700, display: 'block' }}>
                        ✓ Version {plan.current_version?.version_num} Approved & Frozen
                      </span>
                      <span style={{ color: '#94A3B8', fontSize: '12px' }}>
                        Ready to distribute to the {group.members.length} enrolled learners.
                      </span>
                    </div>
                  ) : plan.status === 'assigned' ? (
                    <div>
                      <span style={{ color: '#22D3EE', fontSize: '13px', fontWeight: 700, display: 'block' }}>
                        ● Active Assignment in Progress
                      </span>
                      <span style={{ color: '#94A3B8', fontSize: '12px' }}>
                        Learners can now complete their fresh diagnostic reassessment quiz.
                      </span>
                    </div>
                  ) : plan.status === 'reassessed' ? (
                    <div>
                      <span style={{ color: '#34D399', fontSize: '13px', fontWeight: 700, display: 'block' }}>
                        ✓ Fresh Reassessment Submitted
                      </span>
                      <span style={{ color: '#94A3B8', fontSize: '12px' }}>
                        All learners have completed the quiz. Ready for teacher progress review.
                      </span>
                    </div>
                  ) : (
                    <div>
                      <span style={{ color: '#34D399', fontSize: '13px', fontWeight: 700, display: 'block' }}>
                        ✓ Intervention Closed (Mastery Achieved)
                      </span>
                      <span style={{ color: '#94A3B8', fontSize: '12px' }}>
                        Historical evidence snapshot preserved.
                      </span>
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  {plan.status === 'draft' && (
                    <>
                      <button
                        onClick={handleSaveDraft}
                        disabled={isSaving}
                        style={{
                          backgroundColor: '#27325E',
                          color: '#F6F3EC',
                          border: 'none',
                          borderRadius: '6px',
                          padding: '10px 18px',
                          fontSize: '13px',
                          fontWeight: 600,
                          cursor: isSaving ? 'not-allowed' : 'pointer',
                        }}
                      >
                        {isSaving ? 'Saving...' : 'Save Draft Edits'}
                      </button>

                      <button
                        onClick={handleApprove}
                        disabled={isApproving || !signOffChecked}
                        style={{
                          backgroundColor: signOffChecked ? '#34D399' : '#334155',
                          color: signOffChecked ? '#0B1020' : '#64748B',
                          border: 'none',
                          borderRadius: '6px',
                          padding: '10px 20px',
                          fontSize: '13px',
                          fontWeight: 700,
                          cursor: signOffChecked ? 'pointer' : 'not-allowed',
                          boxShadow: signOffChecked ? '0 4px 14px rgba(52, 211, 153, 0.4)' : 'none',
                        }}
                      >
                        {isApproving ? 'Freezing Version...' : 'Approve & Freeze Version'}
                      </button>
                    </>
                  )}

                  {plan.status === 'reviewed' && (
                    <button
                      onClick={() => setIsAssignModalOpen(true)}
                      style={{
                        backgroundColor: '#7C5CFF',
                        color: '#FFFFFF',
                        border: 'none',
                        borderRadius: '6px',
                        padding: '10px 22px',
                        fontSize: '13px',
                        fontWeight: 700,
                        cursor: 'pointer',
                        boxShadow: '0 4px 14px rgba(124, 92, 255, 0.4)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                      }}
                    >
                      <span>→</span> Distribute Assignment to Cohort
                    </button>
                  )}

                  {(plan.status === 'assigned' || plan.status === 'reassessed') && (
                    <div style={{ display: 'flex', gap: '10px' }}>
                      {assignment && (
                        <button
                          onClick={() => setIsQuizModalOpen(true)}
                          style={{
                            backgroundColor: '#22D3EE',
                            color: '#0B1020',
                            border: 'none',
                            borderRadius: '6px',
                            padding: '10px 18px',
                            fontSize: '13px',
                            fontWeight: 800,
                            cursor: 'pointer',
                            boxShadow: '0 4px 14px rgba(34, 211, 238, 0.4)',
                          }}
                        >
                          Simulate Reassessment Quiz ✍
                        </button>
                      )}

                      <button
                        onClick={() => setIsProgressModalOpen(true)}
                        style={{
                          backgroundColor: '#34D399',
                          color: '#0B1020',
                          border: 'none',
                          borderRadius: '6px',
                          padding: '10px 20px',
                          fontSize: '13px',
                          fontWeight: 800,
                          cursor: 'pointer',
                          boxShadow: '0 4px 14px rgba(52, 211, 153, 0.4)',
                        }}
                      >
                        Review Progress & Close 📊
                      </button>
                    </div>
                  )}

                  {plan.status === 'closed' && (
                    <button
                      onClick={() => setIsProgressModalOpen(true)}
                      style={{
                        backgroundColor: '#34D399',
                        color: '#0B1020',
                        border: 'none',
                        borderRadius: '6px',
                        padding: '10px 20px',
                        fontSize: '13px',
                        fontWeight: 800,
                        cursor: 'pointer',
                      }}
                    >
                      View Final Closed Trajectory 📊
                    </button>
                  )}
                </div>
              </div>
            </>
          )}
        </div>

        {/* Phase 5 Sub-Modals */}
        {isAssignModalOpen && plan && group && (
          <AssignmentModal
            isOpen={isAssignModalOpen}
            onClose={() => setIsAssignModalOpen(false)}
            group={group}
            plan={plan}
            onAssigned={handleAssignmentCompleted}
          />
        )}

        {isQuizModalOpen && assignment && (
          <ReassessmentQuizModal
            isOpen={isQuizModalOpen}
            onClose={() => setIsQuizModalOpen(false)}
            assignment={assignment}
            onQuizSubmitted={handleAssignmentCompleted}
          />
        )}

        {isProgressModalOpen && plan && group && (
          <ProgressReviewModal
            isOpen={isProgressModalOpen}
            onClose={() => setIsProgressModalOpen(false)}
            group={group}
            plan={plan}
            onPlanClosed={handleAssignmentCompleted}
          />
        )}
      </div>
    </div>
  );
};
