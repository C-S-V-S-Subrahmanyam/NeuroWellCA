'use client';

import { useEffect } from 'react';
import { usePathname } from 'next/navigation';

const ACCENTS: Record<string, { bgStart: string; bgMid: string; bgEnd: string; accent50: string; accent100: string; accent200: string; accent500: string; accent600: string; accent700: string }> = {
  blue: {
    bgStart: '#eef6ff',
    bgMid: '#f8fbff',
    bgEnd: '#dbeafe',
    accent50: '#eff6ff',
    accent100: '#dbeafe',
    accent200: '#bfdbfe',
    accent500: '#3b82f6',
    accent600: '#2563eb',
    accent700: '#1d4ed8',
  },
  green: {
    bgStart: '#effaf4',
    bgMid: '#f8fffb',
    bgEnd: '#d1fae5',
    accent50: '#f0fdf4',
    accent100: '#dcfce7',
    accent200: '#bbf7d0',
    accent500: '#22c55e',
    accent600: '#16a34a',
    accent700: '#15803d',
  },
  yellow: {
    bgStart: '#fffaf0',
    bgMid: '#fffcf4',
    bgEnd: '#fef3c7',
    accent50: '#fffbeb',
    accent100: '#fef3c7',
    accent200: '#fde68a',
    accent500: '#eab308',
    accent600: '#ca8a04',
    accent700: '#a16207',
  },
  pink: {
    bgStart: '#fff1f7',
    bgMid: '#fff8fb',
    bgEnd: '#fce7f3',
    accent50: '#fdf2f8',
    accent100: '#fce7f3',
    accent200: '#f9a8d4',
    accent500: '#ec4899',
    accent600: '#db2777',
    accent700: '#be185d',
  },
  orange: {
    bgStart: '#fff7ed',
    bgMid: '#fffbf6',
    bgEnd: '#ffedd5',
    accent50: '#fff7ed',
    accent100: '#ffedd5',
    accent200: '#fed7aa',
    accent500: '#f97316',
    accent600: '#ea580c',
    accent700: '#c2410c',
  },
  violet: {
    bgStart: '#f5f3ff',
    bgMid: '#faf7ff',
    bgEnd: '#ede9fe',
    accent50: '#f5f3ff',
    accent100: '#ede9fe',
    accent200: '#ddd6fe',
    accent500: '#8b5cf6',
    accent600: '#7c3aed',
    accent700: '#6d28d9',
  },
  black: {
    bgStart: '#f3f4f6',
    bgMid: '#e5e7eb',
    bgEnd: '#d1d5db',
    accent50: '#f3f4f6',
    accent100: '#e5e7eb',
    accent200: '#d1d5db',
    accent500: '#374151',
    accent600: '#1f2937',
    accent700: '#111827',
  },
};

function applyTheme(forceSystemAppearance = false) {
  if (typeof window === 'undefined') return;

  const root = document.documentElement;
  const appearance = forceSystemAppearance ? 'system' : (localStorage.getItem('neurowell_appearance') || 'system');
  const accent = localStorage.getItem('neurowell_accent') || 'blue';
  const palette = ACCENTS[accent] || ACCENTS.blue;
  const resolvedAppearance = appearance === 'system'
    ? window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    : appearance;

  root.dataset.appearance = appearance;
  root.dataset.accent = accent;
  if (resolvedAppearance === 'dark') {
    root.style.setProperty('--app-bg-start', '#0f172a');
    root.style.setProperty('--app-bg-mid', '#111827');
    root.style.setProperty('--app-bg-end', '#1e293b');
  } else {
    root.style.setProperty('--app-bg-start', palette.bgStart);
    root.style.setProperty('--app-bg-mid', palette.bgMid);
    root.style.setProperty('--app-bg-end', palette.bgEnd);
  }
  root.style.setProperty('--accent-50', palette.accent50);
  root.style.setProperty('--accent-100', palette.accent100);
  root.style.setProperty('--accent-200', palette.accent200);
  root.style.setProperty('--accent-500', palette.accent500);
  root.style.setProperty('--accent-600', palette.accent600);
  root.style.setProperty('--accent-700', palette.accent700);

  root.dataset.resolvedAppearance = resolvedAppearance;
  root.style.colorScheme = resolvedAppearance;
}

export default function AppTheme() {
  const pathname = usePathname();

  useEffect(() => {
    const isPublicRoute = pathname === '/' || pathname?.startsWith('/login') || pathname?.startsWith('/register');

    applyTheme(isPublicRoute);

    const onThemeChange = () => applyTheme();
    const onStorage = () => applyTheme();
    const onSystemThemeChange = () => {
      if (isPublicRoute || (localStorage.getItem('neurowell_appearance') || 'system') === 'system') {
        applyTheme(isPublicRoute);
      }
    };

    window.addEventListener('neurowell-theme-change', onThemeChange as EventListener);
    window.addEventListener('storage', onStorage);
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', onSystemThemeChange);

    return () => {
      window.removeEventListener('neurowell-theme-change', onThemeChange as EventListener);
      window.removeEventListener('storage', onStorage);
      window.matchMedia('(prefers-color-scheme: dark)').removeEventListener('change', onSystemThemeChange);
    };
  }, [pathname]);

  return null;
}