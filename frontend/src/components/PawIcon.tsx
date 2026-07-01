export function PawIcon({
  size = 18,
  color = "#ffffff",
}: {
  size?: number;
  color?: string;
}) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill={color} aria-hidden="true">
      <circle cx="6.5" cy="9.5" r="2.05" />
      <circle cx="11.4" cy="7.2" r="2.2" />
      <circle cx="16.3" cy="9.5" r="2.05" />
      <path d="M11.4 11.2c2.9 0 5 2.1 5 4.3 0 1.8-1.7 2.6-3.4 2.6-.7 0-1-.2-1.6-.2s-.9.2-1.6.2c-1.7 0-3.4-.8-3.4-2.6 0-2.2 2.1-4.3 5-4.3z" />
    </svg>
  );
}
