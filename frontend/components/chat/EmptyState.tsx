const EXAMPLE_PROMPTS = [
  'Explain how the checkout flow works',
  'Which functions call `apply_discount`?',
  'Show me the auth domain',
] as const;

interface EmptyStateProps {
  onSubmit: (prompt: string) => void;
}

export function EmptyState({ onSubmit }: EmptyStateProps) {
  return (
    <div
      style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem',
        gap: '2rem',
      }}
    >
      {/* Heading */}
      <div style={{ textAlign: 'center' }}>
        <h1
          style={{
            fontFamily: "'Instrument Serif', Georgia, serif",
            fontSize: '2.25rem',
            fontWeight: 400,
            color: 'var(--text)',
            lineHeight: 1.1,
            margin: '0 0 0.5rem',
          }}
        >
          Ask CodeLens
        </h1>
        <p
          style={{
            fontFamily: 'var(--font-sans)',
            fontSize: '0.9375rem',
            color: 'var(--text-dim)',
            margin: 0,
          }}
        >
          Query your codebase in natural language
        </p>
      </div>

      {/* Example prompt cards */}
      <div
        style={{
          display: 'flex',
          gap: '0.75rem',
          flexWrap: 'wrap',
          justifyContent: 'center',
          maxWidth: '640px',
        }}
      >
        {EXAMPLE_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            onClick={() => onSubmit(prompt)}
            style={{
              flex: '1 1 180px',
              padding: '0.875rem 1rem',
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              fontFamily: 'var(--font-sans)',
              fontSize: '0.875rem',
              color: 'var(--text-muted)',
              lineHeight: 1.5,
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'border-color 150ms, color 150ms',
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border-strong)';
              (e.currentTarget as HTMLButtonElement).style.color = 'var(--text)';
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--border)';
              (e.currentTarget as HTMLButtonElement).style.color = 'var(--text-muted)';
            }}
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
