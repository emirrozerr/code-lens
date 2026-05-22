# CodeLens Frontend — Next.js Build Plan

> **For:** AI coding agent (Cursor, Claude Code, Copilot)  
> **Project:** CodeLens presentation layer rebuild (Streamlit → Next.js)  
> **Branch:** `feature/nextjs-frontend`  
> **Related:** Closed PR #20 (Streamlit V1), Epic #11 (Admin Panel), Epic #12 (Demo Interface)  
> **Architecture decision:** [ADR-003](./docs/decisions/ADR-003-presentation-tier-strategy.md) — thin client over HTTP to FastAPI

---

## What This Project Is

CodeLens is a **code intelligence infrastructure layer**. It parses codebases into a Neo4j knowledge graph and exposes that graph through an MCP server. The presentation layer (this frontend) is the human-facing surface — both an **admin panel** for managing the system and an **"Ask CodeLens" demo interface** where users query the codebase in natural language.

This frontend replaces a Streamlit prototype that was rejected for three reasons:
1. Streamlit's server-rerun model produces visible latency and flicker — not acceptable for a premium SaaS demo
2. CodeLens is a graph product; Streamlit cannot render the interactive force-directed graph that proves what the system is
3. 500+ lines of CSS targeting undocumented Streamlit DOM (`[data-testid="..."]`) is fragile maintenance debt

**This rebuild's mission: a presentation layer that visibly looks and feels like a real product, with an interactive graph that lands the "wow factor" for the stakeholder demo.**

---

## Hard Constraints

These are non-negotiable. Do not deviate without explicit confirmation.

### Architecture
- **Thin HTTP client.** The frontend never talks to Neo4j directly. All data access goes through the FastAPI backend over REST and SSE. This satisfies the multi-tier requirement.
- **Mock mode.** A `NEXT_PUBLIC_MOCK_MODE` env flag must allow the entire app to run from in-memory fixtures, with zero backend dependency. The Streamlit prototype had this and it was correct.
- **Role-based routing.** Two roles: `user` (chat only) and `admin` (full panel). Admin routes return 403 to non-admin tokens.
- **No persona parameter on MCP/API tools.** Persona (Developer / Product Manager / Legal) is purely a client-side system-prompt concern. Do not push it into backend signatures.

### Stack
- **Framework:** Next.js 15 with App Router and TypeScript (strict mode)
- **Styling:** Tailwind CSS v4 + shadcn/ui (use only when shadcn primitives are the right fit; do not over-rely)
- **State:** TanStack Query for server state, React Context for persona/auth
- **Animation:** Framer Motion (or Motion library) for page transitions and micro-interactions
- **Graph viz:** `react-force-graph-2d` for the domain cluster visualisation
- **Streaming:** Native `EventSource` for SSE chat
- **Auth:** JWT in httpOnly cookie set via Next.js Route Handler, attached as `Authorization: Bearer` on backend calls

### What NOT to do
- Do not use localStorage or sessionStorage for the JWT — httpOnly cookie only
- Do not render anything important without a loading skeleton — flicker is the enemy
- Do not pick the default shadcn/Inter look — this is a graph intelligence product, not a generic SaaS template (see Design Direction below)
- Do not put `console.log` statements in committed code
- Do not write any code without TypeScript types; never use `any`

---

## Design Direction

This is the part that separates a real product from "another Vercel template." Commit to it.

### Aesthetic
**Refined editorial × technical infrastructure.** Think Vercel's monochrome severity meets Linear's restraint meets Stripe's polish. The product is about precision and structure — the UI must feel structurally precise. Not playful. Not toy-like. Not over-animated.

### Concrete tokens

```css
/* Color */
--bg: #0a0a0a;          /* near-black background */
--surface: #141414;      /* card surface */
--surface-elevated: #1c1c1c;
--border: #262626;
--border-strong: #404040;
--text: #f5f5f5;
--text-muted: #a3a3a3;
--text-dim: #525252;
--accent: #8b5cf6;       /* single sharp accent — violet for "graph intelligence" */
--accent-glow: rgba(139, 92, 246, 0.15);
--success: #10b981;
--warning: #f59e0b;
--danger: #ef4444;

/* Typography */
--font-display: 'Instrument Serif', Georgia, serif;   /* hero headings only, sparingly */
--font-sans: 'Geist', system-ui, sans-serif;          /* body, UI */
--font-mono: 'Geist Mono', ui-monospace, monospace;   /* code, identifiers, IDs */

/* Spacing — generous, not cramped */
/* Radius — small (4-6px); this is technical software, not a kids app */
```

The display serif used **once or twice per page** (page title, hero number) on top of the sans body creates the editorial signature. Don't overuse it.

### Motion

- Page transitions: 200ms ease-out fades between routes
- Skeleton loaders for every data-bound view (no spinners)
- Staggered list reveals on first paint (50ms delay step)
- Subtle hover state on every interactive element — opacity or border, not transform
- The force-directed graph is the only "alive" element on the page; everything else is calm by contrast

### Layout rules

- Admin: persistent left sidebar, content area with breathing room
- Demo (Ask): full-bleed chat with collapsible left sidebar for domains
- All pages: max-width 1400px content container, generous padding
- Mobile is **not** in scope for MVP — desktop-only is acceptable. Render a "best on desktop" notice below 1024px

---

## Folder Structure

Create this exact structure inside the repo at `frontend/`:

```
frontend/
├── app/
│   ├── layout.tsx                  # root layout, fonts, theme provider
│   ├── globals.css                 # tailwind + tokens
│   ├── page.tsx                    # marketing landing or redirect to /login
│   ├── (auth)/
│   │   └── login/
│   │       └── page.tsx
│   ├── (admin)/
│   │   ├── layout.tsx              # sidebar + admin header
│   │   └── admin/
│   │       ├── dashboard/page.tsx
│   │       ├── repositories/page.tsx
│   │       ├── domains/page.tsx
│   │       └── users/page.tsx
│   ├── (demo)/
│   │   ├── layout.tsx              # chat header + domain sidebar
│   │   └── ask/page.tsx
│   ├── api/
│   │   └── auth/
│   │       ├── login/route.ts      # sets httpOnly cookie
│   │       └── logout/route.ts     # clears cookie
│   └── middleware.ts               # route protection
├── components/
│   ├── ui/                         # shadcn primitives
│   ├── admin/
│   │   ├── KpiCard.tsx
│   │   ├── JobsTable.tsx
│   │   ├── HealthCard.tsx
│   │   ├── ReposTable.tsx
│   │   ├── DomainCard.tsx
│   │   └── UsersTable.tsx
│   ├── chat/
│   │   ├── ChatPage.tsx
│   │   ├── MessageList.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── ToolCallCard.tsx
│   │   ├── PersonaToggle.tsx
│   │   ├── DomainSidebar.tsx
│   │   ├── EmptyState.tsx
│   │   └── ChatInput.tsx
│   ├── graph/
│   │   └── DomainGraph.tsx         # react-force-graph wrapper
│   └── layout/
│       ├── AppSidebar.tsx
│       └── AppHeader.tsx
├── lib/
│   ├── api/
│   │   ├── client.ts               # typed fetch wrapper
│   │   ├── mocks.ts                # fixture data for MOCK_MODE
│   │   ├── endpoints.ts            # one function per backend endpoint
│   │   └── sse.ts                  # EventSource wrapper for chat
│   ├── auth.ts                     # JWT helpers, useAuth hook
│   ├── persona.ts                  # PersonaContext provider
│   └── utils.ts                    # cn(), formatters
├── types/
│   ├── api.ts                      # all API response shapes
│   ├── domain.ts
│   ├── user.ts
│   └── chat.ts
├── public/
│   └── fonts/                      # self-hosted Geist + Instrument Serif
├── .env.local.example
├── .eslintrc.json
├── .prettierrc
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── README.md
```

---

## Story-by-Story Build Order

Stories below map 1-to-1 with GitHub issues #41-#53. Follow this order strictly — each builds on the previous.

### #41 — Next.js skeleton (P0, S)

**Branch:** `feature/41-nextjs-skeleton` off `feature/nextjs-frontend`

- Initialize Next.js 15 app under `frontend/` with App Router and TypeScript
- Install Tailwind v4, configure with the design tokens above in `globals.css`
- Install shadcn/ui, scaffold base components: button, input, dialog, dropdown, badge, table, skeleton, toast
- Add Geist font + Instrument Serif (self-host in `public/fonts/`)
- Configure TS strict mode with these `tsconfig.json` paths:
  ```json
  "paths": {
    "@/*": ["./*"],
    "@/components/*": ["./components/*"],
    "@/lib/*": ["./lib/*"],
    "@/types/*": ["./types/*"]
  }
  ```
- ESLint config: extend `next/core-web-vitals`, `@typescript-eslint/recommended`. No `any`.
- Prettier config: 2-space, single quotes, trailing comma all
- `.env.local.example` with: `NEXT_PUBLIC_API_BASE_URL`, `NEXT_PUBLIC_MOCK_MODE`, `JWT_COOKIE_NAME`
- Default `app/page.tsx` renders a styled landing showing the design tokens working — Instrument Serif heading + Geist body, dark background, violet accent button

**Done when:** `pnpm dev` shows the landing on localhost:3000 with the design tokens visibly applied. `pnpm typecheck` and `pnpm lint` are clean.

### #47 — Typed API client with mock mode (P0, M)

**Build this before any UI that fetches data.** Otherwise you'll write throwaway hardcoded data.

- `lib/api/client.ts` — typed `fetch` wrapper with `MOCK_MODE` check at the top of every call
- `lib/api/mocks.ts` — fixture data covering:
  - 2 mock users (1 admin, 1 regular)
  - 3 indexed repositories with realistic numbers (Spring PetClinic-style)
  - 12 domains with summaries
  - 50 recent indexing jobs
  - Sample chat conversations with tool calls
  - Sample graph data: ~200 nodes, ~400 edges
- `lib/api/endpoints.ts` — one function per endpoint:
  ```ts
  login(email, password)
  logout()
  me()
  getStats()
  listRepos()
  addRepo(url, paths)
  reindexRepo(id)
  deleteRepo(id)
  listDomains(repoId?)
  updateDomain(id, summary, humanVerified)
  regenerateDomainSummary(id)
  listUsers()
  addUser(email)
  resetUserPassword(id)
  setUserRole(id, role)
  deleteUser(id)
  sendChatMessage(message, persona)  // returns EventSource for SSE
  getGraph(repoId)
  ```
- `types/api.ts` — every endpoint has fully-typed request and response shapes
- Centralized error class `ApiError` with `status` and `message`
- Retry once on network error for idempotent GETs

**Done when:** Toggling `NEXT_PUBLIC_MOCK_MODE=true` in `.env.local` makes every endpoint return realistic data. With it `false`, calls go to the real `NEXT_PUBLIC_API_BASE_URL`.

### #42 — JWT auth flow (P0, M)

- `/login` page — centered card on dark background, email + password, Instrument Serif "Sign in" heading
- `app/api/auth/login/route.ts` — Route Handler that:
  - Calls `POST /auth/login` on the FastAPI backend
  - On success, sets httpOnly cookie with the JWT (`secure: true`, `sameSite: 'lax'`, `maxAge: 86400`)
  - Returns `{ ok: true, user }` to the client
- `app/api/auth/logout/route.ts` — clears the cookie
- `middleware.ts` — protect `(admin)` and `(demo)` route groups, redirect to `/login` when no cookie
- `lib/auth.ts` — `useAuth()` hook returning `{ user, role, loading, logout }`
- Auth-aware nav: admin role sees full sidebar, user role sees only "Ask" link
- Friendly error states: invalid credentials, network failure, expired token

**Done when:** Logging in with `admin@codelens.dev` / any password in mock mode lands on `/admin/dashboard`. Logging in with `user@codelens.dev` / any password lands on `/ask`. Visiting `/admin/*` without auth redirects to `/login`.

### #53 — Auth gate for demo pages (P0, S)

Already covered by #42 middleware if `(demo)` route group is protected. **Verify and close the issue** rather than reimplementing. Add the header chip (user email + persona badge) and the logout button on the chat header here.

### #43 — Dashboard page (P1, M)

Route: `/admin/dashboard`

Layout:
- Hero KPI row: 4 large numbers in Instrument Serif (Repos Indexed / Total Nodes / Domains / Active Users) with Geist Mono labels above
- Below: two-column grid
  - Left: "Recent indexing jobs" table — last 10 jobs with status pill (succeeded / running / failed)
  - Right: "System health" card — Neo4j status, MCP server uptime, last successful index
- Skeleton state for every block before data resolves
- Staggered reveal on first paint

Use TanStack Query for the data fetch. Refetch on window focus.

### #44 — Repositories CRUD (P1, L)

Route: `/admin/repositories`

- Table view: name, path, last indexed, node count, status, actions menu
- "Add repository" button → dialog with GitHub URL input + optional path filter, posts to backend, optimistic insert
- Row actions menu: View detail / Re-index / Delete
- Re-index: toast with progress indicator, refetch on completion
- Delete: typed confirmation ("type the repo name to confirm")
- Repository detail view: `/admin/repositories/[id]` — shows per-repo stats, indexing history, link to its domains

### #45 — Domains management (P1, M)

Route: `/admin/domains`

- Filter dropdown at top: scope by repository
- Grid of domain cards (3 per row at desktop width):
  - Domain name (sans bold)
  - Member count (mono)
  - Summary text (editable inline — click to edit, save on blur or Cmd+Enter)
  - Human-verified toggle (small switch, top-right of card)
  - "Regenerate" button (only on hover, top-right corner)
  - Last-updated timestamp at bottom (dim text)
- Optimistic updates: toggle and save respond instantly, rollback on error
- Regenerate calls LLM endpoint, shows pulsing loader on the card, replaces summary on success

### #46 — Users management (P2, M)

Route: `/admin/users`

- Table: email, role badge, created, last login, actions
- "Add user" dialog: email input → on submit, backend returns one-time temp password → display password in a copyable code block (copy button + warning "this will not be shown again")
- Reset password action: same temp-password flow
- Role toggle dropdown (User / Admin) with confirm dialog
- Delete with confirm dialog
- Currently-logged-in admin row: delete and demote actions are disabled with a tooltip explaining why

### #48 — Chat page layout + empty state (P0, M)

Route: `/ask`

Layout:
- Header bar with: CodeLens wordmark (left), persona toggle (center), user chip + logout (right)
- Main: full-bleed chat area
- Left sidebar: collapsible, holds domain browser (filled by #51)
- Bottom: input area pinned to bottom, multi-line textarea, Enter submits, Shift+Enter newline

Empty state (no messages):
- Centered, vertically aligned
- Instrument Serif "Ask CodeLens" + small subtitle in Geist
- Three example prompt cards in a row:
  1. "Explain how the checkout flow works"
  2. "Which functions call `apply_discount`?"
  3. "Show me the auth domain"
- Clicking a card sends it as the first user message

Message bubbles:
- User: right-aligned, surface-elevated background, tight corners
- Assistant: left-aligned, no background, just text with subtle border-left accent
- Markdown rendering for assistant: code blocks with syntax highlighting (use `shiki` or `prismjs`), lists, links

### #49 — SSE streaming + tool-call transparency (P0, L)

This is the most technically demanding story. Plan it carefully.

- `lib/api/sse.ts` — `EventSource` wrapper with typed event parsing
- Event types:
  ```ts
  type ChatEvent =
    | { type: 'token'; content: string }
    | { type: 'tool_call_start'; tool: string; args: Record<string, unknown>; id: string }
    | { type: 'tool_call_end'; id: string; result: string; durationMs: number }
    | { type: 'done' }
    | { type: 'error'; message: string }
  ```
- Tool call card UI (collapsible):
  - Running state: pulsing border, tool name + spinner, args shown in mono
  - Done state: solid border, duration badge, click to expand result preview (max 200 chars then "..." with full expand)
  - Errored state: red border + error message
- Tokens stream into the active assistant message bubble character-by-character
- Cancel button: kills the EventSource, marks the response as cancelled, preserves the partial text
- Reconnect on transient errors (one retry)

### #50 — Persona toggle (P1, S)

- Segmented control at top of chat (3 options): Developer · Product · Legal
- Each persona has a one-line description shown on hover
- Selection persists in `sessionStorage` and is sent with every chat request as `persona: 'developer' | 'product' | 'legal'` — backend converts to system prompt instruction
- Visual: selected option gets the violet accent border, others are muted
- Switching mid-conversation only affects the next response (do not rewrite past messages)

### #51 — Domain browser sidebar (P1, M)

- Collapsible left sidebar on `/ask` page
- Header: "Domains" + count
- Search input filters list as you type (client-side)
- Domain list: each item shows name + 1-line summary preview + member count
- Click handler: inserts templated prompt into input ("Tell me about the X domain — what does it do, what are its key functions, and what are its dependencies?") and auto-submits
- Highlight last-clicked domain (subtle violet border)
- Empty state: "No domains discovered yet. Index a repository first."

### #52 — Force-directed graph viz (P1, L)

This is the **wow factor** — make it sing.

- Route: `/graph` (or a fullscreen modal accessible from anywhere with kbd shortcut `g`)
- `react-force-graph-2d` rendering domain clusters from `/api/graph`
- Visual:
  - Black background
  - Nodes colored by domain (palette of 12 distinct but harmonious colors — generate from a base hue rotation, not random)
  - Node radius proportional to degree (incoming + outgoing edges)
  - Edges as thin lines with low opacity (~0.3)
  - On node hover: highlight node and direct neighbors, dim everything else
  - On node click: side panel slides in from right with node details (name, file, signature, domain, neighbors list)
- Controls overlay (top-left):
  - Repository selector dropdown
  - Domain filter chips (multi-select, click to toggle)
  - "Reset view" button
- Pan and zoom enabled (default react-force-graph behavior)
- Initial layout: warm up simulation for ~300 ticks before first paint so the graph doesn't jitter into place
- Performance target: 500 nodes / 1000 edges at 60fps on a typical laptop

---

## After All Stories Are Done

1. Run `pnpm typecheck` and `pnpm lint` — both clean
2. Run the app with `NEXT_PUBLIC_MOCK_MODE=true` and walk through every page
3. Update the repo root `README.md` with a "Frontend" section pointing to `frontend/README.md`
4. Open a PR from `feature/nextjs-frontend` to `main` titled `feat: Next.js presentation layer (replaces PR #20)` with description listing every closed issue (#41-#53)
5. Tag Emir for review

---

## Working Conventions

- **Branch per story:** `feature/<issue-number>-<short-name>`, e.g. `feature/42-jwt-auth`
- **Commits:** Reference the issue: `feat(auth): implement login route handler (#42)`
- **PR per story:** Open a small PR for each story merged into `feature/nextjs-frontend`. Don't merge to `main` until the whole epic is done.
- **Close issues via PR:** Use `Closes #42` in the PR description

---

## Definition of Done (project-wide)

A story is done when **all** of these are true:
- [ ] All tasks in the issue checklist are complete
- [ ] All acceptance criteria pass
- [ ] TypeScript compiles with zero errors and zero `any`
- [ ] ESLint passes with no warnings
- [ ] Works in `MOCK_MODE=true` with realistic fixture data
- [ ] Loading states are present for any data-bound view
- [ ] Error states are handled (not just `throw`)
- [ ] No `console.log` left in committed code
- [ ] PR merged into `feature/nextjs-frontend`

---

## What to Ask Before Starting

If anything below is unclear, **ask before writing code:**

1. The backend FastAPI endpoints are not yet implemented for some admin routes. Confirm which endpoints you should mock vs. wait for.
2. The exact shape of the `/api/graph` response for #52 — confirm with the backend team before building the graph viz.
3. Whether to self-host the fonts or use Google Fonts — recommendation: self-host for performance and consistency.
4. Whether the demo will be deployed to a public URL (Vercel) or only run locally for the presentation — affects auth cookie domain config.

---

**End of plan. Begin with #41.**
