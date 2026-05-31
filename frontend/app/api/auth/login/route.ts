import { type NextRequest, NextResponse } from 'next/server';

const COOKIE_NAME = process.env.JWT_COOKIE_NAME ?? 'codelens_token';

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
