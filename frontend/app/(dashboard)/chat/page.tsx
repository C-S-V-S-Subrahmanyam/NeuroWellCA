'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';
import { chatService, ChatMessage, ChatSessionInfo } from '@/lib/chat';

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
      if (data.length > 0 && !currentSessionId) {
        setCurrentSessionId(data[0].session_id);
      }
    } catch (err) {
      console.error('Failed to load sessions', err);
    }
  };

  const loadMessages = async (sessionId: string) => {
    setIsLoading(true);
    try {
      const data = await chatService.getHistory(sessionId);
      // Map backend SessionMessage to frontend ChatMessage format
      const mappedMessages: ChatMessage[] = data.map((msg) => ({
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

      const aiMessage: ChatMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, aiMessage]);

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

  const handleNewChat = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setCrisisAlert(null);
  };

  const handleDeleteSession = async (sessionId: string) => {
    if (!confirm('Delete this chat session?')) return;

    try {
      await chatService.deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.session_id !== sessionId));
      if (currentSessionId === sessionId) {
        handleNewChat();
      }
    } catch (err) {
      setError('Failed to delete session');
    }
  };

  if (isLoading && messages.length === 0) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ width: '48px', height: '48px', border: '4px solid #e5e7eb', borderTopColor: '#4f46e5', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto' }}></div>
          <p style={{ marginTop: '1rem', color: '#6b7280' }}>Loading chat...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 64px)', background: '#f3f4f6' }}>
      {/* Sidebar */}
      <div style={{ width: '256px', background: 'white', borderRight: '1px solid #e5e7eb', display: 'flex', flexDirection: 'column' }}>
        <div className="p-4 border-b border-gray-200">
          <button
            onClick={handleNewChat}
            className="btn-primary"
            style={{ width: '100%' }}
          >
            + New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {sessions.map((session) => (
            <div
              key={session.session_id}
              className={`p-3 rounded-lg cursor-pointer group relative ${
                currentSessionId === session.session_id
                  ? 'bg-blue-100 border border-blue-300'
                  : 'bg-gray-50 hover:bg-gray-100 border border-gray-200'
              }`}
              onClick={() => setCurrentSessionId(session.session_id)}
            >
              <div className="text-sm font-medium text-gray-900 truncate">
                {session.title}
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {new Date(session.started_at).toLocaleDateString('en-US', { 
                  month: 'short', 
                  day: 'numeric',
                  year: 'numeric'
                })}
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteSession(session.session_id);
                }}
                className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-700"
              >
                ×
              </button>
            </div>
          ))}
        </div>
        
        {/* Profile Section - Bottom Left */}
        <div className="p-4 border-t border-gray-200">
          <div 
            onClick={() => router.push('/profile')}
            className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-100 cursor-pointer"
          >
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontWeight: 'bold',
              fontSize: '1.125rem'
            }}>
              {authService.getUser()?.username?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="flex-1 overflow-hidden">
              <div className="text-sm font-medium text-gray-900 truncate">
                {authService.getUser()?.username || 'User'}
              </div>
              <div className="text-xs text-gray-500">View Profile</div>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Crisis Alert */}
        {crisisAlert && (
          <div className="bg-red-600 text-white p-4 text-center">
            <p className="font-semibold">{crisisAlert}</p>
            <p className="text-sm mt-1">National Suicide Prevention Lifeline: 988</p>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="bg-yellow-100 border-l-4 border-yellow-500 p-4">
            <p className="text-yellow-700">{error}</p>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 mt-20">
              <p className="text-xl font-semibold mb-2">Welcome to NeuroWell Chat</p>
              <p>Start a conversation by typing a message below.</p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-2xl rounded-lg px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-900 border border-gray-200'
                  }`}
                >
                  <div 
                    className="prose prose-sm max-w-none"
                    style={{
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                      overflowWrap: 'break-word',
                      maxWidth: '100%'
                    }}
                    dangerouslySetInnerHTML={{
                      __html: (() => {
                        let html = msg.content;
                        // Process markdown
                        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                        html = html.replace(/(?<!\*)\*(?!\*)(.*?)\*(?!\*)/g, '<em>$1</em>');
                        html = html.replace(/^### (.*$)/gm, '<h3 style="margin-top:0.5em;margin-bottom:0.5em;">$1</h3>');
                        html = html.replace(/^## (.*$)/gm, '<h2 style="margin-top:0.5em;margin-bottom:0.5em;">$1</h2>');
                        html = html.replace(/^# (.*$)/gm, '<h1 style="margin-top:0.5em;margin-bottom:0.5em;">$1</h1>');
                        // Convert lists
                        const lines = html.split('\n');
                        let inList = false;
                        const processed: string[] = [];
                        lines.forEach(line => {
                          if (line.trim().startsWith('- ')) {
                            if (!inList) {
                              processed.push('<ul style="margin:0.5em 0;padding-left:1.5em;">');
                              inList = true;
                            }
                            processed.push(`<li style="margin:0.25em 0;">${line.trim().substring(2)}</li>`);
                          } else {
                            if (inList) {
                              processed.push('</ul>');
                              inList = false;
                            }
                            processed.push(line);
                          }
                        });
                        if (inList) processed.push('</ul>');
                        html = processed.join('<br/>');
                        return html;
                      })()
                    }}
                  />
                  <p
                    className={`text-xs mt-1 ${
                      msg.role === 'user' ? 'text-blue-100' : 'text-gray-500'
                    }`}
                  >
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))
          )}
          {isSending && (
            <div className="flex justify-start">
              <div className="bg-gray-200 rounded-lg px-4 py-3">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100"></div>
                  <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200"></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-gray-200 bg-white p-4">
          <form onSubmit={handleSend} className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
              placeholder="Type your message..."
              disabled={isSending}
              style={{
                flex: 1,
                padding: '0.75rem 1rem',
                border: '1px solid #d1d5db',
                borderRadius: '0.5rem',
                fontSize: '0.875rem',
                outline: 'none',
                transition: 'all 0.2s'
              }}
              onFocus={(e) => e.currentTarget.style.borderColor = '#3b82f6'}
              onBlur={(e) => e.currentTarget.style.borderColor = '#d1d5db'}
            />
            <button
              type="submit"
              disabled={isSending || !input.trim()}
              className="btn-primary"
              style={{
                opacity: (isSending || !input.trim()) ? 0.5 : 1,
                cursor: (isSending || !input.trim()) ? 'not-allowed' : 'pointer',
                minWidth: '80px'
              }}
            >
              {isSending ? 'Sending...' : 'Send'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
