import type { ChatEvent, Persona } from '@/types/api';
import { MOCK_MODE, ApiError } from './client';
import { MOCK_CHAT_EVENTS } from './mocks';

export type { ChatEvent };

// ─── ChatStream interface ──────────────────────────────────────────────────

export interface ChatStream {
  onEvent: (handler: (event: ChatEvent) => void) => void;
  cancel: () => void;
}

// ─── Mock stream ───────────────────────────────────────────────────────────

function createMockStream(_message: string, _persona: Persona): ChatStream {
  let handler: ((event: ChatEvent) => void) | null = null;
  let cancelled = false;
  const timers: ReturnType<typeof setTimeout>[] = [];

  const scheduleEvents = () => {
    let delay = 0;

    for (const event of MOCK_CHAT_EVENTS) {
      const t = setTimeout(() => {
        if (!cancelled && handler) handler(event);
      }, delay);
      timers.push(t);

      if (event.type === 'token') delay += 40;
      else if (event.type === 'tool_call_start') delay += 200;
      else if (event.type === 'tool_call_end') delay += 800;
      else delay += 100;
    }
  };

  return {
    onEvent(h) {
      handler = h;
      scheduleEvents();
    },
    cancel() {
      cancelled = true;
      for (const t of timers) clearTimeout(t);
    },
  };
}

// ─── Real stream (fetch-based SSE for POST) ────────────────────────────────

function createRealStream(message: string, persona: Persona): ChatStream {
  let handler: ((event: ChatEvent) => void) | null = null;
  let cancelled = false;
  const controller = new AbortController();

  const run = async () => {
    const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

    let res: Response;
    try {
      res = await fetch(`${base}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
        body: JSON.stringify({ message, persona }),
        credentials: 'include',
        signal: controller.signal,
      });
    } catch (err) {
      if (!cancelled && handler) {
        handler({
          type: 'error',
          message: err instanceof Error ? err.message : 'Network error',
        });
      }
      return;
    }

    if (!res.ok || !res.body) {
      if (!cancelled && handler) {
        handler({ type: 'error', message: `HTTP ${res.status}: ${res.statusText}` });
      }
      return;
    }

    const reader = res.body.pipeThrough(new TextDecoderStream()).getReader();
    let buffer = '';

    while (!cancelled) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += value;

      const parts = buffer.split('\n\n');
      buffer = parts.pop() ?? '';

      for (const part of parts) {
        const dataLine = part.split('\n').find((l) => l.startsWith('data: '));
        if (!dataLine) continue;
        const json = dataLine.slice(6).trim();
        if (json === '[DONE]') {
          if (!cancelled && handler) handler({ type: 'done' });
          return;
        }
        try {
          const event = JSON.parse(json) as ChatEvent;
          if (!cancelled && handler) handler(event);
        } catch {
          // malformed SSE frame — skip
        }
      }
    }
  };

  // Run async without blocking the caller
  run().catch((err: unknown) => {
    if (!cancelled && handler) {
      handler({
        type: 'error',
        message: err instanceof Error ? err.message : 'Stream error',
      });
    }
  });

  return {
    onEvent(h) {
      handler = h;
    },
    cancel() {
      cancelled = true;
      controller.abort(new ApiError(0, 'Cancelled'));
    },
  };
}

// ─── Public factory ────────────────────────────────────────────────────────

export function createChatStream(message: string, persona: Persona): ChatStream {
  if (MOCK_MODE) return createMockStream(message, persona);
  return createRealStream(message, persona);
}
