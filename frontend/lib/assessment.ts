import api from './api';

export interface AssessmentSubmit {
  phq9_answers: number[];
  gad7_answers: number[];
  stress_level: number;
  notes?: string;
}

export interface AssessmentResponse {
  id: number;
  phq9_score: number;
  gad7_score: number;
  stress_level: number;
  severity_interpretation?: string;
  risk_level?: string;
  created_at: string;
}

export const assessmentService = {
  async submit(data: AssessmentSubmit): Promise<AssessmentResponse> {
    const response = await api.post('/api/assessments/submit', data);
    return response.data;
  },

  async getHistory(): Promise<AssessmentResponse[]> {
    const response = await api.get('/api/assessments/history');
    return response.data;
  },
};
