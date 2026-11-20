import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { AuditEvent, SystemHealth } from '../types';
import { useModalA11y } from '../hooks/useModalA11y';

interface AuditViewModalProps {
  isOpen: boolean;
  onClose: () => void;
  schoolName: string;
}

export const AuditViewModal: React.FC<AuditViewModalProps> = ({
  isOpen,
  onClose,
  schoolName,
}) => {
  const containerRef = useModalA11y({
    isOpen,
    onClose,
    closeOnEscape: true,
  });

  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [filterAction, setFilterAction] = useState<string>('ALL');

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [auditPage, healthData] = await Promise.all([
        api.getAuditEvents(50, 0),
        api.getSystemDiagnostics(),
      ]);
      setEvents(auditPage.events);
      setHealth(healthData);
    } catch (err) {
      console.error('Failed to load audit and diagnostic data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const filteredEvents = filterAction === 'ALL'
    ? events
    : events.filter(e => e.action.toLowerCase().includes(filterAction.toLowerCase()));

  return (
    <div
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(11, 16, 32, 0.85)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '24px',
      }}
    >
      <div
        ref={containerRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="audit-modal-title"
        style={{
          backgroundColor: '#151B3A',
          border: '1px solid #2D3766',
          borderRadius: '14px',
          width: '100%',
          maxWidth: '1050px',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6)',
          overflow: 'hidden',
          color: '#F8FAFC',
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: '20px 28px',
            borderBottom: '1px solid #2D3766',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            backgroundColor: '#0F152E',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '1.25rem' }}>🛡️</span>
              <h2 id="audit-modal-title" style={{ margin: 0, fontSize: '1.2rem', fontWeight: 600 }}>
                Audit Trail & Operational Visibility
              </h2>
              <span
                style={{
                  backgroundColor: 'rgba(34, 211, 238, 0.15)',
                  color: '#22D3EE',
                  padding: '2px 10px',
                  borderRadius: '12px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                }}
              >
                {schoolName}
              </span>
            </div>
            <p style={{ margin: '4px 0 0 0', color: '#94A3B8', fontSize: '0.82rem' }}>
              Append-only audit log scoped strictly to your school tenancy (Section 13.3)
            </p>
          </div>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <button
              onClick={loadData}
              disabled={isLoading}
              style={{
                backgroundColor: 'rgba(255, 255, 255, 0.06)',
                border: '1px solid #334155',
                color: '#CBD5E1',
                padding: '6px 12px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '0.8rem',
              }}
            >
              {isLoading ? 'Refreshing...' : '↻ Refresh'}
            </button>
            <button
              onClick={onClose}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#94A3B8',
                fontSize: '1.3rem',
                cursor: 'pointer',
                padding: '4px 8px',
              }}
            >
              ✕
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div style={{ padding: '24px 28px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* System Diagnostics Strip */}
          {health && (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: '12px',
              }}
            >
              <div
                style={{
                  backgroundColor: '#0F152E',
                  border: '1px solid #2D3766',
                  borderRadius: '10px',
                  padding: '14px',
                }}
              >
                <div style={{ color: '#94A3B8', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Database Engine
                </div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '4px' }}>
                  <span style={{ color: '#34D399', fontWeight: 600, fontSize: '1rem' }}>
                    ● {health.database.status}
                  </span>
                  <span style={{ color: '#64748B', fontSize: '0.8rem' }}>
                    ({health.database.ping_latency_ms} ms ping)
                  </span>
                </div>
              </div>

              <div
                style={{
                  backgroundColor: '#0F152E',
                  border: '1px solid #2D3766',
                  borderRadius: '10px',
                  padding: '14px',
                }}
              >
                <div style={{ color: '#94A3B8', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Job Queue State
                </div>
                <div style={{ display: 'flex', gap: '10px', marginTop: '4px', fontSize: '0.82rem' }}>
                  <span style={{ color: '#34D399' }}>✓ {health.job_queue.succeeded} succ</span>
                  <span style={{ color: '#22D3EE' }}>⚙ {health.job_queue.running} run</span>
                  <span style={{ color: '#FFB547' }}>⏳ {health.job_queue.queued} queue</span>
                  {health.job_queue.failed > 0 && (
                    <span style={{ color: '#FF6B6B' }}>✕ {health.job_queue.failed} fail</span>
                  )}
                </div>
              </div>

              <div
                style={{
                  backgroundColor: '#0F152E',
                  border: '1px solid #2D3766',
                  borderRadius: '10px',
                  padding: '14px',
                }}
              >
                <div style={{ color: '#94A3B8', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Transactional Outbox
                </div>
                <div style={{ display: 'flex', gap: '12px', marginTop: '4px', fontSize: '0.82rem' }}>
                  <span style={{ color: '#34D399' }}>✓ {health.outbox.dispatched} dispatched</span>
                  <span style={{ color: '#94A3B8' }}>• {health.outbox.pending} pending</span>
                </div>
              </div>

              <div
                style={{
                  backgroundColor: '#0F152E',
                  border: '1px solid #2D3766',
                  borderRadius: '10px',
                  padding: '14px',
                }}
              >
                <div style={{ color: '#94A3B8', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  Tenant Boundary
                </div>
                <div style={{ marginTop: '4px', fontSize: '0.82rem', color: '#22D3EE', fontWeight: 600 }}>
                  Isolated (RLS Active)
                </div>
              </div>
            </div>
          )}

          {/* Action Filter */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontSize: '0.88rem', fontWeight: 600, color: '#E2E8F0' }}>
              Recent Audit Events ({filteredEvents.length})
            </div>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <span style={{ fontSize: '0.78rem', color: '#94A3B8' }}>Filter:</span>
              {['ALL', 'decision', 'plan', 'assign', 'quiz', 'import'].map((f) => (
                <button
                  key={f}
                  onClick={() => setFilterAction(f)}
                  style={{
                    backgroundColor: filterAction === f ? '#7C5CFF' : '#1E293B',
                    color: filterAction === f ? '#FFFFFF' : '#94A3B8',
                    border: '1px solid #334155',
                    borderRadius: '4px',
                    padding: '3px 8px',
                    fontSize: '0.75rem',
                    cursor: 'pointer',
                    textTransform: 'uppercase',
                  }}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          {/* Audit Events Table */}
          <div
            style={{
              border: '1px solid #2D3766',
              borderRadius: '8px',
              overflow: 'hidden',
              backgroundColor: '#0B1020',
            }}
          >
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
              <thead>
                <tr style={{ backgroundColor: '#151B3A', borderBottom: '1px solid #2D3766', color: '#94A3B8' }}>
                  <th style={{ padding: '10px 14px' }}>Timestamp (UTC)</th>
                  <th style={{ padding: '10px 14px' }}>Actor</th>
                  <th style={{ padding: '10px 14px' }}>Action</th>
                  <th style={{ padding: '10px 14px' }}>Entity</th>
                  <th style={{ padding: '10px 14px' }}>Entity ID</th>
                  <th style={{ padding: '10px 14px' }}>Trace ID</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvents.length === 0 ? (
                  <tr>
                    <td colSpan={6} style={{ padding: '30px', textAlign: 'center', color: '#64748B' }}>
                      {isLoading ? 'Loading events...' : 'No audit events recorded yet for this session.'}
                    </td>
                  </tr>
                ) : (
                  filteredEvents.map((evt) => {
                    const actionBadgeColor = evt.action.includes('confirm') || evt.action.includes('approved')
                      ? '#34D399'
                      : evt.action.includes('dismiss')
                      ? '#FF6B6B'
                      : evt.action.includes('assigned')
                      ? '#22D3EE'
                      : '#FFB547';

                    return (
                      <tr
                        key={evt.id}
                        style={{
                          borderBottom: '1px solid #1E293B',
                          transition: 'background-color 0.15s ease',
                        }}
                      >
                        <td style={{ padding: '10px 14px', color: '#94A3B8', fontFamily: 'monospace' }}>
                          {evt.created_at ? evt.created_at.replace('T', ' ').slice(0, 19) : '—'}
                        </td>
                        <td style={{ padding: '10px 14px', color: '#E2E8F0', fontWeight: 500 }}>
                          {evt.actor_name || evt.actor_id || 'System'}
                        </td>
                        <td style={{ padding: '10px 14px' }}>
                          <span
                            style={{
                              backgroundColor: `${actionBadgeColor}15`,
                              color: actionBadgeColor,
                              border: `1px solid ${actionBadgeColor}40`,
                              padding: '2px 8px',
                              borderRadius: '4px',
                              fontSize: '0.72rem',
                              fontWeight: 600,
                              fontFamily: 'monospace',
                            }}
                          >
                            {evt.action}
                          </span>
                        </td>
                        <td style={{ padding: '10px 14px', color: '#CBD5E1' }}>
                          {evt.entity_type}
                        </td>
                        <td style={{ padding: '10px 14px', color: '#94A3B8', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                          {evt.entity_id.slice(0, 16)}...
                        </td>
                        <td style={{ padding: '10px 14px', color: '#64748B', fontFamily: 'monospace', fontSize: '0.72rem' }}>
                          {evt.request_id ? `${evt.request_id.slice(0, 8)}...` : '—'}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '16px 28px',
            borderTop: '1px solid #2D3766',
            backgroundColor: '#0F152E',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ color: '#64748B', fontSize: '0.78rem' }}>
            🔒 All records are stored with tamper-evident actor timestamps and request context correlation.
          </div>
          <button
            onClick={onClose}
            style={{
              backgroundColor: '#334155',
              border: 'none',
              color: '#FFFFFF',
              padding: '8px 18px',
              borderRadius: '6px',
              fontSize: '0.85rem',
              cursor: 'pointer',
              fontWeight: 500,
            }}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
