import type { ChatMessage } from '@/types/api';
import { MarkdownContent } from './MarkdownContent';

interface MessageBubbleProps {
  message: ChatMessage;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  if (message.role === 'user') {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'flex-end',
          padding: '0 1rem',
        }}
      >
        <div
          style={{
            maxWidth: '70%',
            backgroundColor: 'var(--surface-elevated)',
            border: '1px solid var(--border)',
            borderRadius: '8px',
            padding: '0.625rem 0.875rem',
            fontFamily: 'var(--font-sans)',
            fontSize: '0.9375rem',
            color: 'var(--text)',
            lineHeight: 1.6,
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
          }}
        >
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'flex-start',
        padding: '0 1rem',
      }}
    >
      <div
        style={{
          maxWidth: '80%',
          borderLeft: '2px solid var(--accent)',
          paddingLeft: '0.875rem',
          fontFamily: 'var(--font-sans)',
          fontSize: '0.9375rem',
          color: 'var(--text-muted)',
          lineHeight: 1.7,
          wordBreak: 'break-word',
        }}
      >
        <MarkdownContent content={message.content} />
      </div>
    </div>
  );
}
