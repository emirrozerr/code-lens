import type {
  LoginRequest,
  LoginResponse,
  User,
  Stats,
  Repository,
  AddRepoRequest,
  Domain,
  UpdateDomainRequest,
  GraphData,
  Persona,
  AddUserResponse,
  ResetPasswordResponse,
  Role,
  IndexingJob,
} from '@/types/api';
import { apiFetch } from './client';
import type { ChatStream } from './sse';
import { createChatStream } from './sse';

// ─── Auth ──────────────────────────────────────────────────────────────────

export async function login(email: string, password: string): Promise<LoginResponse> {
  return apiFetch<LoginResponse>('/api/auth/login', {
    method: 'POST',
    body: { email, password } satisfies LoginRequest,
  });
}

export async function logout(): Promise<void> {
  await apiFetch<void>('/api/auth/logout', { method: 'POST' });
}

export async function me(): Promise<User> {
  return apiFetch<User>('/api/users/me');
}

// ─── Stats ─────────────────────────────────────────────────────────────────

export async function getStats(): Promise<Stats> {
  return apiFetch<Stats>('/api/stats');
}

// ─── Repositories ──────────────────────────────────────────────────────────

export async function listRepos(): Promise<Repository[]> {
  return apiFetch<Repository[]>('/api/repos');
}

export async function addRepo(url: string, paths?: string[]): Promise<Repository> {
  return apiFetch<Repository>('/api/repos', {
    method: 'POST',
    body: { url, paths } satisfies AddRepoRequest,
  });
}

export async function reindexRepo(id: string): Promise<IndexingJob> {
  return apiFetch<IndexingJob>(`/api/repos/${id}/reindex`, { method: 'POST' });
}

export async function deleteRepo(id: string): Promise<void> {
  await apiFetch<void>(`/api/repos/${id}`, { method: 'DELETE' });
}

// ─── Jobs ──────────────────────────────────────────────────────────────────

export async function listJobs(limit = 50): Promise<IndexingJob[]> {
  return apiFetch<IndexingJob[]>(`/api/jobs?limit=${limit}`);
}

// ─── Domains ───────────────────────────────────────────────────────────────

export async function listDomains(repoId?: string): Promise<Domain[]> {
  const qs = repoId ? `?repoId=${encodeURIComponent(repoId)}` : '';
  return apiFetch<Domain[]>(`/api/domains${qs}`);
}

export async function updateDomain(
  id: string,
  summary: string,
  humanVerified: boolean,
): Promise<Domain> {
  return apiFetch<Domain>(`/api/domains/${id}`, {
    method: 'PATCH',
    body: { summary, humanVerified } satisfies UpdateDomainRequest,
  });
}

export async function regenerateDomainSummary(id: string): Promise<Domain> {
  return apiFetch<Domain>(`/api/domains/${id}/regenerate`, { method: 'POST' });
}

// ─── Users ─────────────────────────────────────────────────────────────────

export async function listUsers(): Promise<User[]> {
  return apiFetch<User[]>('/api/users');
}

export async function addUser(email: string, password?: string): Promise<AddUserResponse> {
  return apiFetch<AddUserResponse>('/api/users', { method: 'POST', body: { email, password } });
}

export async function resetUserPassword(id: string): Promise<ResetPasswordResponse> {
  return apiFetch<ResetPasswordResponse>(`/api/users/${id}/reset-password`, { method: 'POST' });
}

export async function setUserRole(id: string, role: Role): Promise<User> {
  return apiFetch<User>(`/api/users/${id}/role`, { method: 'PATCH', body: { role } });
}

export async function deleteUser(id: string): Promise<void> {
  await apiFetch<void>(`/api/users/${id}`, { method: 'DELETE' });
}

// ─── Chat ──────────────────────────────────────────────────────────────────

export function sendChatMessage(message: string, persona: Persona): ChatStream {
  return createChatStream(message, persona);
}

// ─── Graph ─────────────────────────────────────────────────────────────────

export async function getGraph(repoId?: string): Promise<GraphData> {
  const qs = repoId ? `?repoId=${encodeURIComponent(repoId)}` : '';
  return apiFetch<GraphData>(`/api/graph${qs}`);
}
