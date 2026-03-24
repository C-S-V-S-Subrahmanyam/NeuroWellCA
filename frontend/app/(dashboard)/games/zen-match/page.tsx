'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';

const ZEN_EMOJIS = ['🌿', '🌸', '🦋', '🐢', '🌙', '☀️', '☁️', '🌊'];

interface Card {
  id: number;
  emoji: string;
  isFlipped: boolean;
  isMatched: boolean;
}

export default function ZenMatchPage() {
  const [cards, setCards] = useState<Card[]>([]);
  const [flippedIndices, setFlippedIndices] = useState<number[]>([]);
  const [matches, setMatches] = useState(0);
  const [moves, setMoves] = useState(0);
  const [isLocked, setIsLocked] = useState(false);

  const initializeGame = () => {
    const shuffledCards = [...ZEN_EMOJIS, ...ZEN_EMOJIS]
      .sort(() => Math.random() - 0.5)
      .map((emoji, index) => ({ id: index, emoji, isFlipped: false, isMatched: false }));
    setCards(shuffledCards);
    setFlippedIndices([]);
    setMatches(0);
    setMoves(0);
    setIsLocked(false);
  };

  useEffect(() => {
    initializeGame();
  }, []);

  const handleCardClick = (index: number) => {
    if (isLocked || cards[index].isFlipped || cards[index].isMatched) return;

    const newCards = [...cards];
    newCards[index].isFlipped = true;
    setCards(newCards);

    const newFlippedIndices = [...flippedIndices, index];
    setFlippedIndices(newFlippedIndices);

    if (newFlippedIndices.length === 2) {
      setIsLocked(true);
      setMoves((m) => m + 1);
      const [firstIndex, secondIndex] = newFlippedIndices;

      if (cards[firstIndex].emoji === cards[secondIndex].emoji) {
        setTimeout(() => {
          const matchedCards = [...cards];
          matchedCards[firstIndex].isMatched = true;
          matchedCards[secondIndex].isMatched = true;
          setCards(matchedCards);
          setFlippedIndices([]);
          setMatches((m) => m + 1);
          setIsLocked(false);
        }, 500);
      } else {
        setTimeout(() => {
          const resetCards = [...cards];
          resetCards[firstIndex].isFlipped = false;
          resetCards[secondIndex].isFlipped = false;
          setCards(resetCards);
          setFlippedIndices([]);
          setIsLocked(false);
        }, 1000);
      }
    }
  };

  const isGameComplete = matches === ZEN_EMOJIS.length;

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col items-center p-6">
      <div className="w-full max-w-4xl flex justify-between items-center mb-6">
        <Link href="/games" className="text-slate-300 hover:text-white flex items-center bg-slate-800 px-4 py-2 rounded-lg transition-colors">
          ← Back to Relaxation
        </Link>
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold text-white tracking-wide">🧩 Zen Match</h1>
          <button onClick={initializeGame} className="bg-slate-700 hover:bg-slate-600 text-slate-200 px-4 py-1 rounded-full text-sm transition-colors">
            Restart Game
          </button>
        </div>
        <div className="w-24"></div>
      </div>

      <div className="flex gap-8 mb-8 text-slate-300 bg-slate-800/50 px-8 py-3 rounded-2xl border border-slate-700/50">
        <div className="text-center">
          <p className="text-sm text-slate-400 uppercase tracking-wider">Moves</p>
          <p className="text-2xl font-mono text-emerald-400">{moves}</p>
        </div>
        <div className="w-px bg-slate-700"></div>
        <div className="text-center">
          <p className="text-sm text-slate-400 uppercase tracking-wider">Matches</p>
          <p className="text-2xl font-mono text-teal-400">{matches} / {ZEN_EMOJIS.length}</p>
        </div>
      </div>

      <div className="w-full max-w-2xl bg-slate-800/30 p-8 rounded-3xl border border-slate-700 shadow-2xl backdrop-blur-sm">
        {isGameComplete ? (
          <div className="py-12 flex flex-col items-center text-center animate-[fadeIn_0.5s_ease-out]">
            <div className="text-6xl mb-4">🧘‍♂️</div>
            <h2 className="text-3xl font-bold text-white mb-2">Mind Clear</h2>
            <p className="text-slate-400 mb-8">You found all the matches in {moves} moves. Take a deep breath.</p>
            <button onClick={initializeGame} className="bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-400 hover:to-emerald-400 text-white font-semibold px-8 py-3 rounded-xl transition-all shadow-lg hover:-translate-y-1">
              Play Again
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-4 gap-4 sm:gap-6">
            {cards.map((card, index) => (
              <div
                key={card.id}
                onClick={() => handleCardClick(index)}
                className={`
                  aspect-square rounded-2xl cursor-pointer transition-all duration-300 transform flex items-center justify-center text-4xl sm:text-5xl shadow-md
                  ${card.isFlipped || card.isMatched
                    ? 'bg-slate-700 scale-100'
                    : 'bg-gradient-to-br from-teal-500/20 to-emerald-500/20 hover:from-teal-500/30 hover:to-emerald-500/30 hover:scale-105 border border-teal-500/30'}
                  ${card.isMatched ? 'opacity-50 border border-emerald-500/50 bg-emerald-900/20' : ''}
                `}
              >
                <div className={`transition-all duration-300 ${card.isFlipped || card.isMatched ? 'scale-100 opacity-100' : 'scale-0 opacity-0'}`}>
                  {card.emoji}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
