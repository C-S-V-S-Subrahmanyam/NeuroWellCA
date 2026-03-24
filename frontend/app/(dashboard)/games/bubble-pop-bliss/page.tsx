'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

type Bubble = { id: number; x: number; y: number; size: number };
const affirmations = ['You are enough', 'This too shall pass', "You're doing your best", 'Be kind to yourself'];

export default function BubblePopBlissPage() {
  const [bubbles, setBubbles] = useState<Bubble[]>([]);
  const [popped, setPopped] = useState(0);
  const [text, setText] = useState('');

  useEffect(() => {
    const timer = setInterval(() => {
      setBubbles((prev) => [
        ...prev.map((b) => ({ ...b, y: b.y - 4 })).filter((b) => b.y > -15),
        { id: Date.now() + Math.random(), x: Math.random() * 90, y: 100, size: 50 + Math.random() * 40 },
      ].slice(-18));
    }, 500);
    return () => clearInterval(timer);
  }, []);

  const popBubble = (id: number) => {
    setBubbles((prev) => prev.filter((b) => b.id !== id));
    setPopped((p) => p + 1);
    setText(affirmations[Math.floor(Math.random() * affirmations.length)]);
    setTimeout(() => setText(''), 1600);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-cyan-100 via-blue-100 to-indigo-200 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <Link href="/games" className="bg-white/70 hover:bg-white px-4 py-2 rounded-lg border border-slate-200">← Back</Link>
          <h1 className="text-3xl font-bold text-slate-900">🫧 Bubble Pop Bliss</h1>
          <div className="text-slate-700 font-semibold">Popped: {popped}</div>
        </div>

        <div className="relative h-[70vh] rounded-3xl bg-white/60 border border-white/80 overflow-hidden">
          {bubbles.map((b) => (
            <button
              key={b.id}
              onClick={() => popBubble(b.id)}
              className="absolute rounded-full bg-gradient-to-br from-cyan-200/80 to-blue-300/80 border border-cyan-300/80 shadow"
              style={{ left: `${b.x}%`, top: `${b.y}%`, width: `${b.size}px`, height: `${b.size}px` }}
            />
          ))}
          {text && <p className="absolute left-1/2 -translate-x-1/2 top-8 text-xl font-semibold text-indigo-700">{text}</p>}
        </div>
      </div>
    </div>
  );
}
