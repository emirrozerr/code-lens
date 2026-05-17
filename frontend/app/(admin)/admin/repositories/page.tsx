'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { listRepos, addRepo, reindexRepo, deleteRepo } from '@/lib/api/endpoints';
import { ApiError } from '@/lib/api/client';
import type { Repository } from '@/types/api';
import { ReposTable } from '@/components/admin/ReposTable';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Plus } from 'lucide-react';

// ─── Add repo dialog ────────────────────────────────────────────────────────

interface AddDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAdd: (url: string, paths: string[]) => void;
  isPending: boolean;
}

function AddRepoDialog({ open, onOpenChange, onAdd, isPending }: AddDialogProps) {
  const [url, setUrl] = useState('');
  const [paths, setPaths] = useState('');

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const pathList = paths
      .split(',')
      .map((p) => p.trim())
      .filter(Boolean);
    onAdd(url.trim(), pathList);
  }

  return (
    <Dialog open={open} onOpenChange={(v: boolean) => { onOpenChange(v); if (!v) { setUrl(''); setPaths(''); } }}>
      <DialogContent style={{ maxWidth: '480px' }}>
        <DialogHeader>
          <DialogTitle>Add repository</DialogTitle>
        </DialogHeader>
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
              GitHub URL
            </label>
            <Input
              type="url"
              placeholder="https://github.com/owner/repo"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
            />
          </div>
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
              Path filter{' '}
              <span style={{ color: 'var(--text-dim)' }}>(optional, comma-separated)</span>
            </label>
            <Input
              type="text"
              placeholder="src/main/java, lib"
              value={paths}
              onChange={(e) => setPaths(e.target.value)}
            />
          </div>
          <DialogFooter>
            <Button type="submit" disabled={!url.trim() || isPending}>
              {isPending ? 'Adding…' : 'Add repository'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

// ─── Delete confirmation dialog ─────────────────────────────────────────────

interface DeleteDialogProps {
  repo: Repository | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  isPending: boolean;
}

function DeleteRepoDialog({ repo, open, onOpenChange, onConfirm, isPending }: DeleteDialogProps) {
  const [typed, setTyped] = useState('');
  const matches = typed === repo?.name;

  return (
    <Dialog open={open} onOpenChange={(v: boolean) => { onOpenChange(v); if (!v) setTyped(''); }}>
      <DialogContent style={{ maxWidth: '440px' }}>
        <DialogHeader>
          <DialogTitle>Delete repository</DialogTitle>
        </DialogHeader>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.875rem' }}>
          <p
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: '0.875rem',
              color: 'var(--text-muted)',
              lineHeight: 1.6,
            }}
          >
            This will permanently delete{' '}
            <span
              style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)', fontSize: '0.8125rem' }}
            >
              {repo?.name}
            </span>{' '}
            and all its indexed data. This action cannot be undone.
          </p>
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
              Type <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text)' }}>{repo?.name}</span> to confirm
            </label>
            <Input
              type="text"
              placeholder={repo?.name ?? ''}
              value={typed}
              onChange={(e) => setTyped(e.target.value)}
            />
          </div>
          <DialogFooter>
            <Button
              variant="destructive"
              disabled={!matches || isPending}
              onClick={onConfirm}
            >
              {isPending ? 'Deleting…' : 'Delete repository'}
            </Button>
          </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function RepositoriesPage() {
  const router = useRouter();
  const queryClient = useQueryClient();

  const [addOpen, setAddOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Repository | null>(null);

  const { data: repos = [], isLoading } = useQuery({
    queryKey: ['repos'],
    queryFn: listRepos,
    refetchOnWindowFocus: true,
  });

  const addMutation = useMutation({
    mutationFn: ({ url, paths }: { url: string; paths: string[] }) => addRepo(url, paths),
    onSuccess: (newRepo) => {
      void queryClient.invalidateQueries({ queryKey: ['repos'] });
      setAddOpen(false);
      toast.success(`Added ${newRepo.name}`);
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : 'Failed to add repository');
    },
  });

  const reindexMutation = useMutation({
    mutationFn: (id: string) => reindexRepo(id),
    onSuccess: (job) => {
      void queryClient.invalidateQueries({ queryKey: ['repos'] });
      void queryClient.invalidateQueries({ queryKey: ['jobs'] });
      toast.success(`Re-indexing ${job.repoName} started`);
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : 'Failed to start re-indexing');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteRepo(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['repos'] });
      setDeleteTarget(null);
      toast.success('Repository deleted');
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : 'Failed to delete repository');
    },
  });

  return (
    <div
      style={{
        padding: '2rem',
        maxWidth: '1400px',
        margin: '0 auto',
      }}
    >
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
            Repositories
          </h1>
          <p
            style={{
              fontFamily: 'var(--font-sans)',
              fontSize: '0.875rem',
              color: 'var(--text-dim)',
              marginTop: '0.375rem',
            }}
          >
            {repos.length} repositor{repos.length === 1 ? 'y' : 'ies'} indexed
          </p>
        </div>
        <Button onClick={() => setAddOpen(true)} style={{ display: 'flex', alignItems: 'center', gap: '0.375rem' }}>
          <Plus size={14} />
          Add repository
        </Button>
      </div>

      {/* Table */}
      <div style={{ animation: 'fade-up 300ms ease-out 50ms both' }}>
        <ReposTable
          repos={repos}
          isLoading={isLoading}
          onView={(repo) => router.push(`/admin/repositories/${repo.id}`)}
          onReindex={(repo) => reindexMutation.mutate(repo.id)}
          onDelete={(repo) => setDeleteTarget(repo)}
        />
      </div>

      {/* Dialogs */}
      <AddRepoDialog
        open={addOpen}
        onOpenChange={setAddOpen}
        onAdd={(url, paths) => addMutation.mutate({ url, paths })}
        isPending={addMutation.isPending}
      />
      <DeleteRepoDialog
        repo={deleteTarget}
        open={deleteTarget !== null}
        onOpenChange={(open) => { if (!open) setDeleteTarget(null); }}
        onConfirm={() => { if (deleteTarget) deleteMutation.mutate(deleteTarget.id); }}
        isPending={deleteMutation.isPending}
      />
    </div>
  );
}
