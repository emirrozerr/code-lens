import { type NextRequest, NextResponse } from 'next/server';
import type { User } from '@/types/api';
import { MOCK_USERS } from '@/lib/api/mocks';

const COOKIE_NAME = process.env.JWT_COOKIE_NAME ?? 'codelens_token';
const IS_MOCK = process.env.NEXT_PUBLIC_MOCK_MODE === 'true';

// Minimal JWT-shaped token for mock mode: header.payload.sig
// Real JWTs from the FastAPI backend are used as-is in production mode.
function createMockToken(user: User): string {
  const header = Buffer.from(JSON.stringify({ alg: 'none', typ: 'JWT' })).toString('base64url');
  const payload = Buffer.from(
    JSON.stringify({
      sub: user.id,
      email: user.email,
      role: user.role,
      exp: Math.floor(Date.now() / 1000) + 86400,
    }),
  ).toString('base64url');
  return `${header}.${payload}.mock_sig`;
}

function setCookie(response: NextResponse, token: string): void {
  response.cookies.set(COOKIE_NAME, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 86400,
    path: '/',
  });
}

export async function POST(request: NextRequest): Promise<NextResponse> {
  let body: { email?: unknown; password?: unknown };
  try {
    body = (await request.json()) as { email?: unknown; password?: unknown };
  } catch {
    return NextResponse.json({ ok: false, error: 'Invalid request body' }, { status: 400 });
  }

  const email = typeof body.email === 'string' ? body.email.trim() : '';
  const password = typeof body.password === 'string' ? body.password : '';

  if (!email || !password) {
    return NextResponse.json({ ok: false, error: 'Email and password are required' }, { status: 400 });
  }

  // ── Mock mode ────────────────────────────────────────────────────────────
  if (IS_MOCK) {
    const user = MOCK_USERS.find((u) => u.email === email);
    if (!user) {
      return NextResponse.json({ ok: false, error: 'Invalid credentials' }, { status: 401 });
    }
    // Accept any password in mock mode
    const token = createMockToken(user);
    const response = NextResponse.json({ ok: true, user });
    setCookie(response, token);
    return response;
  }

  // ── Real backend ─────────────────────────────────────────────────────────
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';
  try {
    const res = await fetch(`${baseUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });

    if (!res.ok) {
      let errorMessage = 'Invalid credentials';
      try {
        const err = (await res.json()) as Record<string, unknown>;
        if (typeof err.detail === 'string') errorMessage = err.detail;
        else if (typeof err.message === 'string') errorMessage = err.message;
      } catch {
        // non-JSON error body
      }
      return NextResponse.json({ ok: false, error: errorMessage }, { status: res.status });
    }

    const data = (await res.json()) as Record<string, unknown>;
    const token = typeof data.access_token === 'string' ? data.access_token : '';
    if (!token) {
      return NextResponse.json({ ok: false, error: 'Backend returned no token' }, { status: 502 });
    }

    const response = NextResponse.json({ ok: true, user: data.user });
    setCookie(response, token);
    return response;
  } catch {
    return NextResponse.json(
      { ok: false, error: 'Could not reach the authentication service. Check your connection.' },
      { status: 503 },
    );
  }
}
