# Execution Phases

Ez a terv a factory altal futtathato, kontextusmeret-tudatos fazisokra bontja a megvalositast.

## Phase 0 - Contract Baseline

Cel:

- kozos fogalmak es repo-hatarok rogzitese
- session es gateway parhuzamos inditasanak elfogadtatasa
- factory-jobok elso korehez elegendo DoD megfogalmazasa

Output:

- architecture summary
- component boundary table
- first job list
- known risks

Context limit:

- ne olvasd be a teljes thead exportokat
- hasznald a normalized review artifactokat

## Phase 1A - cic-mcp-session Baseline

Cel:

- meglevo `cic-mcp-session` repo allapotanak auditja
- mi letezik, mi scaffold, mi concept
- minimalis uzemszeru celhatar kijelolese

Elso capability-k:

- `session-repo-baseline-audit-001`
- `session-ingress-envelope-contract-001`
- `session-postgres-storage-design-001`

Tiltott rovidites:

- repo letezik != implemented
- fajl letezik != capability
- schema draft != validated contract

## Phase 1B - cic-mcp-gateway Baseline

Cel:

- gateway kulon komponenskent induljon
- ne varjuk meg, amig a session sajat API-vilagot noveszt
- koran legyen GatewayContextEnvelope es source registry contract

Elso capability-k:

- `gateway-repo-baseline-or-bootstrap-001`
- `gateway-context-envelope-contract-001`
- `gateway-source-registry-contract-001`

Tiltott rovidites:

- gateway != proxy
- gateway != vector store
- route_query != search_all

## Phase 2 - Session + Gateway Integration

Cel:

- session context pack gateway-compatible legyen
- gateway tudjon session source-bol contextet forditani
- factory job session_id es session catalog kapcsolodik

Elso capability-k:

- `gateway-session-adapter-contract-001`
- `factory-session-bridge-001`
- `session-context-pack-v1-001`

Kimenet:

```text
factory job
  -> session ingress/catalog
  -> session.context_pack
  -> gateway.compile_context
  -> agent working context
```

## Phase 3 - DB-backed Session Runtime

Cel:

- PostgreSQL schema-k elso mukodo valtozata
- trigger/outbox alapu mechanikus feldolgozas
- FTS/vector/metadata indexek
- session-scope retrieval MCP tools

Elso capability-k:

- `session-raw-event-store-001`
- `session-turn-projector-001`
- `session-chunk-indexer-001`
- `session-search-api-001`

Kimenet:

- SQL migration
- API function contract
- minimal MCP tool contract
- evidence/test report

## Phase 4 - cic-mcp-shared

Cel:

- cross-session aggregation
- sulyozas
- factory job/PR/artifact kapcsolas
- candidate memory

Elso capability-k:

- `shared-session-catalog-consumer-001`
- `shared-cross-session-search-001`
- `shared-weighting-model-001`

Korlatozas:

- shared meg mindig nem canonical
- knowledge promotion kulon review flow

## Phase 5 - Historical Import

Cel:

- ChatGPT export / provider JSONL backfill
- historical source -> SessionIngressEnvelope
- dedupe/idempotency

Elso capability-k:

- `historical-chatgpt-export-importer-001`
- `historical-dedupe-idempotency-001`

Feltetel:

- SessionIngressEnvelope stabil
- session raw/core store stabil
- source_ref es content_hash strategia kesz
