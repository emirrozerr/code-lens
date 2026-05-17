'use client';

import { useQuery } from '@tanstack/react-query';
import { getStats, listJobs } from '@/lib/api/endpoints';
import { KpiCard } from '@/components/admin/KpiCard';
import { JobsTable } from '@/components/admin/JobsTable';
import { HealthCard } from '@/components/admin/HealthCard';

export default function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
    refetchOnWindowFocus: true,
  });

  const { data: jobs = [], isLoading: jobsLoading } = useQuery({
    queryKey: ['jobs', 10],
    queryFn: () => listJobs(10),
    refetchOnWindowFocus: true,
  });

  return (
    <div
      style={{
        padding: '2rem',
        maxWidth: '1400px',
        margin: '0 auto',
      }}
    >
      {/* Page heading */}
      <div style={{ marginBottom: '2rem', animation: 'fade-up 300ms ease-out both' }}>
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
          Dashboard
        </h1>
        <p
          style={{
            fontFamily: 'var(--font-sans)',
            fontSize: '0.875rem',
            color: 'var(--text-dim)',
            marginTop: '0.375rem',
          }}
        >
          System overview and recent indexing activity
        </p>
      </div>

      {/* KPI row */}
      <div
        style={{
          display: 'flex',
          gap: '1rem',
          marginBottom: '1.5rem',
          flexWrap: 'wrap',
        }}
      >
        <KpiCard
          label="Repos Indexed"
          value={stats?.reposCount ?? 0}
          isLoading={statsLoading}
          delay={50}
        />
        <KpiCard
          label="Total Nodes"
          value={stats?.totalNodes ?? 0}
          isLoading={statsLoading}
          delay={100}
        />
        <KpiCard
          label="Domains"
          value={stats?.domainsCount ?? 0}
          color="var(--success)"
          isLoading={statsLoading}
          delay={150}
        />
        <KpiCard
          label="Active Users"
          value={stats?.activeUsers ?? 0}
          color="var(--accent)"
          isLoading={statsLoading}
          delay={200}
        />
      </div>

      {/* Two-column grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr 320px',
          gap: '1rem',
          alignItems: 'start',
        }}
      >
        <JobsTable jobs={jobs} isLoading={jobsLoading} />
        <HealthCard stats={stats} isLoading={statsLoading} />
      </div>
    </div>
  );
}
