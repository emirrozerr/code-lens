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
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.25rem' }}>
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

      {/* Hover description */}
      <div
        style={{
          height: '1rem',
          fontFamily: 'var(--font-sans)',
          fontSize: '0.6875rem',
          color: 'var(--text-dim)',
          transition: 'opacity 150ms',
          opacity: hoveredOption ? 1 : 0,
        }}
      >
        {hoveredOption?.desc ?? ''}
      </div>
    </div>
  );
}
