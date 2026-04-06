'use client';

import { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Image from 'next/image';
import { authService } from '@/lib/auth';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [resolvedAppearance, setResolvedAppearance] = useState<'light' | 'dark'>('light');
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  
  const activeMenu = pathname?.includes('/chat')
    ? 'chat'
    : pathname?.includes('/assessment')
    ? 'assessment'
    : pathname?.includes('/games')
    ? 'games'
    : pathname?.includes('/admin')
    ? 'admin'
    : 'dashboard';

  useEffect(() => {
    const checkAuth = async () => {
      if (!authService.isAuthenticated()) {
        router.push('/login');
        return;
      }

      try {
        const userData = await authService.getCurrentUser();
        setUser(userData);
        
        // Redirect to assessment if not completed, but allow admin and games routes.
        if (
          !userData.has_completed_initial_assessment &&
          !pathname?.includes('/assessment') &&
          !pathname?.includes('/admin') &&
          !pathname?.includes('/games')
        ) {
          router.push('/assessment');
        }
      } catch (err) {
        router.push('/login');
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, [router, pathname]);

  useEffect(() => {
    const syncAppearance = () => {
      if (typeof document === 'undefined') return;
      const current = document.documentElement.dataset.resolvedAppearance;
      setResolvedAppearance(current === 'dark' ? 'dark' : 'light');
    };

    syncAppearance();
    window.addEventListener('neurowell-theme-change', syncAppearance);
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', syncAppearance);
    return () => {
      window.removeEventListener('neurowell-theme-change', syncAppearance);
      window.matchMedia('(prefers-color-scheme: dark)').removeEventListener('change', syncAppearance);
    };
  }, []);

  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('[data-user-menu]')) {
        setUserMenuOpen(false);
      }
    };

    document.addEventListener('click', handleOutsideClick);
    return () => document.removeEventListener('click', handleOutsideClick);
  }, []);

  const isDark = resolvedAppearance === 'dark';
  const activeGradient = `linear-gradient(135deg, var(--accent-700), var(--accent-600))`;
  const activeGradientHover = `linear-gradient(135deg, var(--accent-700), var(--accent-600))`;
  const hoverBg = isDark ? 'rgba(30, 41, 59, 0.9)' : '#f3f4f6';
  const inactiveText = isDark ? '#cbd5e1' : '#4b5563';
  const cardBg = isDark ? 'rgba(15, 23, 42, 0.88)' : 'rgba(255, 255, 255, 0.92)';
  const headerText = 'var(--text-primary)';
  const logoutBg = isDark ? 'rgba(15, 23, 42, 0.92)' : 'white';
  const logoutHoverBg = isDark ? 'rgba(30, 41, 59, 0.98)' : '#fef2f2';
  const logoutBorder = isDark ? 'rgba(248, 113, 113, 0.35)' : '#fee2e2';

  const handleLogout = () => {
    authService.logout();
    router.push('/');
  };

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div style={{ width: '48px', height: '48px', border: '4px solid #e5e7eb', borderTopColor: '#4f46e5', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, var(--app-bg-start) 0%, var(--app-bg-mid) 50%, var(--app-bg-end) 100%)' }}>
      {/* Modern Navigation Bar */}
      <nav className="glass-effect" style={{ position: 'sticky', top: 0, zIndex: 50, borderBottom: `1px solid var(--surface-border)` }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', height: '4rem' }}>
            {/* Logo & Brand */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Image src="/logo.PNG" alt="NeuroWell Logo" width={45} height={45} />
              <span style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--text-primary)' }}>
                NeuroWell
              </span>
            </div>

            {/* Desktop Menu */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <button
                onClick={() => router.push('/dashboard')}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  background: activeMenu === 'dashboard' ? activeGradient : 'transparent',
                  color: activeMenu === 'dashboard' ? 'white' : inactiveText,
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = activeMenu === 'dashboard' ? activeGradientHover : hoverBg}
                onMouseLeave={(e) => e.currentTarget.style.background = activeMenu === 'dashboard' ? activeGradient : 'transparent'}
              >
                📊 Dashboard
              </button>
              <button
                onClick={() => router.push('/chat')}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  background: activeMenu === 'chat' ? activeGradient : 'transparent',
                  color: activeMenu === 'chat' ? 'white' : inactiveText,
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = activeMenu === 'chat' ? activeGradientHover : hoverBg}
                onMouseLeave={(e) => e.currentTarget.style.background = activeMenu === 'chat' ? activeGradient : 'transparent'}
              >
                💬 Chat
              </button>
              <button
                onClick={() => router.push('/assessment')}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  background: activeMenu === 'assessment' ? activeGradient : 'transparent',
                  color: activeMenu === 'assessment' ? 'white' : inactiveText,
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = activeMenu === 'assessment' ? activeGradientHover : hoverBg}
                onMouseLeave={(e) => e.currentTarget.style.background = activeMenu === 'assessment' ? activeGradient : 'transparent'}
              >
                📝 Assessment
              </button>
              <button
                onClick={() => router.push('/games')}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  background: activeMenu === 'games' ? activeGradient : 'transparent',
                  color: activeMenu === 'games' ? 'white' : inactiveText,
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = activeMenu === 'games' ? activeGradientHover : hoverBg}
                onMouseLeave={(e) => e.currentTarget.style.background = activeMenu === 'games' ? activeGradient : 'transparent'}
              >
                🎮 Games
              </button>
              
              {/* Admin Panel - Only show for admin user */}
              {user?.username === 'admin' && (
                <button
                  onClick={() => router.push('/admin')}
                  style={{
                    padding: '0.5rem 1rem',
                    borderRadius: '0.5rem',
                    fontSize: '0.875rem',
                    fontWeight: 600,
                    background: pathname?.includes('/admin') ? 'linear-gradient(135deg, #dc2626, #ef4444)' : 'transparent',
                    color: pathname?.includes('/admin') ? 'white' : '#dc2626',
                    border: '2px solid #fecaca',
                    cursor: 'pointer',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    if (!pathname?.includes('/admin')) {
                      e.currentTarget.style.background = '#fef2f2';
                      e.currentTarget.style.borderColor = '#fca5a5';
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (!pathname?.includes('/admin')) {
                      e.currentTarget.style.background = 'transparent';
                      e.currentTarget.style.borderColor = '#fecaca';
                    }
                  }}
                >
                  👑 Admin
                </button>
              )}
            </div>

            {/* User Menu */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', position: 'relative' }} data-user-menu>
              {user && (
                <button
                  type="button"
                  onClick={() => setUserMenuOpen((prev) => !prev)}
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem', background: cardBg, borderRadius: '9999px', border: `1px solid var(--surface-border)`, cursor: 'pointer' }}
                >
                  <div style={{ width: '2rem', height: '2rem', borderRadius: '50%', background: 'linear-gradient(135deg, var(--accent-600), var(--accent-500))', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold', fontSize: '0.875rem' }}>
                    {user.username?.[0]?.toUpperCase() || 'U'}
                  </div>
                  <span style={{ fontSize: '0.875rem', fontWeight: 600, color: headerText }}>
                    {user.username}
                  </span>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>▾</span>
                </button>
              )}
              {userMenuOpen && (
                <div style={{ position: 'absolute', top: 'calc(100% + 0.5rem)', right: 0, minWidth: '180px', background: cardBg, border: `1px solid var(--surface-border)`, borderRadius: '0.9rem', boxShadow: '0 20px 35px rgba(0,0,0,0.15)', overflow: 'hidden', zIndex: 60 }}>
                  <button
                    type="button"
                    onClick={() => {
                      setUserMenuOpen(false);
                      router.push('/profile');
                    }}
                    style={{ width: '100%', padding: '0.85rem 1rem', textAlign: 'left', background: 'transparent', border: 'none', color: 'var(--text-primary)', cursor: 'pointer' }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = hoverBg; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                  >
                    Settings
                  </button>
                  <button
                    type="button"
                    onClick={handleLogout}
                    style={{ width: '100%', padding: '0.85rem 1rem', textAlign: 'left', background: 'transparent', border: 'none', color: '#dc2626', cursor: 'pointer', borderTop: `1px solid var(--surface-border)` }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = logoutHoverBg; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main>{children}</main>
    </div>
  );
}
