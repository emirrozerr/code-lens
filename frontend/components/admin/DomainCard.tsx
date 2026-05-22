'use client';

import { useState, useRef, useCallback } from 'react';
import type { Domain } from '@/types/api';
import { RefreshCw } from 'lucide-react';

interface DomainCardProps {
  domain: Domain;
  isRegenerating?: boolean;
  onSave: (id: string, summary: string, humanVerified: boolean) => void;
  onRegenerate: (id: string) => void;
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-GB', { dateStyle: 'medium' });
}

export function DomainCard({ domain, isRegenerating, onSave, onRegenerate }: DomainCardProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(domain.summary);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  function startEdit() {
    setDraft(domain.summary);
    setEditing(true);
    // Focus after render
    setTimeout(() => textareaRef.current?.focus(), 0);
  }

  const commitEdit = useCallback(() => {
    setEditing(false);
    const trimmed = draft.trim();
    if (trimmed && trimmed !== domain.summary) {
      onSave(domain.id, trimmed, domain.humanVerified);
    }
  }, [draft, domain.id, domain.summary, domain.humanVerified, onSave]);

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault();
      commitEdit();
    }
    if (e.key === 'Escape') {
      setEditing(false);
      setDraft(domain.summary);
    }
  }

  function toggleVerified() {
    onSave(domain.id, domain.summary, !domain.humanVerified);
  }

  return (
    <div
      className="group"
      style={{
        backgroundColor: isRegenerating ? 'var(--surface-elevated)' : 'var(--surface)',
        border: '1px solid var(--border)',
        borderRadius: '8px',
        padding: '1.25rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.75rem',
        position: 'relative',
        transition: 'background-color 200ms',
        animation: 'fade-up 300ms ease-out both',
      }}
    >
      {/* Regenerate button — hover only */}
      <button
        className="opacity-0 group-hover:opacity-100"
        onClick={() => onRegenerate(domain.id)}
        disabled={isRegenerating}
        title="Regenerate summary"
        style={{
          position: 'absolute',
          top: '0.75rem',
          right: '0.75rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '24px',
          height: '24px',
          borderRadius: '4px',
          border: '1px solid var(--border)',
          backgroundColor: 'var(--surface-elevated)',
          color: 'var(--text-dim)',
          cursor: 'pointer',
          transition: 'opacity 150ms',
        }}
      >
        <RefreshCw
          size={12}
          style={isRegenerating ? { animation: 'spin 1s linear infinite' } : undefined}
        />
      </button>

      {/* Human-verified toggle — top right (behind regenerate when hovered) */}
      <div
        style={{
          position: 'absolute',
          top: '0.75rem',
          right: '3rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.375rem',
        }}
      >
        <button
          onClick={toggleVerified}
          title={domain.humanVerified ? 'Human verified' : 'Mark as verified'}
          style={{
            width: '32px',
            height: '18px',
            borderRadius: '999px',
            border: 'none',
            cursor: 'pointer',
            backgroundColor: domain.humanVerified ? 'var(--success)' : 'var(--border-strong)',
            position: 'relative',
            transition: 'background-color 200ms',
            flexShrink: 0,
          }}
        >
          <span
            style={{
              position: 'absolute',
              top: '2px',
              left: domain.humanVerified ? '16px' : '2px',
              width: '14px',
              height: '14px',
              borderRadius: '50%',
              backgroundColor: '#fff',
              transition: 'left 200ms',
            }}
          />
        </button>
      </div>

      {/* Name + member count */}
      <div style={{ paddingRight: '4rem' }}>
        <div
          style={{
            fontFamily: 'var(--font-sans)',
            fontSize: '0.9375rem',
            fontWeight: 500,
            color: 'var(--text)',
            lineHeight: 1.3,
          }}
        >
          {domain.name}
        </div>
        <div
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            color: 'var(--text-dim)',
            marginTop: '0.125rem',
          }}
        >
          {domain.memberCount} members · {domain.repoName}
        </div>
      </div>

      {/* Summary — editable */}
      {editing ? (
        <textarea
          ref={textareaRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onBlur={commitEdit}
          onKeyDown={handleKeyDown}
          rows={4}
          style={{
            fontFamily: 'var(--font-sans)',
            fontSize: '0.8125rem',
            color: 'var(--text)',
            lineHeight: 1.6,
            backgroundColor: 'var(--surface-elevated)',
            border: '1px solid var(--accent)',
            borderRadius: '4px',
            padding: '0.5rem 0.625rem',
            resize: 'vertical',
            outline: 'none',
            width: '100%',
            boxSizing: 'border-box',
          }}
        />
      ) : (
        <p
          onClick={startEdit}
          title="Click to edit"
          style={{
            fontFamily: 'var(--font-sans)',
            fontSize: '0.8125rem',
            color: isRegenerating ? 'var(--text-dim)' : 'var(--text-muted)',
            lineHeight: 1.6,
            cursor: 'text',
            margin: 0,
            animation: isRegenerating ? 'pulse 1.5s ease-in-out infinite' : undefined,
          }}
        >
          {domain.summary}
        </p>
      )}

      {/* Footer: timestamp + verified label */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginTop: 'auto',
        }}
      >
        <span
          style={{
            fontFamily: 'var(--font-sans)',
            fontSize: '0.75rem',
            color: 'var(--text-dim)',
          }}
        >
          Updated {formatDate(domain.lastUpdated)}
        </span>
        {domain.humanVerified && (
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.6875rem',
              color: 'var(--success)',
              letterSpacing: '0.04em',
            }}
          >
            verified
          </span>
        )}
      </div>
    </div>
  );
}
