// ─── Shared primitives ─────────────────────────────────────────────────────

export type Role = 'admin' | 'user';
export type Persona = 'developer' | 'product' | 'legal';
export type JobStatus = 'succeeded' | 'running' | 'failed' | 'pending';
export type EdgeType = 'calls' | 'imports' | 'inherits' | 'uses';

// ─── Auth ──────────────────────────────────────────────────────────────────

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  ok: true;
  user: User;
}

// ─── User ──────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  email: string;
  role: Role;
  createdAt: string;
  lastLogin: string | null;
}

export interface AddUserRequest {
  email: string;
}

export interface AddUserResponse {
  user: User;
  temporaryPassword: string;
}

export interface ResetPasswordResponse {
  temporaryPassword: string;
}

export interface SetRoleRequest {
  role: Role;
}

// ─── Stats ─────────────────────────────────────────────────────────────────

export interface Stats {
  reposCount: number;
  totalNodes: number;
  domainsCount: number;
  activeUsers: number;
  neo4jStatus: 'ok' | 'degraded' | 'down';
  mcpUptime: number;
  lastSuccessfulIndex: string | null;
}

// ─── Repository ────────────────────────────────────────────────────────────

export interface Repository {
  id: string;
  name: string;
  url: string;
  paths: string[];
  lastIndexed: string | null;
  nodeCount: number;
  status: 'indexed' | 'indexing' | 'failed' | 'pending';
}

export interface AddRepoRequest {
  url: string;
  paths?: string[];
}

// ─── Indexing Job ──────────────────────────────────────────────────────────

export interface IndexingJob {
  id: string;
  repoId: string;
  repoName: string;
  status: JobStatus;
  startedAt: string;
  finishedAt: string | null;
  durationMs: number | null;
  nodeCount: number | null;
  error: string | null;
}

// ─── Domain ────────────────────────────────────────────────────────────────

export interface Domain {
  id: string;
  name: string;
  repoId: string;
  repoName: string;
  memberCount: number;
  summary: string;
  humanVerified: boolean;
  lastUpdated: string;
}

export interface UpdateDomainRequest {
  summary: string;
  humanVerified: boolean;
}

// ─── Graph ─────────────────────────────────────────────────────────────────

export interface GraphNode {
  id: string;
  label: string;
  file: string;
  signature: string;
  domain: string;
  domainId: string;
  degree: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: EdgeType;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

// ─── Chat / SSE ────────────────────────────────────────────────────────────

export interface ChatMessageRequest {
  message: string;
  persona: Persona;
}

export interface ToolCallRecord {
  id: string;
  tool: string;
  args: Record<string, unknown>;
  result: string | null;
  durationMs: number | null;
  status: 'running' | 'done' | 'error';
  error: string | null;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  toolCalls?: ToolCallRecord[];
}

export type ChatEvent =
  | { type: 'token'; content: string }
  | { type: 'tool_call_start'; tool: string; args: Record<string, unknown>; id: string }
  | { type: 'tool_call_end'; id: string; result: string; durationMs: number }
  | { type: 'done' }
  | { type: 'error'; message: string };
