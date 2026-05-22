'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, GitMerge, Network, Users, LogOut } from 'lucide-react';
import { useAuth } from '@/lib/auth';

const NAV_ITEMS = [
  { href: '/admin/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/admin/repositories', label: 'Repositories', icon: GitMerge },
  { href: '/admin/domains', label: 'Domains', icon: Network },
  { href: '/admin/users', label: 'Users', icon: Users },
] as const;

export function AppSidebar() {
  const pathname = usePathname();
  const { logout } = useAuth();

  return (
    <aside
      style={{
        width: '220px',
        minWidth: '220px',
        backgroundColor: 'var(--surface)',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        position: 'sticky',
        top: 0,
        height: '100vh',
      }}
    >
      {/* Wordmark */}
      <div
        style={{
          height: '52px',
          display: 'flex',
          alignItems: 'center',
          padding: '0 1.25rem',
          borderBottom: '1px solid var(--border)',
          flexShrink: 0,
        }}
      >
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.8125rem',
            color: 'var(--accent)',
            letterSpacing: '0.08em',
          }}
        >
          CodeLens
        </span>
      </div>

      {/* Nav */}
      <nav
        style={{
          flex: 1,
          padding: '0.625rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '2px',
          overflowY: 'auto',
        }}
      >
        {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.625rem',
                padding: '0.5rem 0.75rem',
                borderRadius: '6px',
                fontFamily: 'var(--font-sans)',
                fontSize: '0.8125rem',
                color: active ? 'var(--text)' : 'var(--text-muted)',
                backgroundColor: active ? 'var(--surface-elevated)' : 'transparent',
                textDecoration: 'none',
              }}
            >
              <Icon
                size={15}
                style={{ color: active ? 'var(--accent)' : 'var(--text-dim)', flexShrink: 0 }}
              />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Logout */}
      <div style={{ padding: '0.625rem', borderTop: '1px solid var(--border)', flexShrink: 0 }}>
        <button
          onClick={() => void logout()}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.625rem',
            padding: '0.5rem 0.75rem',
            width: '100%',
            borderRadius: '6px',
            fontFamily: 'var(--font-sans)',
            fontSize: '0.8125rem',
            color: 'var(--text-dim)',
            backgroundColor: 'transparent',
            border: 'none',
            cursor: 'pointer',
            textAlign: 'left',
          }}
        >
          <LogOut size={15} style={{ flexShrink: 0 }} />
          Log out
        </button>
      </div>
    </aside>
  );
}
