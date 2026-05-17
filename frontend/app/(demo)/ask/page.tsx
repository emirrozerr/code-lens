'use client';

import { useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { PersonaToggle } from '@/components/chat/PersonaToggle';
import { DomainSidebar } from '@/components/chat/DomainSidebar';
import type { Persona } from '@/types/api';

// ─── Storage keys (imported by Story #49 chat implementation) ──────────────
export const QUESTION_KEY = 'codelens_pending_question';
export const PERSONA_KEY = 'codelens_persona';

const PERSONAS: Persona[] = ['developer', 'product', 'legal'];

// ─── 401 re-auth helper (called by chat SSE handler in Story #49) ──────────
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
  const [inputValue, setInputValue] = useState('');
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
      setInputValue(savedQ);
      sessionStorage.removeItem(QUESTION_KEY);
    }
  }, []);

  // Persist persona selection
  useEffect(() => {
    sessionStorage.setItem(PERSONA_KEY, persona);
  }, [persona]);

  // Redirect unauthenticated users
  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [loading, user, router]);

  function handlePersonaChange(p: Persona) {
    setPersona(p);
    // Switching mid-conversation only affects the next response — no message rewrite needed
  }

  function handleInsertPrompt(prompt: string) {
    setInputValue(prompt);
  }

  return (
    <div
      style={{
        height: '100vh',
        backgroundColor: 'var(--bg)',
        display: 'flex',
        overflow: 'hidden',
      }}
    >
      {/* Domain browser sidebar (Story #51) */}
      <DomainSidebar onInsertPrompt={handleInsertPrompt} />

      {/* Chat column */}
      <div
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          minWidth: 0,
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
            gap: '1rem',
          }}
        >
          {/* Wordmark */}
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.8125rem',
              color: 'var(--accent)',
              letterSpacing: '0.08em',
              flexShrink: 0,
            }}
          >
            CodeLens
          </span>

          {/* Persona toggle (Story #50) */}
          <PersonaToggle value={persona} onChange={handlePersonaChange} />

          {/* User chip + logout */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexShrink: 0 }}>
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

        {/* ── Messages area ───────────────────────────────────────────────── */}
        <main
          style={{
            flex: 1,
            overflowY: 'auto',
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

          {/* Empty state — replaced by ChatPage in Story #48 */}
          <div
            style={{
              textAlign: 'center',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '0.5rem',
            }}
          >
            <p
              style={{
                fontFamily: "'Instrument Serif', Georgia, serif",
                fontSize: '1.75rem',
                fontWeight: 400,
                color: 'var(--text)',
                margin: 0,
              }}
            >
              Ask CodeLens
            </p>
            <p
              style={{
                fontFamily: 'var(--font-sans)',
                fontSize: '0.875rem',
                color: 'var(--text-dim)',
                margin: 0,
              }}
            >
              Chat implementation — Story #48
            </p>
          </div>
        </main>

        {/* ── Chat input stub (replaced by ChatInput in Story #48) ─────── */}
        <div
          style={{
            borderTop: '1px solid var(--border)',
            backgroundColor: 'var(--surface)',
            padding: '0.875rem 1.5rem',
            flexShrink: 0,
          }}
        >
          <div
            style={{
              maxWidth: '720px',
              margin: '0 auto',
              display: 'flex',
              gap: '0.75rem',
              alignItems: 'flex-end',
            }}
          >
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask about your codebase…"
              rows={2}
              style={{
                flex: 1,
                fontFamily: 'var(--font-sans)',
                fontSize: '0.9375rem',
                color: 'var(--text)',
                backgroundColor: 'var(--surface-elevated)',
                border: '1px solid var(--border)',
                borderRadius: '8px',
                padding: '0.625rem 0.875rem',
                resize: 'none',
                outline: 'none',
                lineHeight: 1.5,
              }}
            />
            <button
              disabled
              title="Chat implementation coming in Story #48"
              style={{
                padding: '0.625rem 1.25rem',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: 'var(--accent)',
                color: '#fff',
                fontFamily: 'var(--font-sans)',
                fontSize: '0.875rem',
                cursor: 'not-allowed',
                opacity: 0.5,
                flexShrink: 0,
              }}
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
