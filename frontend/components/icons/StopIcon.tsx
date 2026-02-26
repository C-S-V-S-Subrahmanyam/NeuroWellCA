interface StopIconProps {
  className?: string;
  size?: number;
}

const StopIcon = ({ className = "", size = 20 }: StopIconProps) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <defs>
      <linearGradient id="stopGradient" x1="0%" y1="0%" x2="100%" y2="100%" gradientTransform="rotate(135)">
        <stop offset="0%" stopColor="#2563EB" />
        <stop offset="100%" stopColor="#3B82F6" />
      </linearGradient>
    </defs>
    <rect 
      x="6" 
      y="6" 
      width="12" 
      height="12" 
      rx="2" 
      fill="url(#stopGradient)" 
    />
  </svg>
);

export default StopIcon;