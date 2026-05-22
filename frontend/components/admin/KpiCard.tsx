import { Skeleton } from '@/components/ui/skeleton';

interface KpiCardProps {
  label: string;
  value: number;
  color?: string;
  isLoading?: boolean;
  delay?: number;
}

export function KpiCard({
  label,
  value,
  color = 'var(--text)',
  isLoading = false,
  delay = 0,
}: KpiCardProps) {
  return (
    <div
      style={{
        flex: 1,
        padding: '1.5rem',
        backgroundColor: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: '8px',
        animation: `fade-up 300ms ease-out ${delay}ms both`,
      }}
    >
      <div
        style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '0.6875rem',
          color: 'var(--text-dim)',
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          marginBottom: '0.75rem',
        }}
      >
        {label}
      </div>
      {isLoading ? (
        <Skeleton className="h-10 w-4/5" />
      ) : (
        <div
          style={{
            fontFamily: "'Instrument Serif', Georgia, serif",
            fontSize: '2.5rem',
            lineHeight: 1,
            color,
          }}
        >
          {value.toLocaleString()}
        </div>
      )}
    </div>
  );
}
