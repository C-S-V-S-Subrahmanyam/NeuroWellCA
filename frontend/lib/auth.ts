import api from './api';

export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  age?: number;
  guardian_contact?: string;
  email_verified?: boolean;
  has_completed_initial_assessment: boolean;
  created_at: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  requires_assessment: boolean;
}

export const authService = {
  async register(data: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
    age?: number;
    guardian_contact?: string;
  }): Promise<{ message: string; email: string }> {
    const response = await api.post('/api/auth/register', data);
    return response.data;
  },

  async verifyOTP(email: string, otp: string): Promise<User> {
    const response = await api.post('/api/auth/verify-otp', { email, otp });
    const user = response.data;
    
    // Auto-login after successful verification
    // Note: The backend should return tokens or we need to login separately
    // For now, we'll login after verification
    return user;
  },

  async resendOTP(email: string): Promise<void> {
    await api.post('/api/auth/resend-otp', { email });
  },

  async login(username: string, password: string): Promise<LoginResponse> {
    const response = await api.post('/api/auth/login', { username, password });
    const data = response.data;
    
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
    }
    
    return data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await api.get('/api/auth/me');
    const user = response.data;
    
    if (typeof window !== 'undefined') {
      localStorage.setItem('user', JSON.stringify(user));
    }
    
    return user;
  },

  logout() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  },

  isAuthenticated(): boolean {
    if (typeof window !== 'undefined') {
      return !!localStorage.getItem('access_token');
    }
    return false;
  },

  getUser(): User | null {
    if (typeof window !== 'undefined') {
      const user = localStorage.getItem('user');
      return user ? JSON.parse(user) : null;
    }
    return null;
  },
};
