'use client';

import { use } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { listRepos, listJobs, listDomains } from '@/lib/api/endpoints';
import { JobsTable } from '@/components/admin/JobsTable';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft } from 'lucide-react';
import { buttonVariants } from '@/components/ui/button';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function RepoDetailPage({ params }: PageProps) {
  const { id } = use(params);

  const { data: repos = [], isLoading: reposLoading } = useQuery({
    queryKey: ['repos'],
    queryFn: listRepos,
  });

  const { data: jobs = [], isLoading: jobsLoading } = useQuery({
    queryKey: ['jobs', 50],
    queryFn: () => listJobs(50),
  });

  const { data: domains = [] } = useQuery({
    queryKey: ['domains', id],
    queryFn: () => listDomains(id),
  });

  const repo = repos.find((r) => r.id === id);
  const repoJobs = jobs.filter((j) => j.repoId === id);

  if (!reposLoading && !repo) {
    return (
      <div
        style={{
          padding: '2rem',
          maxWidth: '1400px',
          margin: '0 auto',
          fontFamily: 'var(--font-sans)',
          color: 'var(--text-dim)',
        }}
      >
        Repository not found.{' '}
        <Link href="/admin/repositories" style={{ color: 'var(--accent)' }}>
          Back to repositories
        </Link>
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Back link */}
      <div style={{ marginBottom: '1.5rem' }}>
        <Link
          href="/admin/repositories"
          className={buttonVariants({ variant: 'ghost', size: 'sm' })}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.375rem',
            color: 'var(--text-dim)',
            textDecoration: 'none',
          }}
        >
          <ArrowLeft size={14} />
          Repositories
        </Link>
      </div>

      {/* Heading */}
      <div style={{ marginBottom: '2rem', animation: 'fade-up 300ms ease-out both' }}>
        {reposLoading ? (
          <Skeleton className="h-8 w-64" />
        ) : (
          <h1
            style={{
              fontFamily: "'Instrument Serif', Georgia, serif",
              fontSize: '2rem',
              fontWeight: 400,
              color: 'var(--text)',
              lineHeight: 1.1,
              margin: 0,
            }}
          >
            {repo?.name}
          </h1>
        )}
        {repo && (
          <p
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              color: 'var(--text-dim)',
              marginTop: '0.375rem',
            }}
          >
            {repo.url}
          </p>
        )}
      </div>

      {/* Stats row */}
      <div
        style={{
          display: 'flex',
          gap: '1rem',
          marginBottom: '2rem',
          animation: 'fade-up 300ms ease-out 50ms both',
        }}
      >
        {[
          { label: 'Nodes', value: repo?.nodeCount.toLocaleString() ?? '—' },
          { label: 'Domains', value: domains.length.toString() },
          { label: 'Status', value: repo?.status ?? '—' },
          {
            label: 'Last indexed',
            value: repo?.lastIndexed
              ? new Date(repo.lastIndexed).toLocaleDateString('en-GB', { dateStyle: 'medium' })
              : '—',
          },
        ].map(({ label, value }) => (
          <div
            key={label}
            style={{
              flex: 1,
              padding: '1.25rem',
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
            }}
          >
            <div
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.6875rem',
                color: 'var(--text-dim)',
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                marginBottom: '0.5rem',
              }}
            >
              {label}
            </div>
            {reposLoading ? (
              <Skeleton className="h-6 w-3/4" />
            ) : (
              <div
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '1.125rem',
                  color: 'var(--text)',
                }}
              >
                {value}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Domains section */}
      <div
        style={{
          marginBottom: '2rem',
          animation: 'fade-up 300ms ease-out 100ms both',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '0.75rem',
          }}
        >
          <h2
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: '0.875rem',
              fontWeight: 500,
              color: 'var(--text-muted)',
              margin: 0,
            }}
          >
            Domains ({domains.length})
          </h2>
          <Link
            href={`/admin/domains?repo=${id}`}
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: '0.8125rem',
              color: 'var(--accent)',
              textDecoration: 'none',
            }}
          >
            Manage domains →
          </Link>
        </div>
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '0.5rem',
          }}
        >
          {domains.map((d) => (
            <span
              key={d.id}
              style={{
                padding: '0.25rem 0.625rem',
                backgroundColor: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: '4px',
                fontFamily: 'var(--font-sans)',
                fontSize: '0.8125rem',
                color: 'var(--text-muted)',
              }}
            >
              {d.name}
              <span
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.6875rem',
                  color: 'var(--text-dim)',
                  marginLeft: '0.375rem',
                }}
              >
                {d.memberCount}
              </span>
            </span>
          ))}
        </div>
      </div>

      {/* Jobs history */}
      <div style={{ animation: 'fade-up 300ms ease-out 150ms both' }}>
        <h2
          style={{
            fontFamily: 'var(--font-sans)',
            fontSize: '0.875rem',
            fontWeight: 500,
            color: 'var(--text-muted)',
            marginBottom: '0.75rem',
          }}
        >
          Indexing history
        </h2>
        <JobsTable jobs={repoJobs} isLoading={jobsLoading} />
      </div>
    </div>
  );
}
