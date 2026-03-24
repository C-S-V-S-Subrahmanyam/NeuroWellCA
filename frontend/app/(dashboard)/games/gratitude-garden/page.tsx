'use client';

import Link from 'next/link';
import { useState } from 'react';

const prompts = [
  'What made you smile today?',
  'Who are you thankful for?',
  'What is one good thing that happened?',
  'What do you like about yourself today?',
];

export default function GratitudeGardenPage() {
  const [entries, setEntries] = useState<string[]>(['', '', '']);
  const [garden, setGarden] = useState<string[]>([]);
  const [history, setHistory] = useState<string[][]>([]);

  const plant = () => {
    const valid = entries.map((e) => e.trim()).filter(Boolean);
    if (valid.length < 3) return;
    const flowers = ['🌸', '🌺', '🌻', '🌷', '🌹', '🌼', '💐'];
    const newBlooms = valid.map((_, i) => flowers[(garden.length + i) % flowers.length]);
    setGarden((prev) => [...prev, ...newBlooms]);
    setHistory((prev) => [valid, ...prev].slice(0, 14));
    setEntries(['', '', '']);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-lime-50 to-teal-100 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <Link href="/games" className="bg-white hover:bg-slate-50 px-4 py-2 rounded-lg border border-slate-200">← Back</Link>
          <h1 className="text-3xl font-bold text-slate-900">🌷 Gratitude Garden</h1>
          <div className="text-sm text-slate-700">Blooms: {garden.length}</div>
        </div>

        <div className="rounded-2xl bg-white/80 border border-slate-200 p-6 mb-5">
          <p className="font-semibold text-slate-800 mb-2">Your Garden</p>
          <div className="text-3xl leading-loose min-h-16">{garden.join(' ') || 'Plant your first gratitude flowers today.'}</div>
        </div>

        <div className="rounded-2xl bg-white/80 border border-slate-200 p-6 mb-5">
          <p className="font-semibold text-slate-800 mb-3">Today\'s Gratitude</p>
          {entries.map((e, i) => (
            <input
              key={i}
              value={e}
              onChange={(ev) => {
                const next = [...entries];
                next[i] = ev.target.value;
                setEntries(next);
              }}
              placeholder={prompts[i % prompts.length]}
              className="w-full mb-3 px-3 py-2 rounded-lg border border-slate-300"
            />
          ))}
          <button onClick={plant} className="px-5 py-2 rounded-lg bg-emerald-600 text-white hover:bg-emerald-500">Plant Flowers 🌱</button>
        </div>

        <div className="rounded-2xl bg-white/80 border border-slate-200 p-6">
          <p className="font-semibold text-slate-800 mb-2">Past Entries 📖</p>
          {history.length === 0 ? <p className="text-slate-500 text-sm">No past entries yet.</p> : (
            <div className="space-y-3">
              {history.map((h, idx) => (
                <div key={idx} className="rounded-lg bg-slate-50 p-3 text-sm text-slate-700">
                  {h.map((line, li) => <p key={li}>• {line}</p>)}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
