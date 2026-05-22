import { type NextRequest, NextResponse } from 'next/server';

const COOKIE_NAME = process.env.JWT_COOKIE_NAME ?? 'codelens_token';

// base64url → string (Edge-safe: uses atob, not Buffer)
function decodeBase64Url(str: string): string {
  return atob(str.replace(/-/g, '+').replace(/_/g, '/'));
}

interface TokenPayload {
  sub?: string;
  role?: string;
  exp?: number;
}

function getPayload(token: string): TokenPayload | null {
  const parts = token.split('.');
  if (parts.length !== 3) return null;
  try {
    return JSON.parse(decodeBase64Url(parts[1] ?? '')) as TokenPayload;
  } catch {
    return null;
  }
}

export function middleware(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get(COOKIE_NAME)?.value;

  const isAdminPath = pathname.startsWith('/admin');
  const isDemoPath = pathname.startsWith('/ask') || pathname.startsWith('/graph');

  if (!isAdminPath && !isDemoPath) {
    return NextResponse.next();
  }

  // No cookie → redirect to login, preserving the intended destination
  if (!token) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = '/login';
    loginUrl.searchParams.set('from', pathname);
    return NextResponse.redirect(loginUrl);
  }

  const payload = getPayload(token);

  // Malformed token → force re-login
  if (!payload) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = '/login';
    return NextResponse.redirect(loginUrl);
  }

  // Expired token → force re-login
  if (payload.exp && payload.exp < Math.floor(Date.now() / 1000)) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = '/login';
    loginUrl.searchParams.set('reason', 'expired');
    return NextResponse.redirect(loginUrl);
  }

  // Non-admin trying to reach admin routes → send to /ask
  if (isAdminPath && payload.role !== 'admin') {
    return NextResponse.redirect(new URL('/ask', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/admin/:path*', '/ask/:path*', '/graph/:path*', '/graph'],
};
