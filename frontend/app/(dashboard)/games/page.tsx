'use client';

import Link from 'next/link';

const items = [
  {
    title: 'Breathe & Balance',
    desc: 'Guided inhale-hold-exhale cycles with streak and calm score.',
    href: '/games/breathe-balance',
    emoji: '🌬️',
  },
  {
    title: 'Zen Match',
    desc: 'A calming memory match game to improve focus and reduce stress.',
    href: '/games/zen-match',
    emoji: '🧩',
  },
  {
    title: 'Emoji Catcher',
    desc: 'Catch positive emojis and avoid negative ones in a quick reflex game.',
    href: '/games/emoji-catcher',
    emoji: '😊',
  },
  {
    title: 'Bubble Pop Bliss',
    desc: 'Pop floating bubbles at your own pace with calming affirmations.',
    href: '/games/bubble-pop-bliss',
    emoji: '🫧',
  },
  {
    title: 'Gratitude Garden',
    desc: 'Plant flowers by writing gratitude entries and grow your garden.',
    href: '/games/gratitude-garden',
    emoji: '🌷',
  },
  {
    title: 'Focus Flow',
    desc: 'A gentle reaction game to train attention with minimal pressure.',
    href: '/games/focus-flow',
    emoji: '🎯',
  },
  {
    title: 'Exercises',
    desc: 'Quick grounding and relaxation exercises for emotional reset.',
    href: '/games/exercises',
    emoji: '🧘',
  },
  {
    title: 'Music & Videos',
    desc: 'Stress relief playlists and calming video content library.',
    href: '/games/media-library',
    emoji: '🎵',
  },
];

export default function GamesHubPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-teal-50 to-cyan-100 py-10 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="mb-10">
          <h1 className="text-4xl font-extrabold text-slate-900">Games & Exercises</h1>
          <p className="text-slate-600 mt-2">Play calming mini-games and short wellness exercises.</p>
          <div className="mt-4 rounded-2xl border border-teal-200 bg-teal-50 p-4 text-sm text-teal-900">
            <p className="font-semibold mb-2">How To Use This Zone</p>
            <ul className="list-disc pl-5 space-y-1">
              <li>Choose one activity and use it for 3-10 minutes.</li>
              <li>If you feel overwhelmed, switch to Breathing or Exercises first.</li>
              <li>For best results, pause notifications and focus only on the game.</li>
            </ul>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {items.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="group rounded-3xl border border-slate-200 bg-white/80 backdrop-blur p-6 shadow-lg hover:shadow-xl transition"
            >
              <div className="text-4xl mb-3">{item.emoji}</div>
              <h2 className="text-2xl font-bold text-slate-900 group-hover:text-cyan-700 transition">{item.title}</h2>
              <p className="text-slate-600 mt-2">{item.desc}</p>
              <p className="text-cyan-700 font-semibold mt-4">Open →</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
