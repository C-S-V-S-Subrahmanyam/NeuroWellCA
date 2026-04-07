'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';

type Phase = 'Inhale' | 'Hold' | 'Exhale';
const phaseSeconds: Record<Phase, number> = { Inhale: 4, Hold: 4, Exhale: 6 };
const phaseOrder: Phase[] = ['Inhale', 'Hold', 'Exhale'];

export default function BreathingRhythmPage() {
  const [phase, setPhase] = useState<Phase>('Inhale');
  const [secondsLeft, setSecondsLeft] = useState(phaseSeconds.Inhale);
  const [round, setRound] = useState(1);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (!running) return;
    const timer = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev > 1) return prev - 1;
        const currentIndex = phaseOrder.indexOf(phase);
        const nextPhase = phaseOrder[(currentIndex + 1) % phaseOrder.length];
        setPhase(nextPhase);
        if (nextPhase === 'Inhale') setRound((r) => r + 1);
        return phaseSeconds[nextPhase];
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [running, phase]);

  const scaleClass = useMemo(() => {
    if (phase === 'Inhale') return 'scale-110';
    if (phase === 'Hold') return 'scale-100';
    return 'scale-90';
  }, [phase]);

  const reset = () => {
    setRunning(false);
    setPhase('Inhale');
    setSecondsLeft(phaseSeconds.Inhale);
    setRound(1);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-900 via-teal-900 to-slate-900 text-white p-6">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <Link href="/games" className="bg-white/10 hover:bg-white/20 px-4 py-2 rounded-lg">← Back</Link>
          <h1 className="text-3xl font-bold">🌬️ Breathing Rhythm</h1>
          <div className="w-20" />
        </div>

        <div className="rounded-3xl bg-white/10 border border-white/20 p-10 text-center">
          <p className="text-cyan-100 text-sm uppercase tracking-[0.2em] mb-2">Round {round}</p>
          <p className="text-4xl font-extrabold mb-4">{phase}</p>
          <p className="text-xl text-cyan-100 mb-8">{secondsLeft}s</p>

          <div className="flex justify-center mb-10">
            <div className={`w-40 h-40 rounded-full bg-gradient-to-br from-teal-300 to-cyan-500 transition-transform duration-1000 ${scaleClass} shadow-[0_0_60px_rgba(45,212,191,0.45)]`} />
          </div>

          <div className="flex justify-center gap-3">
            {!running ? (
              <button className="px-6 py-3 rounded-xl bg-teal-500 hover:bg-teal-400 font-semibold" onClick={() => setRunning(true)}>Start</button>
            ) : (
              <button className="px-6 py-3 rounded-xl bg-amber-500 hover:bg-amber-400 font-semibold" onClick={() => setRunning(false)}>Pause</button>
            )}
            <button className="px-6 py-3 rounded-xl bg-white/20 hover:bg-white/30 font-semibold" onClick={reset}>Reset</button>
          </div>
        </div>
      </div>
    </div>
  );
}
