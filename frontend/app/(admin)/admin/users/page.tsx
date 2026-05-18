'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { listUsers, addUser, resetUserPassword, setUserRole, deleteUser } from '@/lib/api/endpoints';
import { ApiError } from '@/lib/api/client';
import { useAuth } from '@/lib/auth';
import type { User, Role } from '@/types/api';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { MoreHorizontal, Plus, Copy, Check } from 'lucide-react';

// ─── Temp password display ──────────────────────────────────────────────────

function TempPasswordBlock({ password }: { password: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(password);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          backgroundColor: 'var(--surface-elevated)',
          border: '1px solid var(--border)',
          borderRadius: '6px',
          padding: '0.5rem 0.75rem',
        }}
      >
        <code
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.875rem',
            color: 'var(--text)',
            flex: 1,
            letterSpacing: '0.05em',
          }}
        >
          {password}
        </code>
        <button
          onClick={() => void handleCopy()}
          title="Copy password"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '24px',
            height: '24px',
            borderRadius: '4px',
            border: 'none',
            backgroundColor: 'transparent',
            color: copied ? 'var(--success)' : 'var(--text-dim)',
            cursor: 'pointer',
            flexShrink: 0,
          }}
        >
          {copied ? <Check size={13} /> : <Copy size={13} />}
        </button>
      </div>
      <p
        style={{
          fontFamily: 'var(--font-sans)',
          fontSize: '0.75rem',
          color: 'var(--warning)',
          margin: 0,
          lineHeight: 1.5,
        }}
      >
        ⚠ This password will not be shown again. Copy it now.
      </p>
    </div>
  );
}

// ─── Add user dialog ────────────────────────────────────────────────────────

interface AddUserDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function AddUserDialog({ open, onOpenChange }: AddUserDialogProps) {
  const queryClient = useQueryClient();
  const [email, setEmail] = useState('');
  const [tempPassword, setTempPassword] = useState<string | null>(null);

  function handleClose(v: boolean) {
    if (!v) {
      setEmail('');
      setTempPassword(null);
    }
    onOpenChange(v);
  }

  const mutation = useMutation({
    mutationFn: (e: string) => addUser(e),
    onSuccess: (data) => {
      void queryClient.invalidateQueries({ queryKey: ['users'] });
      setTempPassword(data.temporaryPassword);
      toast.success(`User ${data.user.email} added`);
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : 'Failed to add user');
    },
  });

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    mutation.mutate(email.trim());
  }

  return (
    <Dialog open={open} onOpenChange={(v: boolean) => handleClose(v)}>
      <DialogContent style={{ maxWidth: '420px' }}>
        <DialogHeader>
          <DialogTitle>Add user</DialogTitle>
        </DialogHeader>

        {tempPassword ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <p
              style={{
                fontFamily: 'var(--font-sans)',
                fontSize: '0.875rem',
                color: 'var(--text-muted)',
                margin: 0,
              }}
            >
              User created. Share this temporary password:
            </p>
            <TempPasswordBlock password={tempPassword} />
            <DialogFooter>
              <Button onClick={() => handleClose(false)}>Done</Button>
            </DialogFooter>
          </div>
        ) : (
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
            <div>
              <label
                style={{
                  display: 'block',
                  fontFamily: 'var(--font-sans)',
                  fontSize: '0.8125rem',
                  color: 'var(--text-muted)',
                  marginBottom: '0.375rem',
                }}
              >
                Email address
              </label>
              <Input
                type="email"
                placeholder="user@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoFocus
              />
            </div>
            <DialogFooter>
              <Button type="submit" disabled={!email.trim() || mutation.isPending}>
                {mutation.isPending ? 'Creating…' : 'Create user'}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}

// ─── Reset password dialog ───────────────────────────────────────────────────

interface ResetPasswordDialogProps {
  user: User | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function ResetPasswordDialog({ user, open, onOpenChange }: ResetPasswordDialogProps) {
  const [tempPassword, setTempPassword] = useState<string | null>(null);

  function handleClose(v: boolean) {
    if (!v) setTempPassword(null);
    onOpenChange(v);
  }

  const mutation = useMutation({
    mutationFn: (id: string) => resetUserPassword(id),
    onSuccess: (data) => {
      setTempPassword(data.temporaryPassword);
      toast.success('Password reset');
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : 'Failed to reset password');
    },
  });

  return (
    <Dialog open={open} onOpenChange={(v: boolean) => handleClose(v)}>
      <DialogContent style={{ maxWidth: '420px' }}>
        <DialogHeader>
          <DialogTitle>Reset password</DialogTitle>
        </DialogHeader>

        {tempPassword ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <p
              style={{
                fontFamily: 'var(--font-sans)',
                fontSize: '0.875rem',
                color: 'var(--text-muted)',
                margin: 0,
              }}
            >
              New temporary password for{' '}
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', color: 'var(--text)' }}>
                {user?.email}
              </span>
              :
            </p>
            <TempPasswordBlock password={tempPassword} />
            <DialogFooter>
              <Button onClick={() => handleClose(false)}>Done</Button>
            </DialogFooter>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <p
              style={{
                fontFamily: 'var(--font-sans)',
                fontSize: '0.875rem',
                color: 'var(--text-muted)',
                lineHeight: 1.6,
                margin: 0,
              }}
            >
              Generate a new temporary password for{' '}
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', color: 'var(--text)' }}>
                {user?.email}
              </span>
              ? The user will need to change it on next login.
            </p>
            <DialogFooter>
              <Button
                disabled={mutation.isPending}
                onClick={() => { if (user) mutation.mutate(user.id); }}
              >
                {mutation.isPending ? 'Generating…' : 'Reset password'}
              </Button>
            </DialogFooter>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

// ─── Role confirm dialog ─────────────────────────────────────────────────────

interface RoleDialogProps {
  user: User | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (id: string, role: Role) => void;
  isPending: boolean;
}

function RoleDialog({ user, open, onOpenChange, onConfirm, isPending }: RoleDialogProps) {
  const newRole: Role = user?.role === 'admin' ? 'user' : 'admin';
  return (
    <Dialog open={open} onOpenChange={(v: boolean) => onOpenChange(v)}>
      <DialogContent style={{ maxWidth: '400px' }}>
        <DialogHeader>
          <DialogTitle>Change role</DialogTitle>
        </DialogHeader>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <p
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: '0.875rem',
              color: 'var(--text-muted)',
              lineHeight: 1.6,
              margin: 0,
            }}
          >
            Change{' '}
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', color: 'var(--text)' }}>
              {user?.email}
            </span>{' '}
            from <strong>{user?.role}</strong> to <strong>{newRole}</strong>?
          </p>
          <DialogFooter>
            <Button
              disabled={isPending}
              onClick={() => { if (user) onConfirm(user.id, newRole); }}
            >
              {isPending ? 'Saving…' : `Set to ${newRole}`}
            </Button>
          </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ─── Delete confirm dialog ───────────────────────────────────────────────────

interface DeleteDialogProps {
  user: User | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (id: string) => void;
  isPending: boolean;
}

function DeleteUserDialog({ user, open, onOpenChange, onConfirm, isPending }: DeleteDialogProps) {
  return (
    <Dialog open={open} onOpenChange={(v: boolean) => onOpenChange(v)}>
      <DialogContent style={{ maxWidth: '400px' }}>
        <DialogHeader>
          <DialogTitle>Delete user</DialogTitle>
        </DialogHeader>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <p
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: '0.875rem',
              color: 'var(--text-muted)',
              lineHeight: 1.6,
              margin: 0,
            }}
          >
            Permanently delete{' '}
            <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8125rem', color: 'var(--text)' }}>
              {user?.email}
            </span>
            ? This cannot be undone.
          </p>
          <DialogFooter>
            <Button
              variant="destructive"
              disabled={isPending}
              onClick={() => { if (user) onConfirm(user.id); }}
            >
              {isPending ? 'Deleting…' : 'Delete user'}
            </Button>
          </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatDate(iso: string | null) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-GB', { dateStyle: 'medium' });
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function UsersPage() {
  const queryClient = useQueryClient();
  const { user: currentUser } = useAuth();

  const [addOpen, setAddOpen] = useState(false);
  const [resetTarget, setResetTarget] = useState<User | null>(null);
  const [roleTarget, setRoleTarget] = useState<User | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<User | null>(null);

  const { data: users = [], isLoading, isError } = useQuery({
    queryKey: ['users'],
    queryFn: listUsers,
    refetchOnWindowFocus: true,
  });

  const roleMutation = useMutation({
    mutationFn: ({ id, role }: { id: string; role: Role }) => setUserRole(id, role),
    onSuccess: (updated) => {
      void queryClient.invalidateQueries({ queryKey: ['users'] });
      setRoleTarget(null);
      toast.success(`${updated.email} is now ${updated.role}`);
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : 'Failed to update role');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteUser(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['users'] });
      setDeleteTarget(null);
      toast.success('User deleted');
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : 'Failed to delete user');
    },
  });

  return (
    <div style={{ padding: '2rem', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          marginBottom: '2rem',
          animation: 'fade-up 300ms ease-out both',
        }}
      >
        <div>
          <h1
            style={{
              fontFamily: "'Instrument Serif', Georgia, serif",
              fontSize: '2rem',
              fontWeight: 400,
              color: 'var(--text)',
              lineHeight: 1.1,
              margin: 0,
            }}
          >
            Users
          </h1>
          <p
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: '0.875rem',
              color: 'var(--text-dim)',
              marginTop: '0.375rem',
            }}
          >
            {users.length} user{users.length === 1 ? '' : 's'}
          </p>
        </div>
        <Button
          onClick={() => setAddOpen(true)}
          style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}
        >
          <Plus size={14} />
          Add user
        </Button>
      </div>

      {/* Table */}
      <div
        style={{
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          overflow: 'hidden',
          animation: 'fade-up 300ms ease-out 50ms both',
        }}
      >
        {isLoading ? (
          <div style={{ padding: '1rem 1.25rem', display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : isError ? (
          <div style={{ padding: '2rem', textAlign: 'center', fontFamily: 'var(--font-sans)', fontSize: '0.875rem', color: 'var(--danger)' }}>
            Failed to load users. Check your connection and try again.
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Email</TableHead>
                <TableHead style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Role</TableHead>
                <TableHead style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Created</TableHead>
                <TableHead style={{ color: 'var(--text-dim)', fontSize: '0.75rem' }}>Last login</TableHead>
                <TableHead style={{ color: 'var(--text-dim)', fontSize: '0.75rem', width: '48px' }} />
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map((u) => {
                const isSelf = u.id === currentUser?.id;
                return (
                  <TableRow key={u.id}>
                    <TableCell>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span
                          style={{
                            fontFamily: 'var(--font-mono)',
                            fontSize: '0.8125rem',
                            color: 'var(--text)',
                          }}
                        >
                          {u.email}
                        </span>
                        {isSelf && (
                          <span
                            style={{
                              fontFamily: 'var(--font-mono)',
                              fontSize: '0.6875rem',
                              color: 'var(--text-dim)',
                              border: '1px solid var(--border)',
                              borderRadius: '4px',
                              padding: '0 0.375rem',
                            }}
                          >
                            you
                          </span>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={u.role === 'admin' ? 'default' : 'secondary'}
                        style={
                          u.role === 'admin'
                            ? { backgroundColor: 'var(--accent-glow)', color: 'var(--accent)', border: '1px solid rgba(139,92,246,0.3)' }
                            : {}
                        }
                      >
                        {u.role}
                      </Badge>
                    </TableCell>
                    <TableCell
                      style={{
                        fontFamily: 'var(--font-sans)',
                        fontSize: '0.8125rem',
                        color: 'var(--text-dim)',
                      }}
                    >
                      {formatDate(u.createdAt)}
                    </TableCell>
                    <TableCell
                      style={{
                        fontFamily: 'var(--font-sans)',
                        fontSize: '0.8125rem',
                        color: 'var(--text-dim)',
                      }}
                    >
                      {formatDate(u.lastLogin)}
                    </TableCell>
                    <TableCell>
                      <DropdownMenu>
                        <DropdownMenuTrigger
                          aria-label={`Actions for ${u.email}`}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            width: '28px',
                            height: '28px',
                            borderRadius: '4px',
                            border: 'none',
                            backgroundColor: 'transparent',
                            color: 'var(--text-dim)',
                            cursor: 'pointer',
                          }}
                        >
                          <MoreHorizontal size={15} />
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onSelect={() => setResetTarget(u)}>
                            Reset password
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            disabled={isSelf}
                            title={isSelf ? 'You cannot change your own role' : undefined}
                            onSelect={() => !isSelf && setRoleTarget(u)}
                          >
                            {u.role === 'admin' ? 'Demote to user' : 'Promote to admin'}
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem
                            variant="destructive"
                            disabled={isSelf}
                            title={isSelf ? 'You cannot delete your own account' : undefined}
                            onSelect={() => !isSelf && setDeleteTarget(u)}
                          >
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </div>

      {/* Dialogs */}
      <AddUserDialog open={addOpen} onOpenChange={setAddOpen} />
      <ResetPasswordDialog
        user={resetTarget}
        open={resetTarget !== null}
        onOpenChange={(v) => { if (!v) setResetTarget(null); }}
      />
      <RoleDialog
        user={roleTarget}
        open={roleTarget !== null}
        onOpenChange={(v) => { if (!v) setRoleTarget(null); }}
        onConfirm={(id, role) => roleMutation.mutate({ id, role })}
        isPending={roleMutation.isPending}
      />
      <DeleteUserDialog
        user={deleteTarget}
        open={deleteTarget !== null}
        onOpenChange={(v) => { if (!v) setDeleteTarget(null); }}
        onConfirm={(id) => deleteMutation.mutate(id)}
        isPending={deleteMutation.isPending}
      />
    </div>
  );
}
