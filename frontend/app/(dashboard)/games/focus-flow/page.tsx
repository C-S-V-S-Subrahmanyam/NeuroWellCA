'use client';

import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';

export default function FocusFlowPage() {
  const [target, setTarget] = useState(1);
  const [speed, setSpeed] = useState(1200);
  const [score, setScore] = useState(0);
  const [streak, setStreak] = useState(0);
  const [running, setRunning] = useState(false);
  const [timeLeft, setTimeLeft] = useState(30);
  const [gameOver, setGameOver] = useState(false);
  const [highScore, setHighScore] = useState(0);
  const [level, setLevel] = useState(1);

  // 🔊 Sound refs
  const correctSound = useRef<HTMLAudioElement | null>(null);
  const wrongSound = useRef<HTMLAudioElement | null>(null);

  // ✅ THIS IS THE KEY FIX (works inside app folder)
  useEffect(() => {
    correctSound.current = new Audio(new URL('./correct.mp3', import.meta.url).toString());
    wrongSound.current = new Audio(new URL('./wrong.mp3', import.meta.url).toString());
  }, []);

  // 🏆 Load high score
  useEffect(() => {
    const hs = localStorage.getItem('focusflow-highscore');
    if (hs) setHighScore(Number(hs));
  }, []);

  // ⏱ Timer
  useEffect(() => {
    if (!running) return;

    if (timeLeft <= 0) {
      setRunning(false);
      setGameOver(true);

      if (score > highScore) {
        localStorage.setItem('focusflow-highscore', String(score));
        setHighScore(score);
      }
      return;
    }

    const timer = setTimeout(() => {
      setTimeLeft((t) => t - 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [running, timeLeft]);

  // 🎯 Random target + speed
  useEffect(() => {
    if (!running) return;

    const timeout = setTimeout(() => {
      setTarget(Math.floor(Math.random() * 9) + 1);
      setSpeed((s) => Math.max(500, s - 10));
    }, speed);

    return () => clearTimeout(timeout);
  }, [target, speed, running]);

  const playSound = (type: 'correct' | 'wrong') => {
    const sound = type === 'correct' ? correctSound.current : wrongSound.current;
    if (sound) {
      sound.currentTime = 0;
      sound.play().catch(() => {});
    }
  };

  const handlePick = (n: number) => {
    if (!running) return;

    if (n === target) {
      playSound('correct');

      const newStreak = streak + 1;
      const newScore = score + 10 + newStreak;

      setScore(newScore);
      setStreak(newStreak);
      setLevel(Math.floor(newScore / 50) + 1);

      setTarget(Math.floor(Math.random() * 9) + 1);
    } else {
      playSound('wrong');

      setStreak(0);
      setScore((s) => Math.max(0, s - 5));
    }
  };

  const reset = () => {
    setRunning(false);
    setTarget(1);
    setSpeed(1200);
    setScore(0);
    setStreak(0);
    setTimeLeft(30);
    setGameOver(false);
    setLevel(1);
  };

  return (
    <div className="h-screen overflow-hidden bg-gradient-to-br from-slate-900 via-indigo-950 to-blue-950 text-white flex items-center justify-center">
      <div className="w-full max-w-3xl h-[95vh] flex flex-col justify-between p-4">

        {/* Header */}
        <div className="flex items-center justify-between">
          <Link href="/games" className="bg-white/10 px-3 py-1 rounded-lg text-sm">← Back</Link>
          <h1 className="text-2xl font-bold">🎯 Focus Flow</h1>
          <div className="text-sm">🏆 {highScore}</div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-5 text-center text-sm">
          <div>Score<br /><b>{score}</b></div>
          <div>Streak<br /><b>{streak}</b></div>
          <div>Target<br /><b className="text-cyan-300 text-lg">{target}</b></div>
          <div>Time<br /><b>{timeLeft}s</b></div>
          <div>Level<br /><b>{level}</b></div>
        </div>

        <p className="text-xs text-slate-300 text-center">
          Tap the current target number quickly. Correct picks build streak and level, wrong picks reduce score.
        </p>

        {/* Grid */}
        <div className="grid grid-cols-3 gap-3 flex-grow max-h-[50vh]">
          {Array.from({ length: 9 }, (_, i) => i + 1).map((n) => (
            <button
              key={n}
              onClick={() => handlePick(n)}
              className="rounded-2xl bg-gradient-to-br from-indigo-500/30 to-blue-500/30 border border-blue-300/30 hover:bg-blue-500/40 transition text-2xl font-bold flex items-center justify-center active:scale-95"
            >
              {n}
            </button>
          ))}
        </div>

        {/* Controls */}
        <div className="flex justify-center gap-3">
          {!running && !gameOver && (
            <button
              className="px-5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400"
              onClick={() => setRunning(true)}
            >
              Start
            </button>
          )}

          {running && (
            <button
              className="px-5 py-2 rounded-xl bg-amber-500 hover:bg-amber-400"
              onClick={() => setRunning(false)}
            >
              Pause
            </button>
          )}

          <button
            className="px-5 py-2 rounded-xl bg-white/20 hover:bg-white/30"
            onClick={reset}
          >
            Reset
          </button>
        </div>

        {/* Game Over */}
        {gameOver && (
          <div className="text-center">
            <h2 className="text-xl font-bold text-red-400">Game Over</h2>
            <p>Final Score: {score}</p>
          </div>
        )}
      </div>
    </div>
  );
}