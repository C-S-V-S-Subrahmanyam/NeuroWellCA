'use client';

import { useState } from 'react';
import Link from 'next/link';

const exercises = [
  {
    title: '4-7-8 Breathing',
    body: 'Inhale 4s, hold 7s, exhale 8s. Repeat 4 rounds to reduce anxiety and support sleep.',
  },
  {
    title: 'Box Breathing (4-4-4-4)',
    body: 'Inhale 4s, hold 4s, exhale 4s, hold 4s. Good for fast calm before exams or meetings.',
  },
  {
    title: 'Progressive Muscle Relaxation',
    body: 'Tense each muscle group for 5 seconds and release for 10 seconds from feet to face.',
  },
  {
    title: '5-4-3-2-1 Grounding',
    body: 'Name 5 things you see, 4 things you feel, 3 things you hear, 2 things you smell, and 1 thing you taste.',
  },
  {
    title: 'Progressive Muscle Release',
    body: 'Tense each body area for 5 seconds, then release for 10 seconds: hands, shoulders, jaw, legs, feet.',
  },
  {
    title: 'Guided Beach Visualization',
    body: 'Close eyes and imagine waves, warm sand, and slow breathing for 5-7 minutes.',
  },
  {
    title: 'Body Scan Meditation',
    body: 'Move awareness from feet to head, noticing sensations without judging them.',
  },
  {
    title: 'Thought Defusion',
    body: 'Say: "I am having the thought that..." before your worry. Repeat slowly and notice distance from the thought.',
  },
];

export default function ExercisesPage() {
  const [done, setDone] = useState<Record<number, boolean>>({});

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-100 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <Link href="/games" className="bg-white hover:bg-slate-50 px-4 py-2 rounded-lg border border-slate-200">← Back</Link>
          <h1 className="text-3xl font-bold text-slate-900">🧘 Exercises</h1>
          <div className="w-20" />
        </div>

        <div className="grid gap-4">
          {exercises.map((ex, idx) => (
            <div key={ex.title} className="rounded-2xl bg-white/80 border border-slate-200 p-5 shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h2 className="text-xl font-semibold text-slate-900">{ex.title}</h2>
                  <p className="text-slate-700 mt-2">{ex.body}</p>
                </div>
                <button
                  className={`px-3 py-2 rounded-lg text-sm font-semibold ${done[idx] ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}`}
                  onClick={() => setDone((prev) => ({ ...prev, [idx]: !prev[idx] }))}
                >
                  {done[idx] ? 'Completed' : 'Mark done'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
