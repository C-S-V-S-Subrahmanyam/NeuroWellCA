'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import  { assessmentService } from '@/lib/assessment';
import { authService } from '@/lib/auth';

// PHQ-9 Questions (Depression screening)
const PHQ9_QUESTIONS = [
  "Little interest or pleasure in doing things?",
  "Feeling down, depressed, or hopeless?",
  "Trouble falling/staying asleep, or sleeping too much?",
  "Feeling tired or having little energy?",
  "Poor appetite or overeating?",
  "Feeling bad about yourself or that you're a failure?",
  "Trouble concentrating on things?",
  "Moving or speaking slowly, or being fidgety/restless?",
  "Thoughts that you would be better off dead or hurting yourself?"
];

// GAD-7 Questions (Anxiety screening)
const GAD7_QUESTIONS = [
  "Feeling nervous, anxious, or on edge?",
  "Not being able to stop or control worrying?",
  "Worrying too much about different things?",
  "Trouble relaxing?",
  "Being so restless that it's hard to sit still?",
  "Becoming easily annoyed or irritable?",
  "Feeling afraid as if something awful might happen?"
];

const ANSWER_OPTIONS = [
  { value: 0, label: 'Not at all', color: 'from-green-500 to-emerald-500', emoji: '😊', bgColor: 'bg-green-50', borderColor: 'border-green-500' },
  { value: 1, label: 'Several days', color: 'from-yellow-500 to-amber-500', emoji: '😐', bgColor: 'bg-yellow-50', borderColor: 'border-yellow-500' },
  { value: 2, label: 'More than half the days', color: 'from-orange-500 to-red-500', emoji: '😟', bgColor: 'bg-orange-50', borderColor: 'border-orange-500' },
  { value: 3, label: 'Nearly every day', color: 'from-red-600 to-rose-700', emoji: '😢', bgColor: 'bg-red-50', borderColor: 'border-red-500' }
];

export default function AssessmentWizard() {
  const router = useRouter();
  const [section, setSection] = useState<'intro' | 'phq9' | 'gad7' | 'stress' | 'notes'>('intro');
  const [phq9Answers, setPhq9Answers] = useState<number[]>(Array(9).fill(-1));
  const [gad7Answers, setGad7Answers] = useState<number[]>(Array(7).fill(-1));
  const [stressLevel, setStressLevel] = useState<number>(-1);
  const [notes, setNotes] = useState('');
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const getCurrentQuestions = () => {
    if (section === 'phq9') return PHQ9_QUESTIONS;
    if (section === 'gad7') return GAD7_QUESTIONS;
    return [];
  };

  const getCurrentAnswers = () => {
    if (section === 'phq9') return phq9Answers;
    if (section === 'gad7') return gad7Answers;
    return [];
  };

  const setCurrentAnswer = (value: number) => {
    if (section === 'phq9') {
      const newAnswers = [...phq9Answers];
      newAnswers[currentQuestionIndex] = value;
      setPhq9Answers(newAnswers);
    } else if (section === 'gad7') {
      const newAnswers = [...gad7Answers];
      newAnswers[currentQuestionIndex] = value;
      setGad7Answers(newAnswers);
    }
  };

  const getTotalProgress = () => {
    if (section === 'intro') return 0;
    else if (section === 'phq9') return 10 + (currentQuestionIndex / PHQ9_QUESTIONS.length) * 35;
    else if (section === 'gad7') return 45 + (currentQuestionIndex / GAD7_QUESTIONS.length) * 30;
    else if (section === 'stress') return 75;
    else if (section === 'notes') return 90;
    
    return 0;
  };

  const handleNext = () => {
    const questions = getCurrentQuestions();
    
    if (section === 'intro') {
      setSection('phq9');
      setCurrentQuestionIndex(0);
    } else if (section === 'phq9' || section === 'gad7') {
      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      } else {
        if (section === 'phq9') {
          setSection('gad7');
          setCurrentQuestionIndex(0);
        } else {
          setSection('stress');
        }
      }
    } else if (section === 'stress') {
      setSection('notes');
    } else if (section === 'notes') {
      handleSubmit();
    }
  };

  const handleBack = () => {
    if (section === 'notes') {
      setSection('stress');
    } else if (section === 'stress') {
      setSection('gad7');
      setCurrentQuestionIndex(GAD7_QUESTIONS.length - 1);
    } else if (section === 'gad7') {
      if (currentQuestionIndex > 0) {
        setCurrentQuestionIndex(currentQuestionIndex - 1);
      } else {
        setSection('phq9');
        setCurrentQuestionIndex(PHQ9_QUESTIONS.length - 1);
      }
    } else if (section === 'phq9') {
      if (currentQuestionIndex > 0) {
        setCurrentQuestionIndex(currentQuestionIndex - 1);
      } else {
        setSection('intro');
      }
    }
  };

  const canContinue = () => {
    if (section === 'intro') return true;
    if (section === 'phq9') return phq9Answers[currentQuestionIndex] !== -1;
    if (section === 'gad7') return gad7Answers[currentQuestionIndex] !== -1;
    if (section === 'stress') return stressLevel !== -1;
    if (section === 'notes') return true; // Notes are optional
    return false;
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError('');
    
    try {
      const result = await assessmentService.submit({
        phq9_answers: phq9Answers,
        gad7_answers: gad7Answers,
        stress_level: stressLevel,
        notes: notes || undefined
      });
      
      // Update user's has_completed_initial_assessment status
      const user = authService.getUser();
      if (user) {
        user.has_completed_initial_assessment = true;
        localStorage.setItem('user', JSON.stringify(user));
      }
      
      // Always redirect to chat page after completion
      router.push('/chat');
    } catch (err: any) {
      console.error('Assessment submission error:', err);
      setError(err.response?.data?.detail || 'Failed to submit assessment. Please try again.');
      setIsSubmitting(false);
    }
  };

  if (section === 'intro') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-blue-50 to-cyan-50 flex items-center justify-center p-6">
        <div className="max-w-2xl w-full bg-white/90 backdrop-blur-xl rounded-3xl shadow-2xl p-10 border border-blue-100">
          <div className="text-center">
            <div className="inline-block p-5 bg-gradient-to-br from-blue-500 to-blue-600 rounded-3xl shadow-2xl mb-6 animate-pulse">
              <span className="text-6xl">🧠</span>
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-700 to-blue-700 bg-clip-text text-transparent mb-4">
              Mental Health Assessment
            </h1>
            <p className="text-lg text-gray-700 mb-8">
              Let's understand how you're feeling with standard clinical assessments.
            </p>
            
            <div className="bg-gradient-to-r from-blue-50 to-blue-50 border-l-4 border-blue-500 p-6 rounded-r-xl mb-8 text-left shadow-inner">
              <h3 className="font-bold text-blue-900 mb-4 text-lg flex items-center gap-2">
                <span className="text-2xl">📋</span> What to expect:
              </h3>
              <ul className="space-y-3 text-gray-700">
                <li className="flex items-start gap-3 group">
                  <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold text-sm flex-shrink-0 group-hover:scale-110 transition-transform">1</div>
                  <div>
                    <span className="font-semibold text-blue-900">PHQ-9 Depression Screening</span>
                    <p className="text-sm text-gray-600">9 questions about your mood (2-3 min)</p>
                  </div>
                </li>
                <li className="flex items-start gap-3 group">
                  <div className="w-8 h-8 rounded-full bg-blue-500 text-white flex items-center justify-center font-bold text-sm flex-shrink-0 group-hover:scale-110 transition-transform">2</div>
                  <div>
                    <span className="font-semibold text-blue-900">GAD-7 Anxiety Screening</span>
                    <p className="text-sm text-gray-600">7 questions about anxiety (2-3 min)</p>
                  </div>
                </li>
                <li className="flex items-start gap-3 group">
                  <div className="w-8 h-8 rounded-full bg-cyan-500 text-white flex items-center justify-center font-bold text-sm flex-shrink-0 group-hover:scale-110 transition-transform">3</div>
                  <div>
                    <span className="font-semibold text-cyan-900">Stress Level Assessment</span>
                    <p className="text-sm text-gray-600">Rate your stress 0-10 (1 min)</p>
                  </div>
                </li>
              </ul>
            </div>

            <div className="bg-amber-50 border-l-4 border-amber-400 p-4 rounded-r-xl mb-8">
              <p className="text-sm text-amber-900 flex items-center gap-2">
                <span className="text-xl">🔒</span>
                <span><strong>100% Confidential</strong> - Your responses help us provide personalized support</span>
              </p>
            </div>

            <button
              onClick={handleNext}
              className="w-full font-bold py-5 px-8 rounded-2xl shadow-2xl transition-all duration-300 hover:scale-[1.02] active:scale-[0.98] mb-3"
              style={{
                background: 'linear-gradient(135deg, var(--accent-700), var(--accent-600))',
                color: '#ffffff',
                boxShadow: '0 16px 34px rgba(37, 99, 235, 0.35)',
              }}
            >
              <span className="flex items-center justify-center gap-3 text-lg">
                <span>Begin Assessment</span>
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                </svg>
              </span>
            </button>

            <button
              onClick={() => router.push('/chat')}
              className="text-sm text-gray-500 hover:text-gray-700 underline transition-colors"
            >
              I'll do this later
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (section === 'stress') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-blue-50 to-cyan-50 flex items-center justify-center p-6">
        <div className="max-w-3xl w-full">
          {/* Progress */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-600">Overall Progress</span>
              <span className="text-sm font-medium text-blue-600">{Math.round(getTotalProgress())}%</span>
            </div>
            <div className="w-full h-2 bg-white rounded-full overflow-hidden shadow-inner">
              <div
                className="h-full bg-gradient-to-r from-blue-600 to-blue-600 transition-all duration-500"
                style={{ width: `${getTotalProgress()}%` }}
              />
            </div>
          </div>

          <div className="bg-white/90 backdrop-blur-xl rounded-3xl shadow-2xl p-10 border border-blue-100">
            <div className="mb-8">
              <span className="bg-cyan-100 text-cyan-700 text-sm font-semibold px-4 py-2 rounded-full">Stress Assessment</span>
            </div>

            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              How stressed have you felt in the past 2 weeks?
            </h2>
            <p className="text-gray-600 mb-8">Select a number from 0 to 10</p>

            <div className="mb-6">
              <div className="flex justify-between text-sm font-medium text-gray-600 mb-2">
                <span className="flex items-center gap-1">
                  <span className="text-xl">😌</span> No Stress
                </span>
                <span className="flex items-center gap-1">
                  Extremely Stressed <span className="text-xl">😰</span>
                </span>
              </div>
            </div>

            <div className="grid grid-cols-11 gap-3 mb-10">
              {[...Array(11)].map((_, i) => {
                const getColor = (level: number) => {
                  if (level <= 3) return 'from-green-500 to-emerald-600';
                  if (level <= 6) return 'from-yellow-500 to-amber-600';
                  if (level <= 8) return 'from-orange-500 to-red-600';
                  return 'from-red-600 to-rose-700';
                };
                
                const getBgColor = (level: number) => {
                  if (level <= 3) return 'bg-green-50 border-green-500';
                  if (level <= 6) return 'bg-yellow-50 border-yellow-500';
                  if (level <= 8) return 'bg-orange-50 border-orange-500';
                  return 'bg-red-50 border-red-500';
                };

                const isSelected = stressLevel === i;
                
                return (
                  <button
                    key={i}
                    onClick={() => setStressLevel(i)}
                    className={`aspect-square rounded-xl font-bold text-xl transition-all duration-300 transform ${
                      isSelected
                        ? `bg-gradient-to-br ${getColor(i)} text-white shadow-2xl scale-125 border-2 ${getBgColor(i).split(' ')[1]}`
                        : 'bg-white text-gray-700 hover:bg-gray-100 border-2 border-gray-200 hover:border-blue-400 hover:scale-110 shadow-md'
                    }`}
                  >
                    {i}
                  </button>
                );
              })}
            </div>

            {stressLevel !== -1 && (
              <div className="mb-6 p-4 bg-blue-50 border-l-4 border-blue-500 rounded-r-xl">
                <p className="text-blue-900 font-semibold">
                  Selected stress level: <span className="text-2xl">{stressLevel}/10</span>
                  {stressLevel <= 3 && ' - Mild stress'}
                  {stressLevel > 3 && stressLevel <= 6 && ' - Moderate stress'}
                  {stressLevel > 6 && stressLevel <= 8 && ' - High stress'}
                  {stressLevel > 8 && ' - Very high stress'}
                </p>
              </div>
            )}

            {error && (
              <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded">
                {error}
              </div>
            )}

            <div className="flex justify-between">
              <button
                onClick={handleBack}
                className="px-6 py-3 text-gray-600 font-semibold rounded-xl hover:bg-gray-100 transition-all flex items-center gap-2"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Back
              </button>
              <button
                onClick={handleNext}
                disabled={!canContinue()}
                className="font-bold py-3 px-8 rounded-2xl shadow-lg disabled:cursor-not-allowed transition-all flex items-center gap-2"
                style={canContinue()
                  ? {
                      background: 'linear-gradient(135deg, var(--accent-700), var(--accent-600))',
                      color: '#ffffff',
                    }
                  : {
                      background: '#e5e7eb',
                      color: '#6b7280',
                    }}
              >
                Next
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (section === 'notes') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-blue-50 to-cyan-50 flex items-center justify-center p-6">
        <div className="max-w-3xl w-full">
          {/* Progress */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-gray-600">Overall Progress</span>
              <span className="text-sm font-medium text-blue-600">80%</span>
            </div>
            <div className="w-full h-2 bg-white rounded-full overflow-hidden shadow-inner">
              <div className="h-full bg-gradient-to-r from-blue-600 to-blue-600 w-4/5" />
            </div>
          </div>

          <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl p-10">
            <div className="mb-8">
              <span className="bg-cyan-100 text-cyan-700 text-sm font-semibold px-4 py-2 rounded-full">Final Step (Optional)</span>
            </div>

            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Is there anything else you'd like us to know?
            </h2>
            <p className="text-gray-600 mb-8">Any additional information that might help us support you better (optional)</p>

            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Your thoughts, concerns, or anything you'd like to share..."
              className="w-full p-5 border-2 border-gray-200 rounded-2xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 outline-none resize-none transition-all text-gray-800"
              rows={6}
            />

            {error && (
              <div className="mt-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded">
                {error}
              </div>
            )}

            <div className="flex justify-between mt-8">
              <button
                onClick={handleBack}
                disabled={isSubmitting}
                className="px-6 py-3 text-gray-600 font-semibold rounded-xl hover:bg-gray-100 disabled:opacity-50 transition-all"
              >
                ← Back
              </button>
              <button
                onClick={handleNext}
                disabled={isSubmitting}
                className="font-bold py-4 px-10 rounded-2xl shadow-xl disabled:cursor-not-allowed transition-all flex items-center gap-2"
                style={isSubmitting
                  ? {
                      background: '#e5e7eb',
                      color: '#6b7280',
                    }
                  : {
                      background: 'linear-gradient(135deg, #15803d, #16a34a)',
                      color: '#ffffff',
                    }}
              >
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Submitting...
                  </>
                ) : (
                  <>
                    Complete Assessment ✓
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // PHQ-9 or GAD-7 questions
  const questions = getCurrentQuestions();
  const currentQuestion = questions[currentQuestionIndex];
  const sectionName = section === 'phq9' ? 'Depression Screening (PHQ-9)' : 'Anxiety Screening (GAD-7)';
  const sectionColor = section === 'phq9' ? 'blue' : 'blue';
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-blue-50 to-cyan-50 flex items-center justify-center p-4">
      <div className="max-w-3xl w-full">
        {/* Progress */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-xs font-medium text-gray-600">Overall Progress</span>
            <span className="text-xs font-medium text-blue-600">{Math.round(getTotalProgress())}%</span>
          </div>
          <div className="w-full h-1.5 bg-white rounded-full overflow-hidden shadow-inner">
            <div
              className="h-full bg-gradient-to-r from-blue-600 to-blue-600 transition-all duration-500"
              style={{ width: `${getTotalProgress()}%` }}
            />
          </div>
        </div>

        <div className="bg-white/90 backdrop-blur-xl rounded-3xl shadow-2xl p-6 border border-blue-100">
          {/* Section Header */}
          <div className="mb-5 flex items-center justify-between">
            <span className={`bg-${sectionColor}-100 text-${sectionColor}-700 text-xs font-semibold px-3 py-1.5 rounded-full`}>
              {sectionName}
            </span>
            <span className="text-xs text-gray-600">
              Question {currentQuestionIndex + 1} / {questions.length}
            </span>
          </div>

          {/* Question */}
          <h2 className="text-xl font-bold text-gray-900 mb-2">
            Over the last 2 weeks, how often have you been bothered by:
          </h2>
          <p className="text-lg text-gray-800 mb-6">"{currentQuestion}"</p>

          {/* Answer Options */}
          <div className="space-y-3 mb-6">
            {ANSWER_OPTIONS.map((option) => {
              const isSelected = getCurrentAnswers()[currentQuestionIndex] === option.value;
              return (
                <button
                  key={option.value}
                  onClick={() => setCurrentAnswer(option.value)}
                  className={`group w-full p-4 text-left rounded-xl border-2 transition-all duration-300 transform ${
                    isSelected
                      ? `${option.borderColor} ${option.bgColor} shadow-xl scale-[1.02]`
                      : 'border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50/50 hover:shadow-lg hover:scale-[1.01]'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-full border-2 flex items-center justify-center transition-all duration-300 ${
                        isSelected ? `${option.borderColor} bg-gradient-to-br ${option.color}` : 'border-gray-300 bg-gray-50 group-hover:border-blue-400'
                      }`}>
                        {isSelected ? (
                          <svg className="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        ) : (
                          <span className="text-xl transition-all">{option.emoji}</span>
                        )}
                      </div>
                      <div>
                        <span className="text-base font-bold text-gray-800 block">{option.label}</span>
                        <span className="text-xs text-gray-500">Score: {option.value}/3</span>
                      </div>
                    </div>
                    <div className={`px-3 py-1.5 rounded-lg font-bold text-lg transition-all ${
                      isSelected 
                        ? `bg-gradient-to-r ${option.color} text-white shadow-lg` 
                        : 'bg-gray-100 text-gray-400 group-hover:bg-blue-100 group-hover:text-blue-600'
                    }`}>
                      {option.value}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {error && (
            <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded">
              {error}
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between items-center">
            <button
              onClick={handleBack}
              className="px-5 py-2.5 text-gray-600 font-semibold rounded-xl hover:bg-gray-100 transition-all text-sm"
            >
              ← Back
            </button>
            
            <div className="flex gap-1.5">
              {questions.map((_, idx) => (
                <div
                  key={idx}
                  className={`w-1.5 h-1.5 rounded-full transition-all ${
                    idx < currentQuestionIndex
                      ? 'bg-green-500'
                      : idx === currentQuestionIndex
                      ? 'bg-blue-500 w-5'
                      : 'bg-gray-300'
                  }`}
                />
              ))}
            </div>

            <button
              onClick={handleNext}
              disabled={!canContinue()}
              className="font-bold py-2.5 px-6 rounded-xl shadow-lg disabled:cursor-not-allowed transition-all text-sm"
              style={canContinue()
                ? {
                    background: 'linear-gradient(135deg, var(--accent-700), var(--accent-600))',
                    color: '#ffffff',
                  }
                : {
                    background: '#e5e7eb',
                    color: '#6b7280',
                  }}
            >
              {currentQuestionIndex === questions.length - 1 && section === 'gad7' ? 'Continue →' : 'Next →'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
