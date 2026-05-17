'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { PersonaToggle } from '@/components/chat/PersonaToggle';
import { DomainSidebar } from '@/components/chat/DomainSidebar';
import { EmptyState } from '@/components/chat/EmptyState';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { createChatStream } from '@/lib/api/sse';
import type { ChatEvent, ChatMessage, Persona, ToolCallRecord } from '@/types/api';
import { ArrowUp, Square } from 'lucide-react';

// ─── Storage keys ──────────────────────────────────────────────────────────
export const QUESTION_KEY = 'codelens_pending_question';
export const PERSONA_KEY = 'codelens_persona';

const PERSONAS: Persona[] = ['developer', 'product', 'legal'];
const MAX_HISTORY = 10;

// ─── 401 re-auth helper ────────────────────────────────────────────────────
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
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [restoredQuestion, setRestoredQuestion] = useState<string | null>(null);

  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const restored = useRef(false);
  // Tracks the active stream so we can cancel it
  const activeStreamRef = useRef<{ cancel: () => void } | null>(null);
  // Tracks the current pending question for 401 reauth
  const pendingQuestionRef = useRef<string>('');
  // Tracks retry state — one retry per submit
  const hasRetriedRef = useRef(false);

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

  // Cancel the active stream
  const cancelStream = useCallback(() => {
    if (activeStreamRef.current) {
      activeStreamRef.current.cancel();
      activeStreamRef.current = null;
    }
    setIsStreaming(false);
  }, []);

  const runStream = useCallback(
    (
      text: string,
      currentPersona: Persona,
      history: ChatMessage[],
      assistantMsgId: string,
    ) => {
      hasRetriedRef.current = false;
      setStreamError(null);

      const stream = createChatStream(text, currentPersona, history);
      activeStreamRef.current = stream;

      // Mutable accumulator for this stream run — kept in closure, flushed to React state via setMessages
      const toolMap = new Map<string, ToolCallRecord>();
      const toolOrder: string[] = [];
      let textContent = '';

      const flush = () => {
        const toolCalls = toolOrder.map((id) => toolMap.get(id)!);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsgId
              ? { ...m, content: textContent, toolCalls }
              : m,
          ),
        );
      };

      const handleEvent = (event: ChatEvent) => {
        if (event.type === 'token') {
          textContent += event.content;
          flush();
        } else if (event.type === 'tool_call_start') {
          const tc: ToolCallRecord = {
            id: event.id,
            tool: event.tool,
            args: event.args,
            result: null,
            durationMs: null,
            status: 'running',
            error: null,
          };
          toolMap.set(event.id, tc);
          toolOrder.push(event.id);
          flush();
        } else if (event.type === 'tool_call_end') {
          const existing = toolMap.get(event.id);
          if (existing) {
            toolMap.set(event.id, {
              ...existing,
              result: event.result,
              durationMs: event.durationMs,
              status: 'done',
            });
          } else {
            const orphan: ToolCallRecord = {
              id: event.id,
              tool: 'unknown',
              args: {},
              result: event.result,
              durationMs: event.durationMs,
              status: 'error',
              error: 'Unmatched tool_call_end',
            };
            toolMap.set(event.id, orphan);
            toolOrder.push(event.id);
          }
          flush();
        } else if (event.type === 'done') {
          activeStreamRef.current = null;
          setIsStreaming(false);
        } else if (event.type === 'error') {
          activeStreamRef.current = null;

          // 401 → re-auth
          if (event.message.includes('401') || event.message.includes('Unauthorized')) {
            triggerReAuth(pendingQuestionRef.current);
            return;
          }

          // First failure → retry once silently
          if (!hasRetriedRef.current) {
            hasRetriedRef.current = true;
            toolMap.clear();
            toolOrder.length = 0;
            textContent = '';
            flush();

            const retryStream = createChatStream(text, currentPersona, history);
            activeStreamRef.current = retryStream;
            retryStream.onEvent(handleEvent);
            return;
          }

          // Second failure → show error state
          setStreamError(event.message);
          setIsStreaming(false);
        }
      };

      stream.onEvent(handleEvent);
    },
    [],
  );

  const submitMessage = useCallback(
    (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isStreaming) return;

      pendingQuestionRef.current = trimmed;
      setInputValue('');
      setStreamError(null);
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }

      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content: trimmed,
        timestamp: new Date().toISOString(),
      };

      const assistantMsgId = crypto.randomUUID();
      const assistantMsg: ChatMessage = {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        toolCalls: [],
      };

      setMessages((prev) => {
        const next = [...prev, userMsg, assistantMsg];
        // Build history from all messages before the new ones (last MAX_HISTORY)
        const history = prev.slice(-MAX_HISTORY);
        // Defer stream start after state update
        setTimeout(() => {
          setIsStreaming(true);
          runStream(trimmed, persona, history, assistantMsgId);
        }, 0);
        return next;
      });
    },
    [isStreaming, persona, runStream],
  );

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitMessage(inputValue);
    }
  }

  const handleInsertPrompt = useCallback(
    (prompt: string) => {
      submitMessage(prompt);
    },
    [submitMessage],
  );

  function handlePersonaChange(p: Persona) {
    setPersona(p);
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
                    submitMessage(restoredQuestion);
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
            <EmptyState onSubmit={submitMessage} />
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

              {/* Streaming indicator (only when no content yet) */}
              {isStreaming &&
                messages.length > 0 &&
                messages[messages.length - 1].content === '' &&
                (!messages[messages.length - 1].toolCalls ||
                  messages[messages.length - 1].toolCalls!.length === 0) && (
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

              {/* Stream error with retry */}
              {streamError && (
                <div
                  style={{
                    padding: '0 1rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                  }}
                >
                  <span
                    style={{
                      fontFamily: 'var(--font-sans)',
                      fontSize: '0.875rem',
                      color: 'var(--danger)',
                    }}
                  >
                    Connection lost: {streamError}
                  </span>
                  <button
                    onClick={() => {
                      if (!pendingQuestionRef.current) return;
                      // Remove the failed assistant message and retry
                      setMessages((prev) => {
                        const withoutLast =
                          prev[prev.length - 1].role === 'assistant'
                            ? prev.slice(0, -1)
                            : prev;
                        const history = withoutLast.slice(-MAX_HISTORY);
                        const newAssistantId = crypto.randomUUID();
                        const newAssistant: ChatMessage = {
                          id: newAssistantId,
                          role: 'assistant',
                          content: '',
                          timestamp: new Date().toISOString(),
                          toolCalls: [],
                        };
                        setStreamError(null);
                        setIsStreaming(true);
                        setTimeout(() => {
                          runStream(
                            pendingQuestionRef.current,
                            persona,
                            history,
                            newAssistantId,
                          );
                        }, 0);
                        return [...withoutLast, newAssistant];
                      });
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
                    Retry
                  </button>
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
              disabled={isStreaming}
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
                opacity: isStreaming ? 0.6 : 1,
              }}
            />
            {/* Cancel button during streaming */}
            {isStreaming ? (
              <button
                onClick={cancelStream}
                style={{
                  width: '38px',
                  height: '38px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-strong)',
                  backgroundColor: 'var(--surface-elevated)',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                }}
                title="Cancel"
              >
                <Square size={14} />
              </button>
            ) : (
              <button
                onClick={() => submitMessage(inputValue)}
                disabled={!inputValue.trim() || isStreaming}
                style={{
                  width: '38px',
                  height: '38px',
                  borderRadius: '8px',
                  border: 'none',
                  backgroundColor:
                    inputValue.trim() && !isStreaming
                      ? 'var(--accent)'
                      : 'var(--surface-elevated)',
                  color: inputValue.trim() && !isStreaming ? '#fff' : 'var(--text-dim)',
                  cursor: inputValue.trim() && !isStreaming ? 'pointer' : 'not-allowed',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  transition: 'background-color 150ms, color 150ms',
                }}
              >
                <ArrowUp size={16} />
              </button>
            )}
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
            {' · '}
            {isStreaming ? 'Streaming…' : 'Enter to send'}
          </p>
        </div>
      </div>
    </div>
  );
}
