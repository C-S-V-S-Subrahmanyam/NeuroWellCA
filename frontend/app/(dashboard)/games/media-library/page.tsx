'use client';

import Link from 'next/link';

const musicPlaylists = [
  {
    title: 'Deep Focus Session',
    intent: 'Study, coding, writing, mindful work',
    duration: '30-60 min',
    tips: ['Use low volume', 'Pair with Focus Flow game'],
  },
  {
    title: 'Anxiety De-escalation',
    intent: 'Reduce panic symptoms, steady breathing',
    duration: '10-20 min',
    tips: ['Inhale 4 sec, exhale 6 sec', 'Sit with grounded posture'],
  },
  {
    title: 'Mood Lift & Energy Reset',
    intent: 'Low mood, fatigue, emotional heaviness',
    duration: '10-15 min',
    tips: ['Play while walking slowly', 'Sip water during listening'],
  },
  {
    title: 'Sleep Wind-Down',
    intent: 'Night routine and racing thoughts',
    duration: '20-45 min',
    tips: ['Dim lights', 'Avoid scrolling'],
  },
];

const videoModules = [
  { title: '5-Minute Box Breathing', type: 'Breathing' },
  { title: 'Gentle Neck and Shoulder Release', type: 'Stretching' },
  { title: 'Grounding Through 5-4-3-2-1', type: 'Psychoeducation' },
  { title: 'Body Scan for Sleep', type: 'Meditation' },
  { title: 'Nature Calm Stream', type: 'Ambient' },
];

export default function MediaLibraryPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-950 to-indigo-950 text-white p-6">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <Link href="/games" className="bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg">← Back</Link>
          <h1 className="text-3xl font-bold">🎵 Music & Videos</h1>
          <div className="w-20" />
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          <div className="rounded-2xl bg-white/10 border border-white/20 p-5 space-y-4">
            <h2 className="text-xl font-semibold">Stress Relief Music Plans</h2>
            <p className="text-sm text-slate-200">Choose by intent, not random scrolling.</p>
            <div className="space-y-3 text-sm">
              {musicPlaylists.map((m) => (
                <div key={m.title} className="p-3 rounded-lg bg-white/10 border border-white/10">
                  <p className="font-semibold">{m.title}</p>
                  <p className="text-slate-200 mt-1">{m.intent}</p>
                  <p className="text-xs text-cyan-200 mt-1">Recommended: {m.duration}</p>
                  <p className="text-xs text-slate-300 mt-1">{m.tips.join(' · ')}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl bg-white/10 border border-white/20 p-5">
            <h2 className="text-xl font-semibold mb-3">Guided Videos</h2>
            <div className="space-y-3 text-sm mb-4">
              {videoModules.map((v) => (
                <div key={v.title} className="p-3 rounded-lg bg-white/10 border border-white/10 flex items-center justify-between">
                  <span>{v.title}</span>
                  <span className="text-xs text-cyan-200">{v.type}</span>
                </div>
              ))}
            </div>
            <p className="text-sm text-slate-300 mb-2">Embedded calming stream:</p>
            <div className="aspect-video rounded-lg overflow-hidden border border-white/20">
              <iframe
                title="Calming Nature Stream"
                className="w-full h-full"
                src="https://www.youtube.com/embed/jfKfPfyJRdk"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
              />
            </div>
            <div className="mt-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-300/20 text-sm text-emerald-100">
              If your stress is high, start with 2 minutes of breathing before playing any other game.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
