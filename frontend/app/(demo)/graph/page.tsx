'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '@/lib/auth';
import { getGraph, listRepos } from '@/lib/api/endpoints';
import { DomainGraph } from '@/components/graph/DomainGraph';

export default function GraphPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const [selectedRepo, setSelectedRepo] = useState('');

  const reposQuery = useQuery({
    queryKey: ['repos'],
    queryFn: () => listRepos(),
  });

  const graphQuery = useQuery({
    queryKey: ['graph', selectedRepo],
    queryFn: () => getGraph(selectedRepo || undefined),
    staleTime: 60_000,
  });

  const repos = (reposQuery.data ?? []).map((r) => ({ id: r.id, name: r.name }));
  const data = graphQuery.data;
  const isEmpty = data && data.nodes.length === 0;

  return (
    <div
      style={{
        height: '100vh',
        backgroundColor: 'var(--bg)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <header
        style={{
          height: '52px',
          borderBottom: '1px solid var(--border)',
          backgroundColor: 'var(--surface)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 1.5rem',
          flexShrink: 0,
          gap: '1rem',
          zIndex: 5,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.8125rem',
              color: 'var(--accent)',
              letterSpacing: '0.08em',
            }}
          >
            CodeLens
          </span>
          <span
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: '0.75rem',
              color: 'var(--text-dim)',
            }}
          >
            /
          </span>
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              color: 'var(--text-muted)',
            }}
          >
            graph
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Link
            href="/ask"
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: '0.75rem',
              color: 'var(--text-dim)',
              textDecoration: 'none',
              backgroundColor: 'transparent',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '0.25rem 0.625rem',
              transition: 'color 150ms, border-color 150ms',
            }}
          >
            ← Ask
          </Link>

          {!loading && user && (
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.75rem',
                color: 'var(--text-muted)',
                backgroundColor: 'var(--surface-elevated)',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                padding: '0.25rem 0.625rem',
              }}
            >
              {user.email}
            </span>
          )}
          <button
            onClick={() => {
              void logout();
              router.push('/login');
            }}
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: '0.75rem',
              color: 'var(--text-dim)',
              backgroundColor: 'transparent',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '0.25rem 0.625rem',
              cursor: 'pointer',
            }}
          >
            Log out
          </button>
        </div>
      </header>

      {/* Graph area */}
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        {graphQuery.isLoading && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 2,
            }}
          >
            <span
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.875rem',
                color: 'var(--text-dim)',
              }}
            >
              Loading graph…
            </span>
          </div>
        )}

        {graphQuery.isError && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column',
              gap: '0.75rem',
              zIndex: 2,
            }}
          >
            <span
              style={{
                fontFamily: 'var(--font-sans)',
                fontSize: '0.9375rem',
                color: 'var(--text-muted)',
              }}
            >
              No graph data. Index a repository first.
            </span>
            {user?.role === 'admin' && (
              <Link
                href="/admin/repositories"
                style={{
                  fontFamily: 'var(--font-sans)',
                  fontSize: '0.8125rem',
                  color: 'var(--accent)',
                  textDecoration: 'underline',
                  textUnderlineOffset: '2px',
                }}
              >
                Go to Repositories →
              </Link>
            )}
          </div>
        )}

        {isEmpty && !graphQuery.isLoading && (
          <div
            style={{
              position: 'absolute',
              inset: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column',
              gap: '0.75rem',
              zIndex: 2,
            }}
          >
            <span
              style={{
                fontFamily: 'var(--font-sans)',
                fontSize: '0.9375rem',
                color: 'var(--text-muted)',
              }}
            >
              No graph data. Index a repository first.
            </span>
            {user?.role === 'admin' && (
              <Link
                href="/admin/repositories"
                style={{
                  fontFamily: 'var(--font-sans)',
                  fontSize: '0.8125rem',
                  color: 'var(--accent)',
                  textDecoration: 'underline',
                  textUnderlineOffset: '2px',
                }}
              >
                Go to Repositories →
              </Link>
            )}
          </div>
        )}

        {data && data.nodes.length > 0 && (
          <DomainGraph
            data={data}
            repos={repos}
            selectedRepo={selectedRepo}
            onRepoChange={setSelectedRepo}
          />
        )}
      </div>
    </div>
  );
}
