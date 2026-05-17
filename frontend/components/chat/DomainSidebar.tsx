'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { listDomains } from '@/lib/api/endpoints';
import { ChevronLeft, ChevronRight, Search } from 'lucide-react';

interface DomainSidebarProps {
  onInsertPrompt: (prompt: string) => void;
}

export function DomainSidebar({ onInsertPrompt }: DomainSidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [search, setSearch] = useState('');
  const [activeDomainId, setActiveDomainId] = useState<string | null>(null);

  const { data: domains = [] } = useQuery({
    queryKey: ['domains', ''],
    queryFn: () => listDomains(),
  });

  const filtered = domains.filter(
    (d) =>
      d.name.toLowerCase().includes(search.toLowerCase()) ||
      d.summary.toLowerCase().includes(search.toLowerCase()),
  );

  function handleDomainClick(id: string, name: string) {
    setActiveDomainId(id);
    onInsertPrompt(
      `Tell me about the ${name} domain — what does it do, what are its key functions, and what are its dependencies?`,
    );
  }

  if (collapsed) {
    return (
      <div
        style={{
          width: '36px',
          minWidth: '36px',
          backgroundColor: 'var(--surface)',
          borderRight: '1px solid var(--border)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          paddingTop: '0.75rem',
          flexShrink: 0,
        }}
      >
        <button
          onClick={() => setCollapsed(false)}
          title="Expand domain browser"
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '4px',
            border: '1px solid var(--border)',
            backgroundColor: 'transparent',
            color: 'var(--text-dim)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <ChevronRight size={14} />
        </button>
      </div>
    );
  }

  return (
    <div
      style={{
        width: '260px',
        minWidth: '260px',
        backgroundColor: 'var(--surface)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          height: '52px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 0.75rem',
          borderBottom: '1px solid var(--border)',
          flexShrink: 0,
        }}
      >
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.6875rem',
            color: 'var(--text-dim)',
            letterSpacing: '0.1em',
            textTransform: 'uppercase',
          }}
        >
          Domains
          {domains.length > 0 && (
            <span style={{ marginLeft: '0.375rem', color: 'var(--text-dim)', opacity: 0.6 }}>
              {domains.length}
            </span>
          )}
        </span>
        <button
          onClick={() => setCollapsed(true)}
          title="Collapse domain browser"
          style={{
            width: '24px',
            height: '24px',
            borderRadius: '4px',
            border: 'none',
            backgroundColor: 'transparent',
            color: 'var(--text-dim)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <ChevronLeft size={13} />
        </button>
      </div>

      {/* Search */}
      <div style={{ padding: '0.625rem 0.75rem', borderBottom: '1px solid var(--border)', flexShrink: 0 }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            backgroundColor: 'var(--surface-elevated)',
            border: '1px solid var(--border)',
            borderRadius: '6px',
            padding: '0.375rem 0.625rem',
          }}
        >
          <Search size={12} style={{ color: 'var(--text-dim)', flexShrink: 0 }} />
          <input
            type="text"
            placeholder="Filter domains…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: '0.8125rem',
              color: 'var(--text)',
              backgroundColor: 'transparent',
              border: 'none',
              outline: 'none',
              width: '100%',
            }}
          />
        </div>
      </div>

      {/* Domain list */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {domains.length === 0 ? (
          <div
            style={{
              padding: '2rem 1rem',
              fontFamily: 'var(--font-sans)',
              fontSize: '0.8125rem',
              color: 'var(--text-dim)',
              lineHeight: 1.6,
              textAlign: 'center',
            }}
          >
            No domains discovered yet.
            <br />
            Index a repository first.
          </div>
        ) : filtered.length === 0 ? (
          <div
            style={{
              padding: '2rem 1rem',
              fontFamily: 'var(--font-sans)',
              fontSize: '0.8125rem',
              color: 'var(--text-dim)',
              textAlign: 'center',
            }}
          >
            No domains match &ldquo;{search}&rdquo;
          </div>
        ) : (
          filtered.map((domain) => {
            const active = domain.id === activeDomainId;
            return (
              <button
                key={domain.id}
                onClick={() => handleDomainClick(domain.id, domain.name)}
                style={{
                  display: 'block',
                  width: '100%',
                  textAlign: 'left',
                  padding: '0.75rem 0.875rem',
                  borderTop: 'none',
                  borderRight: 'none',
                  borderBottom: '1px solid var(--border)',
                  borderLeft: active ? '2px solid var(--accent)' : '2px solid transparent',
                  backgroundColor: active ? 'var(--accent-glow)' : 'transparent',
                  cursor: 'pointer',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'baseline',
                    justifyContent: 'space-between',
                    gap: '0.5rem',
                    marginBottom: '0.25rem',
                  }}
                >
                  <span
                    style={{
                      fontFamily: 'var(--font-sans)',
                      fontSize: '0.8125rem',
                      fontWeight: 500,
                      color: active ? 'var(--text)' : 'var(--text-muted)',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                    }}
                  >
                    {domain.name}
                  </span>
                  <span
                    style={{
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.6875rem',
                      color: 'var(--text-dim)',
                      flexShrink: 0,
                    }}
                  >
                    {domain.memberCount}
                  </span>
                </div>
                <p
                  style={{
                    fontFamily: 'var(--font-sans)',
                    fontSize: '0.75rem',
                    color: 'var(--text-dim)',
                    margin: 0,
                    overflow: 'hidden',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    lineHeight: 1.5,
                  }}
                >
                  {domain.summary}
                </p>
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
