# ADR-002 — Code Discovery Strategy: Semantic Search vs Agent-Led Entry Points

**Status:** Accepted  
**Date:** April 2026  
**Deciders:** Project team  

---

## Context

CodeLens exposes a graph of indexed code to AI agents via an MCP server. When an agent needs to understand a part of the codebase — for example "how does the discount logic work?" — it needs a way to find the relevant code nodes in the graph before graph traversal can begin.

The question is: **who is responsible for finding the initial entry point into the graph, and how?**

This is distinct from the rule interpretation question (ADR-001). Discovery answers "where in the graph do we start?" — traversal and interpretation answer "what do we learn from there?"

---

## Options Considered

### Option 1 — Semantic Search Inside CodeLens (Vector Embeddings)

Every code node (functions, classes, branches) receives a vector embedding at index time using an embedding model (e.g., `text-embedding-3-small` or `nomic-embed-code`). These embeddings are stored in Neo4j's built-in vector index. When the agent queries `search_code("discount logic")`, CodeLens performs a vector similarity search and returns the most semantically similar nodes.

**Advantages:**
- Handles synonym and semantic variation — "reduction" matches "discount", "refund" matches "return"
- Agents can query with natural language without prior knowledge of the codebase
- Non-technical users can discover relevant code areas without knowing function or file names

**Disadvantages:**
- Embedding model dependency at index time — an API call (or a local model) per code node
- Adds infrastructure: embedding generation, vector index management, embedding model versioning
- Embeddings go stale when code is renamed or semantically changed — requires re-embedding on change
- Embedding quality on code varies significantly by language and naming quality; poorly named code produces poor results regardless of the model
- Adds cost: embedding the entire codebase of even a mid-sized repository is non-trivial
- Semantic similarity is a probabilistic match, not a structural one — it can surface false positives

### Option 2 — Full-Text Keyword Search (Neo4j Lucene Index)

Code node names, docstrings, and inline comments are indexed in Neo4j's built-in full-text index (powered by Lucene). Queries match on keywords. After keyword match, the MCP tool expands the result via graph traversal — so searching "discount" returns not only the `apply_discount` function but also everything it calls and everything that calls it.

**Advantages:**
- No embedding model, no vector index, no external API calls at index time
- Deterministic — the same query always returns the same result
- Full-text indexing is built into Neo4j, zero extra infrastructure
- Combined with graph traversal, structural relationships expand the result beyond plain keyword hits

**Disadvantages:**
- True synonyms are not matched — "reduction" does not match "discount" unless both words appear in the code
- Quality depends on code naming conventions — poorly named code (e.g., `processItem()`) produces poor results
- Not suitable for conceptual queries ("find all places where we make external API calls") without the code using those exact words

### Option 3 — Agent-Led Discovery, Graph for Context (No Search in CodeLens)

The agent (Claude Code, Cursor, Codex, or any MCP client) performs its own code discovery using its native tools — file reading, grep, ripgrep, its own semantic file search, or AST tools it has access to. Once the agent identifies a relevant symbol or file, it calls CodeLens MCP tools to get the structural graph context around that entry point: who calls this function, what does it call, what domain does it belong to, what conditional branches govern its behaviour.

CodeLens does not implement any search functionality. It is purely a graph traversal and context enrichment service.

**Advantages:**
- CodeLens complexity is dramatically reduced — no search index of any kind to build or maintain
- The agent's native discovery tools are already very capable: Claude Code and Cursor perform semantic file search, ripgrep, and AST-aware lookups natively
- The agent brings codebase context that CodeLens does not have — open files, recent edits, the user's current task
- Graph traversal from an agent-supplied entry point is precise and structural rather than probabilistic
- CodeLens becomes a focused, single-purpose service: "given a symbol, give me its full structural context"

**Disadvantages:**
- Natural language queries like "find all refund-related logic" have no guaranteed entry point — the agent may miss parts of the codebase it would not naturally search
- Non-technical users (PM, compliance) querying via the Streamlit demo have no file-level search ability — they need an entry point that CodeLens cannot provide without some form of search
- Cross-cutting conceptual queries (e.g., "find all external API calls across the codebase") are harder without a search mechanism inside the graph

### Option 4 — Hybrid: Agent-Led Primary, Keyword as Fallback

Agents primarily bring their own entry points. CodeLens also exposes a lightweight keyword search tool as a convenience for cases where the agent does not have a starting point. Domain browsing (`get_domains()`) serves as the non-technical user entry point.

---

## Evaluation

| Dimension | Vector Embeddings | Keyword Search | Agent-Led (no search) |
|---|---|---|---|
| Infrastructure required | Embedding model + vector index | Neo4j full-text index (built-in) | None |
| Index-time cost | High (embedding per node) | Low (text indexing) | Zero |
| Synonym handling | Yes | No | Depends on agent |
| Accuracy of results | Probabilistic | Deterministic | High (agent contextual) |
| Non-technical user support | Good | Moderate | Poor without domain browsing |
| Conceptual queries | Good | Limited | Depends on agent |
| MVP complexity | High | Low | Lowest |

---

## Decision

**Option 3 — Agent-Led Discovery with domain browsing as the non-technical entry point — is adopted for the MVP.**

Vector embeddings are explicitly excluded from the MVP scope. Keyword search is not implemented in this phase.

**Primary reasons:**

1. The agent already performs discovery better than CodeLens can. Claude Code, Cursor, and similar tools have native file search, semantic search over file contents, ripgrep, and AST-awareness. Replicating these capabilities inside CodeLens is duplication of work that is already solved in the client layer.

2. CodeLens's unique value is the graph — structural relationships, multi-hop traversal, domain context. An agent that has found `apply_discount()` via its own grep cannot know from the file alone that it transitively depends on `get_user_tier()` in a different module, that it belongs to the "Checkout" domain cluster, or that three other functions call it. That is what CodeLens provides. The discovery step is not where CodeLens adds value.

3. Embedding infrastructure at the MVP stage is disproportionate to the problem. The synonym matching gap is real but affects a minority of queries. It can be added later as an incremental improvement once the core graph traversal value is proven.

4. For non-technical users (PM, compliance), domain browsing via `get_domains()` and `get_domain_content(domain)` is the natural entry point. They do not issue arbitrary code queries — they browse by business domain.

---

## Consequences

**We accept:**
- Synonym and semantic variation in queries may not be matched — an agent querying "reduction" will not automatically discover "discount" unless it reformulates the query
- Cross-cutting conceptual discovery ("find all external API calls") is not supported in MVP — the agent must know or find the relevant symbols first
- Non-technical users in the demo UI have domain browsing only — they cannot issue arbitrary natural language code queries without first selecting a domain

**We gain:**
- No embedding model dependency at index time
- No vector index infrastructure
- CodeLens MCP tools remain focused and structurally precise
- The indexing pipeline is simpler and faster

**Upgrade path:**
Full-text keyword search (Option 2) is the recommended first upgrade — it requires only enabling Neo4j's built-in Lucene index with no external dependencies. Vector embeddings (Option 1) are the recommended second upgrade if synonym handling proves to be a recurring user complaint once the product is in use.

---

## MCP Tool Design Consequence

This decision shapes the MCP tool surface. Tools are traversal-oriented, not search-oriented:

```python
get_code_context(symbol_name)      # subgraph around a function or class
get_callers(symbol_name)           # what calls this symbol
get_callees(symbol_name)           # what this symbol calls
get_domain(symbol_name)            # which domain cluster this symbol belongs to
get_domains()                      # list all domain clusters
get_domain_content(domain)         # all nodes in a domain cluster
```

The agent supplies the symbol name. CodeLens supplies the structural context. This separation of concerns is intentional and is the core of the CodeLens value proposition.
