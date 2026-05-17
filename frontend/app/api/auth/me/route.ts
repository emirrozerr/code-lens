import { type NextRequest, NextResponse } from 'next/server';
import type { User } from '@/types/api';
import { MOCK_USERS } from '@/lib/api/mocks';

const COOKIE_NAME = process.env.JWT_COOKIE_NAME ?? 'codelens_token';
const IS_MOCK = process.env.NEXT_PUBLIC_MOCK_MODE === 'true';

interface JwtPayload {
  sub: string;
  email: string;
  role: string;
  exp: number;
}

function decodePayload(token: string): JwtPayload | null {
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  try {
    const raw = parts[1];
    if (!raw) return null;
    // base64url → base64 → JSON
    const json = Buffer.from(raw, 'base64url').toString('utf-8');
    return JSON.parse(json) as JwtPayload;
  } catch {
    return null;
  }
}

export async function GET(request: NextRequest): Promise<NextResponse> {
  const token = request.cookies.get(COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ error: 'Not authenticated' }, { status: 401 });
  }

  const payload = decodePayload(token);
  if (!payload) {
    return NextResponse.json({ error: 'Invalid token' }, { status: 401 });
  }

  if (payload.exp < Math.floor(Date.now() / 1000)) {
    return NextResponse.json({ error: 'Token expired' }, { status: 401 });
  }

  // ── Mock mode ────────────────────────────────────────────────────────────
  if (IS_MOCK) {
    const user = MOCK_USERS.find((u) => u.id === payload.sub);
    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 401 });
    }
    return NextResponse.json(user);
  }

  // ── Real backend ─────────────────────────────────────────────────────────
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';
  try {
    const res = await fetch(`${baseUrl}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      return NextResponse.json({ error: 'Session invalid or expired' }, { status: 401 });
    }
    const user = (await res.json()) as User;
    return NextResponse.json(user);
  } catch {
    return NextResponse.json({ error: 'Could not verify session' }, { status: 503 });
  }
}
