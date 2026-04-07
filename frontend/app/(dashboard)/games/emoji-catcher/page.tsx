'use client';

import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';

type Item = {
  id: number;
  emoji: string;
  x: number;
  y: number;
  speed: number;
  good: boolean;
};

const GOOD = ['😊', '🌟', '💚', '✨'];
const BAD = ['😢', '💔', '⚡'];

export default function EmojiCatcherPage() {
  const [items, setItems] = useState<Item[]>([]);
  const [score, setScore] = useState(0);
  const [time, setTime] = useState(60);
  const [running, setRunning] = useState(false);
  const [basketX, setBasketX] = useState(50);

  const gameRef = useRef<HTMLDivElement>(null);

  // ⏱ TIMER
  useEffect(() => {
    if (!running) return;
    const t = setInterval(() => {
      setTime((v) => (v > 0 ? v - 1 : 0));
    }, 1000);
    return () => clearInterval(t);
  }, [running]);

  // 🎯 GAME LOOP (NO DEPENDENCY BUG)
  useEffect(() => {
    if (!running) return;

    let frame: number;

    const loop = () => {
      setItems((prev) =>
        prev
          .map((it) => ({ ...it, y: it.y + it.speed }))
          .filter((it) => {
            // Catch
            if (it.y >= 88 && Math.abs(it.x - basketX) < 8) {
              if (it.good) setScore((s) => s + 10);
              else setScore((s) => Math.max(0, s - 5));
              return false;
            }

            // Remove if out
            return it.y <= 100;
          })
      );

      frame = requestAnimationFrame(loop);
    };

    frame = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(frame);
  }, [running, basketX]); // ✅ NO items here → FIXED LOOP

  // 🌱 SPAWN (LIMITED)
  useEffect(() => {
    if (!running) return;

    const spawn = setInterval(() => {
      setItems((prev) => {
        if (prev.length >= 5) return prev;

        const isGood = Math.random() < 0.7;

        return [
          ...prev,
          {
            id: Date.now() + Math.random(),
            emoji: isGood
              ? GOOD[Math.floor(Math.random() * GOOD.length)]
              : BAD[Math.floor(Math.random() * BAD.length)],
            x: Math.random() * 90,
            y: 0,
            speed: 0.4 + Math.random() * 0.3,
            good: isGood,
          },
        ];
      });
    }, 900);

    return () => clearInterval(spawn);
  }, [running]);

  // ⌨️ KEYBOARD
  useEffect(() => {
    const handle = (e: KeyboardEvent) => {
      if (!running) return;

      if (e.key === 'ArrowLeft') setBasketX((x) => Math.max(5, x - 5));
      if (e.key === 'ArrowRight') setBasketX((x) => Math.min(95, x + 5));
    };

    window.addEventListener('keydown', handle);
    return () => window.removeEventListener('keydown', handle);
  }, [running]);

  // 🖱 MOUSE (THROTTLED → prevents crash)
  const lastMove = useRef(0);

  const handleMouseMove = (e: React.MouseEvent) => {
    const now = Date.now();
    if (now - lastMove.current < 30) return; // throttle
    lastMove.current = now;

    if (!gameRef.current) return;

    const rect = gameRef.current.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    setBasketX(Math.max(5, Math.min(95, x)));
  };

  const reset = () => {
    setItems([]);
    setScore(0);
    setTime(60);
    setRunning(false);
    setBasketX(50);
  };

  const isFinished = time === 0;

  return (
    <div className="h-[calc(100vh-70px)] overflow-hidden flex flex-col bg-gradient-to-br from-blue-950 via-blue-950 to-slate-900 text-white">
      
      {/* Header */}
      <div className="flex justify-between px-3 py-2 text-sm">
        <Link href="/games" className="bg-white/10 px-2 py-1 rounded">← Back</Link>
        <p>Score: {score}</p>
        <p>Time: {time}s</p>
        {!running && !isFinished && (
          <button onClick={() => setRunning(true)} className="bg-cyan-500 px-2 rounded">
            Start
          </button>
        )}
      </div>

      <div className="px-3 pb-2 text-xs text-slate-200">
        Catch positive emojis for +10, avoid negative ones (-5). Use arrow keys or move your mouse.
      </div>

      {/* Game */}
      <div
        ref={gameRef}
        onMouseMove={handleMouseMove}
        className="relative flex-1 overflow-hidden"
      >
        {/* Emojis */}
        {items.map((it) => (
          <div
            key={it.id}
            className="absolute text-3xl"
            style={{ left: `${it.x}%`, top: `${it.y}%` }}
          >
            {it.emoji}
          </div>
        ))}

        {/* Basket ALWAYS visible */}
        <div
          className="absolute bottom-3 text-4xl"
          style={{ left: `${basketX}%`, transform: 'translateX(-50%)' }}
        >
          🧺
        </div>

        {/* End */}
        {isFinished && (
          <div className="absolute inset-0 flex items-center justify-center text-lg font-bold">
            Final Score: {score}
          </div>
        )}
      </div>
    </div>
  );
}