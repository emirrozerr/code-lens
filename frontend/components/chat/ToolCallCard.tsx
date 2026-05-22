'use client';

import { useState } from 'react';
import type { ToolCallRecord } from '@/types/api';

interface ToolCallCardProps {
  toolCall: ToolCallRecord;
}

export function ToolCallCard({ toolCall }: ToolCallCardProps) {
  const [argsExpanded, setArgsExpanded] = useState(false);
  const [resultExpanded, setResultExpanded] = useState(false);

  const isRunning = toolCall.status === 'running';
  const isError = toolCall.status === 'error';

  const borderColor = isError
    ? 'var(--danger)'
    : isRunning
      ? 'var(--accent)'
      : 'var(--border-strong)';

  const argsJson = JSON.stringify(toolCall.args, null, 2);
  const resultPreview =
    toolCall.result && toolCall.result.length > 200
      ? toolCall.result.slice(0, 200) + '…'
      : toolCall.result;

  return (
    <div
      style={{
        borderRadius: '6px',
        border: `1px solid ${borderColor}`,
        backgroundColor: 'var(--surface)',
        overflow: 'hidden',
        fontSize: '0.8125rem',
        fontFamily: 'var(--font-sans)',
        animation: isRunning ? 'tool-pulse 2s ease-in-out infinite' : undefined,
      }}
    >
      {/* Header row */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          padding: '0.5rem 0.75rem',
          borderBottom: isRunning || toolCall.result || isError ? '1px solid var(--border)' : undefined,
        }}
      >
        {/* Status indicator */}
        {isRunning ? (
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              backgroundColor: 'var(--accent)',
              flexShrink: 0,
              animation: 'pulse 1.2s ease-in-out infinite',
            }}
          />
        ) : isError ? (
          <span style={{ color: 'var(--danger)', flexShrink: 0, lineHeight: 1 }}>✕</span>
        ) : (
          <span style={{ color: 'var(--success)', flexShrink: 0, lineHeight: 1 }}>✓</span>
        )}

        {/* Tool name */}
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            color: isRunning ? 'var(--accent)' : isError ? 'var(--danger)' : 'var(--text-muted)',
            flex: 1,
          }}
        >
          {toolCall.tool}
        </span>

        {/* Duration badge (done only) */}
        {toolCall.status === 'done' && toolCall.durationMs !== null && (
          <span
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.6875rem',
              color: 'var(--text-dim)',
              backgroundColor: 'var(--surface-elevated)',
              border: '1px solid var(--border)',
              borderRadius: '4px',
              padding: '0.1em 0.4em',
            }}
          >
            {toolCall.durationMs}ms
          </span>
        )}

        {/* Args expand toggle */}
        <button
          onClick={() => setArgsExpanded((v) => !v)}
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.6875rem',
            color: 'var(--text-dim)',
            backgroundColor: 'transparent',
            border: 'none',
            cursor: 'pointer',
            padding: '0.1em 0.25em',
          }}
          title={argsExpanded ? 'Collapse args' : 'Expand args'}
        >
          {argsExpanded ? '▲ args' : '▼ args'}
        </button>
      </div>

      {/* Args block */}
      {argsExpanded && (
        <pre
          style={{
            margin: 0,
            padding: '0.5rem 0.75rem',
            backgroundColor: 'var(--surface-elevated)',
            borderBottom:
              (toolCall.result || isError) ? '1px solid var(--border)' : undefined,
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            overflowX: 'auto',
            lineHeight: 1.5,
          }}
        >
          {argsJson}
        </pre>
      )}

      {/* Result / error area */}
      {isError && toolCall.error && (
        <div
          style={{
            padding: '0.5rem 0.75rem',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            color: 'var(--danger)',
            lineHeight: 1.5,
          }}
        >
          {toolCall.error}
        </div>
      )}

      {toolCall.result && !isError && (
        <div
          style={{
            padding: '0.5rem 0.75rem',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.75rem',
            color: 'var(--text-dim)',
            lineHeight: 1.5,
          }}
        >
          {resultExpanded ? toolCall.result : resultPreview}
          {toolCall.result.length > 200 && (
            <button
              onClick={() => setResultExpanded((v) => !v)}
              style={{
                marginLeft: '0.5em',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.6875rem',
                color: 'var(--accent)',
                backgroundColor: 'transparent',
                border: 'none',
                cursor: 'pointer',
                padding: 0,
              }}
            >
              {resultExpanded ? 'collapse' : 'expand'}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
