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
  
  const activeMenu = pathname?.includes('/chat') ? 'chat' : pathname?.includes('/assessment') ? 'assessment' : 'dashboard';

  useEffect(() => {
    const checkAuth = async () => {
      if (!authService.isAuthenticated()) {
        router.push('/login');
        return;
      }

      try {
        const userData = await authService.getCurrentUser();
        setUser(userData);
        
        // Redirect to assessment if not completed (except if already on assessment page)
        if (!userData.has_completed_initial_assessment && !pathname?.includes('/assessment')) {
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
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #eef2ff 0%, #faf5ff 100%)' }}>
      {/* Modern Navigation Bar */}
      <nav className="glass-effect" style={{ position: 'sticky', top: 0, zIndex: 50, borderBottom: '1px solid rgba(229, 231, 235, 0.5)' }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', height: '4rem' }}>
            {/* Logo & Brand */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Image src="/logo.png" alt="NeuroWell Logo" width={45} height={45} />
              <span style={{ fontSize: '1.5rem', fontWeight: 'bold', background: 'linear-gradient(135deg, #4f46e5, #7c3aed)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
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
                  background: activeMenu === 'dashboard' ? 'linear-gradient(135deg, #4f46e5, #7c3aed)' : 'transparent',
                  color: activeMenu === 'dashboard' ? 'white' : '#4b5563',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = activeMenu === 'dashboard' ? 'linear-gradient(135deg, #4338ca, #6d28d9)' : '#f3f4f6'}
                onMouseLeave={(e) => e.currentTarget.style.background = activeMenu === 'dashboard' ? 'linear-gradient(135deg, #4f46e5, #7c3aed)' : 'transparent'}
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
                  background: activeMenu === 'chat' ? 'linear-gradient(135deg, #4f46e5, #7c3aed)' : 'transparent',
                  color: activeMenu === 'chat' ? 'white' : '#4b5563',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = activeMenu === 'chat' ? 'linear-gradient(135deg, #4338ca, #6d28d9)' : '#f3f4f6'}
                onMouseLeave={(e) => e.currentTarget.style.background = activeMenu === 'chat' ? 'linear-gradient(135deg, #4f46e5, #7c3aed)' : 'transparent'}
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
                  background: activeMenu === 'assessment' ? 'linear-gradient(135deg, #4f46e5, #7c3aed)' : 'transparent',
                  color: activeMenu === 'assessment' ? 'white' : '#4b5563',
                  border: 'none',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = activeMenu === 'assessment' ? 'linear-gradient(135deg, #4338ca, #6d28d9)' : '#f3f4f6'}
                onMouseLeave={(e) => e.currentTarget.style.background = activeMenu === 'assessment' ? 'linear-gradient(135deg, #4f46e5, #7c3aed)' : 'transparent'}
              >
                📝 Assessment
              </button>
            </div>

            {/* User Menu */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              {user && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem', background: '#f3f4f6', borderRadius: '9999px' }}>
                  <div style={{ width: '2rem', height: '2rem', borderRadius: '50%', background: 'linear-gradient(135deg, #4f46e5, #7c3aed)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 'bold', fontSize: '0.875rem' }}>
                    {user.username?.[0]?.toUpperCase() || 'U'}
                  </div>
                  <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#111827' }}>
                    {user.username}
                  </span>
                </div>
              )}
              <button
                onClick={handleLogout}
                style={{
                  padding: '0.5rem 1.5rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  background: 'white',
                  color: '#dc2626',
                  border: '2px solid #fee2e2',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
                onMouseEnter={(e) => { e.currentTarget.style.background = '#fef2f2'; e.currentTarget.style.borderColor = '#fecaca'; }}
                onMouseLeave={(e) => { e.currentTarget.style.background = 'white'; e.currentTarget.style.borderColor = '#fee2e2'; }}
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main>{children}</main>
    </div>
  );
}
