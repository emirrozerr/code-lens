import type { IndexingJob, JobStatus } from '@/types/api';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';

interface JobsTableProps {
  jobs: IndexingJob[];
  isLoading: boolean;
}

const STATUS_STYLES: Record<
  JobStatus,
  { label: string; color: string; bg: string; border: string }
> = {
  succeeded: { label: 'succeeded', color: 'var(--success)', bg: 'rgba(16,185,129,0.1)', border: 'rgba(16,185,129,0.3)' },
  running: { label: 'running', color: 'var(--accent)', bg: 'var(--accent-glow)', border: 'rgba(139,92,246,0.3)' },
  failed: { label: 'failed', color: 'var(--danger)', bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.3)' },
  pending: { label: 'pending', color: 'var(--text-dim)', bg: 'var(--surface-elevated)', border: 'var(--border)' },
};

function StatusPill({ status }: { status: JobStatus }) {
  const s = STATUS_STYLES[status];
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '0.125rem 0.5rem',
        borderRadius: '999px',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.6875rem',
        color: s.color,
        backgroundColor: s.bg,
        border: `1px solid ${s.border}`,
        letterSpacing: '0.02em',
      }}
    >
      {s.label}
    </span>
  );
}

function formatDuration(ms: number | null) {
  if (ms === null) return '—';
  if (ms < 1000) return `${ms}ms`;
  return `${(ms / 1000).toFixed(1)}s`;
}

function formatRelative(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60_000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function JobsTable({ jobs, isLoading }: JobsTableProps) {
  return (
    <div
      style={{
        backgroundColor: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: '8px',
        overflow: 'hidden',
        animation: 'fade-up 300ms ease-out 150ms both',
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
        Recent Indexing Jobs
      </div>

      {isLoading ? (
        <div style={{ padding: '1rem 1.25rem', display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-8 w-full" />
          ))}
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Repository</TableHead>
              <TableHead style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Status</TableHead>
              <TableHead style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Duration</TableHead>
              <TableHead style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Started</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {jobs.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={4}
                  style={{
                    textAlign: 'center',
                    padding: '2rem',
                    color: 'var(--text-dim)',
                    fontFamily: 'var(--font-sans)',
                    fontSize: '0.875rem',
                  }}
                >
                  No jobs found
                </TableCell>
              </TableRow>
            ) : (
              jobs.map((job) => (
                <TableRow key={job.id}>
                  <TableCell
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.8125rem',
                      color: 'var(--text)',
                    }}
                  >
                    {job.repoName}
                  </TableCell>
                  <TableCell>
                    <StatusPill status={job.status} />
                  </TableCell>
                  <TableCell
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.8125rem',
                      color: 'var(--text-muted)',
                    }}
                  >
                    {formatDuration(job.durationMs)}
                  </TableCell>
                  <TableCell
                    style={{
                      fontFamily: 'var(--font-sans)',
                      fontSize: '0.8125rem',
                      color: 'var(--text-dim)',
                    }}
                  >
                    {formatRelative(job.startedAt)}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
