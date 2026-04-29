import api from './api';

export interface ChatMessage {
  id?: number;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  gameSuggestion?: SuggestedGame;
}

export interface SuggestedGame {
  title: string;
  href: string;
  emoji: string;
  reason: string;
}

export interface DailyMoodPayload {
  mood: string;
  mood_note?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  user_message_id: number;
  assistant_message_id: number;
  crisis_detected: boolean;
  crisis_message?: string;
  crisis_resources?: any[];
  guardian_alert_sent?: boolean;
  guardian_alert_reason?: string;
  guardian_alert_provider?: string;
  suggested_game?: SuggestedGame | null;
}

export interface SessionMessage {
  id: number;
  message_text: string;
  sender: string;
  created_at: string;
  crisis_detected?: boolean;
}

export interface ChatSessionInfo {
  session_id: string;
  title: string;
  message_count: number;
  started_at: string;
  last_message_at?: string;
}

export const chatService = {
  async sendMessage(message: string, sessionId?: string, mood?: DailyMoodPayload): Promise<ChatResponse> {
    const response = await api.post('/api/chat/message', {
      message,
      session_id: sessionId,
      mood: mood?.mood,
      mood_note: mood?.mood_note,
    });
    return response.data;
  },

  async getHistory(sessionId: string): Promise<SessionMessage[]> {
    const response = await api.get(`/api/chat/history/${sessionId}`);
    return response.data;
  },

  async getSessions(): Promise<ChatSessionInfo[]> {
    const response = await api.get('/api/chat/sessions');
    return response.data;
  },

  async deleteSession(sessionId: string): Promise<void> {
    await api.delete(`/api/chat/session/${sessionId}`);
  },

  async renameSession(sessionId: string, title: string): Promise<{ message: string; title: string }> {
    const response = await api.patch(`/api/chat/session/${sessionId}/rename`, {
      title: title.trim().slice(0, 80),
    });
    return response.data;
  },
};
