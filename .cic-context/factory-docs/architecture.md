# CIC MCP Capability Architecture

## Cel

Ez a dokumentum a `cic-mcp-*` trust-domain alapu MCP komponenscsalad uzemszeru felepiteset rogziti.

A megvalositas nem monolitikus. A session es gateway komponensek elejetol kulon repoban, kulon felelossegi hatarral indulnak, de kozos envelope-, trust- es factory-lifecycle szerzodessel.

## Komponens terkep

```text
cic-mcp-knowledge
  reviewed/canonical tudas, verziozott base knowledge

cic-mcp-workdir
  aktualis repo/worktree/branch/diff/allapot

cic-mcp-session
  session-scope event, timeline, chunk, retrieval, provenance

cic-mcp-shared
  cross-session memoria, klaszterezes, sulyozas, konfliktus, factory/PR/artifact kapcsolas

cic-mcp-gateway
  trust-domain aware context compiler, agent-facing frontend

cic-mcp-factory
  MCP capability-k gyarto es karbantarto factory-ja
```

## Fo hatarok

### cic-mcp-session

Igen:

- `SessionIngressEnvelope` ingest
- raw event store
- turn/timeline projection
- chunk store
- source/provenance refs
- metadata index
- full-text search
- vector search
- session-scope context pack
- stable SQL/API/MCP read tools

Nem:

- canonical tudas
- shared memory
- cross-session graph
- vegleges dontesbanyaszat
- human review nelkuli promotion

### cic-mcp-gateway

Igen:

- query intent felismeres
- trust-domain source routing
- source registry hasznalat
- conflict/proof felszinre hozasa
- `GatewayContextEnvelope` osszeallitasa
- agent-facing context API

Nem:

- raw event store
- embedding store
- factory runner
- canonical promotion

### cic-mcp-shared

Igen:

- tobb session osszefuzese
- factory job/PR/artifact kapcsolas
- visszatero fogalmak
- sulyozas
- konfliktus/superseded jeloltek
- promotion candidates

Nem:

- raw hook ingestion elso igazsagforrasa
- canonical layer

## Postgres-first elv

A session es shared retegek tarolasi es mechanikus feldolgozasi alapja PostgreSQL legyen.

```text
PostgreSQL
  event store
  projection engine
  outbox/job queue
  FTS index
  metadata index
  pgvector/HNSW index
  ranking features
  stable SQL API

Worker
  embedding generalas
  LLM/AI feldolgozas
  import parser
  batch rebuild
  provider adapter

MCP server
  stable read/context API
```

## Schema szeparacio

Javasolt schema-k:

```text
session_raw.*
  SessionIngressEnvelope, raw provider payload, source/import trace

session_core.*
  sessions, turns, chunks, source_refs, manifests

session_idx.*
  FTS, vector refs, ranking features, materialized/cached search views

session_jobs.*
  outbox, projection jobs, retry/dead-letter allapot

session_api.*
  MCP altal hivott stabil SQL fuggvenyek

gateway_core.*
  source registry, source capabilities, route rules

gateway_api.*
  compile_context, route_query, explain_sources stable SQL/API boundary

shared_core.*
  cross-session clusters, summaries, candidate memories, conflicts

knowledge_core.*
  reviewed/promoted/canonical facts, rules, decisions
```

Az MCP szerver ne tablakat turkaljon. Stabil API fuggvenyeket hivjon:

```sql
select * from session_api.search_context(...);
select * from session_api.get_timeline(...);
select * from session_api.get_context_pack(...);
select * from session_api.session_status(...);
```

## Inheritance / partitioning allaspont

A rendszer DB-heavy, de a klasszikus PostgreSQL `INHERITS` nem dogma.

Elfogadott eszkozok:

- declarative partitioning
- table inheritance, ha konkretan indokolt
- common base tables
- generated columns
- views/materialized views
- schema-level API functions
- trigger/outbox

Elv:

```text
Use inheritance/partitioning only where it improves operational clarity.
Do not introduce inheritance just because it is possible.
```

Tipikus particionalasi tengelyek:

- date/month
- provider
- source_kind
- session_kind
- tenant/project, ha kesobb kell

## Trust modell

```text
session
  trust: session_local / session_derived
  canonical: false
  default scope: one session

shared
  trust: mixed / candidate / reviewed_shared
  canonical: false by default

knowledge
  trust: reviewed/canonical
  canonical: true only after review/promotion

gateway
  does not create truth
  compiles context from trust-domain sources
```

## Factory legitimacio

Az AI/factory:

- capability requestet olvas
- tervet keszit
- contractot javasol
- kodot/schema-t ir
- tesztet futtat
- review summaryt ad

Az ember/orchestrator:

- review-zik
- merge/reject/revise allapotot ad
- legitimacios hatart kepvisel

Rogzitett szabaly:

```text
AI gyart es validal, de nem legitimál.
Human merge = state transition authorization.
```
