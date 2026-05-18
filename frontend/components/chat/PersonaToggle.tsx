'use client';

import { useState } from 'react';
import type { Persona } from '@/types/api';

interface PersonaOption {
  value: Persona;
  label: string;
  desc: string;
}

const OPTIONS: PersonaOption[] = [
  {
    value: 'developer',
    label: 'Developer',
    desc: 'Technical implementation details, code structure, and system design',
  },
  {
    value: 'product',
    label: 'Product',
    desc: 'Feature behaviour, user flows, and business logic',
  },
  {
    value: 'legal',
    label: 'Legal',
    desc: 'Compliance concerns, data handling, and regulatory considerations',
  },
];

interface PersonaToggleProps {
  value: Persona;
  onChange: (p: Persona) => void;
}

export function PersonaToggle({ value, onChange }: PersonaToggleProps) {
  const [hovered, setHovered] = useState<Persona | null>(null);
  const hoveredOption = OPTIONS.find((o) => o.value === hovered);

  return (
    <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
      {/* Segmented control */}
      <div
        style={{
          display: 'flex',
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          padding: '3px',
          gap: '2px',
        }}
      >
        {OPTIONS.map((opt) => {
          const active = opt.value === value;
          return (
            <button
              key={opt.value}
              onClick={() => onChange(opt.value)}
              onMouseEnter={() => setHovered(opt.value)}
              onMouseLeave={() => setHovered(null)}
              style={{
                padding: '0.3125rem 0.875rem',
                borderRadius: '5px',
                border: active ? '1px solid var(--accent)' : '1px solid transparent',
                backgroundColor: active ? 'var(--accent-glow)' : 'transparent',
                fontFamily: 'var(--font-sans)',
                fontSize: '0.8125rem',
                color: active ? 'var(--accent)' : 'var(--text-dim)',
                cursor: 'pointer',
                transition: 'color 150ms, background-color 150ms, border-color 150ms',
                whiteSpace: 'nowrap',
              }}
            >
              {opt.label}
            </button>
          );
        })}
      </div>

      {/* Hover description — floats below the header, doesn't affect layout */}
      <div
        style={{
          position: 'absolute',
          top: 'calc(100% + 8px)',
          left: '50%',
          transform: 'translateX(-50%)',
          whiteSpace: 'nowrap',
          fontFamily: 'var(--font-sans)',
          fontSize: '0.75rem',
          color: 'var(--text-muted)',
          backgroundColor: 'var(--surface-elevated)',
          border: '1px solid var(--border)',
          borderRadius: '6px',
          padding: '0.3rem 0.625rem',
          pointerEvents: 'none',
          transition: 'opacity 150ms',
          opacity: hoveredOption ? 1 : 0,
          zIndex: 50,
        }}
      >
        {hoveredOption?.desc ?? ''}
      </div>
    </div>
  );
}
