'use client';

import { Fragment } from 'react';
import Prism from 'prismjs';
import 'prismjs/components/prism-typescript';
import 'prismjs/components/prism-javascript';
import 'prismjs/components/prism-python';
import 'prismjs/components/prism-java';
import 'prismjs/components/prism-bash';
import 'prismjs/components/prism-json';
import 'prismjs/components/prism-sql';
import 'prismjs/components/prism-yaml';

// ─── Inline formatting ──────────────────────────────────────────────────────

function renderInline(text: string): React.ReactNode {
  // Pattern order matters: longer patterns first
  const parts: React.ReactNode[] = [];
  let remaining = text;
  let key = 0;

  while (remaining.length > 0) {
    // Bold **text** or __text__
    const boldMatch = remaining.match(/^([\s\S]*?)\*\*([\s\S]+?)\*\*/);
    // Italic *text* or _text_
    const italicMatch = remaining.match(/^([\s\S]*?)(?<!\*)\*(?!\*)([\s\S]+?)(?<!\*)\*(?!\*)/);
    // Inline code `text`
    const codeMatch = remaining.match(/^([\s\S]*?)`([^`]+)`/);
    // Link [text](url)
    const linkMatch = remaining.match(/^([\s\S]*?)\[([^\]]+)\]\(([^)]+)\)/);

    // Find which match starts earliest
    const candidates = [
      boldMatch ? { start: boldMatch[1].length, type: 'bold', match: boldMatch } : null,
      italicMatch ? { start: italicMatch[1].length, type: 'italic', match: italicMatch } : null,
      codeMatch ? { start: codeMatch[1].length, type: 'code', match: codeMatch } : null,
      linkMatch ? { start: linkMatch[1].length, type: 'link', match: linkMatch } : null,
    ].filter(Boolean) as { start: number; type: string; match: RegExpMatchArray }[];

    if (candidates.length === 0) {
      parts.push(<Fragment key={key++}>{remaining}</Fragment>);
      break;
    }

    candidates.sort((a, b) => a.start - b.start);
    const winner = candidates[0];

    // Push text before the match
    if (winner.start > 0) {
      parts.push(<Fragment key={key++}>{remaining.slice(0, winner.start)}</Fragment>);
    }

    if (winner.type === 'bold') {
      const m = winner.match;
      parts.push(
        <strong key={key++} style={{ color: 'var(--text)', fontWeight: 600 }}>
          {renderInline(m[2])}
        </strong>,
      );
      remaining = remaining.slice(winner.start + m[2].length + 4); // 2*2 for **
    } else if (winner.type === 'italic') {
      const m = winner.match;
      parts.push(
        <em key={key++} style={{ color: 'var(--text-muted)' }}>
          {renderInline(m[3])}
        </em>,
      );
      remaining = remaining.slice(winner.start + m[3].length + 2); // 2 for **
    } else if (winner.type === 'code') {
      const m = winner.match;
      parts.push(
        <code
          key={key++}
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.8125em',
            color: 'var(--accent)',
            backgroundColor: 'var(--accent-glow)',
            padding: '0.1em 0.35em',
            borderRadius: '3px',
          }}
        >
          {m[2]}
        </code>,
      );
      remaining = remaining.slice(winner.start + m[2].length + 2); // 2 for ``
    } else {
      // link
      const m = winner.match;
      parts.push(
        <a
          key={key++}
          href={m[3]}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            color: 'var(--accent)',
            textDecoration: 'underline',
            textUnderlineOffset: '2px',
          }}
        >
          {m[2]}
        </a>,
      );
      remaining = remaining.slice(winner.start + m[0].length - winner.start);
    }
  }

  return parts;
}

// ─── Block rendering ────────────────────────────────────────────────────────

interface Block {
  type: 'code' | 'ul' | 'ol' | 'heading' | 'blockquote' | 'paragraph';
  content: string;
  lang?: string;
  level?: number;
}

function parseBlocks(markdown: string): Block[] {
  const blocks: Block[] = [];
  const lines = markdown.split('\n');
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Fenced code block
    if (line.startsWith('```')) {
      const lang = line.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      blocks.push({ type: 'code', content: codeLines.join('\n'), lang });
      continue;
    }

    // Heading
    const headingMatch = line.match(/^(#{1,6})\s+(.*)/);
    if (headingMatch) {
      blocks.push({ type: 'heading', content: headingMatch[2], level: headingMatch[1].length });
      i++;
      continue;
    }

    // Blockquote
    if (line.startsWith('> ')) {
      const bqLines: string[] = [line.slice(2)];
      i++;
      while (i < lines.length && lines[i].startsWith('> ')) {
        bqLines.push(lines[i].slice(2));
        i++;
      }
      blocks.push({ type: 'blockquote', content: bqLines.join('\n') });
      continue;
    }

    // Unordered list
    if (/^[-*+] /.test(line)) {
      const items: string[] = [line.slice(2)];
      i++;
      while (i < lines.length && /^[-*+] /.test(lines[i])) {
        items.push(lines[i].slice(2));
        i++;
      }
      blocks.push({ type: 'ul', content: items.join('\n') });
      continue;
    }

    // Ordered list
    if (/^\d+\. /.test(line)) {
      const items: string[] = [line.replace(/^\d+\. /, '')];
      i++;
      while (i < lines.length && /^\d+\. /.test(lines[i])) {
        items.push(lines[i].replace(/^\d+\. /, ''));
        i++;
      }
      blocks.push({ type: 'ol', content: items.join('\n') });
      continue;
    }

    // Skip blank lines
    if (line.trim() === '') {
      i++;
      continue;
    }

    // Paragraph — collect until blank line or block element
    const paraLines: string[] = [line];
    i++;
    while (
      i < lines.length &&
      lines[i].trim() !== '' &&
      !lines[i].startsWith('```') &&
      !lines[i].startsWith('> ') &&
      !/^#{1,6} /.test(lines[i]) &&
      !/^[-*+] /.test(lines[i]) &&
      !/^\d+\. /.test(lines[i])
    ) {
      paraLines.push(lines[i]);
      i++;
    }
    blocks.push({ type: 'paragraph', content: paraLines.join(' ') });
  }

  return blocks;
}

function renderBlock(block: Block, idx: number): React.ReactNode {
  switch (block.type) {
    case 'code': {
      const grammar = block.lang ? Prism.languages[block.lang] : undefined;
      const highlighted = grammar
        ? Prism.highlight(block.content, grammar, block.lang ?? '')
        : block.content;
      return (
        <div
          key={idx}
          style={{
            borderRadius: '6px',
            overflow: 'hidden',
            border: '1px solid var(--border)',
            margin: '0.5rem 0',
          }}
        >
          {block.lang && (
            <div
              style={{
                padding: '0.25rem 0.75rem',
                backgroundColor: 'var(--surface-elevated)',
                borderBottom: '1px solid var(--border)',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.6875rem',
                color: 'var(--text-dim)',
                letterSpacing: '0.05em',
              }}
            >
              {block.lang}
            </div>
          )}
          <pre
            style={{
              margin: 0,
              padding: '0.875rem',
              backgroundColor: 'var(--surface)',
              overflowX: 'auto',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.8125rem',
              lineHeight: 1.6,
              color: 'var(--text)',
            }}
          >
            {grammar ? (
              <code dangerouslySetInnerHTML={{ __html: highlighted }} />
            ) : (
              <code>{block.content}</code>
            )}
          </pre>
        </div>
      );
    }

    case 'heading': {
      const fs =
        block.level === 1
          ? '1.125rem'
          : block.level === 2
            ? '1rem'
            : '0.9375rem';
      return (
        <p
          key={idx}
          style={{
            fontFamily: 'var(--font-sans)',
            fontSize: fs,
            fontWeight: 600,
            color: 'var(--text)',
            margin: '0.75rem 0 0.25rem',
          }}
        >
          {renderInline(block.content)}
        </p>
      );
    }

    case 'blockquote':
      return (
        <blockquote
          key={idx}
          style={{
            borderLeft: '3px solid var(--border-strong)',
            paddingLeft: '0.75rem',
            margin: '0.5rem 0',
            color: 'var(--text-dim)',
            lineHeight: 1.6,
          }}
        >
          {renderInline(block.content)}
        </blockquote>
      );

    case 'ul':
      return (
        <ul key={idx} style={{ margin: '0.375rem 0', paddingLeft: '1.25rem', lineHeight: 1.7 }}>
          {block.content.split('\n').map((item, j) => (
            <li key={j} style={{ margin: '0.125rem 0', color: 'inherit' }}>
              {renderInline(item)}
            </li>
          ))}
        </ul>
      );

    case 'ol':
      return (
        <ol key={idx} style={{ margin: '0.375rem 0', paddingLeft: '1.25rem', lineHeight: 1.7 }}>
          {block.content.split('\n').map((item, j) => (
            <li key={j} style={{ margin: '0.125rem 0', color: 'inherit' }}>
              {renderInline(item)}
            </li>
          ))}
        </ol>
      );

    default:
      return (
        <p key={idx} style={{ margin: '0.375rem 0', lineHeight: 1.7 }}>
          {renderInline(block.content)}
        </p>
      );
  }
}

// ─── Export ─────────────────────────────────────────────────────────────────

export function MarkdownContent({ content }: { content: string }) {
  const blocks = parseBlocks(content);
  return <>{blocks.map((b, i) => renderBlock(b, i))}</>;
}
