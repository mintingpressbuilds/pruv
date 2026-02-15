interface PruvBadgeProps {
  className?: string;
  height?: number;
}

export function PruvBadge({ className, height = 32 }: PruvBadgeProps) {
  const width = height * 3;

  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 300 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <rect
        x="1.5"
        y="1.5"
        width="297"
        height="97"
        rx="12"
        fill="var(--surface-secondary, #f9fafb)"
        stroke="var(--color-pruv-500, #6366f1)"
        strokeWidth="2"
      />
      <circle cx="38" cy="50" r="16" fill="var(--color-pruv-500, #6366f1)" />
      <polyline
        points="30,50 35,55 46,44"
        stroke="white"
        strokeWidth="3.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <text
        x="66"
        y="50"
        dominantBaseline="central"
        fill="var(--text-primary, #111827)"
        fontFamily="Inter, system-ui, sans-serif"
        fontSize="16"
        fontWeight="500"
      >
        verified by{" "}
        <tspan fill="var(--color-pruv-500, #6366f1)" fontWeight="700">
          pruv
        </tspan>
      </text>
    </svg>
  );
}
