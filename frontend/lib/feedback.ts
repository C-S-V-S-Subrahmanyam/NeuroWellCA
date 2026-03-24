import api from './api';

export interface FeedbackSubmitPayload {
  conversation_id: number;
  feedback_type: 'positive' | 'negative';
  reason?: string;
}

export const feedbackService = {
  async submitFeedback(payload: FeedbackSubmitPayload): Promise<{ message: string; id: number }> {
    const response = await api.post('/api/feedback/submit', payload);
    return response.data;
  },
};
