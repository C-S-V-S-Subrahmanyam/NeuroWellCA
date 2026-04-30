'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { authService } from '@/lib/auth';
import { chatService, ChatMessage, ChatSessionInfo, DailyMoodPayload, SuggestedGame } from '@/lib/chat';
import { feedbackService } from '@/lib/feedback';
import SendIconNew from '@/components/icons/SendIconNew';
import TypewriterMessage from '@/components/TypewriterMessage';

const MOOD_OPTIONS = [
  { value: 'calm', emoji: '🌿', label: 'Calm' },
  { value: 'stressed', emoji: '🌪️', label: 'Stressed' },
  { value: 'sad', emoji: '💙', label: 'Sad' },
  { value: 'anxious', emoji: '🌬️', label: 'Anxious' },
  { value: 'tired', emoji: '🫶', label: 'Tired' },
  { value: 'motivated', emoji: '✨', label: 'Motivated' },
];

const VALID_GAME_ROUTES = new Set([
  '/games/breathe-balance',
  '/games/breathing-rhythm',
  '/games/bubble-pop-bliss',
  '/games/emoji-catcher',
  '/games/exercises',
  '/games/focus-flow',
  '/games/gratitude-garden',
  '/games/media-library',
  '/games/zen-match',
]);

const MOOD_STORAGE_KEY_PREFIX = 'neurowell_daily_mood';

type StoredMood = DailyMoodPayload & { savedAt: number };

const ONE_DAY_MS = 24 * 60 * 60 * 1000;

const loadStoredMood = (storageKey: string): StoredMood | null => {
  if (typeof window === 'undefined') return null;

  const raw = window.localStorage.getItem(storageKey);
  if (!raw) return null;

  try {
    const parsed: any = JSON.parse(raw);
    const savedAt = parsed?.savedAt ? Number(parsed.savedAt) : null;
    const now = Date.now();

    if (!savedAt || now - savedAt >= ONE_DAY_MS) {
      // expired
      window.localStorage.removeItem(storageKey);
      return null;
    }

    return {
      mood: parsed.mood,
      mood_note: parsed.mood_note,
      savedAt,
    } as StoredMood;
  } catch {
    window.localStorage.removeItem(storageKey);
    return null;
  }
};

export default function ChatPage() {
  const router = useRouter();
  const currentUser = authService.getUser();
  const isAdmin = currentUser?.is_admin === true;
  const getMoodStorageKey = () => `${MOOD_STORAGE_KEY_PREFIX}_${authService.getUser()?.id ?? 'unknown'}`;
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessions, setSessions] = useState<ChatSessionInfo[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState('');
  const [crisisAlert, setCrisisAlert] = useState<string | null>(null);
  const [guardianAlertStatus, setGuardianAlertStatus] = useState<{ sent: boolean; reason: string; provider?: string } | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const [lastMessageIndex, setLastMessageIndex] = useState(-1);
  const [feedbackByMessageId, setFeedbackByMessageId] = useState<Record<number, 'positive' | 'negative'>>({});
  const [activeSessionMenu, setActiveSessionMenu] = useState<string | null>(null);
  const [showArchived, setShowArchived] = useState(false);
  const [dailyMood, setDailyMood] = useState<DailyMoodPayload | null>(null);
  const [moodNote, setMoodNote] = useState('');
  const [showMoodCard, setShowMoodCard] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const moodExpiryTimerRef = useRef<number | null>(null);

  const userMessageStyle = {
    background: 'linear-gradient(135deg, var(--accent-600), var(--accent-700))',
    color: '#ffffff',
  } as const;

  const sendButtonStyle = {
    background: 'linear-gradient(135deg, var(--accent-600), var(--accent-700))',
    color: '#ffffff',
  } as const;

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/login');
      return;
    }

    const syncViewport = () => {
      const mobile = window.innerWidth < 1024;
      setIsMobile(mobile);
      setSidebarOpen(!mobile);
    };

    syncViewport();
    window.addEventListener('resize', syncViewport);
    loadSessions();

    return () => {
      window.removeEventListener('resize', syncViewport);
    };
  }, [router]);

  useEffect(() => {
    const moodStorageKey = getMoodStorageKey();
    const storedMood = loadStoredMood(moodStorageKey);
    if (storedMood) {
      const { savedAt, ...mood } = storedMood;
      setDailyMood(mood);
      setMoodNote(mood.mood_note || '');
      // If the user already saved a mood for today, hide the mood card by default
      setShowMoodCard(false);

      const expiresIn = Math.max(0, ONE_DAY_MS - (Date.now() - savedAt));
      if (moodExpiryTimerRef.current) {
        window.clearTimeout(moodExpiryTimerRef.current);
      }
      moodExpiryTimerRef.current = window.setTimeout(() => {
        setDailyMood(null);
        setMoodNote('');
        setShowMoodCard(true);
      }, expiresIn);
    }

    return () => {
      if (moodExpiryTimerRef.current) {
        window.clearTimeout(moodExpiryTimerRef.current);
        moodExpiryTimerRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (currentSessionId) {
      loadMessages(currentSessionId);
    }
  }, [currentSessionId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const saveDailyMood = (nextMood?: DailyMoodPayload) => {
    const payload = nextMood || dailyMood;
    if (!payload?.mood?.trim()) {
      return;
    }

    const normalizedPayload: DailyMoodPayload = {
      mood: payload.mood.trim(),
      mood_note: (payload.mood_note || '').trim() || undefined,
    };
    const toStore = { ...normalizedPayload, savedAt: Date.now() };
    const moodStorageKey = getMoodStorageKey();
    window.localStorage.setItem(moodStorageKey, JSON.stringify(toStore));
    setDailyMood(normalizedPayload);
    setMoodNote(normalizedPayload.mood_note || '');
    if (moodExpiryTimerRef.current) {
      window.clearTimeout(moodExpiryTimerRef.current);
      moodExpiryTimerRef.current = null;
    }
    moodExpiryTimerRef.current = window.setTimeout(() => {
      setDailyMood(null);
      setMoodNote('');
      setShowMoodCard(true);
    }, ONE_DAY_MS);
    // After saving today's mood, hide the mood card
    setShowMoodCard(false);
  };

  const clearDailyMood = () => {
    const moodStorageKey = getMoodStorageKey();
    window.localStorage.removeItem(moodStorageKey);
    setDailyMood(null);
    setMoodNote('');
    if (moodExpiryTimerRef.current) {
      window.clearTimeout(moodExpiryTimerRef.current);
      moodExpiryTimerRef.current = null;
    }
    // Reveal the mood card when the user wants to change their mood
    setShowMoodCard(true);
  };

  const handleMoodPick = (mood: string) => {
    // Set the in-memory selection; user must click Save to persist for the day
    setDailyMood({ mood, mood_note: moodNote });
  };

  const loadSessions = async () => {
    try {
      const data = await chatService.getSessions();
      setSessions(data);
      // Don't auto-select first session if user explicitly wants a new chat
      if (data.length > 0 && !currentSessionId && messages.length === 0) {
        // Only auto-load if we have no current session
        setCurrentSessionId(data[0].session_id);
      }
    } catch (err) {
      console.error('Failed to load sessions', err);
      setError('Failed to load chat history');
    }
  };

  const loadMessages = async (sessionId: string) => {
    setIsLoading(true);
    try {
      const data = await chatService.getHistory(sessionId);
      const mappedMessages: ChatMessage[] = data.map((msg) => ({
        id: msg.id,
        role: msg.sender === 'user' ? 'user' : 'assistant',
        content: msg.message_text,
        timestamp: msg.created_at,
      }));
      setMessages(mappedMessages);
    } catch (err) {
      setError('Failed to load chat history');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isSending) return;

    const userMessage = input.trim();
    setInput('');
    setIsSending(true);
    setError('');
    setCrisisAlert(null);
    setGuardianAlertStatus(null);

    const tempMessage: ChatMessage = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempMessage]);

    try {
      const response = await chatService.sendMessage(
        userMessage,
        currentSessionId || undefined,
        dailyMood || undefined,
      );

      if (response.crisis_detected) {
        setCrisisAlert(response.crisis_message || 'Crisis detected. Please seek immediate help.');
        setGuardianAlertStatus({
          sent: !!response.guardian_alert_sent,
          reason: response.guardian_alert_reason || 'unknown',
          provider: response.guardian_alert_provider,
        });
      }

      setMessages((prev) => {
        const next = [...prev];
        const lastIdx = next.length - 1;
        if (lastIdx >= 0 && next[lastIdx].role === 'user' && !next[lastIdx].id) {
          next[lastIdx] = { ...next[lastIdx], id: response.user_message_id };
        }
        return next;
      });

      const aiMessage: ChatMessage = {
        id: response.assistant_message_id,
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
        gameSuggestion: response.suggested_game || undefined,
      };
      setMessages((prev) => [...prev, aiMessage]);
      setLastMessageIndex(messages.length + 1);

      if (!currentSessionId && response.session_id) {
        setCurrentSessionId(response.session_id);
        loadSessions();
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (detail === 'daily_mood_required') {
        setError('Please complete the daily mood check before chatting.');
        setShowMoodCard(true);
      } else {
        setError(detail || 'Failed to send message');
      }
      setMessages((prev) => prev.slice(0, -1));
    } finally {
      setIsSending(false);
    }
  };

  const handleFeedback = async (messageId: number | undefined, feedbackType: 'positive' | 'negative') => {
    if (!messageId || feedbackByMessageId[messageId] === feedbackType) return;

    try {
      await feedbackService.submitFeedback({
        conversation_id: messageId,
        feedback_type: feedbackType,
      });
      setFeedbackByMessageId((prev) => ({ ...prev, [messageId]: feedbackType }));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit feedback');
    }
  };

  const handleNewChat = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setCrisisAlert(null);
    setError('');
  };

  const handleRenameSession = async (sessionId: string, currentTitle: string) => {
    const nextTitle = window.prompt('Rename chat', currentTitle || 'New Chat');
    if (!nextTitle || !nextTitle.trim()) return;

    try {
      await chatService.renameSession(sessionId, nextTitle);
      setSessions((prev) =>
        prev.map((s) => (s.session_id === sessionId ? { ...s, title: nextTitle.trim() } : s))
      );
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to rename chat');
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    const shouldDelete = window.confirm('Delete this chat session? This action cannot be undone.');
    if (!shouldDelete) return;

    try {
      await chatService.deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
      if (currentSessionId === sessionId) {
        handleNewChat();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete chat');
    }
  };

  const handleArchiveSession = async (sessionId: string, currentTitle: string) => {
    try {
      const archivedTitle = currentTitle.startsWith('Archived · ') ? currentTitle : `Archived · ${currentTitle || 'New Chat'}`;
      await chatService.renameSession(sessionId, archivedTitle);
      setSessions((prev) => prev.map((s) => (s.session_id === sessionId ? { ...s, title: archivedTitle } : s)));
      if (currentSessionId === sessionId && !showArchived) {
        handleNewChat();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to archive chat');
    }
  };

  const renderGameSuggestion = (suggestion: SuggestedGame) => (
    <Link
      href={suggestion.href}
      className="mt-4 block rounded-2xl border border-cyan-200 bg-cyan-50/80 px-4 py-3 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
    >
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white text-lg shadow-sm">
          {suggestion.emoji}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-cyan-950">
            Try {suggestion.title}
          </p>
          <p className="mt-1 text-xs leading-relaxed text-cyan-900/80">
            {suggestion.reason}
          </p>
          <p className="mt-2 text-sm font-semibold text-cyan-700">
            Open game →
          </p>
        </div>
      </div>
    </Link>
  );

  const fallbackGames: SuggestedGame[] = [
    {
      title: 'Breathe & Balance',
      href: '/games/breathe-balance',
      emoji: '🌬️',
      reason: 'A quick breathing reset can help settle your mind.',
    },
    {
      title: 'Breathing Rhythm',
      href: '/games/breathing-rhythm',
      emoji: '🎵',
      reason: 'Follow a gentle rhythm to regulate pace and focus.',
    },
    {
      title: 'Focus Flow',
      href: '/games/focus-flow',
      emoji: '🎯',
      reason: 'A calm focus challenge can help reset attention and energy.',
    },
    {
      title: 'Bubble Pop Bliss',
      href: '/games/bubble-pop-bliss',
      emoji: '🫧',
      reason: 'A calm, low-pressure game is a good reset between messages.',
    },
  ];

  const pickFallbackGame = (messageId: number | undefined, index: number): SuggestedGame => {
    const seed = (messageId ?? 0) + index;
    return fallbackGames[Math.abs(seed) % fallbackGames.length];
  };

  const resolveSuggestedGame = (suggestion: SuggestedGame | undefined, messageId: number | undefined, index: number): SuggestedGame => {
    if (suggestion && VALID_GAME_ROUTES.has(suggestion.href)) {
      return suggestion;
    }
    return pickFallbackGame(messageId, index);
  };

  const visibleSessions = sessions.filter((session) => {
    if (showArchived) return true;
    return !(session.title || '').startsWith('Archived · ');
  });

  if (isLoading && messages.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen" style={{ background: 'linear-gradient(135deg, var(--app-bg-start) 0%, var(--app-bg-mid) 50%, var(--app-bg-end) 100%)' }}>
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600 font-medium">Loading your chat...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex relative overflow-hidden" style={{ height: 'calc(100vh - 4rem)' }}>
      {/* Sidebar Toggle Button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="absolute top-3 left-3 z-50 p-2 bg-white rounded-lg shadow-lg hover:bg-gray-50 transition-all"
        style={{ display: sidebarOpen ? 'none' : 'block' }}
      >
        <Image src="/assets/sidebar.svg" alt="Open Sidebar" width={24} height={24} />
      </button>

      {isMobile && sidebarOpen && (
        <button
          type="button"
          aria-label="Close sidebar"
          className="absolute inset-0 z-30 bg-black/30"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          bg-white/90 backdrop-blur-xl border-r border-gray-200/50 flex flex-col shadow-xl transition-all duration-300
          ${isMobile ? 'absolute left-0 top-0 bottom-0 z-40 w-[82vw] max-w-[20rem]' : 'relative w-80'}
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0 lg:w-0 lg:hidden'}
        `}
      >
        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-200/50 flex items-center justify-between">
          <h2 className="text-lg font-bold bg-gradient-to-r from-blue-600 to-blue-600 bg-clip-text text-transparent">Chats</h2>
          <button
            onClick={() => setSidebarOpen(false)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-all"
          >
            <Image src="/assets/hamburger.svg" alt="Close Sidebar" width={20} height={20} />
          </button>
        </div>

        {/* New Chat Button */}
        <div className="p-4">
          <button
            onClick={handleNewChat}
            className="w-full font-semibold py-3 px-5 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl hover:scale-[1.02] active:scale-[0.98]"
            style={{
              background: 'linear-gradient(135deg, var(--accent-700), var(--accent-600))',
              color: '#ffffff',
              boxShadow: '0 12px 24px rgba(37, 99, 235, 0.28)',
            }}
          >
            <span className="flex items-center justify-center gap-2">
              <Image src="/assets/newChat.svg" alt="New Chat" width={20} height={20} className="brightness-0 invert" />
              New Chat
            </span>
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto p-4">
          {sessions.length === 0 && (
            <p className="text-center text-gray-400 text-sm mt-8">No previous chats</p>
          )}
          <div className="flex items-center justify-between mb-2">
            <p className="text-xs text-gray-500 uppercase tracking-wide">Recent</p>
            <button
              type="button"
              onClick={() => setShowArchived((prev) => !prev)}
              className="text-xs text-blue-600 hover:text-blue-700"
            >
              {showArchived ? 'Hide Archived' : 'Show Archived'}
            </button>
          </div>

          {visibleSessions.map((session) => (
            <div
              key={session.session_id}
              className={`relative w-full p-4 rounded-xl mb-2 transition-all duration-200 ${
                currentSessionId === session.session_id
                  ? 'bg-gradient-to-r from-blue-50 to-blue-50 border-2 border-blue-500/50 shadow-md'
                  : 'bg-gray-50/50 border-2 border-transparent hover:bg-gray-100/80'
              }`}
            >
              <div className="flex items-start gap-3">
                <button
                  onClick={() => {
                    setCurrentSessionId(session.session_id);
                    if (isMobile) setSidebarOpen(false);
                  }}
                  className="flex items-start gap-3 flex-1 min-w-0 text-left"
                >
                  <span className="text-2xl">💬</span>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-900 truncate text-sm">
                      {session.title || 'New Chat'}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(session.started_at).toLocaleDateString('en-US', {
                        month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
                      })}
                    </p>
                  </div>
                </button>
                <div className="flex gap-1 ml-2">
                  <button
                    type="button"
                    onClick={() => setActiveSessionMenu((prev) => (prev === session.session_id ? null : session.session_id))}
                    className="p-1.5 rounded-md border border-gray-200 hover:bg-white"
                  >
                    <Image src="/assets/ThreeDots.svg" alt="Session options" width={16} height={16} />
                  </button>
                  {activeSessionMenu === session.session_id && (
                    <div className="absolute mt-8 right-4 z-30 bg-white border border-gray-200 rounded-lg shadow-xl py-1 min-w-[130px]">
                      <button
                        type="button"
                        onClick={() => {
                          handleArchiveSession(session.session_id, session.title || 'New Chat');
                          setActiveSessionMenu(null);
                        }}
                        className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50"
                      >
                        Archive
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          handleRenameSession(session.session_id, session.title || 'New Chat');
                          setActiveSessionMenu(null);
                        }}
                        className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50"
                      >
                        Rename
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          handleDeleteSession(session.session_id);
                          setActiveSessionMenu(null);
                        }}
                        className="w-full px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50"
                      >
                        Delete
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* User Profile */}
        <div className="p-4 border-t border-gray-200/50">
          <button
            onClick={() => router.push('/profile')}
            className="w-full flex items-center gap-3 p-3 rounded-xl hover:bg-gray-100/80 transition-all"
          >
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-bold text-lg shadow-lg">
              {authService.getUser()?.username?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="flex-1 text-left">
              <p className="font-semibold text-gray-900 text-sm">
                {authService.getUser()?.username || 'User'}
              </p>
              <p className="text-xs text-blue-600">Open Profile</p>
            </div>
          </button>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Crisis Alert */}
        {crisisAlert && (
          <div className="bg-red-600 text-white p-4 shadow-lg">
            <p className="font-bold text-center">⚠️ {crisisAlert}</p>
            <p className="text-sm text-center mt-1">National Suicide Prevention Lifeline: 988</p>
            {guardianAlertStatus && (
              <div className="mt-2 flex justify-center">
                <span
                  className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold ${
                    guardianAlertStatus.sent
                      ? 'bg-emerald-100 text-emerald-800'
                      : 'bg-amber-100 text-amber-900'
                  }`}
                >
                  {guardianAlertStatus.sent ? '✅ Alert Delivered' : '⚠️ Alert Not Sent'}
                  <span className="opacity-80">({guardianAlertStatus.reason})</span>
                </span>
              </div>
            )}
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="bg-amber-50 border-l-4 border-amber-500 p-4">
            <p className="text-amber-800 font-medium">⚠️ {error}</p>
          </div>
        )}

        {!isAdmin && showMoodCard && (
          <div className="px-3 pt-4 sm:px-6 sm:pt-5">
            <div className="max-w-4xl mx-auto rounded-3xl border border-cyan-200/80 bg-white/85 backdrop-blur-xl p-4 shadow-lg shadow-cyan-100/40">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="max-w-xl">
                <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-600">
                  Daily mood check
                </p>
                <h3 className="mt-2 text-lg font-bold text-slate-900">
                  {dailyMood ? `Today you are feeling ${dailyMood.mood}.` : 'How are you feeling today?'}
                </h3>
                <p className="mt-1 text-sm text-slate-600">
                  This helps the assistant tune its tone and pick a calming game after each reply.
                </p>
                {dailyMood?.mood_note ? (
                  <p className="mt-2 text-sm text-cyan-800">
                    Note: {dailyMood.mood_note}
                  </p>
                ) : null}
              </div>
              {dailyMood ? (
                <button
                  type="button"
                  onClick={clearDailyMood}
                  className="self-start rounded-full border border-cyan-200 px-4 py-2 text-sm font-semibold text-cyan-700 transition hover:bg-cyan-50"
                >
                  Change mood
                </button>
              ) : null}
            </div>

            <div className="mt-4 grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
              {MOOD_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => handleMoodPick(option.value)}
                  className={`rounded-2xl border px-3 py-3 text-left transition ${
                    dailyMood?.mood === option.value
                      ? 'border-cyan-500 bg-cyan-100 text-cyan-950 shadow-sm'
                      : 'border-slate-200 bg-white text-slate-700 hover:border-cyan-200 hover:bg-cyan-50'
                  }`}
                >
                  <div className="text-lg">{option.emoji}</div>
                  <div className="mt-1 text-sm font-semibold">{option.label}</div>
                </button>
              ))}
            </div>

            <div className="mt-4 grid gap-3 md:grid-cols-[1fr_auto] md:items-end">
              <label className="block">
                <span className="mb-2 block text-sm font-medium text-slate-700">
                  Optional note
                </span>
                <textarea
                  value={moodNote}
                  onChange={(e) => {
                    const nextNote = e.target.value;
                    setMoodNote(nextNote);
                    setDailyMood((prev) => (prev ? { ...prev, mood_note: nextNote } : prev));
                  }}
                  placeholder="What is influencing your mood today?"
                  rows={2}
                  className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-cyan-400 focus:ring-4 focus:ring-cyan-100"
                />
              </label>
              <div className="flex flex-col gap-2">
                <button
                  type="button"
                  onClick={() => saveDailyMood()}
                  className="rounded-2xl bg-gradient-to-r from-cyan-500 to-teal-500 px-5 py-3 text-sm font-semibold text-white shadow-lg transition hover:shadow-xl disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={!dailyMood?.mood}
                >
                  Save today’s mood
                </button>
                <p className="text-xs text-slate-500">
                  Stored only for today and used to personalize chat replies.
                </p>
              </div>
            </div>
            </div>
          </div>
        )}

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-3 py-6 sm:px-6 sm:py-8">
          <div className="max-w-4xl mx-auto">
            {messages.length === 0 ? (
              <div className="text-center mt-20">
                <div className="inline-block p-6 bg-gradient-to-br from-blue-500 to-blue-600 rounded-3xl shadow-2xl mb-6">
                  <span className="text-6xl">🧠</span>
                </div>
                <h2 className="text-2xl sm:text-3xl font-bold bg-gradient-to-r from-blue-600 to-blue-600 bg-clip-text text-transparent mb-3">
                  How are you feeling today?
                </h2>
                <p className="text-gray-600 text-base sm:text-lg">
                  I'm here to listen and support you on your mental wellness journey.
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`flex items-start gap-3 ${
                      msg.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    {msg.role === 'assistant' && (
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0 shadow-lg">
                        <span className="text-xl">🧠</span>
                      </div>
                    )}
                    <div
                      className={`max-w-[82%] sm:max-w-2xl rounded-2xl px-4 sm:px-5 py-3 shadow-md ${
                        msg.role === 'user'
                          ? ''
                          : 'bg-white text-gray-900 border border-gray-200'
                      }`}
                      style={msg.role === 'user' ? userMessageStyle : undefined}
                    >
                      {msg.role === 'assistant' ? (
                        <>
                          <TypewriterMessage
                            content={msg.content}
                            isNew={idx === lastMessageIndex}
                            className="text-sm leading-relaxed"
                          />
                          <div className="mt-3 flex flex-wrap items-center gap-2">
                            <button
                              type="button"
                              onClick={() => handleFeedback(msg.id, 'positive')}
                              className={`px-2 py-1 text-xs rounded-lg border transition ${
                                feedbackByMessageId[msg.id || 0] === 'positive'
                                  ? 'bg-green-100 border-green-300 text-green-700'
                                  : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
                              }`}
                            >
                              👍 Helpful
                            </button>
                            <button
                              type="button"
                              onClick={() => handleFeedback(msg.id, 'negative')}
                              className={`px-2 py-1 text-xs rounded-lg border transition ${
                                feedbackByMessageId[msg.id || 0] === 'negative'
                                  ? 'bg-red-100 border-red-300 text-red-700'
                                  : 'bg-white border-gray-300 text-gray-600 hover:bg-gray-50'
                              }`}
                            >
                              👎 Not helpful
                            </button>
                            <Link
                              href={resolveSuggestedGame(msg.gameSuggestion, msg.id, idx).href}
                              className="px-3 py-1 text-xs rounded-full bg-gradient-to-r from-cyan-500 to-teal-500 text-white font-semibold transition hover:opacity-95"
                            >
                              ▶ Play {resolveSuggestedGame(msg.gameSuggestion, msg.id, idx).title}
                            </Link>
                          </div>
                          {renderGameSuggestion(resolveSuggestedGame(msg.gameSuggestion, msg.id, idx))}
                        </>
                      ) : (
                        <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                          {msg.content}
                        </p>
                      )}
                      <p className={`text-xs mt-2 ${
                        msg.role === 'user' ? 'text-blue-200' : 'text-gray-500'
                      }`}>
                        {new Date(msg.timestamp).toLocaleTimeString('en-US', {
                          hour: 'numeric',
                          minute: '2-digit',
                          hour12: true
                        })}
                      </p>
                    </div>
                    {msg.role === 'user' && (
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-500 flex items-center justify-center flex-shrink-0 text-white font-bold shadow-lg">
                        {authService.getUser()?.username?.charAt(0).toUpperCase() || 'U'}
                      </div>
                    )}
                  </div>
                ))}
                {isSending && (
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-lg">
                      <span className="text-xl">🧠</span>
                    </div>
                    <div className="bg-white rounded-2xl px-5 py-3 shadow-md border border-gray-200">
                      <div className="flex gap-2">
                        <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0s'}}></div>
                        <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                        <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-200/50 bg-white/80 backdrop-blur-xl p-3 sm:p-6 shadow-xl">
          <form onSubmit={handleSend} className="max-w-4xl mx-auto">
            <div className="flex items-end gap-2 sm:gap-3">
              <div className="flex-1 relative">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSend(e);
                    }
                  }}
                  placeholder="Type your message here..."
                  disabled={isSending}
                  rows={1}
                  className="w-full px-4 sm:px-5 py-3 sm:py-4 bg-gray-100 border-2 border-transparent rounded-2xl focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-100 outline-none transition-all duration-200 resize-none text-gray-900 placeholder-gray-400"
                  style={{minHeight: '56px', maxHeight: '150px'}}
                />
              </div>
              <button
                type="submit"
                disabled={
                  isSending || !input.trim() || (!isAdmin && !dailyMood)
                }
                className={`p-4 rounded-2xl transition-all duration-200 shadow-lg ${
                  isSending || !input.trim() || (!isAdmin && !dailyMood)
                    ? 'bg-gray-300 cursor-not-allowed'
                    : 'hover:shadow-xl hover:scale-105 active:scale-95'
                }`}
                style={isSending || !input.trim() || (!isAdmin && !dailyMood) ? undefined : sendButtonStyle}
              >
                {isSending ? (
                  <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <SendIconNew className="w-6 h-6 text-white" />
                )}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-3 text-center">
              Press Enter to send • Shift + Enter for new line
            </p>
          </form>
        </div>
      </main>
    </div>
  );
}
