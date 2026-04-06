'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { authService } from '@/lib/auth';

const prompts = [
  'What made you smile today?',
  'Who are you thankful for?',
  'What is one good thing that happened?',
];

type FlowerAnswer = {
  id: string;
  question: string;
  answer: string;
  plantedAt: string;
  left: number;
  top: number;
  flower: string;
};

export default function GratitudeGardenPage() {
  const [entries, setEntries] = useState<string[]>(['', '', '']);
  const [flowers, setFlowers] = useState<FlowerAnswer[]>([]);
  const [selectedFlower, setSelectedFlower] = useState<FlowerAnswer | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);

  const getStorageKey = () => {
    const user = authService.getUser();
    return `neurowell_gratitude_garden_${user?.id ?? 'guest'}`;
  };

  useEffect(() => {
    try {
      const storageKey = getStorageKey();
      const stored = localStorage.getItem(storageKey);
      if (stored) {
        const parsedFlowers = JSON.parse(stored) as FlowerAnswer[];
        setFlowers(Array.isArray(parsedFlowers) ? parsedFlowers : []);
      }
    } catch (error) {
      console.error('Failed to load gratitude garden entries', error);
    } finally {
      setIsHydrated(true);
    }
  }, []);

  useEffect(() => {
    if (!isHydrated) return;

    try {
      const storageKey = getStorageKey();
      localStorage.setItem(storageKey, JSON.stringify(flowers.slice(0, 60)));
    } catch (error) {
      console.error('Failed to save gratitude garden entries', error);
    }
  }, [flowers, isHydrated]);

  const plant = () => {
    const valid = entries.map((e) => e.trim());
    if (valid.some((text) => !text)) return;

    const flowerIcons = ['🌸', '🌺', '🌻', '🌷', '🌹', '🌼'];
    const now = new Date().toISOString();
    const newFlowers: FlowerAnswer[] = valid.map((answer, i) => ({
      id: `${Date.now()}-${i}`,
      question: prompts[i],
      answer,
      plantedAt: now,
      left: 8 + Math.floor(Math.random() * 84),
      top: 20 + Math.floor(Math.random() * 68),
      flower: flowerIcons[(flowers.length + i) % flowerIcons.length],
    }));

    setFlowers((prev) => [...newFlowers, ...prev].slice(0, 60));
    setEntries(['', '', '']);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-100 via-cyan-100 to-emerald-100 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <Link href="/games" className="bg-white hover:bg-slate-50 px-4 py-2 rounded-lg border border-slate-200">← Back</Link>
          <h1 className="text-3xl font-bold text-slate-900">🌿 Gratitude Garden</h1>
          <div className="text-sm text-slate-700">Flowers: {flowers.length}</div>
        </div>

        <div className="rounded-3xl border border-emerald-200 bg-gradient-to-b from-emerald-200/65 via-emerald-300/55 to-emerald-500/50 p-5 mb-5 shadow-xl">
          <p className="font-semibold text-slate-800 mb-3">Forest Garden View</p>
          <div className="relative h-[420px] w-full overflow-hidden rounded-2xl border border-emerald-300 bg-gradient-to-b from-cyan-100 via-emerald-100 to-emerald-300">
            <div className="absolute inset-0 pointer-events-none">
              <div className="absolute -top-8 -left-8 h-36 w-36 rounded-full bg-white/40 blur-xl" />
              <div className="absolute top-10 right-8 h-28 w-28 rounded-full bg-cyan-200/50 blur-2xl" />
              <div className="absolute -bottom-8 left-1/3 h-32 w-72 rounded-full bg-emerald-700/20 blur-xl" />
            </div>

            {flowers.length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center text-slate-600 font-medium">
                Plant 3 gratitude answers to grow your first flowers.
              </div>
            )}

            {flowers.map((bloom) => (
              <button
                key={bloom.id}
                type="button"
                className="group absolute -translate-x-1/2 -translate-y-1/2"
                style={{ left: `${bloom.left}%`, top: `${bloom.top}%` }}
                onClick={() => setSelectedFlower(bloom)}
                title={new Date(bloom.plantedAt).toLocaleString()}
              >
                <span className="block text-4xl drop-shadow-sm transition-transform duration-300 group-hover:scale-110">{bloom.flower}</span>
                <span className="pointer-events-none absolute left-1/2 top-full mt-1 -translate-x-1/2 whitespace-nowrap rounded-md bg-slate-900/85 px-2 py-1 text-[11px] text-white opacity-0 transition-opacity group-hover:opacity-100">
                  {new Date(bloom.plantedAt).toLocaleString()}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="rounded-2xl bg-white/80 border border-slate-200 p-6 mb-5">
          <p className="font-semibold text-slate-800 mb-3">Today&apos;s Gratitude (3 Questions)</p>
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
          <button onClick={plant} className="px-5 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-500">Plant Flowers 🌱</button>
        </div>

        {selectedFlower && (
          <div className="fixed inset-0 z-40 bg-slate-900/45 backdrop-blur-sm flex items-center justify-center p-4" onClick={() => setSelectedFlower(null)}>
            <div className="w-full max-w-lg rounded-2xl border border-blue-200 bg-white p-6 shadow-2xl" onClick={(ev) => ev.stopPropagation()}>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-xl font-bold text-slate-900">{selectedFlower.flower} Flower Memory</h2>
                <button className="text-slate-500 hover:text-slate-700" onClick={() => setSelectedFlower(null)}>✕</button>
              </div>
              <p className="text-sm text-slate-500 mb-4">Planted: {new Date(selectedFlower.plantedAt).toLocaleString()}</p>
              <div className="rounded-xl bg-blue-50 border border-blue-100 p-4">
                <p className="text-sm font-semibold text-blue-900 mb-1">Question</p>
                <p className="text-slate-800 mb-3">{selectedFlower.question}</p>
                <p className="text-sm font-semibold text-blue-900 mb-1">Your Answer</p>
                <p className="text-slate-800">{selectedFlower.answer}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
