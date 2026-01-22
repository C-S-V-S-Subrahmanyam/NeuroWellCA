'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authService } from '@/lib/auth';
import Image from 'next/image';

export default function HomePage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-purple-50 to-pink-100">
      {/* Navigation */}
      <nav className="glass-effect fixed w-full top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-3">
              <Image src="/logo.png" alt="NeuroWell Logo" width={50} height={50} />
              <span className="text-2xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                NeuroWell
              </span>
            </div>
            <div className="flex space-x-4">
              <button
                onClick={() => router.push('/login')}
                className="px-6 py-2 text-indigo-600 font-semibold hover:bg-indigo-50 rounded-lg transition-all"
              >
                Login
              </button>
              <button
                onClick={() => router.push('/register')}
                className="btn-primary"
              >
                Get Started
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="pt-32 pb-20 px-6">
        <div className="max-w-7xl mx-auto text-center">
          <div className="mb-8 inline-block">
            <div className="glass-effect px-6 py-3 rounded-full">
              <span className="text-indigo-600 font-semibold">🧠 AI-Powered Mental Health Support</span>
            </div>
          </div>
          
          <h1 className="text-6xl md:text-7xl font-bold mb-6 leading-tight">
            <span className="bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">
              Your Mental Health
            </span>
            <br />
            <span className="text-gray-900">Companion</span>
          </h1>
          
          <p className="text-xl text-gray-600 mb-12 max-w-3xl mx-auto leading-relaxed">
            Experience compassionate, AI-driven mental health support available 24/7. 
            Take scientifically-backed assessments, chat with our AI counselor, and track your wellness journey.
          </p>

          <div className="flex justify-center space-x-6">
            <button
              onClick={() => router.push('/register')}
              className="btn-primary text-lg px-10 py-4"
            >
              Start Your Journey →
            </button>
            <button
              onClick={() => router.push('/login')}
              className="btn-secondary text-lg px-10 py-4"
            >
              Sign In
            </button>
          </div>

          {/* Stats */}
          <div className="mt-20 grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="glass-effect p-6 rounded-2xl card-hover">
              <div className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent mb-2">
                24/7
              </div>
              <div className="text-gray-600">Always Available Support</div>
            </div>
            <div className="glass-effect p-6 rounded-2xl card-hover">
              <div className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-2">
                100%
              </div>
              <div className="text-gray-600">Confidential & Secure</div>
            </div>
            <div className="glass-effect p-6 rounded-2xl card-hover">
              <div className="text-4xl font-bold bg-gradient-to-r from-pink-600 to-rose-600 bg-clip-text text-transparent mb-2">
                AI
              </div>
              <div className="text-gray-600">Powered Insights</div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Everything You Need for Mental Wellness
            </h2>
            <p className="text-xl text-gray-600">
              Comprehensive tools designed to support your mental health journey
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {/* Feature 1 - AI Counseling Chat */}
            <div className="glass-effect p-8 rounded-3xl card-hover">
              <div style={{ width: '4rem', height: '4rem', background: 'linear-gradient(135deg, #4f46e5, #7c3aed)', borderRadius: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.5rem', boxShadow: '0 10px 15px -3px rgba(79, 70, 229, 0.3)' }}>
                <span style={{ fontSize: '1.875rem' }}>💬</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">AI Counseling Chat</h3>
              <p className="text-gray-600 leading-relaxed mb-4">
                Chat with our empathetic AI counselor trained in cognitive behavioral therapy. Available 24/7 for judgment-free support.
              </p>
              <ul className="space-y-2">
                <li className="flex items-center text-gray-700 text-sm">
                  <span className="text-green-500 mr-2">✓</span> Real-time empathetic responses
                </li>
                <li className="flex items-center text-gray-700 text-sm">
                  <span className="text-green-500 mr-2">✓</span> Crisis detection & alerts
                </li>
                <li className="flex items-center text-gray-700 text-sm">
                  <span className="text-green-500 mr-2">✓</span> Session history tracking
                </li>
              </ul>
            </div>

            {/* Feature 2 - Mental Health Assessment */}
            <div className="glass-effect p-8 rounded-3xl card-hover">
              <div style={{ width: '4rem', height: '4rem', background: 'linear-gradient(135deg, #7c3aed, #ec4899)', borderRadius: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.5rem', boxShadow: '0 10px 15px -3px rgba(124, 58, 237, 0.3)' }}>
                <span style={{ fontSize: '1.875rem' }}>📊</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Mental Health Assessments</h3>
              <p className="text-gray-600 leading-relaxed mb-4">
                Take standardized PHQ-9 and GAD-7 assessments to understand your mental health with personalized insights.
              </p>
              <ul className="space-y-2">
                <li className="flex items-center text-gray-700 text-sm">
                  <span className="text-green-500 mr-2">✓</span> Clinical-grade PHQ-9 & GAD-7
                </li>
                <li className="flex items-center text-gray-700 text-sm">
                  <span className="text-green-500 mr-2">✓</span> Custom stress scale
                </li>
                <li className="flex items-center text-gray-700 text-sm">
                  <span className="text-green-500 mr-2">✓</span> Progress tracking over time
                </li>
              </ul>
            </div>

            {/* Feature 3 - Wellness Dashboard */}
            <div className="glass-effect p-8 rounded-3xl card-hover">
              <div style={{ width: '4rem', height: '4rem', background: 'linear-gradient(135deg, #ec4899, #f43f5e)', borderRadius: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.5rem', boxShadow: '0 10px 15px -3px rgba(236, 72, 153, 0.3)' }}>
                <span style={{ fontSize: '1.875rem' }}>📈</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Wellness Dashboard</h3>
              <p className="text-gray-600 leading-relaxed mb-4">
                Visualize your mental health journey with comprehensive analytics, trends, and personalized recommendations.
              </p>
              <ul className="space-y-2">
                <li className="flex items-center text-gray-700 text-sm">
                  <span className="text-green-500 mr-2">✓</span> Mood & score visualization
                </li>
                <li className="flex items-center text-gray-700 text-sm">
                  <span className="text-green-500 mr-2">✓</span> Trend analysis & insights
                </li>
                <li className="flex items-center text-gray-700 text-sm">
                  <span className="text-green-500 mr-2">✓</span> Timeline history view
                </li>
              </ul>
            </div>

            {/* Feature 4 - Guardian Alerts */}
            <div className="glass-effect p-8 rounded-3xl card-hover">
              <div style={{ width: '4rem', height: '4rem', background: 'linear-gradient(135deg, #f43f5e, #fb923c)', borderRadius: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.5rem', boxShadow: '0 10px 15px -3px rgba(244, 63, 94, 0.3)' }}>
                <span style={{ fontSize: '1.875rem' }}>📱</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Guardian WhatsApp Alerts</h3>
              <p className="text-gray-600 leading-relaxed mb-4">
                Automatic notifications sent to trusted guardians when high-risk mental health conditions are detected.
              </p>
              <ul className="space-y-2">
                <li className="flex items-center text-gray-700 text-sm">
                  <span className="text-green-500 mr-2">✓</span> Instant WhatsApp alerts
                </li>
                <li className="flex items-center text-gray-700 text-sm">
                  <span className="text-green-500 mr-2">✓</span> Risk level detection
                </li>
                <li className="flex items-center text-gray-700 text-sm">
                  <span className="text-green-500 mr-2">✓</span> Emergency resource links
                </li>
              </ul>
            </div>

            {/* Feature 5 - Therapeutic Games */}
            <div className="glass-effect p-8 rounded-3xl card-hover">
              <div style={{ width: '4rem', height: '4rem', background: 'linear-gradient(135deg, #fb923c, #fbbf24)', borderRadius: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.5rem', boxShadow: '0 10px 15px -3px rgba(251, 146, 60, 0.3)' }}>
                <span style={{ fontSize: '1.875rem' }}>🎮</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Stress Relief Games</h3>
              <p className="text-gray-600 leading-relaxed mb-4">
                5 therapeutic mini-games designed to reduce stress, improve focus, and promote mindfulness through play.
              </p>
              <ul className="space-y-2">
                <li className="flex items-center text-gray-700 text-sm">
                  <span className="text-green-500 mr-2">✓</span> Breathing exercises game
                </li>
                <li className="flex items-center text-gray-700 text-sm">
                  <span className="text-green-500 mr-2">✓</span> Mindfulness puzzles
                </li>
                <li className="flex items-center text-gray-700 text-sm">
                  <span className="text-green-500 mr-2">✓</span> Relaxation activities
                </li>
              </ul>
            </div>

            {/* Feature 6 - Wellness Resources */}
            <div className="glass-effect p-8 rounded-3xl card-hover">
              <div style={{ width: '4rem', height: '4rem', background: 'linear-gradient(135deg, #fbbf24, #10b981)', borderRadius: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1.5rem', boxShadow: '0 10px 15px -3px rgba(251, 191, 36, 0.3)' }}>
                <span style={{ fontSize: '1.875rem' }}>🎵</span>
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">Relaxation Media Library</h3>
              <p className="text-gray-600 leading-relaxed mb-4">
                Curated collection of stress-relief music, guided meditation videos, and calming nature sounds.
              </p>
              <ul className="space-y-2">
                <li className="flex items-center text-gray-700 text-sm">
                  <span className="text-green-500 mr-2">✓</span> Stress relief music playlists
                </li>
                <li className="flex items-center text-gray-700 text-sm">
                  <span className="text-green-500 mr-2">✓</span> Guided meditation videos
                </li>
                <li className="flex items-center text-gray-700 text-sm">
                  <span className="text-green-500 mr-2">✓</span> Breathing exercise tutorials
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-20 px-6">
        <div className="max-w-4xl mx-auto glass-effect p-12 rounded-3xl text-center">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Ready to Start Your Wellness Journey?
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Join thousands who have taken the first step towards better mental health
          </p>
          <button
            onClick={() => router.push('/register')}
            className="btn-primary text-lg px-12 py-4"
          >
            Get Started for Free →
          </button>
          <p className="text-sm text-gray-500 mt-4">
            No credit card required • 100% confidential • HIPAA compliant
          </p>
        </div>
      </div>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-gray-200">
        <div className="max-w-7xl mx-auto text-center">
          <div className="flex items-center justify-center space-x-3 mb-4">
            <Image src="/logo.png" alt="NeuroWell" width={40} height={40} />
            <span className="text-xl font-bold text-gray-900">NeuroWell</span>
          </div>
          <p className="text-gray-600 mb-4">
            AI-powered mental health support • Available 24/7 • Completely confidential
          </p>
          <p className="text-sm text-gray-500">
            © 2026 NeuroWell. If you're in crisis, please call 988 (Suicide & Crisis Lifeline)
          </p>
        </div>
      </footer>
    </div>
  );
}
