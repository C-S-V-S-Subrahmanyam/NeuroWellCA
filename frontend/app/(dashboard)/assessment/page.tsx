'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';
import { assessmentService } from '@/lib/assessment';
import Button from '@/components/Button';
import Card from '@/components/Card';
import Loading from '@/components/Loading';

const PHQ9_QUESTIONS = [
  'Little interest or pleasure in doing things',
  'Feeling down, depressed, or hopeless',
  'Trouble falling/staying asleep, sleeping too much',
  'Feeling tired or having little energy',
  'Poor appetite or overeating',
  'Feeling bad about yourself or that you are a failure',
  'Trouble concentrating on things',
  'Moving or speaking slowly or being fidgety/restless',
  'Thoughts that you would be better off dead or hurting yourself',
];

const GAD7_QUESTIONS = [
  'Feeling nervous, anxious, or on edge',
  'Not being able to stop or control worrying',
  'Worrying too much about different things',
  'Trouble relaxing',
  'Being so restless that it is hard to sit still',
  'Becoming easily annoyed or irritable',
  'Feeling afraid as if something awful might happen',
];

const OPTIONS = [
  { value: 0, label: 'Not at all' },
  { value: 1, label: 'Several days' },
  { value: 2, label: 'More than half the days' },
  { value: 3, label: 'Nearly every day' },
];

export default function AssessmentPage() {
  const router = useRouter();
  const [phq9Answers, setPhq9Answers] = useState<number[]>(Array(9).fill(-1));
  const [gad7Answers, setGad7Answers] = useState<number[]>(Array(7).fill(-1));
  const [stressLevel, setStressLevel] = useState(5);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/login');
    } else {
      setIsChecking(false);
    }
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (phq9Answers.includes(-1) || gad7Answers.includes(-1)) {
      setError('Please answer all questions');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await assessmentService.submit({
        phq9_answers: phq9Answers,
        gad7_answers: gad7Answers,
        stress_level: stressLevel,
      });

      // Update user assessment status
      await authService.getCurrentUser();

      router.push('/chat');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit assessment');
    } finally {
      setIsLoading(false);
    }
  };

  if (isChecking) {
    return <Loading />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 py-8 px-4">
      <div className="max-w-3xl mx-auto">
        <Card>
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Mental Health Assessment</h1>
            <p className="text-gray-600">
              Please answer these questions based on how you've been feeling over the past 2 weeks.
            </p>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-8">
            {/* PHQ-9 */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                PHQ-9: Depression Screening
              </h2>
              <div className="space-y-6">
                {PHQ9_QUESTIONS.map((question, index) => (
                  <div key={index} className="p-4 bg-gray-50 rounded-lg">
                    <p className="font-medium text-gray-800 mb-3">
                      {index + 1}. {question}
                    </p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      {OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => {
                            const newAnswers = [...phq9Answers];
                            newAnswers[index] = option.value;
                            setPhq9Answers(newAnswers);
                          }}
                          className={`p-2 rounded-lg border text-sm ${
                            phq9Answers[index] === option.value
                              ? 'bg-blue-600 text-white border-blue-600'
                              : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400'
                          }`}
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* GAD-7 */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                GAD-7: Anxiety Screening
              </h2>
              <div className="space-y-6">
                {GAD7_QUESTIONS.map((question, index) => (
                  <div key={index} className="p-4 bg-gray-50 rounded-lg">
                    <p className="font-medium text-gray-800 mb-3">
                      {index + 1}. {question}
                    </p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                      {OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => {
                            const newAnswers = [...gad7Answers];
                            newAnswers[index] = option.value;
                            setGad7Answers(newAnswers);
                          }}
                          className={`p-2 rounded-lg border text-sm ${
                            gad7Answers[index] === option.value
                              ? 'bg-blue-600 text-white border-blue-600'
                              : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400'
                          }`}
                        >
                          {option.label}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Stress Level */}
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Current Stress Level
              </h2>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="font-medium text-gray-800 mb-3">
                  On a scale of 0 to 10, how stressed do you feel?
                </p>
                <div className="flex items-center gap-4">
                  <span className="text-sm text-gray-600">No stress</span>
                  <input
                    type="range"
                    min="0"
                    max="10"
                    value={stressLevel}
                    onChange={(e) => setStressLevel(parseInt(e.target.value))}
                    className="flex-1"
                  />
                  <span className="text-sm text-gray-600">Extreme stress</span>
                </div>
                <div className="text-center mt-2">
                  <span className="text-2xl font-bold text-blue-600">{stressLevel}/10</span>
                </div>
              </div>
            </div>

            <Button type="submit" isLoading={isLoading} className="w-full">
              Submit Assessment
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
}
