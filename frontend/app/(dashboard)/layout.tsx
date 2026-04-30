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
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  
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
    const handleOutsideClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('[data-user-menu]')) {
        setUserMenuOpen(false);
      }
    };

    document.addEventListener('click', handleOutsideClick);
    return () => document.removeEventListener('click', handleOutsideClick);
  }, []);

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [pathname]);

  const activeGradient = `linear-gradient(135deg, var(--accent-700), var(--accent-600))`;
  const activeGradientHover = `linear-gradient(135deg, var(--accent-700), var(--accent-600))`;
  const hoverBg = 'var(--surface-2)';
  const inactiveText = 'var(--text-secondary)';
  const cardBg = 'var(--surface-1)';
  const headerText = 'var(--text-primary)';
  const logoutHoverBg = 'color-mix(in srgb, #ef4444 12%, var(--surface-1))';

  const handleLogout = () => {
    authService.logout();
    router.push('/');
  };

  const navigateTo = (path: string) => {
    router.push(path);
    setMobileMenuOpen(false);
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
        <div className="mx-auto max-w-7xl px-3 sm:px-6">
          <div className="flex h-16 items-center justify-between">
            {/* Logo & Brand */}
            <div className="flex items-center gap-2 sm:gap-3">
              <Image src="/logo.PNG" alt="NeuroWell Logo" width={40} height={40} />
              <span style={{ fontSize: '1.1rem', fontWeight: 'bold', color: 'var(--text-primary)' }} className="sm:text-2xl">
                NeuroWell
              </span>
            </div>

            {/* Desktop Menu */}
            <div className="hidden md:flex" style={{ alignItems: 'center', gap: '0.5rem' }}>
              <button
                onClick={() => navigateTo('/dashboard')}
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
              >
                📊 Dashboard
              </button>
              <button
                onClick={() => navigateTo('/chat')}
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
              >
                💬 Chat
              </button>
              <button
                onClick={() => navigateTo('/assessment')}
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
              >
                📝 Assessment
              </button>
              <button
                onClick={() => navigateTo('/games')}
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
              >
                🎮 Games
              </button>
              
              {/* Admin Panel - Only show for admin user */}
              {user?.username === 'admin' && (
                <button
                  onClick={() => navigateTo('/admin')}
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
                >
                  👑 Admin
                </button>
              )}
            </div>

            <button
              type="button"
              onClick={() => setMobileMenuOpen((prev) => !prev)}
              className="md:hidden rounded-lg border px-3 py-2 text-sm font-semibold"
              style={{ borderColor: 'var(--surface-border)', color: 'var(--text-primary)', background: cardBg }}
            >
              ☰
            </button>

            {/* User Menu */}
            <div className="hidden sm:flex" style={{ alignItems: 'center', gap: '1rem', position: 'relative' }} data-user-menu>
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
                <div style={{ position: 'absolute', top: 'calc(100% + 0.5rem)', right: 0, minWidth: '180px', background: 'var(--surface-1)', border: `1px solid var(--surface-border)`, borderRadius: '0.9rem', boxShadow: '0 20px 35px rgba(0,0,0,0.15)', overflow: 'hidden', zIndex: 60 }}>
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

          {mobileMenuOpen && (
            <div className="md:hidden pb-3">
              <div className="flex flex-col gap-2 rounded-2xl border p-2" style={{ borderColor: 'var(--surface-border)', background: cardBg }}>
                <button
                  type="button"
                  onClick={() => navigateTo('/dashboard')}
                  className="rounded-lg px-3 py-2 text-left text-sm font-semibold"
                  style={{
                    background: activeMenu === 'dashboard' ? activeGradient : 'transparent',
                    color: activeMenu === 'dashboard' ? '#ffffff' : inactiveText,
                  }}
                >
                  📊 Dashboard
                </button>
                <button
                  type="button"
                  onClick={() => navigateTo('/chat')}
                  className="rounded-lg px-3 py-2 text-left text-sm font-semibold"
                  style={{
                    background: activeMenu === 'chat' ? activeGradient : 'transparent',
                    color: activeMenu === 'chat' ? '#ffffff' : inactiveText,
                  }}
                >
                  💬 Chat
                </button>
                <button
                  type="button"
                  onClick={() => navigateTo('/assessment')}
                  className="rounded-lg px-3 py-2 text-left text-sm font-semibold"
                  style={{
                    background: activeMenu === 'assessment' ? activeGradient : 'transparent',
                    color: activeMenu === 'assessment' ? '#ffffff' : inactiveText,
                  }}
                >
                  📝 Assessment
                </button>
                <button
                  type="button"
                  onClick={() => navigateTo('/games')}
                  className="rounded-lg px-3 py-2 text-left text-sm font-semibold"
                  style={{
                    background: activeMenu === 'games' ? activeGradient : 'transparent',
                    color: activeMenu === 'games' ? '#ffffff' : inactiveText,
                  }}
                >
                  🎮 Games
                </button>
                {user?.username === 'admin' && (
                  <button
                    type="button"
                    onClick={() => navigateTo('/admin')}
                    className="rounded-lg px-3 py-2 text-left text-sm font-semibold"
                    style={{
                      background: pathname?.includes('/admin') ? 'linear-gradient(135deg, #dc2626, #ef4444)' : 'transparent',
                      color: pathname?.includes('/admin') ? '#ffffff' : '#dc2626',
                      border: '1px solid #fecaca',
                    }}
                  >
                    👑 Admin
                  </button>
                )}

                <div className="mt-2 border-t pt-2" style={{ borderColor: 'var(--surface-border)' }}>
                  <button
                    type="button"
                    onClick={() => {
                      setMobileMenuOpen(false);
                      router.push('/profile');
                    }}
                    className="w-full rounded-lg px-3 py-2 text-left text-sm"
                    style={{ color: 'var(--text-primary)' }}
                  >
                    Settings
                  </button>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="mt-1 w-full rounded-lg px-3 py-2 text-left text-sm"
                    style={{ color: '#dc2626' }}
                  >
                    Logout
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </nav>

      {/* Main Content */}
      <main>{children}</main>
    </div>
  );
}
