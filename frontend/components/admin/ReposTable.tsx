'use client';

import type { Repository } from '@/types/api';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Skeleton } from '@/components/ui/skeleton';
import { MoreHorizontal } from 'lucide-react';

interface ReposTableProps {
  repos: Repository[];
  isLoading: boolean;
  onView: (repo: Repository) => void;
  onReindex: (repo: Repository) => void;
  onDelete: (repo: Repository) => void;
}

const STATUS_STYLES: Record<
  Repository['status'],
  { label: string; color: string; bg: string; border: string }
> = {
  indexed: { label: 'indexed', color: 'var(--success)', bg: 'rgba(16,185,129,0.1)', border: 'rgba(16,185,129,0.3)' },
  indexing: { label: 'indexing', color: 'var(--accent)', bg: 'var(--accent-glow)', border: 'rgba(139,92,246,0.3)' },
  failed: { label: 'failed', color: 'var(--danger)', bg: 'rgba(239,68,68,0.1)', border: 'rgba(239,68,68,0.3)' },
  pending: { label: 'pending', color: 'var(--text-dim)', bg: 'var(--surface-elevated)', border: 'var(--border)' },
};

function StatusPill({ status }: { status: Repository['status'] }) {
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
      }}
    >
      {s.label}
    </span>
  );
}

function formatDate(iso: string | null) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-GB', { dateStyle: 'medium' });
}

export function ReposTable({ repos, isLoading, onView, onReindex, onDelete }: ReposTableProps) {
  return (
    <div
      style={{
        backgroundColor: 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: '8px',
        overflow: 'hidden',
      }}
    >
      {isLoading ? (
        <div style={{ padding: '1rem 1.25rem', display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-10 w-full" />
          ))}
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Name</TableHead>
              <TableHead style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Status</TableHead>
              <TableHead style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Nodes</TableHead>
              <TableHead style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Last Indexed</TableHead>
              <TableHead style={{ color: 'var(--text-dim)', fontSize: '0.75rem', width: '48px' }} />
            </TableRow>
          </TableHeader>
          <TableBody>
            {repos.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={5}
                  style={{
                    textAlign: 'center',
                    padding: '3rem',
                    color: 'var(--text-dim)',
                    fontFamily: 'var(--font-sans)',
                    fontSize: '0.875rem',
                  }}
                >
                  No repositories yet. Add one to get started.
                </TableCell>
              </TableRow>
            ) : (
              repos.map((repo) => (
                <TableRow key={repo.id}>
                  <TableCell>
                    <div>
                      <div
                        style={{
                          fontFamily: 'var(--font-mono)',
                          fontSize: '0.8125rem',
                          color: 'var(--text)',
                        }}
                      >
                        {repo.name}
                      </div>
                      <div
                        style={{
                          fontFamily: 'var(--font-sans)',
                          fontSize: '0.75rem',
                          color: 'var(--text-dim)',
                          marginTop: '0.125rem',
                        }}
                      >
                        {repo.paths.length > 0 ? repo.paths.join(', ') : repo.url}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <StatusPill status={repo.status} />
                  </TableCell>
                  <TableCell
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.8125rem',
                      color: 'var(--text-muted)',
                    }}
                  >
                    {repo.nodeCount.toLocaleString()}
                  </TableCell>
                  <TableCell
                    style={{
                      fontFamily: 'var(--font-sans)',
                      fontSize: '0.8125rem',
                      color: 'var(--text-dim)',
                    }}
                  >
                    {formatDate(repo.lastIndexed)}
                  </TableCell>
                  <TableCell>
                    <DropdownMenu>
                      <DropdownMenuTrigger
                        aria-label={`Actions for ${repo.name}`}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          width: '28px',
                          height: '28px',
                          borderRadius: '4px',
                          border: 'none',
                          backgroundColor: 'transparent',
                          color: 'var(--text-dim)',
                          cursor: 'pointer',
                        }}
                      >
                        <MoreHorizontal size={15} />
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onSelect={() => onView(repo)}>
                          View detail
                        </DropdownMenuItem>
                        <DropdownMenuItem onSelect={() => onReindex(repo)}>
                          Re-index
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem variant="destructive" onSelect={() => onDelete(repo)}>
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
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
