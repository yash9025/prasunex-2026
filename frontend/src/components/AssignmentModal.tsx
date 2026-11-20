import React, { useState } from 'react';
import { api } from '../services/api';
import { SupportGroup, SupportPlan } from '../types';
import { useModalA11y } from '../hooks/useModalA11y';

interface AssignmentModalProps {
  isOpen: boolean;
  onClose: () => void;
  group: SupportGroup;
  plan: SupportPlan;
  onAssigned: () => void;
}

export const AssignmentModal: React.FC<AssignmentModalProps> = ({
  isOpen,
  onClose,
  group,
  plan,
  onAssigned,
}) => {
  const containerRef = useModalA11y({
    isOpen,
    onClose,
    closeOnEscape: true,
  });

  const [dueDate, setDueDate] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const currentVer = plan.current_version;

  const handleAssign = async () => {
    if (!currentVer) {
      setErrorMsg('No current version found for this plan.');
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMsg(null);
      await api.createAssignment(plan.id, currentVer.id, dueDate || undefined);
      onAssigned();
      onClose();
    } catch (e: any) {
      setErrorMsg(e.message || 'Failed to distribute assignment');
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
        aria-labelledby="assignment-modal-title"
        style={{
          backgroundColor: '#151B3A',
          border: '1px solid #27325E',
          borderRadius: '16px',
          width: '560px',
          maxWidth: '94vw',
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
            <span style={{
              backgroundColor: '#7C5CFF',
              color: '#FFFFFF',
              fontSize: '10px',
              fontWeight: 700,
              padding: '2px 8px',
              borderRadius: '4px',
              textTransform: 'uppercase',
            }}>
              Intervention Assignment
            </span>
            <h3 id="assignment-modal-title" style={{ fontSize: '18px', fontWeight: 700, color: '#F6F3EC', marginTop: '4px' }}>
              Assign Intervention to Cohort
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
        <div style={{ padding: '24px' }}>
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

          <div style={{
            backgroundColor: '#0B1020',
            border: '1px solid #27325E',
            borderRadius: '10px',
            padding: '16px',
            marginBottom: '18px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '12px', color: '#94A3B8' }}>Target Group:</span>
              <strong style={{ fontSize: '12px', color: '#F6F3EC' }}>{group.name}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '12px', color: '#94A3B8' }}>Curriculum Topic:</span>
              <strong style={{ fontSize: '12px', color: '#22D3EE' }}>{group.topic_name} ({group.topic_code})</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '12px', color: '#94A3B8' }}>Approved Plan Version:</span>
              <strong style={{ fontSize: '12px', color: '#34D399' }}>Version {currentVer?.version_num || 1} (Frozen)</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '12px', color: '#94A3B8' }}>Designated Recipients:</span>
              <strong style={{ fontSize: '12px', color: '#FFB547' }}>{group.members.length} Enrolled Learners</strong>
            </div>
          </div>

          <div style={{ marginBottom: '18px' }}>
            <label style={{ fontSize: '12px', color: '#94A3B8', display: 'block', marginBottom: '6px' }}>
              Optional Completion Due Date:
            </label>
            <input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
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

          <div style={{
            fontSize: '12px',
            color: '#94A3B8',
            lineHeight: '1.4',
            backgroundColor: 'rgba(124, 92, 255, 0.08)',
            padding: '12px',
            borderRadius: '6px',
            border: '1px solid #7C5CFF',
          }}>
            <strong>Traceability Note:</strong> Distributing this intervention freezes Version {currentVer?.version_num}. Any subsequent edits by teachers will create a new draft version, ensuring current learners complete the exact approved content version.
          </div>
        </div>

        {/* Footer */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid #27325E',
          display: 'flex',
          justifyContent: 'flex-end',
          gap: '12px',
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
            Cancel
          </button>
          <button
            onClick={handleAssign}
            disabled={isSubmitting}
            style={{
              backgroundColor: '#7C5CFF',
              color: '#FFFFFF',
              border: 'none',
              padding: '8px 20px',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: 700,
              cursor: isSubmitting ? 'not-allowed' : 'pointer',
              boxShadow: '0 2px 10px rgba(124, 92, 255, 0.4)',
            }}
          >
            {isSubmitting ? 'Distributing...' : 'Confirm & Distribute Assignment'}
          </button>
        </div>
      </div>
    </div>
  );
};
