'use client';

import { use } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { listRepos, listJobs, listDomains } from '@/lib/api/endpoints';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft } from 'lucide-react';
import { buttonVariants } from '@/components/ui/button';
import type { IndexingJob } from '@/types/api';

interface PageProps {
  params: Promise<{ id: string }>;
}

function JobRow({ job }: { job: IndexingJob }) {
  const statusColor: Record<string, string> = {
    succeeded: 'var(--success)',
    failed: 'var(--danger)',
    running: 'var(--accent)',
    pending: 'var(--text-dim)',
  };
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '1rem',
        padding: '0.625rem 1rem',
        borderBottom: '1px solid var(--border)',
        fontFamily: 'var(--font-mono)',
        fontSize: '0.75rem',
      }}
    >
      <span style={{ color: statusColor[job.status] ?? 'var(--text-dim)', width: '80px', flexShrink: 0 }}>
        {job.status}
      </span>
      <span style={{ color: 'var(--text-dim)', flex: 1 }}>
        {new Date(job.startedAt).toLocaleString('en-GB')}
      </span>
      {job.nodeCount != null && (
        <span style={{ color: 'var(--text-muted)' }}>{job.nodeCount} nodes</span>
      )}
      {job.durationMs != null && (
        <span style={{ color: 'var(--text-dim)' }}>{(job.durationMs / 1000).toFixed(1)}s</span>
      )}
      {job.error && (
        <span style={{ color: 'var(--danger)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '300px' }}>
          {job.error}
        </span>
      )}
    </div>
  );
}

export default function RepoDetailPage({ params }: PageProps) {
  const { id } = use(params);

  const { data: repos = [], isLoading: reposLoading, isError: reposError } = useQuery({
    queryKey: ['repos'],
    queryFn: listRepos,
  });

  const { data: jobs = [], isLoading: jobsLoading } = useQuery({
    queryKey: ['jobs', 50],
    queryFn: () => listJobs(50),
    refetchInterval: 3000,
  });

  const { data: domains = [] } = useQuery({
    queryKey: ['domains', id],
    queryFn: () => listDomains(id),
  });

  const repo = repos.find((r) => r.id === id);
  const repoJobs = jobs.filter((j) => j.repoId === id);

  if (reposError) {
    return (
      <div style={{ padding: '2rem', fontFamily: 'var(--font-sans)', fontSize: '0.875rem', color: 'var(--danger)' }}>
        Failed to load repository data.
      </div>
    );
  }

  if (!reposLoading && !repo) {
    return (
      <div style={{ padding: '2rem', fontFamily: 'var(--font-sans)', color: 'var(--text-dim)' }}>
        Repository not found.{' '}
        <Link href="/admin/repositories" style={{ color: 'var(--accent)' }}>Back to repositories</Link>
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <Link
          href="/admin/repositories"
          className={buttonVariants({ variant: 'ghost', size: 'sm' })}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.375rem', color: 'var(--text-dim)', textDecoration: 'none' }}
        >
          <ArrowLeft size={14} />
          Repositories
        </Link>
      </div>

      <div style={{ marginBottom: '2rem', animation: 'fade-up 300ms ease-out both' }}>
        {reposLoading ? <Skeleton className="h-8 w-64" /> : (
          <h1 style={{ fontFamily: "'Instrument Serif', Georgia, serif", fontSize: '2rem', fontWeight: 400, color: 'var(--text)', lineHeight: 1.1, margin: 0 }}>
            {repo?.name}
          </h1>
        )}
        {repo && (
          <p style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.375rem' }}>
            {repo.url}
          </p>
        )}
      </div>

      {/* Stats */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', animation: 'fade-up 300ms ease-out 50ms both' }}>
        {[
          { label: 'Nodes', value: repo?.nodeCount.toLocaleString() ?? '—' },
          { label: 'Domains', value: domains.length.toString() },
          { label: 'Status', value: repo?.status ?? '—' },
          { label: 'Last indexed', value: repo?.lastIndexed ? new Date(repo.lastIndexed).toLocaleDateString('en-GB', { dateStyle: 'medium' }) : '—' },
        ].map(({ label, value }) => (
          <div key={label} style={{ flex: 1, padding: '1.25rem', backgroundColor: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '8px' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6875rem', color: 'var(--text-dim)', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
              {label}
            </div>
            {reposLoading ? <Skeleton className="h-6 w-3/4" /> : (
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '1.125rem', color: 'var(--text)' }}>{value}</div>
            )}
          </div>
        ))}
      </div>

      {/* Domains */}
      {domains.length > 0 && (
        <div style={{ marginBottom: '2rem', animation: 'fade-up 300ms ease-out 100ms both' }}>
          <h2 style={{ fontFamily: 'var(--font-sans)', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
            Domains ({domains.length})
          </h2>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {domains.map((d) => (
              <span key={d.id} style={{ padding: '0.25rem 0.625rem', backgroundColor: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '4px', fontFamily: 'var(--font-sans)', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                {d.name}
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.6875rem', color: 'var(--text-dim)', marginLeft: '0.375rem' }}>
                  {d.memberCount}
                </span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Indexing history */}
      <div style={{ animation: 'fade-up 300ms ease-out 150ms both' }}>
        <h2 style={{ fontFamily: 'var(--font-sans)', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
          Indexing history
        </h2>
        <div style={{ backgroundColor: 'var(--surface)', border: '1px solid var(--border)', borderRadius: '8px', overflow: 'hidden' }}>
          {jobsLoading ? (
            <div style={{ padding: '1rem' }}><Skeleton className="h-8 w-full" /></div>
          ) : repoJobs.length === 0 ? (
            <div style={{ padding: '2rem', textAlign: 'center', fontFamily: 'var(--font-sans)', fontSize: '0.875rem', color: 'var(--text-dim)' }}>
              No indexing jobs yet.
            </div>
          ) : (
            repoJobs.map((job) => <JobRow key={job.id} job={job} />)
          )}
        </div>
      </div>
    </div>
  );
}
