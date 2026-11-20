import React from 'react';
import { UserMe } from '../types';

interface NavbarProps {
  user: UserMe | null;
  onLogout: () => void;
  systemHealthy: boolean;
  onOpenAudit?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ user, onLogout, systemHealthy, onOpenAudit }) => {
  return (
    <header style={{
      backgroundColor: '#151B3A',
      borderBottom: '1px solid #27325E',
      padding: '14px 28px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{
          width: '32px',
          height: '32px',
          borderRadius: '8px',
          background: 'linear-gradient(135deg, #7C5CFF, #22D3EE)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontWeight: 800,
          color: '#0B1020',
          fontSize: '16px',
        }}>
          LB
        </div>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 700, color: '#F6F3EC', letterSpacing: '-0.01em' }}>
            LearningBridge
          </h1>
          <p style={{ fontSize: '11px', color: '#94A3B8' }}>
            Diagnostic Assessment &amp; Traceable Intervention
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* System Health Badge & Audit Trigger */}
        <button
          onClick={onOpenAudit}
          title="Click to view School Audit Trail & System Diagnostics"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: '#0B1020',
            padding: '5px 14px',
            borderRadius: '20px',
            border: '1px solid #27325E',
            fontSize: '12px',
            cursor: onOpenAudit ? 'pointer' : 'default',
            color: '#F8FAFC',
          }}
        >
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: systemHealthy ? '#34D399' : '#FF6B6B',
          }} />
          <span style={{ color: '#94A3B8' }}>System:</span>
          <span style={{ color: systemHealthy ? '#34D399' : '#FF6B6B', fontWeight: 600 }}>
            {systemHealthy ? 'Healthy' : 'Unreachable'}
          </span>
          <span style={{ color: '#22D3EE', marginLeft: '4px', fontSize: '11px' }}>
            🛡️ Audit
          </span>
        </button>

        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            {/* School Context */}
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#F6F3EC' }}>
                {user.active_school_name}
              </div>
              <div style={{ fontSize: '11px', color: '#22D3EE', fontWeight: 500 }}>
                {user.full_name} · <span style={{ textTransform: 'capitalize' }}>{user.role}</span>
              </div>
            </div>

            <button
              onClick={onLogout}
              style={{
                backgroundColor: 'transparent',
                border: '1px solid #27325E',
                color: '#94A3B8',
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '12px',
                transition: 'all 0.15s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.color = '#F6F3EC';
                e.currentTarget.style.borderColor = '#7C5CFF';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.color = '#94A3B8';
                e.currentTarget.style.borderColor = '#27325E';
              }}
            >
              Sign out
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
