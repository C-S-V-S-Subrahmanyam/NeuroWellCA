interface SendIconProps {
  className?: string;
  size?: number;
}

const SendIcon = ({ className = "", size = 20 }: SendIconProps) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <defs>
      <linearGradient id="sendGradient" x1="0%" y1="0%" x2="100%" y2="100%" gradientTransform="rotate(135)">
        <stop offset="0%" stopColor="#2563EB" />
        <stop offset="100%" stopColor="#3B82F6" />
      </linearGradient>
    </defs>
    <path 
      d="M22 2L11 13" 
      stroke="url(#sendGradient)" 
      strokeWidth={2} 
      strokeLinecap="round" 
      strokeLinejoin="round" 
    />
    <path 
      d="M22 2L15 22L11 13L2 9L22 2Z" 
      stroke="url(#sendGradient)" 
      strokeWidth={2} 
      strokeLinecap="round" 
      strokeLinejoin="round" 
    />
  </svg>
);

export default SendIcon;