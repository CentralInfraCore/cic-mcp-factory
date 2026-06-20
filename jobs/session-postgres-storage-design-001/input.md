# Job: session-postgres-storage-design-001

## Kontextus

A `session-ingress-envelope-contract-001` job lezárta a `SessionIngressEnvelope` schemát
(`cic-mcp-session/output/session-ingress-envelope.schema.yaml`) — ez a formátum, amibe minden
jövőbeli hook/importer/manual payload csomagolva lesz. Eddig viszont nincs semmilyen tárolási
réteg, ami ezt tényleg fogadná: a `cic-mcp-session` repo jelenleg PKL-alapú, egyetlen
`kb_data/pkl/` snapshot-tal dolgozik, ami a `thead-review` szerint NEM skálázódik 100-1000 MB
session-adatra (`dec-thead-0003`: "the live store should not be PKL snapshots; use a
DB-backed retrieval store").

Ez a job a `job-slices.yaml` Phase 3 szelete — a PostgreSQL schema-réteg ELSŐ tervezete:
`session_raw`, `session_core`, `session_idx`, `session_jobs`, `session_api`. **Ez egy
DESIGN job, NEM működő migráció** — a kimenet egy SQL DRAFT + egy report, nincs futtatott
adatbázis, nincs valódi migrációs teszt.

## Target

- target repo: `cic-mcp-session`
- target path: `output/` (a kötelező output fájlnevek szerint, lásd lent — ugyanaz a döntés,
  mint az előző jobnál: az explicit "Required Output Files" lista erősebb kötés mint bármilyen
  `docs/` javaslat)
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: ez egy SQL DRAFT, nincs futtatott Postgres instance, nincs migrációs teszt
  — `candidate`-hez kellene legalább egy job, ami ezt a DDL-t tényleg lefuttatja egy valódi
  Postgres instance-on és bizonyítja hogy a táblák/indexek/trigger-ek hibátlanul létrejönnek.

## Sources

- `${WORKDIR}/.cic-context/factory-docs/job-slices.yaml` — `session-postgres-storage-design-001`
  bejegyzés (phase 3, acceptance_gates, required_evidence, forbidden_shortcuts) — NORMATÍV,
  a lenti gate-ek pontosan ebből vannak átemelve
- `${WORKDIR}/.cic-context/factory-docs/architecture.md` — "## Schema szeparacio" (a
  `session_raw.*`/`session_core.*`/`session_idx.*`/`session_jobs.*`/`session_api.*` javasolt
  felosztás) és "## Inheritance / partitioning allaspont" szekciók
- `${WORKDIR}/.cic-context/factory-docs/execution-phases.md` — "## Phase 3 — DB-backed Session
  Runtime" szekció
- `${WORKDIR}/.cic-context/corpus/normalized/thead-review-2026-06-20.yaml` — `dec-thead-0003`
  (PKL nem skálázódik), `dec-thead-0004` (Postgres mint első backend), `sup-0002`
  (PKL csak export/snapshot lehet, nem élő store)
- **KÖTELEZŐ elsődleges forrás:** a `cic-mcp-session` repo `output/session-ingress-envelope.schema.yaml`
  fájlja (a `session-ingress-envelope-contract-001` job eredménye, már a `main`-en) — a
  `session_raw` táblának EZT a schemát kell tudnia tárolni, mezőről mezőre. NE találj ki új
  mezőneveket, ha az envelope schema már definiált egyet.

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el a `cic-mcp-session/output/session-ingress-envelope.schema.yaml`-t TELJESEN,
   MIELŐTT bármilyen DDL-t írnál — a `session_raw` táblának ezt a schemát kell leképeznie

## Feladat

### 1. Schema-szeparáció

Vázold fel mind az 5 Postgres schema-t (`session_raw`, `session_core`, `session_idx`,
`session_jobs`, `session_api`) legalább egy konkrét táblával/funkcióval mindegyikhez:

- `session_raw.*`: a `SessionIngressEnvelope` mezőinek 1:1 leképezése (lásd a kötelező
  forrást) — minden envelope-mező legyen egy oszlop vagy JSONB mező, `idempotency_key`-re
  UNIQUE constraint (ez a dedup mechanizmus)
- `session_core.*`: sessions/turns/chunks/source_refs/manifests — a projektált,
  feldolgozott állapot (NEM raw)
- `session_idx.*`: FTS, vector refs (pgvector/HNSW), ranking features
- `session_jobs.*`: outbox/projection jobs, retry/dead-letter állapot — ez a mechanizmus,
  ami a `session_raw`-ból `session_core`/`session_idx`-be projektál
- `session_api.*`: stabil SQL függvények, amiket az MCP szerver hív (`search_context`,
  `get_timeline`, `get_context_pack`, `session_status` — lásd `architecture.md`)

### 2. Trigger/outbox határok

Definiáld PONTOSAN mi fut trigger-ben (DB-n belül, szinkron) és mi fut worker-ben (DB-n
kívül, async). A `forbidden_shortcuts` szerint a trigger NEM hívhat külső LLM/HTTP-t — ha
embedding-generálás vagy bármilyen AI-feldolgozás kell, az outbox-ba kerül, és egy KÜLSŐ
worker veszi fel, NEM egy DB trigger.

### 3. Index-stratégia

Listázd a `session_id`, metadata, FTS és vector lookup indexeket — konkrét `CREATE INDEX`
parancsokkal, ne csak névvel.

### 4. Particionálás/inheritance döntés v1-re

A `architecture.md` "Inheritance / partitioning allaspont" elve szerint ("ne használj
inheritance-t csak azért mert lehet") — döntsd el ÉS indokold, hogy v1-ben kell-e
particionálás (pl. dátum/provider szerint), vagy ez egy későbbi iteráció. Ha "nem kell még",
ezt explicit indokold (pl. "v1-ben a várt adatmennyiség nem indokolja").

### 5. Worker-felelősség

Listázd mi marad KÍVÜL a Postgres-en, worker-oldali feldolgozásként (pl. embedding-generálás,
LLM/AI-feldolgozás, import parser, batch rebuild, provider adapter — lásd `architecture.md`
"Postgres-first elv" Worker szekció).

## Nem cél

- valódi Postgres instance felállítása vagy a DDL tényleges lefuttatása
- migrációs framework (Alembic/Flyway stb.) bekötése
- a `mcp-server/server.py` átírása, hogy az `session_api.*` függvényeket hívja (külön job:
  `session-search-api-001`, lásd `execution-phases.md` Phase 3)
- a hook/importer tényleges írása a `session_raw`-ba (külön job: `session-hook-collector-001`
  / `session-raw-event-store-001`)

## Required Output Files

- `output/session-postgres-storage-design.md`
- `output/session-postgres-schema.sql`

## Required Report Sections

A report MUST kövesse az `.cic-context/factory-docs/acceptance-contract.md`
"Universal Output Contract" szakaszát:

```markdown
# session-postgres-storage-design-001 Output

## Scope
## Inputs Read
## Findings
## Claim-Evidence Matrix

| Claim | Status | Evidence | Verification Method | Risk |
|---|---|---|---|---|

## Decisions Proposed
## Rejected / Out Of Scope
## Risks
## Definition Of Done Check
## Next Jobs
```

Elfogadott `Status` értékek (DDL-tervezési állítás, nem futtatott-migráció-bizonyíték):
`proven`, `partial`, `missing`, `rejected`, `unknown`. Itt `proven` azt jelenti: "a DDL fájlban
tényleg jelen van a leírt tábla/index/constraint", NEM azt, hogy "egy valódi Postgres-en
lefuttatva validálva van" (az még nem cél, lásd "Nem cél").

## Definition Of Done

- [ ] `output/session-postgres-schema.sql` tartalmazza mind az 5 schema-t legalább egy
      konkrét táblával/funkcióval, idézve a reportban
- [ ] `session_raw` táblája 1:1 leképezi a `SessionIngressEnvelope` minden mezőjét — idézve
      melyik envelope-mező melyik DDL-oszlopnak/JSONB-kulcsnak felel meg
- [ ] `idempotency_key` UNIQUE constraint a `session_raw`-on, idézve a DDL releváns sorát
- [ ] trigger/outbox határ explicit definiálva, idézve melyik konkrét lépés megy trigger-be
      és melyik worker-be
- [ ] index-stratégia konkrét `CREATE INDEX` parancsokkal (session_id, metadata, FTS, vector)
- [ ] particionálás/inheritance döntés v1-re explicit kimondva és indokolva
- [ ] worker-felelősségi lista (mi marad kívül a Postgres-en)
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a DDL fájl létezése nem bizonyítja, hogy a benne leírt constraint/index tényleg helyes
  SQL szintaxis — idézd a konkrét sort, és ha bizonytalan vagy a szintaxisban, jelöld
  `partial`-ként, ne `proven`-ként
- trigger külső LLM/HTTP-t hív — ez TILOS, minden AI/embedding-feldolgozás outbox-on
  keresztül worker-be megy, nem DB trigger-be
- egy globális `chunks.pkl` mint élő store — ez TILOS, a Postgres-nek kell az élő store
  lennie, a PKL legfeljebb export/snapshot lehet (lásd `sup-0002`)
- "a tábla neve `session_raw`, tehát biztos jó" ≠ bizonyíték — minden `proven` állításhoz a
  DDL konkrét, idézett részlete kell

## Git instrukciók

Push a `feature/session-postgres-storage-design-001` branch-re, a `cic-mcp-session`
célrepóban. Main-re az agent NEM pushol.

## Nyelvi szabály

A report magyarul készüljön, az SQL DDL és a mezőnevek angolul.
