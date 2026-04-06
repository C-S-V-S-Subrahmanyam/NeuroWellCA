import './globals.css';
import type { Metadata } from 'next';
import AppTheme from '@/components/AppTheme';

export const metadata: Metadata = {
  title: 'NeurowellCA - Mental Health Support',
  description: 'AI-powered mental health chatbot for emotional support',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AppTheme />
        {children}
      </body>
    </html>
  );
}
