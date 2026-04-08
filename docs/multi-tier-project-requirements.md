# Multi-Tier Project Requirements

## Project Overview

A multitier business application must be built from scratch, adhering to at least three core layers:

- **Presentation** — Front-end for user interactions
- **Application** — Back-end for business logic
- **Data** — Persistence layer

Examples of domains include e-commerce, HR management, or inventory tracking. The project should be deployable, demonstrable online, and serve as a portfolio piece.

---

## Guidelines for Execution

Teams must select their technology stack (e.g., React for front-end, Node.js for back-end, PostgreSQL for database) and document contributions via version control.

Start with a **Minimum Viable Product (MVP)** and iterate through milestones:

| Milestone | Deadline |
|---|---|
| Design Document | Week 4 |
| Prototype | Week 8 |
| Beta | Week 12 |
| Final Submission | Chosen deadline |

Documentation must include a `README.md` with setup instructions, architecture diagram, API docs, and user guide. Automated testing (unit, integration, end-to-end) is required.

---

## Core Requirements

All must be implemented.

### Multitier Architecture
- Separate into at least three tiers with API communication (e.g., REST or GraphQL)
- Middleware for handling requests

### User Authentication and Authorization
- Registration, login, logout, password reset
- Role-based access using secure methods like JWT or OAuth

### Business Logic
- Domain-specific features with CRUD operations
- Input validation and error handling

### Data Management
- Persistent database with related entities
- Seeding, migrations, querying, filtering, sorting, and pagination

### User Interface
- Responsive interfaces with intuitive navigation
- Real-time elements (e.g., WebSockets)

### Integration
- At least one third-party API (e.g., Stripe for payments) with error handling

### Security and Performance
- Data encryption, logging, monitoring
- Optimizations like caching

### Testing
- >70% coverage for unit tests
- Integration and end-to-end tests

### Documentation and Presentation
- Architecture diagram and API docs
- Final report (5–10 pages)
- 10–15 minute demo

---

## Advanced Requirements *(Optional — Bonus)*

Implement at least three for extra credit:

- Advanced data handling with ORM or full-text search
- Real-time collaboration (e.g., live chat)
- Analytics with charts and report exports
- Mobile integration or PWA compatibility
- Internationalization for languages and currencies
- Emerging tech like blockchain if relevant

---

## Getting Started

Teams are required to brainstorm ideas and submit a **one-page proposal** (domain, tech stack, high-level features) by **Week 2**. Questions should be posted in the Teams channel.

> It is necessary to adhere to all deadlines and requirements for successful completion. Collaboration and ethical practices are essential throughout the project.
