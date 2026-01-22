'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';
import { assessmentService } from '@/lib/assessment';
import Card from '@/components/Card';

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/login');
      return;
    }

    loadData();
  }, [router]);

  const loadData = async () => {
    try {
      const historyData = await assessmentService.getHistory();
      setHistory(historyData);

      if (historyData.length > 0) {
        const latest = historyData[0];
        const avgPhq9 = historyData.reduce((sum: number, a: any) => sum + a.phq9_score, 0) / historyData.length;
        const avgGad7 = historyData.reduce((sum: number, a: any) => sum + a.gad7_score, 0) / historyData.length;
        const riskInfo = calculateRiskLevel(latest.phq9_score, latest.gad7_score, latest.stress_level);

        setStats({
          totalAssessments: historyData.length,
          latestPhq9: latest.phq9_score,
          latestGad7: latest.gad7_score,
          latestStress: latest.stress_level,
          avgPhq9: Math.round(avgPhq9 * 10) / 10,
          avgGad7: Math.round(avgGad7 * 10) / 10,
          riskLevel: riskInfo.level,
          riskColor: riskInfo.color,
          riskBg: riskInfo.bg,
        });
      }
    } catch (err) {
      console.error('Failed to load dashboard data', err);
    } finally {
      setIsLoading(false);
    }
  };

  const getSeverityColor = (score: number, type: 'phq9' | 'gad7') => {
    if (type === 'phq9') {
      if (score >= 20) return 'text-red-600';
      if (score >= 15) return 'text-orange-600';
      if (score >= 10) return 'text-yellow-600';
      if (score >= 5) return 'text-blue-600';
      return 'text-green-600';
    } else {
      if (score >= 15) return 'text-red-600';
      if (score >= 10) return 'text-orange-600';
      if (score >= 5) return 'text-yellow-600';
      return 'text-green-600';
    }
  };

  const getSeverityLabel = (score: number, type: 'phq9' | 'gad7') => {
    if (type === 'phq9') {
      if (score >= 20) return 'Severe';
      if (score >= 15) return 'Moderately Severe';
      if (score >= 10) return 'Moderate';
      if (score >= 5) return 'Mild';
      return 'Minimal';
    } else {
      if (score >= 15) return 'Severe';
      if (score >= 10) return 'Moderate';
      if (score >= 5) return 'Mild';
      return 'Minimal';
    }
  };

  const calculateRiskLevel = (phq9: number, gad7: number, stress: number) => {
    // Combine scores to determine overall risk
    const totalScore = phq9 + gad7 + (stress * 2); // Weighted total
    
    if (phq9 >= 20 || gad7 >= 15 || stress >= 9) return { level: 'Severe', color: 'text-red-600', bg: 'bg-red-100' };
    if (phq9 >= 15 || gad7 >= 10 || stress >= 7 || totalScore >= 35) return { level: 'Moderately Severe', color: 'text-orange-600', bg: 'bg-orange-100' };
    if (phq9 >= 10 || gad7 >= 5 || stress >= 5 || totalScore >= 25) return { level: 'Moderate', color: 'text-yellow-600', bg: 'bg-yellow-100' };
    if (phq9 >= 5 || gad7 >= 3 || stress >= 3 || totalScore >= 15) return { level: 'Mild', color: 'text-blue-600', bg: 'bg-blue-100' };
    return { level: 'Minimal', color: 'text-green-600', bg: 'bg-green-100' };
  };

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ width: '48px', height: '48px', border: '4px solid #e5e7eb', borderTopColor: '#4f46e5', borderRadius: '50%', animation: 'spin 1s linear infinite', margin: '0 auto' }}></div>
          <p style={{ marginTop: '1rem', color: '#6b7280' }}>Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Mental Health Dashboard</h1>

        {stats ? (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <Card>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Total Assessments</p>
                  <p className="text-4xl font-bold text-blue-600">{stats.totalAssessments}</p>
                </div>
              </Card>

              <Card>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Latest PHQ-9 Score</p>
                  <p className={`text-4xl font-bold ${getSeverityColor(stats.latestPhq9, 'phq9')}`}>
                    {stats.latestPhq9}/27
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {getSeverityLabel(stats.latestPhq9, 'phq9')}
                  </p>
                </div>
              </Card>

              <Card>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Latest GAD-7 Score</p>
                  <p className={`text-4xl font-bold ${getSeverityColor(stats.latestGad7, 'gad7')}`}>
                    {stats.latestGad7}/21
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {getSeverityLabel(stats.latestGad7, 'gad7')}
                  </p>
                </div>
              </Card>

              <Card>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-2">Overall Risk Level</p>
                  <div className={`inline-flex items-center justify-center w-full mt-2`}>
                    <span className={`px-4 py-2 rounded-lg text-lg font-bold ${stats.riskBg} ${stats.riskColor}`}>
                      {stats.riskLevel}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Stress: {stats.latestStress}/10
                  </p>
                </div>
              </Card>
            </div>

            {/* Assessment History */}
            <Card title="Assessment History">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Date</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">PHQ-9</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">GAD-7</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Stress</th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">Risk Level</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((assessment, idx) => {
                      const riskInfo = calculateRiskLevel(assessment.phq9_score, assessment.gad7_score, assessment.stress_level);
                      return (
                        <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-3 px-4 text-sm text-gray-900">
                            {new Date(assessment.created_at).toLocaleDateString()}
                          </td>
                          <td className="py-3 px-4">
                            <span className={`font-semibold ${getSeverityColor(assessment.phq9_score, 'phq9')}`}>
                              {assessment.phq9_score}
                            </span>
                            <span className="text-gray-400 ml-1 text-xs">
                              ({getSeverityLabel(assessment.phq9_score, 'phq9')})
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <span className={`font-semibold ${getSeverityColor(assessment.gad7_score, 'gad7')}`}>
                              {assessment.gad7_score}
                            </span>
                            <span className="text-gray-400 ml-1 text-xs">
                              ({getSeverityLabel(assessment.gad7_score, 'gad7')})
                            </span>
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-700">
                            {assessment.stress_level}/10
                          </td>
                          <td className="py-3 px-4">
                            <span className={`px-2 py-1 rounded text-xs font-medium ${riskInfo.bg} ${riskInfo.color}`}>
                              {riskInfo.level}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </Card>

            {/* Quick Actions */}
            <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Start New Assessment</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Take a new mental health assessment to track your progress.
                </p>
                <button
                  onClick={() => router.push('/assessment')}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Take Assessment
                </button>
              </Card>

              <Card>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Continue Chatting</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Talk to our AI counselor about your thoughts and feelings.
                </p>
                <button
                  onClick={() => router.push('/chat')}
                  className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
                >
                  Open Chat
                </button>
              </Card>
            </div>
          </>
        ) : (
          <Card>
            <div className="text-center py-12">
              <p className="text-gray-600 mb-4">No assessment data available yet.</p>
              <button
                onClick={() => router.push('/assessment')}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Take Your First Assessment
              </button>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
