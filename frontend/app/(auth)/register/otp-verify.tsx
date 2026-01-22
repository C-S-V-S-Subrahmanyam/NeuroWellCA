'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { authService } from '@/lib/auth';

interface OTPVerifyProps {
  email: string;
  username: string;
  password: string;
  onBack: () => void;
}

export default function OTPVerify({ email, username, password, onBack }: OTPVerifyProps) {
  const router = useRouter();
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isResending, setIsResending] = useState(false);

  const handleOtpChange = (index: number, value: string) => {
    if (value.length > 1) value = value[0];
    if (!/^\d*$/.test(value)) return;

    const newOtp = [...otp];
    newOtp[index] = value;
    setOtp(newOtp);

    // Auto-focus next input
    if (value && index < 5) {
      const nextInput = document.getElementById(`otp-${index + 1}`);
      nextInput?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      const prevInput = document.getElementById(`otp-${index - 1}`);
      prevInput?.focus();
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    const otpCode = otp.join('');
    if (otpCode.length !== 6) {
      setError('Please enter the complete 6-digit OTP');
      return;
    }

    setIsLoading(true);

    try {
      await authService.verifyOTP(email, otpCode);
      
      // After successful verification, log in
      await authService.login(username, password);
      await authService.getCurrentUser();
      
      // Redirect to assessment (mandatory for new users)
      router.push('/assessment');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid OTP. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    setIsResending(true);
    setError('');
    
    try {
      await authService.resendOTP(email);
      setOtp(['', '', '', '', '', '']);
      alert('OTP has been resent to your email');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to resend OTP');
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="min-h-screen" style={{ background: 'linear-gradient(135deg, #eef2ff 0%, #faf5ff 100%)', padding: '1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ width: '100%', maxWidth: '28rem' }}>
        {/* Logo & Title */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
            <Image src="/logo.png" alt="NeuroWell Logo" width={70} height={70} />
          </div>
          <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', background: 'linear-gradient(135deg, #4f46e5, #7c3aed)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', marginBottom: '0.5rem' }}>
            Verify Your Email
          </h1>
          <p style={{ color: '#6b7280', fontSize: '0.875rem' }}>
            We've sent a 6-digit code to<br />
            <strong>{email}</strong>
          </p>
        </div>

        {/* OTP Form */}
        <div className="glass-effect" style={{ padding: '2rem', borderRadius: '1.5rem', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)' }}>
          {error && (
            <div style={{ marginBottom: '1rem', padding: '0.75rem', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '0.5rem', color: '#dc2626', fontSize: '0.875rem' }}>
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* OTP Input */}
            <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'center', marginBottom: '1.5rem' }}>
              {otp.map((digit, index) => (
                <input
                  key={index}
                  id={`otp-${index}`}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleOtpChange(index, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(index, e)}
                  style={{
                    width: '3rem',
                    height: '3.5rem',
                    textAlign: 'center',
                    fontSize: '1.5rem',
                    fontWeight: 'bold',
                    border: '2px solid #d1d5db',
                    borderRadius: '0.5rem',
                    outline: 'none',
                    transition: 'all 0.2s'
                  }}
                  onFocus={(e) => e.currentTarget.style.borderColor = '#8b5cf6'}
                  onBlur={(e) => e.currentTarget.style.borderColor = '#d1d5db'}
                />
              ))}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading || otp.join('').length !== 6}
              className="btn-primary"
              style={{
                width: '100%',
                padding: '0.875rem',
                opacity: (isLoading || otp.join('').length !== 6) ? 0.5 : 1,
                cursor: (isLoading || otp.join('').length !== 6) ? 'not-allowed' : 'pointer'
              }}
            >
              {isLoading ? 'Verifying...' : 'Verify & Continue'}
            </button>
          </form>

          {/* Resend & Back */}
          <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
            <button
              onClick={handleResend}
              disabled={isResending}
              style={{
                color: '#8b5cf6',
                fontSize: '0.875rem',
                fontWeight: '500',
                background: 'none',
                border: 'none',
                cursor: isResending ? 'not-allowed' : 'pointer',
                opacity: isResending ? 0.5 : 1
              }}
            >
              {isResending ? 'Sending...' : 'Resend OTP'}
            </button>
            <span style={{ color: '#9ca3af', margin: '0 0.5rem' }}>|</span>
            <button
              onClick={onBack}
              style={{
                color: '#6b7280',
                fontSize: '0.875rem',
                fontWeight: '500',
                background: 'none',
                border: 'none',
                cursor: 'pointer'
              }}
            >
              Change Email
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
