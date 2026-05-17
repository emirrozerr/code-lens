'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { PersonaToggle } from '@/components/chat/PersonaToggle';
import { DomainSidebar } from '@/components/chat/DomainSidebar';
import { EmptyState } from '@/components/chat/EmptyState';
import { MessageBubble } from '@/components/chat/MessageBubble';
import type { ChatMessage, Persona } from '@/types/api';
import { ArrowUp } from 'lucide-react';

// ─── Storage keys ──────────────────────────────────────────────────────────
export const QUESTION_KEY = 'codelens_pending_question';
export const PERSONA_KEY = 'codelens_persona';

const PERSONAS: Persona[] = ['developer', 'product', 'legal'];

// ─── 401 re-auth helper ────────────────────────────────────────────────────
export function triggerReAuth(pendingQuestion?: string): void {
  if (typeof window === 'undefined') return;
  if (pendingQuestion?.trim()) {
    sessionStorage.setItem(QUESTION_KEY, pendingQuestion.trim());
  }
  window.location.href = '/login?reason=expired';
}

// ─── Stub assistant response ───────────────────────────────────────────────
const STUB_RESPONSE =
  'This is a stub response — SSE streaming will be implemented in **Story #49**.\n\n' +
  'Here is an example of markdown rendering:\n\n' +
  '```typescript\n' +
  'function applyDiscount(price: number, pct: number): number {\n' +
  '  return price * (1 - pct / 100);\n' +
  '}\n' +
  '```\n\n' +
  'Lists, **bold**, and `inline code` are also supported.';

// ─── Page ──────────────────────────────────────────────────────────────────

export default function AskPage() {
  const { user, loading, logout } = useAuth();
  const router = useRouter();

  const [persona, setPersona] = useState<Persona>('developer');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [restoredQuestion, setRestoredQuestion] = useState<string | null>(null);

  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
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

  // Persist persona
  useEffect(() => {
    sessionStorage.setItem(PERSONA_KEY, persona);
  }, [persona]);

  // Redirect unauthenticated users
  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [loading, user, router]);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  function resizeTextarea() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  }

  const submitMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isSubmitting) return;

      setInputValue('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
      setIsSubmitting(true);

      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content: trimmed,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMsg]);

      // Stub: 500ms delay then static assistant response
      // Story #49 will replace this with SSE streaming
      await new Promise<void>((resolve) => setTimeout(resolve, 500));

      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: STUB_RESPONSE,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setIsSubmitting(false);
    },
    [isSubmitting],
  );

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void submitMessage(inputValue);
    }
  }

  // DomainSidebar click now auto-submits (no longer just fills input)
  const handleInsertPrompt = useCallback(
    (prompt: string) => {
      void submitMessage(prompt);
    },
    [submitMessage],
  );

  function handlePersonaChange(p: Persona) {
    setPersona(p);
    // Switching mid-conversation only affects next response
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
      {/* Domain browser sidebar (#51) */}
      <DomainSidebar onInsertPrompt={handleInsertPrompt} />

      {/* Chat column */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* ── Header ──────────────────────────────────────────────────────── */}
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

          {/* Persona toggle (#50) */}
          <PersonaToggle value={persona} onChange={handlePersonaChange} />

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

        {/* ── Messages / Empty state ───────────────────────────────────── */}
        <div
          style={{
            flex: 1,
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Re-auth restored question banner */}
          {restoredQuestion && (
            <div
              style={{
                margin: '1rem auto',
                maxWidth: '720px',
                width: '100%',
                padding: '0 1rem',
              }}
            >
              <div
                style={{
                  backgroundColor: 'var(--surface)',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                  padding: '0.75rem 1rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '1rem',
                }}
              >
                <span
                  style={{
                    fontFamily: 'var(--font-sans)',
                    fontSize: '0.875rem',
                    color: 'var(--text-muted)',
                  }}
                >
                  <span style={{ color: 'var(--text-dim)', marginRight: '0.375rem' }}>↩</span>
                  You were asking:{' '}
                  <span style={{ color: 'var(--text)' }}>&ldquo;{restoredQuestion}&rdquo;</span>
                </span>
                <button
                  onClick={() => {
                    void submitMessage(restoredQuestion);
                    setRestoredQuestion(null);
                  }}
                  style={{
                    fontFamily: 'var(--font-sans)',
                    fontSize: '0.8125rem',
                    color: 'var(--accent)',
                    backgroundColor: 'transparent',
                    border: '1px solid rgba(139,92,246,0.4)',
                    borderRadius: '6px',
                    padding: '0.25rem 0.625rem',
                    cursor: 'pointer',
                    flexShrink: 0,
                  }}
                >
                  Resubmit
                </button>
              </div>
            </div>
          )}

          {messages.length === 0 && !restoredQuestion ? (
            <EmptyState onSubmit={(p) => void submitMessage(p)} />
          ) : (
            <div
              style={{
                flex: 1,
                maxWidth: '720px',
                width: '100%',
                margin: '0 auto',
                padding: '1.5rem 0',
                display: 'flex',
                flexDirection: 'column',
                gap: '1.25rem',
              }}
            >
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}

              {/* Typing indicator */}
              {isSubmitting && (
                <div style={{ padding: '0 1rem' }}>
                  <div
                    style={{
                      display: 'inline-flex',
                      gap: '4px',
                      padding: '0.5rem 0.75rem',
                      borderLeft: '2px solid var(--accent)',
                      paddingLeft: '0.875rem',
                    }}
                  >
                    {[0, 1, 2].map((i) => (
                      <span
                        key={i}
                        style={{
                          width: '5px',
                          height: '5px',
                          borderRadius: '50%',
                          backgroundColor: 'var(--text-dim)',
                          animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite`,
                        }}
                      />
                    ))}
                  </div>
                </div>
              )}

              <div ref={bottomRef} />
            </div>
          )}
        </div>

        {/* ── Input area ──────────────────────────────────────────────────── */}
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
              gap: '0.625rem',
              alignItems: 'flex-end',
            }}
          >
            <textarea
              ref={textareaRef}
              value={inputValue}
              onChange={(e) => {
                setInputValue(e.target.value);
                resizeTextarea();
              }}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your codebase… (Enter to send, Shift+Enter for newline)"
              rows={1}
              disabled={isSubmitting}
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
                minHeight: '42px',
                maxHeight: '200px',
                overflowY: 'auto',
                opacity: isSubmitting ? 0.6 : 1,
              }}
            />
            <button
              onClick={() => void submitMessage(inputValue)}
              disabled={!inputValue.trim() || isSubmitting}
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '8px',
                border: 'none',
                backgroundColor:
                  inputValue.trim() && !isSubmitting ? 'var(--accent)' : 'var(--surface-elevated)',
                color: inputValue.trim() && !isSubmitting ? '#fff' : 'var(--text-dim)',
                cursor: inputValue.trim() && !isSubmitting ? 'pointer' : 'not-allowed',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                transition: 'background-color 150ms, color 150ms',
              }}
            >
              <ArrowUp size={16} />
            </button>
          </div>
          <p
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: '0.6875rem',
              color: 'var(--text-dim)',
              textAlign: 'center',
              margin: '0.375rem 0 0',
            }}
          >
            Persona:{' '}
            <span style={{ color: 'var(--text-muted)', textTransform: 'capitalize' }}>{persona}</span>
            {' · '}Enter to send
          </p>
        </div>
      </div>
    </div>
  );
}
