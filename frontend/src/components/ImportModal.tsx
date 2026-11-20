import React, { useState } from 'react';
import { api } from '../services/api';
import { JobStatus, RowError } from '../types';
import { useModalA11y } from '../hooks/useModalA11y';

interface ImportModalProps {
  classroomId: string;
  onClose: () => void;
  onImportSuccess: (assessmentId: string) => void;
}

export const ImportModal: React.FC<ImportModalProps> = ({
  classroomId,
  onClose,
  onImportSuccess,
}) => {
  const containerRef = useModalA11y({
    isOpen: true,
    onClose,
    closeOnEscape: true,
  });

  const [title, setTitle] = useState('Class 6 Term 1 Diagnostic Baseline');
  const [file, setFile] = useState<File | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errors, setErrors] = useState<RowError[]>([]);
  const [generalError, setGeneralError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setErrors([]);
      setGeneralError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setGeneralError('Please select a question-level CSV assessment file.');
      return;
    }

    setIsSubmitting(true);
    setStatusMessage('Uploading assessment file and verifying schema...');
    setErrors([]);
    setGeneralError(null);

    try {
      const idempotencyKey = `import-${classroomId}-${Date.now()}`;
      const uploadRes = await api.uploadAssessmentCsv(
        classroomId,
        title,
        file,
        idempotencyKey
      );

      setStatusMessage('Checking rational arithmetic equivalence and evidence rules...');

      // Poll job status until terminal state
      let terminal = false;
      let attempts = 0;
      let job: JobStatus | null = null;

      while (!terminal && attempts < 20) {
        attempts++;
        job = await api.getJobStatus(uploadRes.job_id);

        if (job.status === 'succeeded' || job.status === 'failed') {
          terminal = true;
          break;
        }
        await new Promise((resolve) => setTimeout(resolve, 300));
      }

      if (job && job.status === 'succeeded') {
        setStatusMessage('Assessment successfully imported and scored!');
        setTimeout(() => {
          if (job?.result_summary?.assessment_id) {
            onImportSuccess(job.result_summary.assessment_id);
          }
        }, 600);
      } else if (job && job.status === 'failed') {
        setStatusMessage(null);
        if (job.result_summary?.row_errors && job.result_summary.row_errors.length > 0) {
          setErrors(job.result_summary.row_errors);
        } else {
          setGeneralError(job.failure_message || 'Assessment import failed validation.');
        }
      }
    } catch (err: any) {
      setGeneralError(err.message || 'An error occurred during CSV import.');
      setStatusMessage(null);
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
        aria-labelledby="import-modal-title"
        style={{
          backgroundColor: '#151B3A',
          border: '1px solid #27325E',
          borderRadius: '12px',
          width: '100%',
          maxWidth: '560px',
          padding: '28px',
          boxShadow: '0 24px 48px rgba(0, 0, 0, 0.6)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div>
            <h3 id="import-modal-title" style={{ fontSize: '18px', fontWeight: 700, color: '#F6F3EC' }}>
              Upload Question-Level Diagnostic CSV
            </h3>
            <p style={{ fontSize: '12px', color: '#94A3B8', marginTop: '2px' }}>
              All-or-nothing validation, exact rational arithmetic scoring, and explainable evidence generation.
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

        {generalError && (
          <div style={{
            backgroundColor: 'rgba(255, 107, 107, 0.15)',
            border: '1px solid #FF6B6B',
            color: '#FF6B6B',
            padding: '10px 14px',
            borderRadius: '6px',
            fontSize: '13px',
            marginBottom: '18px',
          }}>
            {generalError}
          </div>
        )}

        {statusMessage && (
          <div style={{
            backgroundColor: 'rgba(34, 211, 238, 0.15)',
            border: '1px solid #22D3EE',
            color: '#22D3EE',
            padding: '10px 14px',
            borderRadius: '6px',
            fontSize: '13px',
            marginBottom: '18px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}>
            <span style={{ display: 'inline-block', width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#22D3EE' }} />
            {statusMessage}
          </div>
        )}

        {errors.length > 0 && (
          <div style={{
            backgroundColor: 'rgba(255, 107, 107, 0.1)',
            border: '1px solid #FF6B6B',
            borderRadius: '8px',
            padding: '14px',
            marginBottom: '18px',
            maxHeight: '180px',
            overflowY: 'auto',
          }}>
            <div style={{ color: '#FF6B6B', fontWeight: 700, fontSize: '13px', marginBottom: '8px' }}>
              All-or-Nothing Import Rejected ({errors.length} validation errors)
            </div>
            {errors.map((err, i) => (
              <div key={i} style={{ fontSize: '12px', color: '#F6F3EC', marginBottom: '4px' }}>
                <strong style={{ color: '#FFB547' }}>Row {err.row_num}</strong>
                {err.column ? ` [${err.column}]` : ''}: {err.message}
              </div>
            ))}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '12px', color: '#94A3B8', marginBottom: '6px', fontWeight: 600 }}>
              Assessment Title
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              disabled={isSubmitting}
              style={{
                width: '100%',
                backgroundColor: '#0B1020',
                border: '1px solid #27325E',
                color: '#F6F3EC',
                padding: '10px 14px',
                borderRadius: '6px',
                fontSize: '13px',
                outline: 'none',
              }}
            />
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '12px', color: '#94A3B8', marginBottom: '6px', fontWeight: 600 }}>
              Question-Level CSV File
            </label>
            <input
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              disabled={isSubmitting}
              style={{
                width: '100%',
                backgroundColor: '#0B1020',
                border: '1px dashed #27325E',
                color: '#F6F3EC',
                padding: '14px',
                borderRadius: '6px',
                fontSize: '13px',
                outline: 'none',
              }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px', fontSize: '11px' }}>
              <span style={{ color: '#64748B' }}>Max size 2MB · UTF-8 encoding</span>
              <a
                href={api.getTemplateDownloadUrl()}
                download
                style={{ color: '#22D3EE', textDecoration: 'none', fontWeight: 600 }}
              >
                Download CSV Template
              </a>
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
              disabled={isSubmitting || !file}
              style={{
                backgroundColor: isSubmitting ? '#4B3F72' : '#7C5CFF',
                color: '#FFFFFF',
                fontWeight: 700,
                fontSize: '13px',
                padding: '9px 20px',
                borderRadius: '6px',
                border: 'none',
                cursor: isSubmitting ? 'not-allowed' : 'pointer',
              }}
            >
              {isSubmitting ? 'Validating & Scoring...' : 'Upload & Score Assessment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
