import React, { useState } from 'react';

interface SyntheticNoticeBannerProps {
  onResetDemo?: (preload: boolean) => Promise<void>;
  isResetting?: boolean;
}

export const SyntheticNoticeBanner: React.FC<SyntheticNoticeBannerProps> = ({
  onResetDemo,
  isResetting = false,
}) => {
  const [showOptions, setShowOptions] = useState(false);

  return (
    <div style={{
      backgroundColor: 'rgba(255, 181, 71, 0.12)',
      borderBottom: '1px solid rgba(255, 181, 71, 0.35)',
      color: '#FFB547',
      padding: '7px 20px',
      fontSize: '12px',
      fontWeight: 600,
      letterSpacing: '0.03em',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <span style={{
          backgroundColor: '#FFB547',
          color: '#0B1020',
          padding: '2px 7px',
          borderRadius: '4px',
          fontSize: '10px',
          fontWeight: 800,
          textTransform: 'uppercase',
        }}>
          Synthetic Demo
        </span>
        <span>
          ALL STUDENT RECORDS, ASSESSMENTS, AND RESPONSES ARE EXPLICITLY SYNTHETIC (NO REAL PII / FERPA / DPDP SAFE).
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {onResetDemo && (
          <div style={{ position: 'relative' }}>
            <button
              onClick={() => setShowOptions(!showOptions)}
              disabled={isResetting}
              style={{
                backgroundColor: 'rgba(255, 181, 71, 0.2)',
                border: '1px solid #FFB547',
                color: '#FFB547',
                padding: '3px 10px',
                borderRadius: '4px',
                fontSize: '11px',
                fontWeight: 700,
                cursor: isResetting ? 'not-allowed' : 'pointer',
              }}
            >
              {isResetting ? 'Resetting...' : '↺ Reset Demo State'}
            </button>

            {showOptions && !isResetting && (
              <div
                style={{
                  position: 'absolute',
                  right: 0,
                  top: '28px',
                  backgroundColor: '#151B3A',
                  border: '1px solid #27325E',
                  borderRadius: '8px',
                  padding: '8px',
                  zIndex: 2000,
                  boxShadow: '0 8px 16px rgba(0,0,0,0.5)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                  width: '240px',
                }}
              >
                <button
                  onClick={() => {
                    setShowOptions(false);
                    onResetDemo(false);
                  }}
                  style={{
                    backgroundColor: '#1E2752',
                    border: 'none',
                    color: '#F6F3EC',
                    padding: '8px 10px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    textAlign: 'left',
                    cursor: 'pointer',
                  }}
                >
                  <strong>Clean Reset</strong>
                  <div style={{ color: '#94A3B8', fontSize: '10px' }}>Empty classroom ready for CSV upload drill</div>
                </button>

                <button
                  onClick={() => {
                    setShowOptions(false);
                    onResetDemo(true);
                  }}
                  style={{
                    backgroundColor: 'rgba(124, 92, 255, 0.2)',
                    border: '1px solid #7C5CFF',
                    color: '#F6F3EC',
                    padding: '8px 10px',
                    borderRadius: '4px',
                    fontSize: '11px',
                    textAlign: 'left',
                    cursor: 'pointer',
                  }}
                >
                  <strong>Reset & Preload Baseline</strong>
                  <div style={{ color: '#22D3EE', fontSize: '10px' }}>Instant populated learning map (Section 15.1)</div>
                </button>
              </div>
            )}
          </div>
        )}

        <span style={{ color: '#94A3B8', fontWeight: 500, fontSize: '11px' }}>
          PRASUNEX INNOVATHON 2026
        </span>
      </div>
    </div>
  );
};
