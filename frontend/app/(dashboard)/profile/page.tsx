'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { authService } from '@/lib/auth';
import api from '@/lib/api';

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<any>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [appearance, setAppearance] = useState('system');
  const [accentColor, setAccentColor] = useState('blue');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const [formData, setFormData] = useState({
    full_name: '',
    age: '',
    guardian_contact: '',
    guardian_email: '',
  });

  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  useEffect(() => {
    loadUser();
    const storedAppearance = localStorage.getItem('neurowell_appearance') || 'system';
    const storedAccent = localStorage.getItem('neurowell_accent') || 'blue';
    setAppearance(storedAppearance);
    setAccentColor(storedAccent);
  }, []);

  const saveTheme = (nextAppearance: string, nextAccent: string) => {
    setAppearance(nextAppearance);
    setAccentColor(nextAccent);
    localStorage.setItem('neurowell_appearance', nextAppearance);
    localStorage.setItem('neurowell_accent', nextAccent);
    window.dispatchEvent(new Event('neurowell-theme-change'));
  };

  const loadUser = async () => {
    try {
      if (!authService.isAuthenticated()) {
        router.push('/login');
        return;
      }
      const userData = await authService.getCurrentUser();
      setUser(userData);
      setFormData({
        full_name: userData.full_name || '',
        age: userData.age?.toString() || '',
        guardian_contact: userData.guardian_contact || '',
        guardian_email: userData.guardian_email || '',
      });
    } catch (err) {
      console.error('Failed to load user:', err);
      router.push('/login');
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsSaving(true);

    try {
      await api.put('/api/auth/profile', {
        full_name: formData.full_name || null,
        age: formData.age ? parseInt(formData.age) : null,
        guardian_contact: formData.guardian_contact || null,
        guardian_email: formData.guardian_email || null,
      });

      setSuccess('Profile updated successfully!');
      setIsEditing(false);
      loadUser();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setIsSaving(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (passwordData.new_password !== passwordData.confirm_password) {
      setError('New passwords do not match');
      return;
    }

    setIsSaving(true);

    try {
      await api.post('/api/auth/change-password', {
        current_password: passwordData.current_password,
        new_password: passwordData.new_password,
      });

      setSuccess('Password changed successfully!');
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to change password');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div style={{ width: '48px', height: '48px', border: '4px solid #e5e7eb', borderTopColor: '#4f46e5', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: 'calc(100vh - 64px)', padding: '2rem' }}>
      <div style={{ maxWidth: '56rem', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '2rem' }}>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
            Profile Settings
          </h1>
          <p style={{ color: 'var(--text-secondary)' }}>Manage your account information and preferences</p>
        </div>

        {/* Alerts */}
        {error && (
          <div style={{ marginBottom: '1rem', padding: '1rem', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '0.5rem', color: '#dc2626' }}>
            {error}
          </div>
        )}
        {success && (
          <div style={{ marginBottom: '1rem', padding: '1rem', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '0.5rem', color: '#16a34a' }}>
            {success}
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '1.5rem' }}>
          {/* Profile Information Card */}
          <div className="glass-effect" style={{ padding: '2rem', borderRadius: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
              <h2 style={{ fontSize: '1.25rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                Profile Information
              </h2>
              {!isEditing && (
                <button
                  onClick={() => setIsEditing(true)}
                  className="btn-primary"
                  style={{ padding: '0.5rem 1rem', fontSize: '0.875rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                >
                  <Image src="/assets/EditPencilIcon.svg" alt="Edit" width={16} height={16} />
                  Edit Profile
                </button>
              )}
            </div>

            {/* Profile Avatar */}
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '2rem' }}>
              <div style={{
                width: '80px',
                height: '80px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, var(--accent-600), var(--accent-500))',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontWeight: 'bold',
                fontSize: '2rem'
              }}>
                {user?.username?.charAt(0).toUpperCase() || 'U'}
              </div>
              <div style={{ marginLeft: '1.5rem' }}>
                <div style={{ fontSize: '1.125rem', fontWeight: '600', color: 'var(--text-primary)' }}>
                  {user?.username}
                </div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  {user?.email}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  Member since {new Date(user?.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>

            {/* Profile Form */}
            {isEditing ? (
              <form onSubmit={handleUpdateProfile} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.5rem' }}>
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    placeholder="Enter your full name"
                    style={{ width: '100%', padding: '0.75rem', border: '1px solid #d1d5db', borderRadius: '0.5rem', fontSize: '0.875rem', outline: 'none' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.5rem' }}>
                    Age
                  </label>
                  <input
                    type="number"
                    value={formData.age}
                    onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                    placeholder="Enter your age"
                    style={{ width: '100%', padding: '0.75rem', border: '1px solid #d1d5db', borderRadius: '0.5rem', fontSize: '0.875rem', outline: 'none' }}
                  />
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.5rem' }}>
                    Guardian Contact
                  </label>
                  <input
                    type="tel"
                    value={formData.guardian_contact}
                    onChange={(e) => setFormData({ ...formData, guardian_contact: e.target.value })}
                    placeholder="Emergency contact number"
                    style={{ width: '100%', padding: '0.75rem', border: '1px solid #d1d5db', borderRadius: '0.5rem', fontSize: '0.875rem', outline: 'none' }}
                  />
                </div>

                <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
                  <button
                    type="submit"
                    disabled={isSaving}
                    className="btn-primary"
                    style={{ opacity: isSaving ? 0.5 : 1, cursor: isSaving ? 'not-allowed' : 'pointer' }}
                  >
                    {isSaving ? 'Saving...' : 'Save Changes'}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setIsEditing(false);
                      setFormData({
                        full_name: user?.full_name || '',
                        age: user?.age?.toString() || '',
                        guardian_contact: user?.guardian_contact || '',
                        guardian_email: user?.guardian_email || '',
                      });
                    }}
                    style={{ padding: '0.75rem 1.5rem', border: '1px solid var(--surface-border)', borderRadius: '0.5rem', background: 'var(--surface-1)', color: 'var(--text-primary)', fontWeight: '500', cursor: 'pointer' }}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <div>
                  <div style={{ fontSize: '0.75rem', fontWeight: '500', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>FULL NAME</div>
                  <div style={{ fontSize: '0.875rem', color: 'var(--text-primary)' }}>{user?.full_name || 'Not set'}</div>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.5rem' }}>
                    Guardian Email
                  </label>
                  <input
                    type="email"
                    value={formData.guardian_email}
                    onChange={(e) => setFormData({ ...formData, guardian_email: e.target.value })}
                    placeholder="guardian@example.com"
                    style={{ width: '100%', padding: '0.75rem', border: '1px solid #d1d5db', borderRadius: '0.5rem', fontSize: '0.875rem', outline: 'none' }}
                  />
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', fontWeight: '500', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>AGE</div>
                  <div style={{ fontSize: '0.875rem', color: 'var(--text-primary)' }}>{user?.age || 'Not set'}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', fontWeight: '500', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>GUARDIAN CONTACT</div>
                  <div style={{ fontSize: '0.875rem', color: 'var(--text-primary)' }}>{user?.guardian_contact || 'Not set'}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', fontWeight: '500', color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>GUARDIAN EMAIL</div>
                  <div style={{ fontSize: '0.875rem', color: 'var(--text-primary)' }}>{user?.guardian_email || 'Not set'}</div>
                </div>
              </div>
            )}
          </div>

          {/* Appearance Card */}
          <div className="glass-effect" style={{ padding: '2rem', borderRadius: '1rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '1.5rem' }}>
              Appearance
            </h2>

            <div style={{ marginBottom: '1.25rem' }}>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                Appearance
              </label>
              <div style={{ position: 'relative' }}>
                <select
                  value={appearance}
                  onChange={(e) => saveTheme(e.target.value, accentColor)}
                  style={{ width: '100%', padding: '0.875rem 1rem', border: '1px solid var(--surface-border)', borderRadius: '0.75rem', background: 'var(--surface-1)', color: 'var(--text-primary)', fontSize: '0.9rem', outline: 'none' }}
                >
                  <option value="system">System</option>
                  <option value="dark">Dark</option>
                  <option value="light">Light</option>
                </select>
              </div>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                Accent Color
              </label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '0.75rem' }}>
                {[
                  { key: 'blue', label: 'Blue', color: '#3b82f6' },
                  { key: 'green', label: 'Green', color: '#22c55e' },
                  { key: 'yellow', label: 'Yellow', color: '#eab308' },
                  { key: 'pink', label: 'Pink', color: '#ec4899' },
                  { key: 'orange', label: 'Orange', color: '#f97316' },
                  { key: 'violet', label: 'Violet', color: '#7c3aed' },
                  { key: 'black', label: 'Black', color: '#111827' },
                ].map((option) => (
                  <button
                    key={option.key}
                    type="button"
                    onClick={() => saveTheme(appearance, option.key)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.75rem',
                      padding: '0.85rem 1rem',
                      borderRadius: '0.9rem',
                      border: accentColor === option.key ? `2px solid ${option.color}` : `1px solid var(--surface-border)`,
                      background: accentColor === option.key ? 'var(--accent-50)' : 'var(--surface-1)',
                      cursor: 'pointer',
                      textAlign: 'left',
                    }}
                  >
                    <span style={{ width: '0.9rem', height: '0.9rem', borderRadius: '9999px', background: option.color, boxShadow: '0 0 0 4px rgba(255,255,255,0.75)' }} />
                    <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--text-primary)' }}>{option.label}</span>
                  </button>
                ))}
              </div>
              <p style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Default theme is Blue.
              </p>
            </div>
          </div>

          {/* Change Password Card */}
          <div className="glass-effect" style={{ padding: '2rem', borderRadius: '1rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '600', color: 'var(--text-primary)', marginBottom: '1.5rem' }}>
              Change Password
            </h2>

            <form onSubmit={handleChangePassword} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.5rem' }}>
                  Current Password
                </label>
                <input
                  type="password"
                  value={passwordData.current_password}
                  onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                  required
                  placeholder="Enter current password"
                  style={{ width: '100%', padding: '0.75rem', border: '1px solid #d1d5db', borderRadius: '0.5rem', fontSize: '0.875rem', outline: 'none' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.5rem' }}>
                  New Password
                </label>
                <input
                  type="password"
                  value={passwordData.new_password}
                  onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                  required
                  placeholder="Enter new password"
                  style={{ width: '100%', padding: '0.75rem', border: '1px solid #d1d5db', borderRadius: '0.5rem', fontSize: '0.875rem', outline: 'none' }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.5rem' }}>
                  Confirm New Password
                </label>
                <input
                  type="password"
                  value={passwordData.confirm_password}
                  onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                  required
                  placeholder="Confirm new password"
                  style={{ width: '100%', padding: '0.75rem', border: '1px solid #d1d5db', borderRadius: '0.5rem', fontSize: '0.875rem', outline: 'none' }}
                />
              </div>

              <button
                type="submit"
                disabled={isSaving}
                className="btn-primary"
                style={{ marginTop: '0.5rem', opacity: isSaving ? 0.5 : 1, cursor: isSaving ? 'not-allowed' : 'pointer' }}
              >
                {isSaving ? 'Changing Password...' : 'Change Password'}
              </button>
            </form>
          </div>

          {/* Account Status Card */}
          <div className="glass-effect" style={{ padding: '2rem', borderRadius: '1rem' }}>
            <h2 style={{ fontSize: '1.25rem', fontWeight: '600', color: '#1f2937', marginBottom: '1.5rem' }}>
              Account Status
            </h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>Email Verified</span>
                <span style={{
                  padding: '0.25rem 0.75rem',
                  borderRadius: '9999px',
                  fontSize: '0.75rem',
                  fontWeight: '500',
                  background: user?.email_verified ? '#d1fae5' : '#fee2e2',
                  color: user?.email_verified ? '#065f46' : '#991b1b'
                }}>
                  {user?.email_verified ? 'Verified' : 'Not Verified'}
                </span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>Assessment Completed</span>
                <span style={{
                  padding: '0.25rem 0.75rem',
                  borderRadius: '9999px',
                  fontSize: '0.75rem',
                  fontWeight: '500',
                  background: user?.has_completed_initial_assessment ? '#d1fae5' : '#fef3c7',
                  color: user?.has_completed_initial_assessment ? '#065f46' : '#92400e'
                }}>
                  {user?.has_completed_initial_assessment ? 'Completed' : 'Pending'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
