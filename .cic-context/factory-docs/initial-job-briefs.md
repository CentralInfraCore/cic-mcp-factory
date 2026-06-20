# Initial Job Briefs

Ezek nem vegleges `input.md` fajlok, hanem factory-job alapanyagok. Az orchestrator ezekbol keszitse el a konkret `jobs/<job-id>/input.md` fajlt.

Minden itt szereplo jobra kotelezo az acceptance contract:

```text
.cic-context/factory-docs/acceptance-contract.md
```

## 1. session-repo-baseline-audit-001

Cel:

Megallapitani, hogy a letezo `cic-mcp-session` repo mit tartalmaz valojaban, es az elemek milyen statuszban vannak: implemented, scaffold, concept vagy missing.

Nem cel:

- uj architektura teljes megvalositasa
- Postgres schema implementalasa
- gateway integracio

Kotelezo output:

- `output/session-baseline-audit.md`

Definition of Done:

- minden nagyobb repo elem statusza: implemented/scaffold/concept/missing
- minden implemented allitas mellett reachability vagy runtime evidence
- legalabb 3 kovetkezo factory-job javaslat
- NO-GO lista azokrol, amikre meg nem szabad epitkezni

Kotelezo bizonyitek:

- file/path bizonyitek minden repo allitasra
- runtime/reachability bizonyitek minden implemented allitasra
- "repo exists != implemented" explicit alkalmazasa

## 2. gateway-repo-baseline-or-bootstrap-001

Cel:

A `cic-mcp-gateway` elejetol kulon komponenskent induljon. Audit vagy bootstrap dontes kell: letezik-e repo, ha igen milyen allapotban; ha nem, milyen minimal scaffold kell.

Nem cel:

- session storage
- vector store
- shared memory

Kotelezo output:

- `output/gateway-baseline.md`

Definition of Done:

- repo allapot tisztazva: exists/scaffold/bootstrap-required
- gateway felelosseg elvalasztva session/shared/knowledge retegektol
- GatewayContextEnvelope minimalis mezolistaja megadva
- source registry minimalis felelossege megadva

Kotelezo bizonyitek:

- gateway != proxy
- gateway = trust-domain aware context compiler
- source registry es GatewayContextEnvelope minimalis felelosseg

## 3. session-ingress-envelope-contract-001

Cel:

SessionIngressEnvelope contract elso valtozata.

Kotelezo mezok:

- apiVersion
- kind
- event.id
- provider
- provider_session_id
- provider_event_name
- created_at / received_at
- source_kind
- cwd/repo/job metadata, ha van
- payload raw preservation
- trust.canonical=false
- trust.interpreted=false
- content_hash / idempotency key

Nem cel:

- semantic extraction
- decision/claim felismeres
- canonical promotion

Kotelezo output:

- `output/session-ingress-envelope-contract.md`
- `output/session-ingress-envelope.schema.yaml`

Definition of Done:

- schema tartalmazza az identity/source/payload/trust/raw preservation mezoket
- ingress szinten `canonical=true` es `interpreted=true` tilos
- idempotency key strategia megadva
- 2 valid es 2 invalid pelda szerepel

## 4. session-postgres-storage-design-001

Cel:

PostgreSQL-first session store terv, schema szeparacioval.

Kotelezo schema-k:

- session_raw
- session_core
- session_idx
- session_jobs
- session_api

Kotelezo dontesek:

- trigger mit csinalhat
- trigger mit nem csinalhat
- worker felelossege
- FTS/vector/metadata index strategia
- partitioning/inheritance allaspont

Kotelezo output:

- `output/session-postgres-storage-design.md`
- `output/session-postgres-schema.sql`

Definition of Done:

- SQL draft tartalmazza: session_raw, session_core, session_idx, session_jobs, session_api
- trigger/outbox hatar leirva
- worker felelossegek leirva
- FTS/vector/metadata indexek leirva
- partitioning/inheritance v1 dontes indokolva

## 5. gateway-context-envelope-contract-001

Cel:

GatewayContextEnvelope elso verzioja, amelybe kesobb session/workdir/knowledge/shared forrasokbol forditott kontextus kerul.

Kotelezo mezok:

- answer_type
- query_intent
- scope
- sources_used
- trust_summary
- canonical_facts
- workdir_facts
- session_derived_notes
- shared_memory_notes
- conflicts
- proof_requirements
- refs

Nem cel:

- session storage
- direct DB access to session tables

Kotelezo output:

- `output/gateway-context-envelope-contract.md`
- `output/gateway-context-envelope.schema.yaml`

Definition of Done:

- schema tartalmazza: sources_used, trust_summary, conflicts, proof_requirements, refs
- kulon mezok vannak canonical/workdir/session/shared tartalomra
- gateway nem tarol raw sessiont es nem embedding store
- 2 valid es 2 invalid pelda szerepel

## 6. factory-session-bridge-001

Cel:

A `cic-mcp-factory` job lifecycle es a kesobbi `cic-mcp-session` catalog kozotti hid megtervezese.

Kotelezo vizsgalat:

- `meta.yaml agent.session_id`
- `jobs/<job-id>/output/events.jsonl`
- current hook limitations
- feature branch/job_id/repo metadata

Kotelezo output:

- `output/factory-session-bridge.md`

Definition of Done:

- meta.yaml es job lifecycle session mezoi tisztazva
- current events.jsonl limitation dokumentalva
- SessionIngressEnvelope bridge proposal megadva
- existing jobs kompatibilitasi terv megadva

Nem cel:

- jelenlegi `events.jsonl` vegleges source-of-truthnak nyilvanitasa

## Javasolt sorrend

```text
1. session-repo-baseline-audit-001
2. gateway-repo-baseline-or-bootstrap-001
3. session-ingress-envelope-contract-001
4. gateway-context-envelope-contract-001
5. session-postgres-storage-design-001
6. factory-session-bridge-001
7. gateway-session-adapter-contract-001
```
