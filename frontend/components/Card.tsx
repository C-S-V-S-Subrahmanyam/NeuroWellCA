'use client';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
}

export default function Card({ children, className = '', title }: CardProps) {
  return (
    <div className={`glass-effect rounded-2xl p-6 ${className}`}>
      {title && (
        <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>{title}</h2>
      )}
      {children}
    </div>
  );
}
