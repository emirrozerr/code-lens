export const MOCK_MODE = process.env.NEXT_PUBLIC_MOCK_MODE === 'true';

// ─── Error class ───────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// ─── Core fetch wrapper ────────────────────────────────────────────────────

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

interface FetchOptions {
  method?: HttpMethod;
  body?: unknown;
  headers?: Record<string, string>;
}

async function attemptFetch<T>(url: string, options: FetchOptions): Promise<T> {
  const res = await fetch(url, {
    method: options.method ?? 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...(options.body !== undefined ? { body: JSON.stringify(options.body) } : {}),
    credentials: 'include',
  });

  if (!res.ok) {
    let message = res.statusText;
    try {
      const body = (await res.json()) as Record<string, unknown>;
      if (typeof body.detail === 'string') message = body.detail;
      else if (typeof body.message === 'string') message = body.message;
    } catch {
      // response body may not be JSON
    }
    throw new ApiError(res.status, message);
  }

  return res.json() as Promise<T>;
}

const isIdempotent = (method: HttpMethod = 'GET') =>
  method === 'GET' || method === 'PUT' || method === 'DELETE';

export async function apiFetch<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';
  const url = `${base}${path}`;

  try {
    return await attemptFetch<T>(url, options);
  } catch (err) {
    if (err instanceof ApiError) throw err;

    // Retry once on network error for idempotent methods
    if (isIdempotent(options.method)) {
      try {
        return await attemptFetch<T>(url, options);
      } catch (retryErr) {
        if (retryErr instanceof ApiError) throw retryErr;
        throw new ApiError(0, retryErr instanceof Error ? retryErr.message : 'Network error');
      }
    }

    throw new ApiError(0, err instanceof Error ? err.message : 'Network error');
  }
}
