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
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mx-auto"></div>
          <p className="mt-4 text-gray-600 font-medium">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-10 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="mb-10">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-700 to-indigo-700 bg-clip-text text-transparent mb-2">Mental Health Dashboard</h1>
          <p className="text-gray-600">Track your mental well-being journey</p>
        </div>

        {stats ? (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10">
              <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl p-6 border border-blue-100">
                <div className="text-center">
                  <div className="inline-block p-3 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl mb-3">
                    <span className="text-2xl">📊</span>
                  </div>
                  <p className="text-sm font-medium text-gray-600 mb-2">Total Assessments</p>
                  <p className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">{stats.totalAssessments}</p>
                </div>
              </div>

              <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl p-6 border border-blue-100">
                <div className="text-center">
                  <div className="inline-block p-3 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl mb-3">
                    <span className="text-2xl">😔</span>
                  </div>
                  <p className="text-sm font-medium text-gray-600 mb-2">Latest PHQ-9 Score</p>
                  <p className={`text-5xl font-bold ${getSeverityColor(stats.latestPhq9, 'phq9')}`}>
                    {stats.latestPhq9}<span className="text-2xl text-gray-400">/27</span>
                  </p>
                  <p className="text-sm font-semibold text-gray-600 mt-2">
                    {getSeverityLabel(stats.latestPhq9, 'phq9')}
                  </p>
                </div>
              </div>

              <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl p-6 border border-blue-100">
                <div className="text-center">
                  <div className="inline-block p-3 bg-gradient-to-br from-amber-500 to-orange-600 rounded-xl mb-3">
                    <span className="text-2xl">😰</span>
                  </div>
                  <p className="text-sm font-medium text-gray-600 mb-2">Latest GAD-7 Score</p>
                  <p className={`text-5xl font-bold ${getSeverityColor(stats.latestGad7, 'gad7')}`}>
                    {stats.latestGad7}<span className="text-2xl text-gray-400">/21</span>
                  </p>
                  <p className="text-sm font-semibold text-gray-600 mt-2">
                    {getSeverityLabel(stats.latestGad7, 'gad7')}
                  </p>
                </div>
              </div>

              <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl p-6 border border-blue-100">
                <div className="text-center">
                  <div className="inline-block p-3 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl mb-3">
                    <span className="text-2xl">🛡️</span>
                  </div>
                  <p className="text-sm font-medium text-gray-600 mb-2">Overall Risk Level</p>
                  <div className="mt-3">
                    <span className={`px-5 py-2 rounded-xl text-lg font-bold shadow-md ${stats.riskBg} ${stats.riskColor}`}>
                      {stats.riskLevel}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-3">
                    Stress: <span className="font-bold text-gray-900">{stats.latestStress}/10</span>
                  </p>
                </div>
              </div>
            </div>

            {/* Assessment History */}
            <div className="bg-white/80 backdrop-blur-xl rounded-2xl shadow-xl p-8 border border-blue-100"><h2 className="text-2xl font-bold text-gray-900 mb-6">Assessment History</h2>
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
            </div>

            {/* Quick Actions */}
            <div className="mt-10 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl shadow-2xl p-8 text-white">
                <div className="text-5xl mb-4">📝</div>
                <h3 className="text-2xl font-bold mb-3">Start New Assessment</h3>
                <p className="text-blue-100 mb-6">
                  Track your mental well-being with a comprehensive assessment.
                </p>
                <button
                  onClick={() => router.push('/assessment-wizard')}
                  className="w-full px-6 py-4 bg-white text-blue-600 rounded-xl font-bold hover:bg-blue-50 transition-all shadow-lg hover:shadow-xl"
                >
                  Take Assessment →
                </button>
              </div>

              <div className="bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl shadow-2xl p-8 text-white">
                <div className="text-5xl mb-4">💬</div>
                <h3 className="text-2xl font-bold mb-3">Continue Chatting</h3>
                <p className="text-purple-100 mb-6">
                  Talk to our AI counselor about your thoughts and feelings.
                </p>
                <button
                  onClick={() => router.push('/chat')}
                  className="w-full px-6 py-4 bg-white text-purple-600 rounded-xl font-bold hover:bg-purple-50 transition-all shadow-lg hover:shadow-xl"
                >
                  Open Chat →
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl p-12 border border-blue-100 text-center">
            <div className="inline-block p-6 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-3xl shadow-xl mb-6">
              <span className="text-7xl">📊</span>
            </div>
            <h2 className="text-3xl font-bold text-gray-900 mb-4">No Assessment Data Yet</h2>
            <p className="text-gray-600 mb-8 text-lg">
              Take your first assessment to start tracking your mental well-being journey.
            </p>
            <button
              onClick={() => router.push('/assessment-wizard')}
              className="px-10 py-5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold rounded-2xl hover:from-blue-700 hover:to-indigo-700 transition-all shadow-xl hover:shadow-2xl text-lg"
            >
              Take Your First Assessment →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
