# ERP Light — Complete Project Document

This document is aligned with the **professional SDLC orchestrator** in this repository: **ten sequential stages** with handoffs (gathering → analysis → architecture → database → **web → Android → iOS → desktop** → QA → DevOps). Each stage corresponds to an agent task; **module** and **sprint** scope can be set per run.

### How to regenerate with the crew

Set `OPENAI_API_KEY` (see `.env.example`), use **Python 3.10–3.13**, then from the repo root:

```text
.\.venv\Scripts\python.exe main.py "ERP Light: SMB inventory, sales, purchasing, light AR/AP..." ^
  --constraints "PostgreSQL; modular monolith; single company v1" ^
  --module-scope "Full product" ^
  --sprint "Full pipeline" ^
  --out docs\ERP_Light_from_crew.md
```

**Parallel pipelines** (e.g. one run per bounded context / module), **output order matches the JSON file**:

```text
.\.venv\Scripts\python.exe main.py "Overall ERP Light vision..." --constraints "Shared stack" ^
  --parallel examples\parallel_modules.example.json --max-workers 2 --out docs\ERP_parallel.md
```

The sections below are a **manual baseline** you can compare to crew output; numbering matches the orchestrator’s expected deliverable titles.

---

## 1. Requirements Gathering

*Orchestrator task: discovery and intent — no solution design yet.*

### 1.1 Problem statement and goals

**Problem:** Small and mid-sized businesses need integrated visibility across inventory, sales, purchasing, and basic money flows without the cost and complexity of full enterprise ERP suites.

**Goals:**

- Provide **operational truth** for items, stock, orders, suppliers, and customers through a coherent product (not a pile of spreadsheets).
- Support **role-based access** so finance, warehouse, and sales teams see appropriate data.
- Deliver **actionable reporting** (stock levels, order backlog, light AR/AP aging).
- Keep **implementation and hosting** realistic for teams without a dedicated ERP administrator.

**Non-goals (v1 product boundary):**

- Full manufacturing (MRP, shop floor, BOM explosion), advanced HR/payroll, full statutory GL consolidation, or jurisdiction-specific tax engines.
- Heavy customization / proprietary scripting language.

### 1.2 Stakeholders and scope snapshot

**Primary stakeholders:** company admin, warehouse, sales, purchasing, finance (light), leadership reporting.

**In scope (summary):** master data; inventory movements and reservations; sales and purchasing documents; light AR/AP; audit trail; CSV import/export.

**Out of scope (v1):** payroll, fixed assets, multi-currency hedging, intercompany eliminations, advanced budgeting.

### 1.3 Discovery themes and traceability hooks

| Theme ID | Theme | Notes |
|----------|--------|--------|
| RG-01 | Single company, future multi-company-ready | Data model must not block later expansion |
| RG-02 | Stock correctness under concurrency | Reservations and movements are audit-critical |
| RG-03 | Light finance vs external GL | Export and mapping, not full accounting engine |
| RG-04 | Channels: web first; native clients phased | See platform sections |

### 1.4 Assumptions and open questions

**Assumptions:**

- Single currency per company in v1.
- English-first UI; i18n considered in architecture.
- Managed PostgreSQL is acceptable for SaaS or single-tenant hosting.

**Open questions:**

- Tax: line-level vs header-level; which jurisdictions in v1?
- Approval rules: PO thresholds, SO credit holds?
- Accounting: QuickBooks/Xero connector in v1 or phase 2?
- **Client surfaces:** confirm whether v1 is **web-only** with mobile/desktop in later phases, or parallel releases (impacts sprint planning and the four application plans).

---

## 2. Analysis & Backlog

*Orchestrator task: structured backlog — stories, NFRs, MoSCoW, dependencies.*

### 2.1 Personas / actors

| Actor | Needs |
|--------|--------|
| **Company admin** | Configure org, users, roles, fiscal settings, integrations. |
| **Warehouse / inventory** | Receive goods, adjust stock, transfers, stock counts. |
| **Sales** | Quotes/orders, customers, pricing lists, order status. |
| **Purchasing** | POs, vendors, receipts, light three-way match. |
| **Finance (light)** | Invoices, payments, expense categories, simple AR/AP lists. |
| **Auditor / compliance** | Read-only access to audit trail exports. |

### 2.2 Functional requirements (numbered)

1. **FR-1 Authentication & authorization:** Secure authentication; permissions per module and action (read/write/approve).
2. **FR-2 Organization model:** Single company in v1; schema allows future multi-company without rewrite.
3. **FR-3 Master data:** CRUD for products, customers, vendors; validation; duplicate hints; soft delete.
4. **FR-4 Inventory:** Stock movements; adjustments with reason codes; negative stock only if configured (default off).
5. **FR-5 Sales:** Sales order → reserve/allocate → pick → ship → invoice (invoice may be manual in v1).
6. **FR-6 Purchasing:** PO → receive → match to bill → mark paid.
7. **FR-7 Light finance:** AR/AP subledgers; payment allocation; CSV export for external GL.
8. **FR-8 Search & list:** Pagination and filters; search on names/SKUs (indexes + contains minimum).
9. **FR-9 Notifications:** In-app notifications for low stock, approvals, failed imports.
10. **FR-10 Import/export:** CSV templates (admin); export on major lists.

### 2.3 Non-functional requirements

| Area | Requirement |
|------|-------------|
| **Performance** | Typical list screens &lt; 2s p95 under ~50 concurrent users; monthly reports &lt; 10s for standard aggregates. |
| **Security** | OWASP ASVS-aligned practices; secrets in vault; TLS; encryption at rest per host capability. |
| **Availability** | Target 99.5% monthly for SaaS; documented backup/restore RPO/RTO. |
| **Privacy** | GDPR-oriented: DPA, export/delete process, retention. |
| **Accessibility** | WCAG 2.1 AA on primary flows (full coverage may be phased). |
| **Observability** | Structured logs, correlation IDs, metrics; audit trail for financial posts. |

### 2.4 User stories (Given / When / Then)

1. **Stock visibility** — **Given** a warehouse user, **when** they open the inventory dashboard, **then** they see on-hand by warehouse and SKU with last movement date.
2. **Sales order to shipment** — **Given** a confirmed order with reservation, **when** shipment is posted, **then** inventory decreases and order status and audit reflect it.
3. **Purchase receipt** — **Given** an open PO, **when** a partial receipt is posted, **then** inventory increases and PO shows remaining quantity.
4. **Invoice customer** — **Given** a shipped order, **when** finance creates an invoice, **then** AR shows an open balance until payment.
5. **Admin audit** — **Given** an admin, **when** they export the audit log for a range, **then** they receive CSV with user, timestamp, and entity changes.

### 2.5 MoSCoW (illustrative)

| Priority | Examples |
|----------|-----------|
| **Must** | Auth/RBAC, master data, inventory, sales & purchase documents, light AR/AP, audit |
| **Should** | CSV import, notifications, basic reporting |
| **Could** | Native mobile apps for warehouse; desktop installer for finance |
| **Won’t (v1)** | Full manufacturing, payroll, full tax engine |

---

## 3. Technical Architecture

*Orchestrator task: solution architecture, ADRs, platform coverage (web / Android / iOS / desktop).*

### 3.1 High-level architecture

**Pattern:** Modular monolith (single deployable) with bounded contexts; services extractable later if needed.

**Components:**

- **API:** REST + OpenAPI; server-side validation.
- **Worker:** Queue-backed jobs (email, CSV import, heavy reports).
- **Web:** Primary admin and operations UI (SPA or SSR).
- **Optional clients:** Android/iOS/desktop consuming the **same API contracts** (see Sections 6–8).
- **Database:** PostgreSQL.
- **Files:** Object storage for PDFs and import files.

```text
[Clients: Web | Mobile | Desktop] --> [API] --> [PostgreSQL]
                      |--> [Queue] --> [Worker] --> [Object storage]
```

### 3.2 Main data flows

1. **Order fulfillment:** Order → reservation (transaction) → shipment → inventory movements + status.
2. **Receiving:** PO receipt → inventory in → optional bill match.
3. **Financial:** Invoice/bill lines in subledgers; payments allocate; period close later phase.

### 3.3 Proposed stack (illustrative)

| Layer | Options | Rationale |
|--------|---------|-----------|
| Backend | Node (TS), Python (FastAPI), .NET 8 | Team fit; typing; mature ORMs |
| ORM / migrations | Prisma, SQLAlchemy + Alembic, EF Core | Controlled schema evolution |
| API | OpenAPI-first | Contract tests and client codegen for **all** clients |
| Web | React / Vue + design system | Fast ERP-style grids and forms |
| Mobile (if phased) | Kotlin/Compose; Swift/SwiftUI; or Flutter | Parity with shared API |
| Desktop (if phased) | Tauri / Electron / .NET MAUI | Offline or docked-warehouse scenarios |
| Auth | OIDC-ready (Entra, Auth0, Keycloak) | SSO path |
| Jobs | Redis + worker library | Retries and backpressure |
| Infra | Containers + PaaS or K8s | Match ops maturity |

### 3.4 Platform coverage (ERP Light)

| Surface | v1 recommendation | Notes |
|---------|-------------------|--------|
| **Web** | **Primary** | Full module coverage for admin and daily ops |
| **Android** | Phase 2+ optional | Scanning, receiving, stock lookup “on the floor” |
| **iOS** | Phase 2+ optional | Executive approvals, field sales light |
| **Desktop** | Phase 2+ optional | Finance power users, bulk export, optional offline |

*The orchestrator emits **separate application plans per platform** (Sections 5–8); treat out-of-scope platforms as **N/A with rationale** in those sections until product commits to them.*

### 3.5 Core domain model (conceptual)

**Aggregates (simplified):** `Company`, `User`, `Role`, `Permission`; `Product`, `Warehouse`, `StockLocation`; `InventoryBalance`, `InventoryMovement`; `Customer`, `Vendor`; `SalesOrder`, `Shipment`; `PurchaseOrder`, `GoodsReceipt`; `Invoice`, `Bill`, `Payment`, `Allocation`; `AuditEvent`.

**Rule:** Inventory movements are **append-oriented** with document references; corrections via reversing movements with reason.

### 3.6 External integrations

Email (SMTP/SendGrid); accounting export via CSV/Excel mapping; future OAuth to Xero/QuickBooks.

### 3.7 API surface (representative)

- `POST /api/v1/sales-orders`, state transitions, `POST /api/v1/shipments`, `GET /api/v1/inventory/on-hand`, `POST /api/v1/import/products` (async).

Support **idempotency** on critical mutating operations.

### 3.8 Security, scalability, risks

- RBAC (`inventory:read`, `sales:write`, `finance:approve`, …); rate limits; CORS/CSRF as appropriate.
- Read replicas or reporting snapshots for heavy lists; idempotent workers.
- **Risks:** inventory races (use transactions/locking), scope creep (module flags), list performance (pagination, indexes).

### 3.9 Architecture Decision Records (summary)

1. **ADR-1:** PostgreSQL as system of record — ACID for stock and money.  
2. **ADR-2:** Append-style inventory movements — auditability.  
3. **ADR-3:** Modular monolith for v1 — operations simplicity.  
4. **ADR-4:** API-first for **web + optional native clients** — one contract, many surfaces.

---

## 4. Database Design

*Orchestrator task: ER, logical/physical outline, migrations, concurrency, audit.*

### 4.1 Conceptual and logical highlights

- **Transactional core:** orders, lines, movements, financial documents — normalized; **no** negative stock persisted without movement rows.
- **Identifiers:** UUIDs or snowflake IDs for public references; internal surrogate keys as needed.
- **Audit:** append-only `audit_event` or row-level history for sensitive entities.

### 4.2 Physical outline

- Indexes on foreign keys, `(warehouse_id, sku_id)` for inventory queries, and search columns as needed.
- Consider partial indexes for active-only rows if soft-delete is heavy.

### 4.3 Migrations and change safety

- Forward-only migrations in CI; expand/contract for breaking API/DB changes.
- Backup before production migration; restore tested on a schedule.

### 4.4 Concurrency

- Serializable or `SELECT … FOR UPDATE` on reservation paths; deadlock tests in integration suite.

---

## 5. Web Application Plan

*Orchestrator task: browser client only — stack, routing, auth, API client, a11y.*

**ERP Light web (v1 focus):**

- **Framework:** e.g. React + router; or Next.js if SSR/SEO matters for login/marketing split.
- **UI:** Data grids (virtualization), filters, saved views, keyboard shortcuts for power users.
- **Auth:** OIDC or session + refresh; route guards by permission.
- **API client:** Generated from OpenAPI; centralized error and retry handling.
- **Observability:** Frontend error boundary; RUM optional.

**Key screens (illustrative):** dashboard, product list/detail, inventory by warehouse, sales order lifecycle, PO lifecycle, AR/AP lists, admin users/roles, import status.

---

## 6. Android Application Plan

*Orchestrator task: Kotlin/Jetpack — **align with web via shared API**.*

**Suggested use cases if/when in scope:** receiving, stock lookup, barcode scanning, shipment confirm.

- **Stack:** Kotlin, Jetpack Compose (or XML), Navigation, Hilt/Koin, Coroutines.
- **Compliance:** Play policies; target/min SDK matrix documented.
- **Parity:** Feature flags for modules not yet on mobile; offline read-only cache optional later.

If **not in scope for v1**, state **N/A** and point to web responsive UI.

---

## 7. iOS Application Plan

*Orchestrator task: Swift/SwiftUI — **parity notes with Android and web**.*

**Suggested use cases if/when in scope:** approvals, executive dashboards, light sales lookup.

- **Stack:** SwiftUI; async/await; Keychain for tokens; push if approvals are real-time.
- **Compliance:** App Store review (account deletion, privacy labels).

If **not in scope for v1**, state **N/A** explicitly.

---

## 8. Desktop Application Plan

*Orchestrator task: Electron / Tauri / .NET MAUI / Flutter desktop — **justified for ERP only if needed**.*

**Possible drivers:** dedicated finance workstation, scanner drivers, offline batch export.

- **Packaging:** signed installers, auto-update policy, enterprise deployment (MSI/pkg).
- **Security:** local file access minimized; IPC hardened.

If **not in scope**, prefer **web + PWA** or mark **N/A** until a validated offline requirement exists.

---

## 9. Quality Assurance Plan

*Orchestrator task: pyramid per platform, traceability, automation tooling.*

### 9.1 Strategy

- **Unit:** Domain rules (reservation, payment allocation, state transitions).
- **Integration:** API + DB; concurrency on last-unit stock.
- **E2E:** Web critical paths first; mobile/desktop when those clients exist.
- **Non-functional:** Load on order creation; backup/restore drill.

### 9.2 Environments

Dev (local), Staging (prod-like), Production.

### 9.3 Sample test cases (traceability)

| ID | Objective | Ref |
|----|-----------|-----|
| TC-01 | Reserve within available qty | FR-5, FR-4 |
| TC-02 | Concurrent last-unit conflict | FR-4 |
| TC-03 | Shipment posts inventory | FR-5 |
| TC-04 | Partial PO receipt | FR-6 |
| TC-05 | Partial payment | FR-7 |
| TC-06 | RBAC denial on finance API | FR-1 |
| TC-07 | Audit on price change | FR-10 |

### 9.4 Automation hints

- Web: Playwright/Cypress; API: contract tests from OpenAPI.
- Android: Espresso/UI; iOS: XCTest; Desktop: driver TBD by stack.

---

## 10. DevOps & Release

*Orchestrator task: CI/CD per artifact type, signing, stores, desktop packaging, runbooks.*

### 10.1 Build pipeline

Lint → unit → integration → container build → security scan → deploy staging → smoke → approval → production.

### 10.2 Multi-surface delivery

- **API + web:** container or PaaS; DB migrations gated.
- **Android/iOS:** signing, internal/closed tracks, store listings.
- **Desktop:** signed artifacts, update channel, IT deployment notes.

### 10.3 Secrets and operations

Secrets in vault; separate OAuth clients per env; monitoring (availability, latency, errors, queue depth); incident checklist (acknowledge, triage, mitigate, communicate, postmortem).

---

## Document control

| Version | Date | Notes |
|---------|------|--------|
| 1.0 | 2026-04-21 | Initial ERP Light SDLC package (manual). |
| 2.0 | 2026-04-21 | Aligned with **10-stage orchestrator** (gathering → analysis → architecture → database → web/Android/iOS/desktop → QA → DevOps); parallel run and CLI examples; platform phasing clarified. |
