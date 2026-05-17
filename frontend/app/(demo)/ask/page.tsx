'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import type { Persona } from '@/types/api';

// ─── Storage keys (imported by Story #48 chat implementation) ──────────────
export const QUESTION_KEY = 'codelens_pending_question';
export const PERSONA_KEY = 'codelens_persona';

const PERSONAS: Persona[] = ['developer', 'product', 'legal'];
const PERSONA_LABELS: Record<Persona, string> = {
  developer: 'Developer',
  product: 'Product',
  legal: 'Legal',
};

// ─── 401 re-auth helper (called by chat SSE handler in Story #48) ──────────
export function triggerReAuth(pendingQuestion?: string): void {
  if (typeof window === 'undefined') return;
  if (pendingQuestion?.trim()) {
    sessionStorage.setItem(QUESTION_KEY, pendingQuestion.trim());
  }
  window.location.href = '/login?reason=expired';
}

// ─── Page ──────────────────────────────────────────────────────────────────

export default function AskPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  const [persona, setPersona] = useState<Persona>('developer');
  // Pending question restored after a re-auth redirect
  const [restoredQuestion, setRestoredQuestion] = useState<string | null>(null);
  const restored = useRef(false);

  // Restore sessionStorage on first mount
  useEffect(() => {
    if (restored.current) return;
    restored.current = true;

    const savedPersona = sessionStorage.getItem(PERSONA_KEY);
    if (savedPersona && (PERSONAS as string[]).includes(savedPersona)) {
      setPersona(savedPersona as Persona);
    }

    const savedQ = sessionStorage.getItem(QUESTION_KEY);
    if (savedQ) {
      setRestoredQuestion(savedQ);
      sessionStorage.removeItem(QUESTION_KEY);
    }
  }, []);

  // Persist persona selection
  useEffect(() => {
    sessionStorage.setItem(PERSONA_KEY, persona);
  }, [persona]);

  function cyclePersona() {
    setPersona((p) => {
      const next = PERSONAS[(PERSONAS.indexOf(p) + 1) % PERSONAS.length];
      return next ?? p;
    });
  }

  // Redirect unauthenticated users (extra client-side guard; middleware is primary)
  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [loading, user, router]);

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: 'var(--bg)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* ── Header ─────────────────────────────────────────────────────── */}
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
        }}
      >
        {/* Wordmark */}
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

        {/* Persona badge — full segmented control added in Story #50 */}
        <button
          onClick={cyclePersona}
          title="Click to switch persona (full toggle in Story #50)"
          style={{
            fontFamily: 'var(--font-sans)',
            fontSize: '0.75rem',
            color: 'var(--accent)',
            backgroundColor: 'var(--accent-glow)',
            border: '1px solid var(--accent)',
            borderRadius: '999px',
            padding: '0.25rem 0.75rem',
            cursor: 'pointer',
            letterSpacing: '0.03em',
          }}
        >
          {PERSONA_LABELS[persona]}
        </button>

        {/* User chip + logout */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
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
            onClick={() => void logout()}
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

      {/* ── Chat area (Story #48) ───────────────────────────────────────── */}
      <main
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '2rem',
          gap: '1rem',
        }}
      >
        {restoredQuestion && (
          <div
            style={{
              maxWidth: '560px',
              width: '100%',
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              padding: '1rem 1.25rem',
              fontFamily: 'var(--font-sans)',
              fontSize: '0.875rem',
              color: 'var(--text-muted)',
              lineHeight: 1.6,
            }}
          >
            <span style={{ color: 'var(--text-dim)', marginRight: '0.5rem' }}>↩</span>
            Restored:{' '}
            <span style={{ color: 'var(--text)' }}>&ldquo;{restoredQuestion}&rdquo;</span>
          </div>
        )}

        <p
          style={{
            fontFamily: 'var(--font-sans)',
            fontSize: '0.875rem',
            color: 'var(--text-dim)',
          }}
        >
          Chat UI — Story #48
        </p>
      </main>
    </div>
  );
}
