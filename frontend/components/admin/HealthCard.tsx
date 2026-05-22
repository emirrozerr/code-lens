import type { Stats } from '@/types/api';
import { Skeleton } from '@/components/ui/skeleton';

interface HealthCardProps {
  stats: Stats | undefined;
  isLoading: boolean;
}

function StatusDot({ status }: { status: 'ok' | 'degraded' | 'down' }) {
  const color =
    status === 'ok'
      ? 'var(--success)'
      : status === 'degraded'
        ? 'var(--warning)'
        : 'var(--danger)';
  return (
    <span
      style={{
        display: 'inline-block',
        width: '8px',
        height: '8px',
        borderRadius: '50%',
        backgroundColor: color,
        flexShrink: 0,
      }}
    />
  );
}

function formatUptime(pct: number) {
  return `${pct.toFixed(2)}%`;
}

function formatDate(iso: string | null) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-GB', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

export function HealthCard({ stats, isLoading }: HealthCardProps) {
  const rows = stats
    ? [
        {
          label: 'Neo4j',
          content: (
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <StatusDot status={stats.neo4jStatus} />
              <span
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.8125rem',
                  color:
                    stats.neo4jStatus === 'ok'
                      ? 'var(--success)'
                      : stats.neo4jStatus === 'degraded'
                        ? 'var(--warning)'
                        : 'var(--danger)',
                }}
              >
                {stats.neo4jStatus}
              </span>
            </span>
          ),
        },
        {
          label: 'MCP uptime',
          content: (
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.8125rem',
                color: 'var(--text)',
              }}
            >
              {formatUptime(stats.mcpUptime)}
            </span>
          ),
        },
        {
          label: 'Last index',
          content: (
            <span
              style={{
                fontFamily: 'var(--font-sans)',
                fontSize: '0.8125rem',
                color: 'var(--text-muted)',
              }}
            >
              {formatDate(stats.lastSuccessfulIndex)}
            </span>
          ),
        },
      ]
    : [];

  return (
    <div
      style={{
        backgroundColor: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: '8px',
        overflow: 'hidden',
        animation: 'fade-up 300ms ease-out 200ms both',
      }}
    >
      <div
        style={{
          padding: '1rem 1.25rem',
          borderBottom: '1px solid var(--border)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.6875rem',
          color: 'var(--text-dim)',
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
        }}
      >
        System Health
      </div>

      <div style={{ padding: '0 1.25rem' }}>
        {isLoading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', padding: '1rem 0' }}>
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-6 w-full" />
            ))}
          </div>
        ) : (
          rows.map((row, i) => (
            <div
              key={row.label}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.875rem 0',
                borderBottom: i < rows.length - 1 ? '1px solid var(--border)' : 'none',
              }}
            >
              <span
                style={{
                  fontFamily: 'var(--font-sans)',
                  fontSize: '0.8125rem',
                  color: 'var(--text-dim)',
                }}
              >
                {row.label}
              </span>
              {row.content}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
