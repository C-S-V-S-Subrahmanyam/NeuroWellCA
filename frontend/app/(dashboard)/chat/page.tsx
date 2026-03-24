'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { authService } from '@/lib/auth';
import { chatService, ChatMessage, ChatSessionInfo } from '@/lib/chat';
import { feedbackService } from '@/lib/feedback';
import SendIconNew from '@/components/icons/SendIconNew';
import TypewriterMessage from '@/components/TypewriterMessage';

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessions, setSessions] = useState<ChatSessionInfo[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState('');
  const [crisisAlert, setCrisisAlert] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [lastMessageIndex, setLastMessageIndex] = useState(-1);
  const [feedbackByMessageId, setFeedbackByMessageId] = useState<Record<number, 'positive' | 'negative'>>({});
  const [activeSessionMenu, setActiveSessionMenu] = useState<string | null>(null);
  const [showArchived, setShowArchived] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/login');
      return;
    }
    loadSessions();
  }, [router]);

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

    const tempMessage: ChatMessage = {
      role: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempMessage]);

    try {
      const response = await chatService.sendMessage(userMessage, currentSessionId || undefined);

      if (response.crisis_detected) {
        setCrisisAlert(response.crisis_message || 'Crisis detected. Please seek immediate help.');
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
      };
      setMessages((prev) => [...prev, aiMessage]);
      setLastMessageIndex(messages.length + 1);

      if (!currentSessionId && response.session_id) {
        setCurrentSessionId(response.session_id);
        loadSessions();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send message');
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

  const visibleSessions = sessions.filter((session) => {
    if (showArchived) return true;
    return !(session.title || '').startsWith('Archived · ');
  });

  if (isLoading && messages.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600 font-medium">Loading your chat...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex relative" style={{height: 'calc(100vh - 4rem)'}}>
      {/* Sidebar Toggle Button */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="absolute top-4 left-4 z-50 p-2 bg-white rounded-lg shadow-lg hover:bg-gray-50 transition-all"
        style={{ display: sidebarOpen ? 'none' : 'block' }}
      >
        <Image src="/assets/sidebar.svg" alt="Open Sidebar" width={24} height={24} />
      </button>

      {/* Sidebar */}
      <aside className={`bg-white/80 backdrop-blur-xl border-r border-gray-200/50 flex flex-col shadow-xl transition-all duration-300 ${sidebarOpen ? 'w-80' : 'w-0 hidden'}`}>
        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-200/50 flex items-center justify-between">
          <h2 className="text-lg font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">Chats</h2>
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
            className="w-full bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white font-semibold py-3 px-5 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl hover:scale-[1.02] active:scale-[0.98]"
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
              className={`w-full p-4 rounded-xl mb-2 transition-all duration-200 ${
                currentSessionId === session.session_id
                  ? 'bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-500/50 shadow-md'
                  : 'bg-gray-50/50 border-2 border-transparent hover:bg-gray-100/80'
              }`}
            >
              <div className="flex items-start gap-3">
                <button
                  onClick={() => setCurrentSessionId(session.session_id)}
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
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-lg">
              {authService.getUser()?.username?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="flex-1 text-left">
              <p className="font-semibold text-gray-900 text-sm">
                {authService.getUser()?.username || 'User'}
              </p>
              <p className="text-xs text-blue-600">View Profile</p>
            </div>
            <Image src="/assets/Settings.svg" alt="Settings" width={20} height={20} className="opacity-60" />
          </button>
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col">
        {/* Crisis Alert */}
        {crisisAlert && (
          <div className="bg-red-600 text-white p-4 shadow-lg">
            <p className="font-bold text-center">⚠️ {crisisAlert}</p>
            <p className="text-sm text-center mt-1">National Suicide Prevention Lifeline: 988</p>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="bg-amber-50 border-l-4 border-amber-500 p-4">
            <p className="text-amber-800 font-medium">⚠️ {error}</p>
          </div>
        )}

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-6 py-8">
          <div className="max-w-4xl mx-auto">
            {messages.length === 0 ? (
              <div className="text-center mt-20">
                <div className="inline-block p-6 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-3xl shadow-2xl mb-6">
                  <span className="text-6xl">🧠</span>
                </div>
                <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-3">
                  How are you feeling today?
                </h2>
                <p className="text-gray-600 text-lg">
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
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center flex-shrink-0 shadow-lg">
                        <span className="text-xl">🧠</span>
                      </div>
                    )}
                    <div
                      className={`max-w-2xl rounded-2xl px-5 py-3 shadow-md ${
                        msg.role === 'user'
                          ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white'
                          : 'bg-white text-gray-900 border border-gray-200'
                      }`}
                    >
                      {msg.role === 'assistant' ? (
                        <>
                          <TypewriterMessage
                            content={msg.content}
                            isNew={idx === lastMessageIndex}
                            className="text-sm leading-relaxed"
                          />
                          <div className="mt-3 flex items-center gap-2">
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
                          </div>
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
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-indigo-500 flex items-center justify-center flex-shrink-0 text-white font-bold shadow-lg">
                        {authService.getUser()?.username?.charAt(0).toUpperCase() || 'U'}
                      </div>
                    )}
                  </div>
                ))}
                {isSending && (
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg">
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
        <div className="border-t border-gray-200/50 bg-white/80 backdrop-blur-xl p-6 shadow-xl">
          <form onSubmit={handleSend} className="max-w-4xl mx-auto">
            <div className="flex items-end gap-3">
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
                  className="w-full px-5 py-4 bg-gray-100 border-2 border-transparent rounded-2xl focus:bg-white focus:border-blue-500 focus:ring-4 focus:ring-blue-100 outline-none transition-all duration-200 resize-none text-gray-900 placeholder-gray-400"
                  style={{minHeight: '56px', maxHeight: '150px'}}
                />
              </div>
              <button
                type="submit"
                disabled={isSending || !input.trim()}
                className={`p-4 rounded-2xl transition-all duration-200 shadow-lg ${
                  isSending || !input.trim()
                    ? 'bg-gray-300 cursor-not-allowed'
                    : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 hover:shadow-xl hover:scale-105 active:scale-95'
                }`}
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
