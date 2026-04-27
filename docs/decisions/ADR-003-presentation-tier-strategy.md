# ADR-003 -- Presentation Tier Strategy: Streamlit vs Separate Frontend

**Status:** Proposed (open question -- decision needed before Epic #11 and #12 implementation)
**Date:** April 2026
**Deciders:** Project team

---

## Context

CodeLens has two user-facing interfaces planned:

1. **Admin Panel** (Epic #11) -- CRUD operations for repos, domains, users. Protected by admin role.
2. **Demo Interface** (Epic #12) -- Chat UI with persona toggle for demonstrating CodeLens to stakeholders.

The multi-tier course requirement expects a clear separation between the presentation tier, the business logic tier, and the data tier. The architectural question is: **does Streamlit satisfy the presentation tier requirement, or do we need a separate browser-side frontend?**

---

## The Problem with Streamlit as a Presentation Tier

In a standard multi-tier architecture, the presentation tier runs in the browser and communicates with the backend over HTTP (REST or similar). The tiers are independent processes separated by a network boundary.

Streamlit blurs this boundary. A Streamlit app defines the UI layout and the business logic in the same Python process. When a user interacts with the UI, Streamlit re-runs the Python script server-side. There is no HTTP API call between the presentation and the business logic -- they are the same process.

If the Streamlit code queries Neo4j directly, the architecture is effectively two-tier: Streamlit + database. A strict interpretation of multi-tier would not count this as a proper presentation tier.

However, if the Streamlit code calls the FastAPI backend over HTTP (`requests.get("http://localhost:8000/api/...")`) instead of querying the database directly, the architecture becomes three-tier from a network boundary perspective. Streamlit acts as a thin client that only makes HTTP calls. The business logic lives in FastAPI. The database is accessed only by FastAPI.

---

## Options

### Option A -- Streamlit as a thin client calling FastAPI

Both the admin panel and the demo UI are built in Streamlit. All data access goes through FastAPI endpoints -- Streamlit never touches Neo4j directly. Architecturally three-tier because there is a clear HTTP boundary between presentation and business logic.

**Advantages:**
- Fast to build -- Streamlit is the simplest Python UI framework
- Single language for the entire stack (Python only)
- Still satisfies multi-tier if Streamlit calls API over HTTP
- Chat interface and persona toggle are straightforward in Streamlit

**Disadvantages:**
- The "frontend" is Python server-rendered, not a browser-side application
- A strict professor may question whether this is a real presentation tier
- Limited UI customisation compared to HTML/JS

### Option B -- HTML/JS frontend for admin, Streamlit for demo

The admin panel is a vanilla HTML/CSS/JS application (or minimal React/Vite) that calls FastAPI endpoints. This clearly demonstrates a traditional multi-tier architecture. The demo UI remains Streamlit because a chat interface with LLM integration is harder to build in plain HTML.

**Advantages:**
- Admin panel is unambiguously a proper frontend tier -- browser-side code calling a REST API
- Demonstrates frontend + backend + database separation clearly for grading
- Demo UI stays Streamlit where it is easiest to build

**Disadvantages:**
- Two frontend technologies (HTML/JS + Streamlit)
- More work to build and maintain

### Option C -- HTML/JS for everything

Both admin and demo are browser-side applications. No Streamlit.

**Advantages:**
- Cleanest multi-tier architecture
- Single frontend technology

**Disadvantages:**
- Building a chat interface with LLM streaming in vanilla JS is significantly more work
- Persona toggle and domain browser require more frontend effort
- Streamlit's built-in features (chat, session state, widgets) would need to be reimplemented

---

## Recommendation (Pending)

Option A is likely sufficient if the Streamlit app is disciplined about calling FastAPI over HTTP rather than accessing Neo4j directly. This should be validated with the course requirements or the professor before implementation begins.

If the professor requires a traditional browser-side frontend, Option B is the pragmatic fallback -- use it only for the admin panel (where CRUD is straightforward in HTML/JS) and keep Streamlit for the demo.

---

## Decision

**Not yet decided.** This ADR should be resolved before starting Epic #11 (Admin Panel) or Epic #12 (Demo Interface). The decision depends on how strictly the course interprets "multi-tier architecture" and whether Streamlit-over-HTTP is accepted as a presentation tier.

---

## Action Required

- Clarify with the professor whether Streamlit calling a FastAPI backend satisfies the multi-tier requirement
- Update this ADR status to "Accepted" once the decision is made
