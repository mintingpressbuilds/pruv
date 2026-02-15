interface PruvIconProps {
  size?: number;
  className?: string;
}

export function PruvIcon({ size = 24, className }: PruvIconProps) {
  const radius = size * (10 / 48);

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <rect width="48" height="48" rx={radius} fill="currentColor" />
      <path
        d="M13 25 L20 32 L35 16"
        stroke="white"
        strokeWidth="5"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
    </svg>
  );
}
