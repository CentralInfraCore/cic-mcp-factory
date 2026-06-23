# Job: shared-core-storage-implementation-001

## Kontextus

Phase 6 ("Wiring") első kódjobja a `cic-mcp-shared` repóban. A repóban JELENLEG
**nulla Python/SQL implementáció van** — kizárólag `output/*.md` kontraktus-riport,
három korábbi jobból: `shared-session-catalog-consumer-001`,
`shared-cross-session-search-001`, `shared-weighting-model-001`. Ez a job írja meg az
ELSŐ tényleges kódot: a `shared_core.*` jelölt-rekord Postgres-schemáját, a három
riport mező-tábláiból, MINDEN mezővel, módosítás/újradefiniálás nélkül.

**Kritikus határ** (job-slices.yaml `forbidden_shortcuts`): a `canonical` mezőnek
VALÓDI constraint/default kell mögé, ami kikényszeríti a `cic-mcp-shared` trust
modelljét (`canonical: false by default`, sosem automatikus `true`) — ez NEM csak
dokumentációs állítás lehet, hanem a schema-nak magának kell ezt garantálnia.

## Target

- target repo: `cic-mcp-shared`
- target path: `output/shared-core-storage-implementation.md` + SQL schema-fájl
  (pl. `schema/shared_core_schema.sql` vagy a repo konvenciójának megfelelő hely —
  NÉZD MEG a repo struktúráját, NE találj ki új konvenciót, ha van meglévő `schema/`
  vagy hasonló mappa)
- change_type: `new_capability`
- status_after_merge: `candidate`
- status indoklás: ELLENTÉTBEN a három előző `experimental` kontraktus-riporttal, ez
  TÉNYLEGES, futtatható SQL-t ad ÉS valós Postgres-teszttel bizonyítja — ez megfelel a
  `gateway-session-adapter-contract-001` → `session-context-pack-v1-001` mintának

## Sources

- **KÖTELEZŐ elsődleges forrás (a `cic-mcp-factory` repo `main`-jén, MÁR ott van):**
  - `${WORKDIR}/jobs/index.yaml` — prerequisite-ellenőrzéshez `- id: "<job-id>"`
    kulccsal (NEM `job_id:`)
  - `${WORKDIR}/jobs/shared-session-catalog-consumer-001/output/shared-session-catalog-
    consumer.md` — sor 254-255: `trust: mixed / candidate / reviewed_shared`,
    `canonical: false   # by default`
  - `${WORKDIR}/jobs/shared-cross-session-search-001/output/shared-cross-session-
    search.md` — sor 368-376: a `candidate_id`/`keyword_description`/
    `conflicting_with`/`superseded_by`/`superseded_at`/`superseded_reviewed_by`
    mezőtábla
  - `${WORKDIR}/jobs/shared-weighting-model-001/output/shared-weighting-model.md` —
    sor 317-322: `weight_score`/`recurrence_count`/`linked_factory_job_ids[]`/
    `last_evidence_at`/`recency_flag`/`weighting_evaluated_at` mezőtábla
- **MÁSODIK forrás (a `cic-mcp-shared` repo, a target, KLÓNOZVA):**
  - `cic-mcp-shared/CLAUDE.md` — "Trust modell" szekció
  - a repo gyökerének és `schema/`-szerű mappáinak tartalma (ha van) — NÉZD MEG mielőtt
    új fájlstruktúrát találnál ki

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. Prerequisite-ellenőrzés

```
grep -n '\- id: "shared-session-catalog-consumer-001"' -A 3 jobs/index.yaml
grep -n '\- id: "shared-cross-session-search-001"' -A 3 jobs/index.yaml
grep -n '\- id: "shared-weighting-model-001"' -A 3 jobs/index.yaml
```

Idézd a kimenetet, erősítsd meg mindhárom `status: "done"`. Ha NEM, NO-GO és állj meg.

### 2. SQL schema — minden mező a három riportból

Először GREP-pel erősítsd meg, van-e már meglévő SQL/schema-fájl-konvenció a
`cic-mcp-shared` repóban (teszt-fájlok kizárva):

```
grep -rn "CREATE SCHEMA\|CREATE TABLE" --include="*.sql" . | grep -v test_
find . -iname "*.sql" | grep -v test_
```

Idézd a kimenetet — ha van meglévő `schema/`-szerű mappa/konvenció, kövesd azt; ha
nincs, indokold a választott helyet a "Decisions Proposed"-ben.

Írj egy SQL schema-fájlt, amely létrehoz egy `shared_core` schemát és egy
candidate-record táblát (pl. `shared_core.candidates`), tartalmazva PONTOSAN ezeket
a mezőket (semmi kihagyva, semmi átnevezve indoklás nélkül):

- `candidate_id` (PK)
- `keyword_description` (text)
- `trust` (enum/check: `mixed` | `candidate` | `reviewed_shared`)
- `canonical` (bool, **DEFAULT false, ÉS egy CHECK/constraint, ami megakadályozza,
  hogy `canonical = true` legyen anélkül, hogy `trust = 'reviewed_shared'` is
  fennálljon** — ez a job legkritikusabb pontja, lásd "Kontextus")
- `conflicting_with` (nullable lista `candidate_id`-kra; self-referencing)
- `superseded_by` (nullable self-reference `candidate_id`-ra)
- `superseded_at` (nullable timestamp)
- `superseded_reviewed_by` (nullable identifier)
- `weight_score` (float)
- `recurrence_count` (integer)
- `linked_factory_job_ids` (lista string)
- `last_evidence_at` (nullable timestamp)
- `recency_flag` (bool)
- `weighting_evaluated_at` (timestamp)
- `provenance_refs` (lista `{content_hash, ref_kind, ref_value}` struktúra — JSONB
  vagy külön tábla, indokold a választást)

Ha bármelyik mezőhöz a három riport nem ad elég típus-részletet (pl. pontos string
hossz), indokolt, ésszerű döntést hozz, és dokumentáld a "Decisions Proposed"
szekcióban — de a MEZŐ MAGA nem hagyható ki.

### 3. `canonical` constraint — valós bizonyítás

A riportban add meg a CHECK constraint pontos `file:line` hivatkozását a SQL
schema-fájlban (ez egy schema-szintű job, nincs production call-site, mert a
fogyasztó kód egy KÉSŐBBI job tárgya — de a constraint MAGÁNAK a SQL-ben kell
léteznie, file:line-nal idézve, NEM elég megemlíteni).

A `canonical` mező védelmét VALÓS Postgres teszttel bizonyítsd:
1. egy `INSERT` `trust='mixed', canonical=false` — sikeres
2. egy `INSERT` vagy `UPDATE` próbálkozás `canonical=true` mellett, `trust != 
   'reviewed_shared'` esetén — **EL KELL UTASÍTANIA** a DB-nek (constraint violation)
3. egy `UPDATE` `trust='reviewed_shared', canonical=true` — sikeres

Idézd mindhárom teszt-eset TÉNYLEGES kimenetét (psql/pytest, akármelyiket választod,
de valós Postgres ellen).

### 4. `conflicting_with`/`superseded_by` self-reference teszt

Valós Postgres teszttel bizonyítsd, hogy két candidate-rekord kölcsönösen be tudja
állítani egymást `conflicting_with`-ben (self-referencing FK vagy hasonló, NULL
megengedett), és hogy egy `superseded_by` lánc (A → B) létrehozható és lekérdezhető.

## Nem cél

- a tényleges aggregátor-kód (ami beírná ezeket a sorokat) — az
  `shared-cross-session-aggregator-implementation-001` job tárgya
- a három meglévő design-riport mezőinek megkérdőjelezése/újradefiniálása (ÉPÍTS
  rájuk, ne helyettesítsd őket)
- a canonical promotion emberi review-folyamatának RÉSZLETes kidolgozása (csak a
  DB-szintű constraint kell, ami megakadályozza a bypass-t)

## Required Output Files

- `output/shared-core-storage-implementation.md`
- a SQL schema-fájl (a repo struktúrájának megfelelő helyen, dokumentálva HOL)

## Required Report Sections

```markdown
# shared-core-storage-implementation-001 Output

## Scope
## Inputs Read
## Prerequisite Check
## Schema Design — Field-By-Field Traceability

(minden mező → melyik riport melyik sora alapozta meg)

## Canonical Constraint — Real Postgres Proof
## Conflicting/Superseded Self-Reference Proof
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

Elfogadott `Status` értékek: `proven`, `partial`, `missing`, `rejected`, `unknown`.
`proven` egy "a constraint megakadályozza a bypass-t" állításra KIZÁRÓLAG akkor
használható, ha a TÉNYLEGES, elutasított INSERT/UPDATE hibaüzenete idézve van — a
schema léte ≠ implemented (ez egyetlen soron), a CHECK constraint megírása nem
bizonyítja, hogy tényleg blokkol.

## Definition Of Done

- [ ] mindhárom prerequisite `id:` kulccsal megerősítve, GO/NO-GO döntés indokolva
- [ ] minden mező mind a három riportból átkerült, field-by-field nyomon követve
- [ ] a `canonical` constraint valós, elutasított INSERT/UPDATE-tel bizonyítva
- [ ] a `conflicting_with`/`superseded_by` self-reference valós teszttel bizonyítva
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- mező kihagyása/átnevezése a három riportból indoklás nélkül a "Decisions
  Proposed"-ben
- `canonical` mező valós, elutasított teszt nélkül "bizonyítottnak" állítva
- a fájl/schema léte ≠ implemented (ez egyetlen soron) — a sikertelen INSERT/UPDATE
  hibaüzenete bizonyít, a CHECK constraint megírása nem
- a `weight_score` küszöb elérésének automatikus `canonical: true`-vá fordítása
  bármilyen formában (ez a `shared-weighting-model-001` explicit tiltott
  rövidítése, ide is vonatkozik)

## Git instrukciók

Push a `feature/shared-core-storage-implementation-001` branch-re, KIZÁRÓLAG a
`cic-mcp-shared` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni,
elég a lokális commit). Main-re az agent NEM pushol. **NE módosítsd a `meta.yaml`
`status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek/SQL angolul.
