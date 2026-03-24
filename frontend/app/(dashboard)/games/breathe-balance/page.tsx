'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

type Phase = 'Inhale' | 'Hold' | 'Exhale';
const phaseOrder: Phase[] = ['Inhale', 'Hold', 'Exhale'];
const phaseSeconds: Record<Phase, number> = { Inhale: 4, Hold: 4, Exhale: 6 };
const backgrounds = ['Beach', 'Forest', 'Space'];

export default function BreatheBalancePage() {
  const [phase, setPhase] = useState<Phase>('Inhale');
  const [secondsLeft, setSecondsLeft] = useState(phaseSeconds.Inhale);
  const [cycle, setCycle] = useState(1);
  const [running, setRunning] = useState(false);
  const [streak, setStreak] = useState<number>(() => Number(localStorage.getItem('bb_streak') || '1'));
  const [calmScore, setCalmScore] = useState(100);
  const [bg, setBg] = useState(0);

  useEffect(() => {
    localStorage.setItem('bb_streak', String(streak));
  }, [streak]);

  useEffect(() => {
    if (!running || cycle > 5) return;
    const t = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev > 1) return prev - 1;
        const idx = phaseOrder.indexOf(phase);
        const next = phaseOrder[(idx + 1) % phaseOrder.length];
        setPhase(next);
        if (next === 'Inhale') {
          setCycle((c) => c + 1);
          setCalmScore((s) => Math.max(0, s - Math.floor(Math.random() * 3)));
        }
        return phaseSeconds[next];
      });
    }, 1000);
    return () => clearInterval(t);
  }, [phase, running, cycle]);

  useEffect(() => {
    if (cycle === 6) {
      setRunning(false);
      setStreak((s) => s + 1);
      setBg((b) => Math.min(backgrounds.length - 1, b + 1));
    }
  }, [cycle]);

  const circleStyle = useMemo(() => {
    if (phase === 'Inhale') return 'scale-110 bg-blue-500';
    if (phase === 'Hold') return 'scale-100 bg-violet-500 animate-pulse';
    return 'scale-90 bg-emerald-500';
  }, [phase]);

  const reset = () => {
    setRunning(false);
    setPhase('Inhale');
    setSecondsLeft(4);
    setCycle(1);
    setCalmScore(100);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-900 via-indigo-900 to-slate-900 text-white p-6">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <Link href="/games" className="bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg">← Back</Link>
          <h1 className="text-3xl font-bold">🌬️ Breathe & Balance</h1>
          <div className="w-20" />
        </div>

        <div className="rounded-3xl border border-white/20 bg-white/10 p-8 text-center">
          <p className="text-sm text-sky-100">Background Unlocked: {backgrounds[bg]}</p>
          <div className="my-8 flex justify-center">
            <div className={`w-48 h-48 rounded-full transition-all duration-1000 ${circleStyle}`} />
          </div>
          <h2 className="text-3xl font-bold">{phase}... {secondsLeft}</h2>
          <p className="text-sky-100 mt-3">Progress: {Math.min(cycle, 5)}/5 cycles</p>
          <div className="mt-6 grid grid-cols-2 gap-4 text-sm">
            <div className="bg-white/10 rounded-xl p-3">Streak: {streak} days 🔥</div>
            <div className="bg-white/10 rounded-xl p-3">Calm Score: {calmScore}/100</div>
          </div>
          <div className="mt-6 flex justify-center gap-3">
            {!running ? (
              <button className="px-5 py-3 rounded-xl bg-cyan-500 hover:bg-cyan-400 font-semibold" onClick={() => setRunning(true)}>Start</button>
            ) : (
              <button className="px-5 py-3 rounded-xl bg-amber-500 hover:bg-amber-400 font-semibold" onClick={() => setRunning(false)}>Pause</button>
            )}
            <button className="px-5 py-3 rounded-xl bg-white/20 hover:bg-white/30 font-semibold" onClick={reset}>Reset</button>
          </div>
        </div>
      </div>
    </div>
  );
}
