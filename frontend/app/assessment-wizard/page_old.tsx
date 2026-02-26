'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';

interface AssessmentQuestion {
  id: string;
  question: string;
  type: 'scale' | 'choice' | 'text';
  options?: { value: number; label: string }[];
  choices?: string[];
}

const ASSESSMENT_QUESTIONS: AssessmentQuestion[] = [
  {
    id: 'mood',
    question: 'How would you rate your overall mood this week?',
    type: 'scale',
    options: [
      { value: 0, label: 'Very Poor' },
      { value: 1, label: 'Poor' },
      { value: 2, label: 'Fair' },
      { value: 3, label: 'Good' },
      { value: 4, label: 'Excellent' }
    ]
  },
  {
    id: 'sleep',
    question: 'How many hours of sleep do you typically get per night?',
    type: 'choice',
    choices: ['Less than 4 hours', '4-6 hours', '6-8 hours', '8-10 hours', 'More than 10 hours']
  },
  {
    id: 'stress',
    question: 'On a scale of 0-10, how stressed have you felt lately?',
    type: 'scale',
    options: [
      { value: 0, label: '0 - Not stressed' },
      { value: 2, label: '2' },
      { value: 4, label: '4' },
      { value: 6, label: '6' },
      { value: 8, label: '8' },
      { value: 10, label: '10 - Extremely stressed' }
    ]
  },
  {
    id: 'interests',
    question: 'Have you lost interest in activities you usually enjoy?',
    type: 'choice',
    choices: ['Not at all', 'Somewhat', 'Quite a bit', 'Very much']
  },
  {
    id: 'energy',
    question: 'How would you describe your energy levels recently?',
    type: 'choice',
    choices: ['Very low', 'Low', 'Moderate', 'High', 'Very high']
  },
  {
    id: 'concerns',
    question: 'What areas would you like support with? (Optional)',
    type: 'text'
  }
];

export default function StepAssessmentPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const currentQuestion = ASSESSMENT_QUESTIONS[currentStep];
  const progress = ((currentStep + 1) / ASSESSMENT_QUESTIONS.length) * 100;

  const handleAnswer = (value: any) => {
    setAnswers({ ...answers, [currentQuestion.id]: value });
  };

  const handleNext = () => {
    if (currentStep < ASSESSMENT_QUESTIONS.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleSubmit();
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    try {
      // Submit assessment to backend
      // For now, just redirect to chat
      setTimeout(() => {
        router.push('/chat');
      }, 1000);
    } catch (error) {
      console.error('Failed to submit assessment:', error);
      setIsSubmitting(false);
    }
  };

  const isCurrentAnswered = () => {
    return currentQuestion.id in answers && answers[currentQuestion.id] !== null && answers[currentQuestion.id] !== '';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-sky-50 to-cyan-50 flex items-center justify-center p-6">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex justify-center mb-4">
            <Image src="/logo.PNG" alt="NeuroWell Logo" width={60} height={60} priority />
          </div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-700 to-blue-500 bg-clip-text text-transparent mb-2">
            Initial Assessment
          </h1>
          <p className="text-gray-600">Help us understand how we can best support you</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-600">
              Question {currentStep + 1} of {ASSESSMENT_QUESTIONS.length}
            </span>
            <span className="text-sm font-medium text-blue-600">
              {Math.round(progress)}% Complete
            </span>
          </div>
          <div className="w-full h-3 bg-white rounded-full overflow-hidden shadow-inner">
            <div 
              className="h-full bg-gradient-to-r from-blue-600 to-blue-400 transition-all duration-500 ease-out rounded-full"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Question Card */}
        <div className="glass-effect p-8 rounded-3xl shadow-2xl mb-6">
          <h2 className="text-2xl font-semibold text-gray-800 mb-8">
            {currentQuestion.question}
          </h2>

          <div className="space-y-4">
            {currentQuestion.type === 'scale' && currentQuestion.options && (
              <div className="space-y-3">
                {currentQuestion.options.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => handleAnswer(option.value)}
                    className={`w-full p-4 text-left rounded-xl border-2 transition-all duration-200 ${
                      answers[currentQuestion.id] === option.value
                        ? 'border-blue-500 bg-blue-50 shadow-md'
                        : 'border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-800">{option.label}</span>
                      <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                        answers[currentQuestion.id] === option.value
                          ? 'border-blue-500 bg-blue-500'
                          : 'border-gray-300'
                      }`}>
                        {answers[currentQuestion.id] === option.value && (
                          <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        )}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}

            {currentQuestion.type === 'choice' && currentQuestion.choices && (
              <div className="space-y-3">
                {currentQuestion.choices.map((choice, index) => (
                  <button
                    key={index}
                    onClick={() => handleAnswer(choice)}
                    className={`w-full p-4 text-left rounded-xl border-2 transition-all duration-200 ${
                      answers[currentQuestion.id] === choice
                        ? 'border-blue-500 bg-blue-50 shadow-md'
                        : 'border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-800">{choice}</span>
                      <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                        answers[currentQuestion.id] === choice
                          ? 'border-blue-500 bg-blue-500'
                          : 'border-gray-300'
                      }`}>
                        {answers[currentQuestion.id] === choice && (
                          <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        )}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}

            {currentQuestion.type === 'text' && (
              <textarea
                value={answers[currentQuestion.id] || ''}
                onChange={(e) => handleAnswer(e.target.value)}
                placeholder="Type your answer here (optional)..."
                className="w-full p-4 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-200 outline-none resize-none transition-all"
                rows={4}
              />
            )}
          </div>
        </div>

        {/* Navigation Buttons */}
        <div className="flex justify-between items-center">
          <button
            onClick={handleBack}
            disabled={currentStep === 0}
            className="px-6 py-3 text-gray-600 font-semibold rounded-xl hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            ← Back
          </button>

          <div className="text-sm text-gray-500">
            Step {currentStep + 1} / {ASSESSMENT_QUESTIONS.length}
          </div>

          <button
            onClick={handleNext}
            disabled={!isCurrentAnswered() && currentQuestion.type !== 'text'}
            className="btn-primary px-8 py-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <span className="flex items-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Submitting...
              </span>
            ) : currentStep === ASSESSMENT_QUESTIONS.length - 1 ? (
              'Complete Assessment →'
            ) : (
              'Next →'
            )}
          </button>
        </div>

        {/* Skip Option */}
        <div className="text-center mt-6">
          <button
            onClick={() => router.push('/chat')}
            className="text-sm text-gray-500 hover:text-gray-700 underline"
          >
            Skip for now
          </button>
        </div>
      </div>
    </div>
  );
}
