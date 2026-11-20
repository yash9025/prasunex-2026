import React, { useEffect, useState } from 'react';
import { api } from './services/api';
import { Classroom, ClassroomDetail, UserMe } from './types';
import { SyntheticNoticeBanner } from './components/SyntheticNoticeBanner';
import { Navbar } from './components/Navbar';
import { TeacherWorkspace } from './components/TeacherWorkspace';
import { AuditViewModal } from './components/AuditViewModal';

export const App: React.FC = () => {
  const [user, setUser] = useState<UserMe | null>(null);
  const [classroom, setClassroom] = useState<Classroom | null>(null);
  const [detail, setDetail] = useState<ClassroomDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [systemHealthy, setSystemHealthy] = useState<boolean>(false);
  const [isAuditModalOpen, setIsAuditModalOpen] = useState<boolean>(false);
  const [isResettingDemo, setIsResettingDemo] = useState<boolean>(false);
  const [loginEmail, setLoginEmail] = useState<string>('priya.sharma@demo.learningbridge.internal');
  const [loginPassword, setLoginPassword] = useState<string>('TeacherPass123!');
  const [authError, setAuthError] = useState<string | null>(null);

  const initData = async () => {
    setIsLoading(true);
    try {
      // 1. Health check
      try {
        const health = await api.checkHealth();
        setSystemHealthy(health.status === 'ready');
      } catch (e) {
        setSystemHealthy(false);
      }

      // 2. Fetch authenticated profile
      if (api.getToken()) {
        const me = await api.getMe();
        setUser(me);

        // Fetch assigned classes
        const classes = await api.getClasses();
        if (classes.length > 0) {
          setClassroom(classes[0]);
          const classDetail = await api.getClassDetail(classes[0].id);
          setDetail(classDetail);
        }
      }
    } catch (err: any) {
      console.error('Initialization error:', err);
      api.clearToken();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    initData();
  }, []);

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setAuthError(null);
    setIsLoading(true);
    try {
      await api.login(loginEmail, loginPassword);
      await initData();
    } catch (err: any) {
      setAuthError(err.message || 'Login failed');
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    api.clearToken();
    setUser(null);
    setClassroom(null);
    setDetail(null);
  };

  const handleResetDemo = async (preload: boolean) => {
    setIsResettingDemo(true);
    try {
      await api.resetDemoTenant(preload);
      await initData();
    } catch (err: any) {
      console.error('Demo reset error:', err);
      alert(err.message || 'Failed to reset demo environment');
    } finally {
      setIsResettingDemo(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <SyntheticNoticeBanner
        onResetDemo={user ? handleResetDemo : undefined}
        isResetting={isResettingDemo}
      />
      <Navbar
        user={user}
        onLogout={handleLogout}
        systemHealthy={systemHealthy}
        onOpenAudit={() => setIsAuditModalOpen(true)}
      />

      <AuditViewModal
        isOpen={isAuditModalOpen}
        onClose={() => setIsAuditModalOpen(false)}
        schoolName={user?.active_school_name || 'Oakridge International'}
      />

      <main style={{ flex: 1 }}>
        {!user ? (
          <div style={{
            maxWidth: '440px',
            margin: '80px auto',
            backgroundColor: '#151B3A',
            borderRadius: '12px',
            border: '1px solid #27325E',
            padding: '36px',
            boxShadow: '0 20px 40px rgba(0,0,0,0.5)',
          }}>
            <div style={{ textAlign: 'center', marginBottom: '28px' }}>
              <div style={{
                width: '44px',
                height: '44px',
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #7C5CFF, #22D3EE)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: 800,
                color: '#0B1020',
                fontSize: '20px',
                marginBottom: '12px',
              }}>
                LB
              </div>
              <h2 style={{ fontSize: '20px', fontWeight: 700, color: '#F6F3EC' }}>
                Sign in to LearningBridge
              </h2>
              <p style={{ fontSize: '13px', color: '#94A3B8', marginTop: '4px' }}>
                Round 3 Prototype · Teacher Evidence Workspace
              </p>
            </div>

            {authError && (
              <div style={{
                backgroundColor: 'rgba(255, 107, 107, 0.15)',
                border: '1px solid #FF6B6B',
                color: '#FF6B6B',
                padding: '10px 14px',
                borderRadius: '6px',
                fontSize: '13px',
                marginBottom: '20px',
              }}>
                {authError}
              </div>
            )}

            <form onSubmit={handleLogin}>
              <div style={{ marginBottom: '18px' }}>
                <label style={{ display: 'block', fontSize: '12px', color: '#94A3B8', marginBottom: '6px', fontWeight: 600 }}>
                  Teacher Email
                </label>
                <input
                  type="email"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  required
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

              <div style={{ marginBottom: '24px' }}>
                <label style={{ display: 'block', fontSize: '12px', color: '#94A3B8', marginBottom: '6px', fontWeight: 600 }}>
                  Password
                </label>
                <input
                  type="password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  required
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

              <button
                type="submit"
                style={{
                  width: '100%',
                  backgroundColor: '#7C5CFF',
                  color: '#FFFFFF',
                  fontWeight: 700,
                  fontSize: '14px',
                  padding: '12px',
                  borderRadius: '6px',
                  border: 'none',
                  marginBottom: '14px',
                  transition: 'background-color 0.15s ease',
                }}
              >
                Sign in with Credentials
              </button>

              <button
                type="button"
                onClick={() => {
                  setLoginEmail('priya.sharma@demo.learningbridge.internal');
                  setLoginPassword('TeacherPass123!');
                  handleLogin();
                }}
                style={{
                  width: '100%',
                  backgroundColor: 'transparent',
                  border: '1px solid #22D3EE',
                  color: '#22D3EE',
                  fontWeight: 600,
                  fontSize: '13px',
                  padding: '10px',
                  borderRadius: '6px',
                }}
              >
                1-Click Demo Login (Oakridge Teacher Priya)
              </button>
            </form>
          </div>
        ) : (
          <TeacherWorkspace classroom={classroom} detail={detail} isLoading={isLoading} />
        )}
      </main>

      <footer style={{
        backgroundColor: '#0B1020',
        borderTop: '1px solid #1E2752',
        padding: '16px 28px',
        textAlign: 'center',
        fontSize: '12px',
        color: '#64748B',
      }}>
        LearningBridge Prototype · PRASUNEX INNOVATHON 2026 · Google Senior Developer Clean Architecture
      </footer>
    </div>
  );
};
