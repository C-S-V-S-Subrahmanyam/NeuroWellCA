'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';
import api from '@/lib/api';

interface UserStats {
  total_users: number;
  total_conversations: number;
  total_assessments: number;
  total_crisis_logs: number;
  total_sessions: number;
}

interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  last_login?: string;
  roles: string[];
}

interface Feedback {
  id: number;
  user_id: number;
  username: string;
  conversation_id: number;
  feedback_type: string;
  reason: string;
  status: string;
  review_notes?: string;
  created_at: string;
}

interface LlmProvider {
  id: number;
  name: string;
  provider_type: string;
  model_name: string;
  base_url?: string;
  has_api_key: boolean;
  is_active: boolean;
  is_default: boolean;
}

interface LlmForm {
  name: string;
  provider_type: string;
  model_name: string;
  base_url: string;
  api_key: string;
  is_default: boolean;
}

interface ActiveProviderState {
  mode: 'provider' | 'fallback_ollama';
  message: string;
  active_provider?: {
    id: number;
    name: string;
    provider_type: string;
    model_name?: string;
    has_api_key?: boolean;
  } | null;
}

export default function AdminDashboard() {
  const router = useRouter();
  const [stats, setStats] = useState<UserStats | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [providers, setProviders] = useState<LlmProvider[]>([]);
  const [activeTab, setActiveTab] = useState<'users' | 'feedback' | 'llm'>('users');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [savingUserId, setSavingUserId] = useState<number | null>(null);
  const [feedbackUpdates, setFeedbackUpdates] = useState<Record<number, { status: string; review_notes: string }>>({});
  const [savingFeedbackId, setSavingFeedbackId] = useState<number | null>(null);
  const [llmForm, setLlmForm] = useState<LlmForm>({
    name: '',
    provider_type: 'ollama',
    model_name: '',
    base_url: '',
    api_key: '',
    is_default: false,
  });
  const [savingLlm, setSavingLlm] = useState(false);
  const [activeProvider, setActiveProvider] = useState<ActiveProviderState | null>(null);
  const [providerBusyId, setProviderBusyId] = useState<number | null>(null);

  const toErrorMessage = (err: any, fallback: string) => {
    const detail = err?.response?.data?.detail;
    if (Array.isArray(detail)) {
      const joined = detail
        .map((item: any) => {
          if (typeof item === 'string') return item;
          if (item?.msg) return item.msg;
          return JSON.stringify(item);
        })
        .join(' | ');
      return joined || fallback;
    }
    if (detail && typeof detail === 'object') {
      if (typeof detail.message === 'string') return detail.message;
      return JSON.stringify(detail);
    }
    if (typeof detail === 'string') return detail;
    return fallback;
  };

  useEffect(() => {
    const checkAdminAccess = async () => {
      if (!authService.isAuthenticated()) {
        router.push('/login');
        return;
      }

      try {
        // Refresh cached user profile before admin checks.
        await authService.getCurrentUser();
      } catch {
        router.push('/login');
        return;
      }

      await loadAdminData();
    };

    checkAdminAccess();
  }, [router]);

  const loadAdminData = async () => {
    try {
      setIsLoading(true);
      setError('');
      
      // Load stats
      const statsResponse = await api.get('/api/admin/stats');
      setStats(statsResponse.data);

      // Load users
      const usersResponse = await api.get('/api/admin/rbac/users?limit=100&offset=0');
      setUsers(usersResponse.data.users || []);

      // Load feedback
      const feedbackResponse = await api.get('/api/feedback/all');
      setFeedbacks(feedbackResponse.data.feedbacks || feedbackResponse.data || []);

      // Load LLM providers
      const providerResponse = await api.get('/api/admin/llm/providers');
      setProviders(providerResponse.data.providers || []);
    } catch (err: any) {
      console.error('Failed to load admin data:', err);
      if (!err?.response) {
        setError('Network error while loading admin data. Please check backend service and retry.');
        return;
      }
      if (err.response?.status === 401) {
        authService.logout();
        router.push('/login');
        return;
      }
      if (err.response?.status === 403) {
        setError('You do not have permission to access admin data.');
      } else {
        setError(toErrorMessage(err, 'Failed to load admin data'));
      }
    } finally {
      setIsLoading(false);
    }
  };

  const refreshProviders = async () => {
    const providerResponse = await api.get('/api/admin/llm/providers');
    setProviders(providerResponse.data.providers || []);
    const activeResponse = await api.get('/api/admin/llm/active');
    setActiveProvider(activeResponse.data);
  };

  const toggleUserActive = async (user: User) => {
    try {
      setSavingUserId(user.id);
      await api.put(`/api/admin/rbac/users/${user.id}`, { is_active: !user.is_active });
      setUsers((prev) => prev.map((u) => (u.id === user.id ? { ...u, is_active: !u.is_active } : u)));
    } catch (err: any) {
      setError(toErrorMessage(err, 'Failed to update user status'));
    } finally {
      setSavingUserId(null);
    }
  };

  const deleteUser = async (user: User) => {
    const ok = window.confirm(`Delete user ${user.username}? This cannot be undone.`);
    if (!ok) return;
    try {
      setSavingUserId(user.id);
      await api.delete(`/api/admin/rbac/users/${user.id}`);
      setUsers((prev) => prev.filter((u) => u.id !== user.id));
    } catch (err: any) {
      setError(toErrorMessage(err, 'Failed to delete user'));
    } finally {
      setSavingUserId(null);
    }
  };

  const saveFeedback = async (feedback: Feedback) => {
    try {
      setSavingFeedbackId(feedback.id);
      const update = feedbackUpdates[feedback.id] || {
        status: feedback.status,
        review_notes: feedback.review_notes || '',
      };
      await api.put(`/api/feedback/${feedback.id}`, update);
      setFeedbacks((prev) =>
        prev.map((f) =>
          f.id === feedback.id
            ? { ...f, status: update.status, review_notes: update.review_notes }
            : f
        )
      );
    } catch (err: any) {
      setError(toErrorMessage(err, 'Failed to update feedback'));
    } finally {
      setSavingFeedbackId(null);
    }
  };

  const activateProvider = async (providerId: number) => {
    try {
      setProviderBusyId(providerId);
      await api.post(`/api/admin/llm/providers/${providerId}/activate`);
      await refreshProviders();
    } catch (err: any) {
      setError(toErrorMessage(err, 'Failed to activate provider'));
    } finally {
      setProviderBusyId(null);
    }
  };

  const deleteProvider = async (providerId: number, providerName: string) => {
    const ok = window.confirm(`Delete provider ${providerName}? If no provider remains active, chat will use Ollama fallback.`);
    if (!ok) return;
    try {
      setProviderBusyId(providerId);
      await api.delete(`/api/admin/llm/providers/${providerId}`);
      await refreshProviders();
    } catch (err: any) {
      setError(toErrorMessage(err, 'Failed to delete provider'));
    } finally {
      setProviderBusyId(null);
    }
  };

  const createProvider = async () => {
    try {
      setSavingLlm(true);
      await api.post('/api/admin/llm/providers', {
        ...llmForm,
        is_active: false,
      });
      setLlmForm({
        name: '',
        provider_type: 'ollama',
        model_name: '',
        base_url: '',
        api_key: '',
        is_default: false,
      });
      await refreshProviders();
    } catch (err: any) {
      setError(toErrorMessage(err, 'Failed to create provider'));
    } finally {
      setSavingLlm(false);
    }
  };

  const filteredUsers = users.filter((u) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return (
      u.username.toLowerCase().includes(q) ||
      u.email.toLowerCase().includes(q) ||
      (u.full_name || '').toLowerCase().includes(q)
    );
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600 font-medium">Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-2">
            Admin Dashboard
          </h1>
          <p className="text-gray-600">System overview and user management</p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mb-6 bg-red-50 border-l-4 border-red-500 p-4 rounded-lg">
            <p className="text-red-800 font-medium">⚠️ {error}</p>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <span className="text-3xl">👥</span>
              <span className="text-sm font-semibold text-blue-600 bg-blue-50 px-3 py-1 rounded-full">
                Users
              </span>
            </div>
            <p className="text-3xl font-bold text-gray-900">{stats?.total_users || 0}</p>
            <p className="text-sm text-gray-600 mt-1">Total registered users</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <span className="text-3xl">💬</span>
              <span className="text-sm font-semibold text-green-600 bg-green-50 px-3 py-1 rounded-full">
                Chats
              </span>
            </div>
            <p className="text-3xl font-bold text-gray-900">{stats?.total_conversations || 0}</p>
            <p className="text-sm text-gray-600 mt-1">Total conversations</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <span className="text-3xl">📋</span>
              <span className="text-sm font-semibold text-purple-600 bg-purple-50 px-3 py-1 rounded-full">
                Assessments
              </span>
            </div>
            <p className="text-3xl font-bold text-gray-900">{stats?.total_assessments || 0}</p>
            <p className="text-sm text-gray-600 mt-1">Completed assessments</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <span className="text-3xl">🚨</span>
              <span className="text-sm font-semibold text-orange-600 bg-orange-50 px-3 py-1 rounded-full">
                Crisis
              </span>
            </div>
            <p className="text-3xl font-bold text-gray-900">{stats?.total_crisis_logs || 0}</p>
            <p className="text-sm text-gray-600 mt-1">Crisis logs</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-6 flex gap-4">
          <button
            onClick={() => setActiveTab('users')}
            className={`px-6 py-3 font-semibold rounded-xl transition ${
              activeTab === 'users'
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg'
                : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            👥 Users
          </button>
          <button
            onClick={() => setActiveTab('feedback')}
            className={`px-6 py-3 font-semibold rounded-xl transition ${
              activeTab === 'feedback'
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg'
                : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            💬 Feedback ({feedbacks.length})
          </button>
          <button
            onClick={() => setActiveTab('llm')}
            className={`px-6 py-3 font-semibold rounded-xl transition ${
              activeTab === 'llm'
                ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg'
                : 'bg-white text-gray-600 hover:bg-gray-50'
            }`}
          >
            🤖 LLM Providers
          </button>
        </div>

        {/* Users Table */}
        {activeTab === 'users' && (
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900">Users</h2>
            <p className="text-sm text-gray-600 mt-1">Manage registered users</p>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by username, email, or full name"
              className="mt-4 w-full md:w-96 border border-gray-300 rounded-lg px-3 py-2 text-sm"
            />
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Username
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Roles
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Last Login
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 text-sm text-gray-900 font-medium">
                      #{user.id}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 font-medium">
                      {user.username}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {user.email}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {user.full_name || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {user.is_active ? (
                        <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-semibold">
                          Active
                        </span>
                      ) : (
                        <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-xs font-semibold">
                          Disabled
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {(user.roles || []).join(', ') || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {user.last_login ? new Date(user.last_login).toLocaleString() : '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      <div className="flex gap-2">
                        <button
                          disabled={savingUserId === user.id}
                          onClick={() => toggleUserActive(user)}
                          className="px-3 py-1 rounded-lg bg-blue-50 text-blue-700 text-xs font-semibold hover:bg-blue-100"
                        >
                          {user.is_active ? 'Disable' : 'Enable'}
                        </button>
                        <button
                          disabled={savingUserId === user.id}
                          onClick={() => deleteUser(user)}
                          className="px-3 py-1 rounded-lg bg-red-50 text-red-700 text-xs font-semibold hover:bg-red-100"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {filteredUsers.length === 0 && (
            <div className="p-12 text-center">
              <p className="text-gray-500">No users found</p>
            </div>
          )}
        </div>
        )}

        {/* Feedback Table */}
        {activeTab === 'feedback' && (
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900">User Feedback</h2>
            <p className="text-sm text-gray-600 mt-1">All feedback submitted by users</p>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    ID
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Reason
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Review Notes
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {feedbacks.map((feedback) => (
                  <tr key={feedback.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 text-sm text-gray-900 font-medium">
                      #{feedback.id}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 font-medium">
                      {feedback.username}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        feedback.feedback_type === 'positive' 
                          ? 'bg-green-100 text-green-700'
                          : feedback.feedback_type === 'negative'
                          ? 'bg-red-100 text-red-700'
                          : 'bg-yellow-100 text-yellow-700'
                      }`}>
                        {feedback.feedback_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {feedback.reason || '-'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 max-w-xs">
                      <textarea
                        value={feedbackUpdates[feedback.id]?.review_notes ?? feedback.review_notes ?? ''}
                        onChange={(e) =>
                          setFeedbackUpdates((prev) => ({
                            ...prev,
                            [feedback.id]: {
                              status: prev[feedback.id]?.status ?? feedback.status,
                              review_notes: e.target.value,
                            },
                          }))
                        }
                        rows={2}
                        className="w-56 border border-gray-300 rounded-md px-2 py-1 text-xs"
                        placeholder="Add review notes"
                      />
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <select
                        value={feedbackUpdates[feedback.id]?.status ?? feedback.status}
                        onChange={(e) =>
                          setFeedbackUpdates((prev) => ({
                            ...prev,
                            [feedback.id]: {
                              status: e.target.value,
                              review_notes: prev[feedback.id]?.review_notes ?? feedback.review_notes ?? '',
                            },
                          }))
                        }
                        className="border border-gray-300 rounded-md px-2 py-1 text-xs"
                      >
                        <option value="pending">pending</option>
                        <option value="approved">approved</option>
                        <option value="rejected">rejected</option>
                        <option value="dismissed">dismissed</option>
                      </select>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {new Date(feedback.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      <button
                        disabled={savingFeedbackId === feedback.id}
                        onClick={() => saveFeedback(feedback)}
                        className="px-3 py-1 rounded-lg bg-indigo-50 text-indigo-700 text-xs font-semibold hover:bg-indigo-100"
                      >
                        Save
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {feedbacks.length === 0 && (
            <div className="p-12 text-center">
              <p className="text-gray-500">No feedback found</p>
            </div>
          )}
        </div>
        )}

        {activeTab === 'llm' && (
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-gray-900">Global LLM Control</h2>
            <p className="text-sm text-gray-600 mt-1">
              Add providers first, then explicitly choose one to use globally for all users.
            </p>
            <div className="mt-3 p-3 rounded-lg border border-indigo-100 bg-indigo-50 text-sm text-indigo-900">
              {activeProvider?.mode === 'provider' && activeProvider.active_provider
                ? `Global active provider: ${activeProvider.active_provider.name} (${activeProvider.active_provider.provider_type})`
                : 'No active external provider. Chat currently uses Ollama fallback.'}
            </div>
          </div>

          <div className="p-6 border-b border-gray-100 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <input
              value={llmForm.name}
              onChange={(e) => setLlmForm((p) => ({ ...p, name: e.target.value }))}
              placeholder="Provider name"
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
            />
            <select
              value={llmForm.provider_type}
              onChange={(e) => setLlmForm((p) => ({ ...p, provider_type: e.target.value }))}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
            >
              <option value="ollama">Ollama</option>
              <option value="gemini">Gemini</option>
              <option value="openai">ChatGPT / OpenAI</option>
              <option value="deepseek">DeepSeek</option>
              <option value="custom">Custom (OpenAI-compatible)</option>
            </select>
            <input
              value={llmForm.model_name}
              onChange={(e) => setLlmForm((p) => ({ ...p, model_name: e.target.value }))}
              placeholder="Model name (e.g. gpt-4o-mini)"
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
            />
            <input
              value={llmForm.base_url}
              onChange={(e) => setLlmForm((p) => ({ ...p, base_url: e.target.value }))}
              placeholder="Base URL (optional)"
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
            />
            <input
              value={llmForm.api_key}
              onChange={(e) => setLlmForm((p) => ({ ...p, api_key: e.target.value }))}
              placeholder="API key"
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
            />
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={llmForm.is_default}
                onChange={(e) => setLlmForm((p) => ({ ...p, is_default: e.target.checked }))}
              />
              <span className="text-sm text-gray-700">Set as default</span>
            </div>
            <div className="md:col-span-2 lg:col-span-3">
              <button
                onClick={createProvider}
                disabled={savingLlm || !llmForm.name || !llmForm.model_name}
                className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm font-semibold hover:bg-indigo-700 disabled:opacity-50"
              >
                {savingLlm ? 'Saving...' : 'Add Provider'}
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Model</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">API Key</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {providers.map((provider) => (
                  <tr key={provider.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">{provider.name}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{provider.provider_type}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{provider.model_name}</td>
                    <td className="px-6 py-4 text-sm text-gray-600">{provider.has_api_key ? 'Configured' : 'Missing'}</td>
                    <td className="px-6 py-4 text-sm">
                      {provider.is_active ? (
                        <span className="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-xs font-semibold">Active</span>
                      ) : (
                        <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-xs font-semibold">Inactive</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <div className="flex gap-2">
                        <button
                          onClick={() => activateProvider(provider.id)}
                          disabled={provider.is_active || providerBusyId === provider.id}
                          className="px-3 py-1 rounded-lg bg-emerald-50 text-emerald-700 text-xs font-semibold hover:bg-emerald-100 disabled:opacity-50"
                        >
                          {provider.is_active ? 'In Use' : 'Use For Chat'}
                        </button>
                        <button
                          onClick={() => deleteProvider(provider.id, provider.name)}
                          disabled={providerBusyId === provider.id}
                          className="px-3 py-1 rounded-lg bg-red-50 text-red-700 text-xs font-semibold hover:bg-red-100 disabled:opacity-50"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {providers.length === 0 && (
            <div className="p-6 text-sm text-gray-500">
              No providers configured. Chat will use Ollama fallback globally.
            </div>
          )}
        </div>
        )}

        {/* Back to Dashboard */}
        <div className="mt-8 text-center">
          <button
            onClick={() => router.push('/dashboard')}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-indigo-700 transition shadow-lg"
          >
            ← Back to Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}
