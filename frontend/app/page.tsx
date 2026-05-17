import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const kpis = [
  { label: 'Repos', value: '3', color: 'var(--text)' },
  { label: 'Nodes', value: '14,823', color: 'var(--text)' },
  { label: 'Domains', value: '12', color: 'var(--success)' },
  { label: 'Uptime', value: '99.9%', color: 'var(--accent)' },
] as const;

export default function HomePage() {
  return (
    <main
      style={{
        minHeight: '100vh',
        backgroundColor: 'var(--bg)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem',
      }}
    >
      <div style={{ maxWidth: '720px', width: '100%', textAlign: 'center' }}>
        <div style={{ marginBottom: '1.5rem' }}>
          <Badge
            variant="outline"
            style={{
              borderColor: 'var(--accent)',
              color: 'var(--accent)',
              backgroundColor: 'var(--accent-glow)',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.75rem',
              letterSpacing: '0.05em',
            }}
          >
            Code Intelligence Infrastructure
          </Badge>
        </div>

        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: 'clamp(2.5rem, 6vw, 4rem)',
            fontWeight: 400,
            color: 'var(--text)',
            lineHeight: 1.1,
            letterSpacing: '-0.01em',
            marginBottom: '1.5rem',
          }}
        >
          Your codebase,
          <br />
          <span style={{ color: 'var(--accent)', fontStyle: 'italic' }}>
            structurally understood.
          </span>
        </h1>

        <p
          style={{
            fontFamily: 'var(--font-sans)',
            fontSize: '1.125rem',
            color: 'var(--text-muted)',
            lineHeight: 1.7,
            maxWidth: '540px',
            margin: '0 auto 2.5rem',
          }}
        >
          CodeLens parses your repositories into a Neo4j knowledge graph and exposes that graph
          through an MCP server — giving your AI agents graph-level structural accuracy.
        </p>

        <div
          style={{
            display: 'flex',
            gap: '1rem',
            justifyContent: 'center',
            flexWrap: 'wrap',
            marginBottom: '4rem',
          }}
        >
          <Button
            style={{
              backgroundColor: 'var(--accent)',
              color: '#ffffff',
              border: 'none',
              fontFamily: 'var(--font-sans)',
              fontWeight: 500,
              padding: '0.625rem 1.5rem',
            }}
          >
            Open Admin Panel
          </Button>
          <Button
            variant="outline"
            style={{
              borderColor: 'var(--border-strong)',
              color: 'var(--text-muted)',
              backgroundColor: 'transparent',
              fontFamily: 'var(--font-sans)',
              padding: '0.625rem 1.5rem',
            }}
          >
            Ask CodeLens
          </Button>
        </div>

        <div
          style={{
            padding: '1.5rem',
            backgroundColor: 'var(--surface)',
            borderRadius: '8px',
            border: '1px solid var(--border)',
            display: 'flex',
            gap: '2rem',
            justifyContent: 'center',
            flexWrap: 'wrap',
          }}
        >
          {kpis.map(({ label, value, color }) => (
            <div key={label} style={{ textAlign: 'center' }}>
              <div
                style={{
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.6875rem',
                  color: 'var(--text-dim)',
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  marginBottom: '0.25rem',
                }}
              >
                {label}
              </div>
              <div
                style={{
                  fontFamily: "'Instrument Serif', Georgia, serif",
                  fontSize: '1.75rem',
                  lineHeight: 1,
                  color,
                }}
              >
                {value}
              </div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
