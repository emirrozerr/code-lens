'use client';

import { useState, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { listRepos, listDomains, updateDomain, regenerateDomainSummary } from '@/lib/api/endpoints';
import { ApiError } from '@/lib/api/client';
import type { Domain } from '@/types/api';
import { DomainCard } from '@/components/admin/DomainCard';
import { Skeleton } from '@/components/ui/skeleton';

export default function DomainsPage() {
  const queryClient = useQueryClient();
  const searchParams = useSearchParams();
  const [repoFilter, setRepoFilter] = useState<string>(searchParams.get('repo') ?? '');
  const [regeneratingId, setRegeneratingId] = useState<string | null>(null);

  const { data: repos = [] } = useQuery({
    queryKey: ['repos'],
    queryFn: listRepos,
  });

  const domainQueryKey = ['domains', repoFilter];

  const { data: domains = [], isLoading: domainsLoading, isError: domainsError } = useQuery({
    queryKey: domainQueryKey,
    queryFn: () => listDomains(repoFilter || undefined),
    refetchOnWindowFocus: true,
  });

  const updateMutation = useMutation({
    mutationFn: ({
      id,
      summary,
      humanVerified,
    }: {
      id: string;
      summary: string;
      humanVerified: boolean;
    }) => updateDomain(id, summary, humanVerified),
    onMutate: async ({ id, summary, humanVerified }) => {
      await queryClient.cancelQueries({ queryKey: domainQueryKey });
      const prev = queryClient.getQueryData<Domain[]>(domainQueryKey);
      queryClient.setQueryData<Domain[]>(domainQueryKey, (old) =>
        old?.map((d) => (d.id === id ? { ...d, summary, humanVerified } : d)) ?? [],
      );
      return { prev };
    },
    onError: (_err, _vars, context) => {
      if (context?.prev) {
        queryClient.setQueryData(domainQueryKey, context.prev);
      }
      toast.error('Failed to save changes');
    },
    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: domainQueryKey });
    },
  });

  const regenerateMutation = useMutation({
    mutationFn: (id: string) => regenerateDomainSummary(id),
    onMutate: (id) => {
      setRegeneratingId(id);
    },
    onSuccess: (updated) => {
      queryClient.setQueryData<Domain[]>(domainQueryKey, (old) =>
        old?.map((d) => (d.id === updated.id ? updated : d)) ?? [],
      );
      toast.success('Summary regenerated');
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : 'Failed to regenerate summary');
    },
    onSettled: () => {
      setRegeneratingId(null);
    },
  });

  const handleSave = useCallback(
    (id: string, summary: string, humanVerified: boolean) => {
      updateMutation.mutate({ id, summary, humanVerified });
    },
    [updateMutation],
  );

  const handleRegenerate = useCallback(
    (id: string) => {
      regenerateMutation.mutate(id);
    },
    [regenerateMutation],
  );

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          marginBottom: '2rem',
          animation: 'fade-up 300ms ease-out both',
        }}
      >
        <div>
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
            Domains
          </h1>
          <p
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: '0.875rem',
              color: 'var(--text-dim)',
              marginTop: '0.375rem',
            }}
          >
            {domains.length} domain{domains.length === 1 ? '' : 's'}
            {repoFilter && repos.find((r) => r.id === repoFilter)
              ? ` in ${repos.find((r) => r.id === repoFilter)?.name}`
              : ' across all repositories'}
          </p>
        </div>

        {/* Repo filter */}
        <select
          value={repoFilter}
          onChange={(e) => setRepoFilter(e.target.value)}
          style={{
            fontFamily: 'var(--font-sans)',
            fontSize: '0.8125rem',
            color: 'var(--text-muted)',
            backgroundColor: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: '6px',
            padding: '0.375rem 0.75rem',
            cursor: 'pointer',
            outline: 'none',
            minWidth: '180px',
          }}
        >
          <option value="">All repositories</option>
          {repos.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name}
            </option>
          ))}
        </select>
      </div>

      {/* Domain grid */}
      {domainsError ? (
        <div style={{ padding: '0.75rem 1rem', backgroundColor: 'var(--surface)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: '8px', fontFamily: 'var(--font-sans)', fontSize: '0.875rem', color: 'var(--danger)' }}>
          Failed to load domains. Check your connection and try again.
        </div>
      ) : domainsLoading ? (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '1rem',
          }}
        >
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-48 rounded-lg" />
          ))}
        </div>
      ) : domains.length === 0 ? (
        <div
          style={{
            textAlign: 'center',
            padding: '4rem 2rem',
            fontFamily: 'var(--font-sans)',
            color: 'var(--text-dim)',
            fontSize: '0.875rem',
          }}
        >
          No domains found
          {repoFilter ? ' for this repository' : ''}.
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '1rem',
          }}
        >
          {domains.map((domain, i) => (
            <div
              key={domain.id}
              style={{ animationDelay: `${i * 30}ms` }}
            >
              <DomainCard
                domain={domain}
                isRegenerating={regeneratingId === domain.id}
                onSave={handleSave}
                onRegenerate={handleRegenerate}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
