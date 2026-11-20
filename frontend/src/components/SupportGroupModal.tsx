import React, { useState } from 'react';
import { api } from '../services/api';
import { GapEvidence, SupportGroup } from '../types';
import { useModalA11y } from '../hooks/useModalA11y';

interface SupportGroupModalProps {
  classroomId: string;
  evidenceList: GapEvidence[];
  onClose: () => void;
  onGroupCreated: (newGroup: SupportGroup) => void;
}

export const SupportGroupModal: React.FC<SupportGroupModalProps> = ({
  classroomId,
  evidenceList,
  onClose,
  onGroupCreated,
}) => {
  const containerRef = useModalA11y({
    isOpen: true,
    onClose,
    closeOnEscape: true,
  });

  // Find topics that have confirmed evidence
  const confirmedEvidence = evidenceList.filter((e) => e.status === 'confirmed');

  // Group confirmed evidence by topic
  const topicsMap: Record<string, { topicId: string; topicCode: string; topicName: string; count: number }> = {};
  for (const ev of confirmedEvidence) {
    if (!topicsMap[ev.topic_id]) {
      topicsMap[ev.topic_id] = {
        topicId: ev.topic_id,
        topicCode: ev.topic_code,
        topicName: ev.topic_name,
        count: 0,
      };
    }
    topicsMap[ev.topic_id].count++;
  }

  const topicOptions = Object.values(topicsMap);
  const initialTopicId = topicOptions.length > 0 ? topicOptions[0].topicId : '';

  const [selectedTopicId, setSelectedTopicId] = useState<string>(initialTopicId);
  const [groupName, setGroupName] = useState('Grade 6 Fractions Common Denominators Support');
  const [selectedLearnerIds, setSelectedLearnerIds] = useState<Set<string>>(() => {
    const matching = confirmedEvidence.filter((e) => e.topic_id === initialTopicId);
    return new Set(matching.map((e) => e.learner_id));
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const eligibleLearners = confirmedEvidence.filter((e) => e.topic_id === selectedTopicId);

  const toggleLearner = (learnerId: string) => {
    const next = new Set(selectedLearnerIds);
    if (next.has(learnerId)) {
      next.delete(learnerId);
    } else {
      next.add(learnerId);
    }
    setSelectedLearnerIds(next);
  };

  const handleTopicChange = (newTopicId: string) => {
    setSelectedTopicId(newTopicId);
    const matching = confirmedEvidence.filter((e) => e.topic_id === newTopicId);
    setSelectedLearnerIds(new Set(matching.map((e) => e.learner_id)));
    const top = topicsMap[newTopicId];
    if (top) {
      setGroupName(`Grade 6 ${top.topicName} Targeted Support Cohort`);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedLearnerIds.size === 0) {
      setErrorMsg('Please select at least one learner with confirmed evidence for this support group.');
      return;
    }

    const members = eligibleLearners
      .filter((e) => selectedLearnerIds.has(e.learner_id))
      .map((e) => ({
        learner_id: e.learner_id,
        gap_evidence_id: e.id,
      }));

    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const created = await api.createSupportGroup(
        classroomId,
        selectedTopicId,
        groupName.trim(),
        members
      );
      onGroupCreated(created);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to create support group.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      onClick={(e) => {
        if (e.target === e.currentTarget && !isSubmitting) onClose();
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
        aria-labelledby="group-modal-title"
        style={{
          backgroundColor: '#151B3A',
          border: '1px solid #27325E',
          borderRadius: '12px',
          width: '100%',
          maxWidth: '580px',
          padding: '28px',
          boxShadow: '0 24px 48px rgba(0, 0, 0, 0.6)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
          <div>
            <h3 id="group-modal-title" style={{ fontSize: '18px', fontWeight: 700, color: '#F6F3EC' }}>
              Form Targeted Support Group
            </h3>
            <p style={{ fontSize: '12px', color: '#94A3B8', marginTop: '2px' }}>
              Group learners with teacher-confirmed needs for focused intervention practice.
            </p>
          </div>
          <button
            onClick={onClose}
            disabled={isSubmitting}
            aria-label="Close dialog"
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94A3B8',
              fontSize: '20px',
              cursor: isSubmitting ? 'not-allowed' : 'pointer',
              padding: '4px 8px',
            }}
          >
            ✕
          </button>
        </div>

        {errorMsg && (
          <div style={{
            backgroundColor: 'rgba(255, 107, 107, 0.15)',
            border: '1px solid #FF6B6B',
            color: '#FF6B6B',
            padding: '10px 14px',
            borderRadius: '6px',
            fontSize: '13px',
            marginBottom: '16px',
          }}>
            {errorMsg}
          </div>
        )}

        {topicOptions.length === 0 ? (
          <div style={{
            padding: '24px',
            textAlign: 'center',
            backgroundColor: '#0B1020',
            border: '1px dashed #27325E',
            borderRadius: '8px',
            color: '#FFB547',
            fontSize: '13px',
          }}>
            <p style={{ fontWeight: 600, marginBottom: '6px' }}>
              No Confirmed Evidence Found
            </p>
            <p style={{ color: '#94A3B8', fontSize: '12px' }}>
              Per Section 10.3, support groups can only be formed from <strong>teacher-confirmed evidence</strong>.
              Please inspect a flagged learner (e.g. Aarav Patel) and click <strong>"Confirm Learning Need"</strong> first.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '12px', color: '#94A3B8', marginBottom: '6px', fontWeight: 600 }}>
                Target Intervention Topic
              </label>
              <select
                value={selectedTopicId}
                onChange={(e) => handleTopicChange(e.target.value)}
                style={{
                  width: '100%',
                  backgroundColor: '#0B1020',
                  border: '1px solid #27325E',
                  color: '#F6F3EC',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  fontSize: '13px',
                  outline: 'none',
                }}
              >
                {topicOptions.map((t) => (
                  <option key={t.topicId} value={t.topicId}>
                    {t.topicName} ({t.topicCode}) — {t.count} confirmed learners
                  </option>
                ))}
              </select>
            </div>

            <div style={{ marginBottom: '18px' }}>
              <label style={{ display: 'block', fontSize: '12px', color: '#94A3B8', marginBottom: '6px', fontWeight: 600 }}>
                Support Group Title
              </label>
              <input
                type="text"
                value={groupName}
                onChange={(e) => setGroupName(e.target.value)}
                required
                style={{
                  width: '100%',
                  backgroundColor: '#0B1020',
                  border: '1px solid #27325E',
                  color: '#F6F3EC',
                  padding: '10px 12px',
                  borderRadius: '6px',
                  fontSize: '13px',
                  outline: 'none',
                }}
              />
            </div>

            <div style={{ marginBottom: '22px' }}>
              <label style={{ display: 'block', fontSize: '12px', color: '#94A3B8', marginBottom: '8px', fontWeight: 600 }}>
                Eligible Confirmed Learners ({eligibleLearners.length})
              </label>
              <div style={{
                backgroundColor: '#0B1020',
                border: '1px solid #27325E',
                borderRadius: '8px',
                padding: '12px',
                maxHeight: '180px',
                overflowY: 'auto',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
              }}>
                {eligibleLearners.map((ev) => {
                  const isChecked = selectedLearnerIds.has(ev.learner_id);
                  return (
                    <div
                      key={ev.id}
                      onClick={() => toggleLearner(ev.learner_id)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '8px 12px',
                        borderRadius: '6px',
                        backgroundColor: isChecked ? 'rgba(124, 92, 255, 0.15)' : 'transparent',
                        border: isChecked ? '1px solid #7C5CFF' : '1px solid transparent',
                        cursor: 'pointer',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <input
                          type="checkbox"
                          checked={isChecked}
                          onChange={() => {}} // Handled by div
                          style={{ accentColor: '#7C5CFF' }}
                        />
                        <span style={{ fontSize: '13px', fontWeight: 600, color: '#F6F3EC' }}>
                          {ev.learner_name}
                        </span>
                        <span style={{ fontFamily: 'Consolas, monospace', fontSize: '12px', color: '#22D3EE' }}>
                          {ev.learner_ref}
                        </span>
                      </div>
                      <span style={{ fontSize: '12px', color: '#FFB547', fontWeight: 600 }}>
                        {ev.awarded_marks}/{ev.possible_marks} ({ev.percentage}%)
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                style={{
                  backgroundColor: 'transparent',
                  border: '1px solid #27325E',
                  color: '#94A3B8',
                  padding: '9px 18px',
                  borderRadius: '6px',
                  fontSize: '13px',
                }}
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={isSubmitting || selectedLearnerIds.size === 0}
                style={{
                  backgroundColor: '#FFB547',
                  color: '#0B1020',
                  fontWeight: 700,
                  fontSize: '13px',
                  padding: '9px 20px',
                  borderRadius: '6px',
                  border: 'none',
                  cursor: isSubmitting ? 'not-allowed' : 'pointer',
                }}
              >
                {isSubmitting ? 'Forming Group...' : `Form Support Group (${selectedLearnerIds.size} Learners)`}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
