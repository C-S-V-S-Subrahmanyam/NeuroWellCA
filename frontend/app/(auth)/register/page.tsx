'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { authService } from '@/lib/auth';

export default function RegisterPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
    age: '',
    guardian_contact: '',
  });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setIsLoading(true);

    try {
      await authService.register({
        username: formData.username,
        email: formData.email,
        password: formData.password,
        full_name: formData.full_name || undefined,
        age: formData.age ? parseInt(formData.age) : undefined,
        guardian_contact: formData.guardian_contact || undefined,
      });

      // Auto-login after successful registration
      await authService.login(formData.username, formData.password);
      await authService.getCurrentUser();
      
      // Redirect to step-by-step assessment wizard (mandatory for new users)
      router.push('/assessment-wizard');
    } catch (err: any) {
      // Log the actual error for debugging
      console.error('Registration error:', err);
      console.error('Error response:', err.response);
      console.error('Error message:', err.message);
      
      // Handle validation errors (array of objects) or string errors
      const errorData = err.response?.data;
      if (errorData?.detail) {
        if (Array.isArray(errorData.detail)) {
          // FastAPI validation errors
          const errorMessages = errorData.detail.map((e: any) => 
            `${e.loc?.join(' > ') || 'Field'}: ${e.msg}`
          ).join(', ');
          setError(errorMessages);
        } else {
          setError(errorData.detail);
        }
      } else if (err.message) {
        // Network error or other issues
        setError(`Error: ${err.message}. Please check if backend is running.`);
      } else {
        setError('Registration failed. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #dbeafe 0%, #bfdbfe 50%, #93c5fd 100%)', padding: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ width: '100%', maxWidth: '28rem' }}>
        {/* Logo & Title */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
            <Image src="/logo.PNG" alt="NeuroWell Logo" width={70} height={70} priority />
          </div>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', background: 'linear-gradient(135deg, #1e40af, #3b82f6, #60a5fa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', marginBottom: '0.5rem' }}>
            Create Account
          </h1>
          <p style={{ color: '#6b7280' }}>Join NeuroWell for your wellness journey</p>
        </div>

        {/* Register Form */}
        <div className="glass-effect" style={{ padding: '2rem', borderRadius: '1.5rem', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)' }}>
          {error && (
            <div style={{ marginBottom: '1rem', padding: '0.75rem', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '0.5rem', color: '#dc2626', fontSize: '0.875rem' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Username */}
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.5rem' }}>
                Username
              </label>
              <input
                type="text"
                value={formData.username}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, username: e.target.value })}
                required
                placeholder="Choose a username"
                style={{ width: '100%', padding: '0.75rem', border: '1px solid #d1d5db', borderRadius: '0.75rem', fontSize: '0.875rem', transition: 'all 0.2s', outline: 'none' }}
                onFocus={(e) => e.currentTarget.style.borderColor = '#3b82f6'}
                onBlur={(e) => e.currentTarget.style.borderColor = '#d1d5db'}
              />
            </div>

            {/* Email */}
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.5rem' }}>
                Email
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, email: e.target.value })}
                required
                placeholder="your@email.com"
                style={{ width: '100%', padding: '0.75rem', border: '1px solid #d1d5db', borderRadius: '0.75rem', fontSize: '0.875rem', transition: 'all 0.2s', outline: 'none' }}
                onFocus={(e) => e.currentTarget.style.borderColor = '#3b82f6'}
                onBlur={(e) => e.currentTarget.style.borderColor = '#d1d5db'}
              />
            </div>

            {/* Password */}
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.5rem' }}>
                Password
              </label>
              <input
                type="password"
                value={formData.password}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, password: e.target.value })}
                required
                placeholder="Create a strong password"
                style={{ width: '100%', padding: '0.75rem', border: '1px solid #d1d5db', borderRadius: '0.75rem', fontSize: '0.875rem', transition: 'all 0.2s', outline: 'none' }}
                onFocus={(e) => e.currentTarget.style.borderColor = '#3b82f6'}
                onBlur={(e) => e.currentTarget.style.borderColor = '#d1d5db'}
              />
            </div>

            {/* Confirm Password */}
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.5rem' }}>
                Confirm Password
              </label>
              <input
                type="password"
                value={formData.confirmPassword}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, confirmPassword: e.target.value })}
                required
                placeholder="Confirm your password"
                style={{ width: '100%', padding: '0.75rem', border: '1px solid #d1d5db', borderRadius: '0.75rem', fontSize: '0.875rem', transition: 'all 0.2s', outline: 'none' }}
                onFocus={(e) => e.currentTarget.style.borderColor = '#3b82f6'}
                onBlur={(e) => e.currentTarget.style.borderColor = '#d1d5db'}
              />
            </div>

            {/* Full Name */}
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.5rem' }}>
                Full Name (Optional)
              </label>
              <input
                type="text"
                value={formData.full_name}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, full_name: e.target.value })}
                placeholder="Your full name"
                style={{ width: '100%', padding: '0.75rem', border: '1px solid #d1d5db', borderRadius: '0.75rem', fontSize: '0.875rem', transition: 'all 0.2s', outline: 'none' }}
                onFocus={(e) => e.currentTarget.style.borderColor = '#3b82f6'}
                onBlur={(e) => e.currentTarget.style.borderColor = '#d1d5db'}
              />
            </div>

            {/* Age */}
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.5rem' }}>
                Age (Optional)
              </label>
              <input
                type="number"
                value={formData.age}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, age: e.target.value })}
                placeholder="Your age"
                style={{ width: '100%', padding: '0.75rem', border: '1px solid #d1d5db', borderRadius: '0.75rem', fontSize: '0.875rem', transition: 'all 0.2s', outline: 'none' }}
                onFocus={(e) => e.currentTarget.style.borderColor = '#3b82f6'}
                onBlur={(e) => e.currentTarget.style.borderColor = '#d1d5db'}
              />
            </div>

            {/* Guardian Contact */}
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', color: '#374151', marginBottom: '0.5rem' }}>
                Guardian Contact (Optional)
              </label>
              <input
                type="tel"
                value={formData.guardian_contact}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setFormData({ ...formData, guardian_contact: e.target.value })}
                placeholder="Emergency contact number"
                style={{ width: '100%', padding: '0.75rem', border: '1px solid #d1d5db', borderRadius: '0.75rem', fontSize: '0.875rem', transition: 'all 0.2s', outline: 'none' }}
                onFocus={(e) => e.currentTarget.style.borderColor = '#3b82f6'}
                onBlur={(e) => e.currentTarget.style.borderColor = '#d1d5db'}
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary"
              style={{ width: '100%', opacity: isLoading ? 0.7 : 1, cursor: isLoading ? 'not-allowed' : 'pointer' }}
            >
              {isLoading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          <div style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.875rem', color: '#6b7280' }}>
            Already have an account?{' '}
            <Link href="/login" style={{ color: '#3b82f6', fontWeight: '500', textDecoration: 'none' }}>
              Sign In
            </Link>
          </div>

          <div style={{ marginTop: '1rem', textAlign: 'center' }}>
            <Link href="/" style={{ fontSize: '0.875rem', color: '#9ca3af', textDecoration: 'none' }}>
              ← Back to Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
