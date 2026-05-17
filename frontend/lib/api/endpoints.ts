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
import { MOCK_MODE, apiFetch, ApiError } from './client';
import type { ChatStream } from './sse';
import { createChatStream } from './sse';
import {
  MOCK_USERS,
  MOCK_REPOS,
  MOCK_DOMAINS,
  MOCK_JOBS,
  MOCK_STATS,
  MOCK_GRAPH_DATA,
  generateTempPassword,
} from './mocks';

// ─── Auth ──────────────────────────────────────────────────────────────────

export async function login(email: string, password: string): Promise<LoginResponse> {
  if (MOCK_MODE) {
    const user = MOCK_USERS.find((u) => u.email === email);
    if (!user) throw new ApiError(401, 'Invalid credentials');
    // Accept any password in mock mode
    void password;
    return { ok: true, user };
  }

  return apiFetch<LoginResponse>('/api/auth/login', {
    method: 'POST',
    body: { email, password } satisfies LoginRequest,
  });
}

export async function logout(): Promise<void> {
  if (MOCK_MODE) return;

  await apiFetch<void>('/api/auth/logout', { method: 'POST' });
}

export async function me(): Promise<User> {
  if (MOCK_MODE) {
    const user = MOCK_USERS[0];
    if (!user) throw new ApiError(500, 'No mock users');
    return user;
  }

  return apiFetch<User>('/api/users/me');
}

// ─── Stats ─────────────────────────────────────────────────────────────────

export async function getStats(): Promise<Stats> {
  if (MOCK_MODE) return MOCK_STATS;

  return apiFetch<Stats>('/api/stats');
}

// ─── Repositories ──────────────────────────────────────────────────────────

export async function listRepos(): Promise<Repository[]> {
  if (MOCK_MODE) return MOCK_REPOS;

  return apiFetch<Repository[]>('/api/repos');
}

export async function addRepo(url: string, paths?: string[]): Promise<Repository> {
  if (MOCK_MODE) {
    const newRepo: Repository = {
      id: `r-${Date.now()}`,
      name: url.split('/').pop() ?? url,
      url,
      paths: paths ?? [],
      lastIndexed: null,
      nodeCount: 0,
      status: 'pending',
    };
    MOCK_REPOS.push(newRepo);
    return newRepo;
  }

  return apiFetch<Repository>('/api/repos', {
    method: 'POST',
    body: { url, paths } satisfies AddRepoRequest,
  });
}

export async function reindexRepo(id: string): Promise<IndexingJob> {
  if (MOCK_MODE) {
    const repo = MOCK_REPOS.find((r) => r.id === id);
    if (!repo) throw new ApiError(404, `Repository ${id} not found`);
    const job: IndexingJob = {
      id: `j-${Date.now()}`,
      repoId: id,
      repoName: repo.name,
      status: 'running',
      startedAt: new Date().toISOString(),
      finishedAt: null,
      durationMs: null,
      nodeCount: null,
      error: null,
    };
    MOCK_JOBS.unshift(job);
    return job;
  }

  return apiFetch<IndexingJob>(`/api/repos/${id}/reindex`, { method: 'POST' });
}

export async function deleteRepo(id: string): Promise<void> {
  if (MOCK_MODE) {
    const idx = MOCK_REPOS.findIndex((r) => r.id === id);
    if (idx === -1) throw new ApiError(404, `Repository ${id} not found`);
    MOCK_REPOS.splice(idx, 1);
    return;
  }

  await apiFetch<void>(`/api/repos/${id}`, { method: 'DELETE' });
}

// ─── Domains ───────────────────────────────────────────────────────────────

export async function listDomains(repoId?: string): Promise<Domain[]> {
  if (MOCK_MODE) {
    return repoId ? MOCK_DOMAINS.filter((d) => d.repoId === repoId) : MOCK_DOMAINS;
  }

  const qs = repoId ? `?repoId=${encodeURIComponent(repoId)}` : '';
  return apiFetch<Domain[]>(`/api/domains${qs}`);
}

export async function updateDomain(
  id: string,
  summary: string,
  humanVerified: boolean,
): Promise<Domain> {
  if (MOCK_MODE) {
    const domain = MOCK_DOMAINS.find((d) => d.id === id);
    if (!domain) throw new ApiError(404, `Domain ${id} not found`);
    domain.summary = summary;
    domain.humanVerified = humanVerified;
    domain.lastUpdated = new Date().toISOString();
    return domain;
  }

  return apiFetch<Domain>(`/api/domains/${id}`, {
    method: 'PATCH',
    body: { summary, humanVerified } satisfies UpdateDomainRequest,
  });
}

export async function regenerateDomainSummary(id: string): Promise<Domain> {
  if (MOCK_MODE) {
    const domain = MOCK_DOMAINS.find((d) => d.id === id);
    if (!domain) throw new ApiError(404, `Domain ${id} not found`);
    domain.summary =
      `[Regenerated] ${domain.summary.slice(0, 80)}... ` +
      `This domain contains ${domain.memberCount} members and was last updated ${domain.lastUpdated}.`;
    domain.humanVerified = false;
    domain.lastUpdated = new Date().toISOString();
    return domain;
  }

  return apiFetch<Domain>(`/api/domains/${id}/regenerate`, { method: 'POST' });
}

// ─── Users ─────────────────────────────────────────────────────────────────

export async function listUsers(): Promise<User[]> {
  if (MOCK_MODE) return MOCK_USERS;

  return apiFetch<User[]>('/api/users');
}

export async function addUser(email: string): Promise<AddUserResponse> {
  if (MOCK_MODE) {
    const existing = MOCK_USERS.find((u) => u.email === email);
    if (existing) throw new ApiError(409, `User ${email} already exists`);
    const user: User = {
      id: `u-${Date.now()}`,
      email,
      role: 'user',
      createdAt: new Date().toISOString(),
      lastLogin: null,
    };
    MOCK_USERS.push(user);
    return { user, temporaryPassword: generateTempPassword() };
  }

  return apiFetch<AddUserResponse>('/api/users', { method: 'POST', body: { email } });
}

export async function resetUserPassword(id: string): Promise<ResetPasswordResponse> {
  if (MOCK_MODE) {
    const user = MOCK_USERS.find((u) => u.id === id);
    if (!user) throw new ApiError(404, `User ${id} not found`);
    return { temporaryPassword: generateTempPassword() };
  }

  return apiFetch<ResetPasswordResponse>(`/api/users/${id}/reset-password`, { method: 'POST' });
}

export async function setUserRole(id: string, role: Role): Promise<User> {
  if (MOCK_MODE) {
    const user = MOCK_USERS.find((u) => u.id === id);
    if (!user) throw new ApiError(404, `User ${id} not found`);
    user.role = role;
    return user;
  }

  return apiFetch<User>(`/api/users/${id}/role`, { method: 'PATCH', body: { role } });
}

export async function deleteUser(id: string): Promise<void> {
  if (MOCK_MODE) {
    const idx = MOCK_USERS.findIndex((u) => u.id === id);
    if (idx === -1) throw new ApiError(404, `User ${id} not found`);
    MOCK_USERS.splice(idx, 1);
    return;
  }

  await apiFetch<void>(`/api/users/${id}`, { method: 'DELETE' });
}

// ─── Chat ──────────────────────────────────────────────────────────────────

export function sendChatMessage(message: string, persona: Persona): ChatStream {
  // MOCK_MODE check is inside createChatStream
  return createChatStream(message, persona);
}

// ─── Graph ─────────────────────────────────────────────────────────────────

export async function getGraph(repoId?: string): Promise<GraphData> {
  if (MOCK_MODE) {
    if (!repoId) return MOCK_GRAPH_DATA;
    const filtered = {
      nodes: MOCK_GRAPH_DATA.nodes.filter(
        (n) => MOCK_DOMAINS.find((d) => d.id === n.domainId)?.repoId === repoId,
      ),
      edges: [] as GraphData['edges'],
    };
    const nodeSet = new Set(filtered.nodes.map((n) => n.id));
    filtered.edges = MOCK_GRAPH_DATA.edges.filter(
      (e) => nodeSet.has(e.source) && nodeSet.has(e.target),
    );
    return filtered;
  }

  const qs = repoId ? `?repoId=${encodeURIComponent(repoId)}` : '';
  return apiFetch<GraphData>(`/api/graph${qs}`);
}
