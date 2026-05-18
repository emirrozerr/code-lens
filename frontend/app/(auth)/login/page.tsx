'use client';

import { useState, type FormEvent } from 'react';
import { useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import type { User } from '@/types/api';

// ─── Types ─────────────────────────────────────────────────────────────────

interface LoginSuccess {
  ok: true;
  user: User;
}

interface LoginError {
  ok: false;
  error: string;
}

type LoginResult = LoginSuccess | LoginError;

// ─── Error messages ────────────────────────────────────────────────────────

function friendlyError(raw: string, status: number): string {
  if (status === 401) return 'Invalid email or password.';
  if (status === 503) return 'Authentication service is unavailable. Check your connection.';
  if (raw.toLowerCase().includes('expired')) return 'Your session has expired. Please sign in again.';
  if (raw.toLowerCase().includes('network')) return 'Could not reach the server. Check your connection.';
  return raw || 'Something went wrong. Please try again.';
}

// ─── Page ──────────────────────────────────────────────────────────────────

export default function LoginPage() {
  const searchParams = useSearchParams();

  const reason = searchParams.get('reason');
  const from = searchParams.get('from');

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(
    reason === 'expired' ? 'Your session has expired. Please sign in again.' : null,
  );
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    let result: LoginResult;
    let status = 0;

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      status = res.status;
      result = (await res.json()) as LoginResult;
    } catch {
      setError('Could not reach the server. Check your connection.');
      setLoading(false);
      return;
    }

    if (!result.ok) {
      setError(friendlyError(result.error, status));
      setLoading(false);
      return;
    }

    // Full-page navigation so AuthProvider remounts and re-fetches /api/auth/me
    // with the new cookie. Soft navigation (router.push) keeps the stale auth
    // state from the previous session and triggers the "!user → /login" guard.
    const dest = result.user.role === 'admin' ? '/admin/dashboard' : '/ask';
    window.location.assign(dest);
  }

  return (
    <main
      style={{
        minHeight: '100vh',
        backgroundColor: 'var(--bg)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.5rem',
      }}
    >
      <div style={{ width: '100%', maxWidth: '400px' }}>
        {/* Wordmark */}
        <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
          <p
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              color: 'var(--accent)',
              letterSpacing: '0.15em',
              textTransform: 'uppercase',
              marginBottom: '0.75rem',
            }}
          >
            CodeLens
          </p>
          <h1
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '2rem',
              fontWeight: 400,
              color: 'var(--text)',
              lineHeight: 1.15,
            }}
          >
            Sign in
          </h1>
        </div>

        {/* Card */}
        <div
          style={{
            backgroundColor: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            padding: '2rem',
          }}
        >
          {/* Expired / error banner */}
          {error && (
            <div
              role="alert"
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.08)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                borderRadius: '6px',
                padding: '0.75rem 1rem',
                marginBottom: '1.25rem',
                fontFamily: 'var(--font-sans)',
                fontSize: '0.875rem',
                color: 'var(--danger)',
                lineHeight: 1.5,
              }}
            >
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} noValidate>
            <div style={{ marginBottom: '1rem' }}>
              <label
                htmlFor="email"
                style={{
                  display: 'block',
                  fontFamily: 'var(--font-sans)',
                  fontSize: '0.8125rem',
                  color: 'var(--text-muted)',
                  marginBottom: '0.375rem',
                }}
              >
                Email address
              </label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                autoFocus
                required
                placeholder="you@codelens.dev"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
                style={{
                  backgroundColor: 'var(--surface-elevated)',
                  borderColor: 'var(--border)',
                  color: 'var(--text)',
                  fontFamily: 'var(--font-sans)',
                }}
              />
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label
                htmlFor="password"
                style={{
                  display: 'block',
                  fontFamily: 'var(--font-sans)',
                  fontSize: '0.8125rem',
                  color: 'var(--text-muted)',
                  marginBottom: '0.375rem',
                }}
              >
                Password
              </label>
              <Input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                style={{
                  backgroundColor: 'var(--surface-elevated)',
                  borderColor: 'var(--border)',
                  color: 'var(--text)',
                  fontFamily: 'var(--font-sans)',
                }}
              />
            </div>

            <Button
              type="submit"
              disabled={loading || !email || !password}
              style={{
                width: '100%',
                backgroundColor: loading ? 'var(--surface-elevated)' : 'var(--accent)',
                color: loading ? 'var(--text-muted)' : '#ffffff',
                border: 'none',
                fontFamily: 'var(--font-sans)',
                fontWeight: 500,
                cursor: loading ? 'not-allowed' : 'pointer',
                transition: 'background-color 150ms ease',
              }}
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>
        </div>

        {/* Dev hint */}
        {process.env.NODE_ENV !== 'production' && (
          <p
            style={{
              marginTop: '1.5rem',
              textAlign: 'center',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.6875rem',
              color: 'var(--text-dim)',
              lineHeight: 1.6,
            }}
          >
            mock: admin@codelens.dev · user@codelens.dev
            <br />
            any password
          </p>
        )}
      </div>
    </main>
  );
}
