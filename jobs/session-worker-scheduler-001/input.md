# Job: session-worker-scheduler-001

## Kontextus

Két outbox-worker létezik és mergelve van: `turn_projector.run_projection_batch()`
(`project_envelope` job-ok) és `chunk_indexer.run_indexing_batch()` (`index_turn` job-ok).
Mindkettő reachability-státusza eddig `scaffold` volt minden korábbi job riportjában —
SENKI nem hívja meg őket a saját CLI-jükön/tesztjeiken kívül. Ez a job megírja az ELSŐ
mechanizmust, ami ISMÉTELTEN, ütemezetten hívja meg mindkettőt.

**Fontos, őszinte korlát, amit a jobnak EXPLICIT ki kell mondania**: ennek a repónak
(`cic-mcp-session`) **nincs élő production Postgres instance-e** — minden eddigi teszt
ideiglenes, a job végén törölt Docker-konténerek ellen futott. Ez a job tehát NEM
"deploy"-olja semmit production-be — egy **dokumentált, tesztelhető mechanizmust** ad
(polling loop + systemd timer/service unit pár vagy cron sor), amit VALÓDI, de
ideiglenes Postgres-instance ellen bizonyít működőnek, és EXPLICIT kimondja, hogy ez még
nincs sehol futtatva production-ben. A "dokumentált" és a "production-ben fut" állítás
NEM keverhető össze.

## Target

- target repo: `cic-mcp-session`
- target path: a polling loop helye az agent választása (pl.
  `session_store/worker_loop.py`), a deployment artifact (systemd unit/cron) egy ÚJ
  fájlban (pl. `output/session-worker-scheduler-deployment/` alatt vagy
  `output/session-worker-scheduler-report.md`-be ágyazva — döntsd el és dokumentáld)
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: a loop-mechanizmus VALÓDI, ideiglenes Postgres ellen bizonyítottan
  működik, de SEMMI nincs production-ben deploy-olva (nincs is hova, a repónak nincs élő
  instance-e) — `candidate`-hez kellene egy tényleges, hosszabb-életű deployment
  environment, ami ezt a jobot meghaladja

## Sources

- `${WORKDIR}/.cic-context/factory-docs/job-slices.yaml` — `session-worker-scheduler-001`
  bejegyzés — NORMATÍV
- **KÖTELEZŐ elsődleges forrás (mind már a `cic-mcp-session` `main`-en van):**
  - `cic-mcp-session/session_store/turn_projector.py` — `run_projection_batch()`,
    `_main()` CLI minta — ÚJRAHASZNÁLD a batch-hívást, NE írd újra a projekciós logikát
  - `cic-mcp-session/session_store/chunk_indexer.py` — `run_indexing_batch()`,
    `_main()` CLI minta — ÚJRAHASZNÁLD ugyanígy
  - `cic-mcp-session/tests/test_session_store/test_turn_projector.py` és
    `test_chunk_indexer.py` — a meglévő valódi-Postgres teszt-fixture minták

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti KÖTELEZŐ forrásokat, MIELŐTT bármilyen kódot írnál

## Feladat

### 1. Valódi Postgres teszt-instance + teljes lánc alkalmazása

Indíts egy valódi Postgres instance-t (`pgvector/pgvector:pg16`, lokálisan cache-elve), és
alkalmazd EGYMÁS UTÁN az összes meglévő SQL fájlt (`session-postgres-schema.sql`,
`session-chunk-indexer-migration.sql`, `session-retrieval-quality-migration.sql`,
`session-vector-search-api-migration.sql`, `session-hybrid-search-api-migration.sql`).
**Egyfordulós végrehajtási fegyelem**: fejezd be a teljes munkát egyetlen menetben.

### 2. Polling loop implementáció

Írj egy Python modult (pl. `session_store/worker_loop.py`), ami:
- minden iterációban meghívja `turn_projector.run_projection_batch()`-et ÉS
  `chunk_indexer.run_indexing_batch()`-et (ebben a sorrendben — előbb projekció, utána
  indexelés, mert az indexelésnek szüksége van a már projektált turn-ökre)
- támogat egy `--max-iterations N` (vagy ekvivalens) paramétert, hogy TESZTELHETŐ legyen
  véges iterációszámmal, NE csak végtelen ciklusban fusson
- iterációk között egy konfigurálható `--interval-seconds` alvást tart (a tesztekben ezt
  rövidre állítva, pl. 0.1-1 mp, NE valós production-intervallummal)
- üres backlog esetén NEM dob hibát, egyszerűen nincs mit feldolgoznia abban az
  iterációban

### 3. Deployment artifact (dokumentált, NEM deploy-olt)

Dokumentálj egy systemd timer+service unit párt (vagy cron sort, ha azt indokoltabbnak
találod) a loop production-futtatásához. Az artifactban EXPLICIT mondd ki: "ez egy
dokumentált deployment-minta, NEM jelenti azt, hogy ez bárhol production-ben fut — a
`cic-mcp-session` repónak jelenleg nincs élő production Postgres instance-e."

### 4. Teszt: VALÓDI backlog, TÖBB iteráción át lecsapolva

Hozz létre TÖBB (legalább 3) envelope-ot a VALÓDI `insert_envelope()` hívással, anélkül,
hogy MANUÁLISAN meghívnád a `run_projection_batch()`/`run_indexing_batch()`-et előtte.
Indítsd el a loop-ot `--max-iterations` ≥ 2-vel, és bizonyítsd:
- a loop a SAJÁT iterációi során, manuális worker-hívás KÖZBEAVATKOZÁS NÉLKÜL, teljesen
  lecsapolja a backlogot (minden envelope-hoz létrejön a turn, chunk, embedding sor)
- dokumentáld iterációnként, mennyi job-ot dolgozott fel a loop (NE csak a végeredményt
  idézd — a "loop tényleg több körön át dolgozik" állítást az iterációnkénti
  haladás bizonyítja, nem csak a végállapot)

### 5. Teszt: üres backlog kezelése

Indítsd el a loop-ot, amikor nincs pending job — bizonyítsd, hogy nem dob hibát, több
iteráción át sem.

### 6. Reachability ellenőrzés (kötelező)

```bash
grep -rn "<loop_function_name>" --include="*.py" . | grep -v "test_" | grep -v "/tests/"
```

`file:line` hivatkozással minden találatra. Dokumentáld explicit: a loop LÉTEZÉSE/
TESZTELTSÉGE különálló állítás a "VALAKI/VALAMI TÉNYLEG ÜTEMEZETTEN FUTTATJA
production-ben" állítástól — az utóbbi `missing`, mert nincs production deployment.

## Nem cél

- tényleges production deployment (nincs is hova — nincs élő instance)
- a `--interval-seconds` valós production-értékének meghatározása/hangolása
- multi-worker konkurencia-kezelés (ugyanaz a single-instance feltétel, mint
  `turn_projector`-nál és `chunk_indexer`-nél)
- monitoring/alerting integráció
- az MCP szerver átírása

## Required Output Files

- `output/session-worker-scheduler-report.md`

## Required Report Sections

```markdown
# session-worker-scheduler-001 Output

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

Elfogadott `Status` értékek: `proven`, `partial`, `missing`, `rejected`, `unknown`.
`proven` KIZÁRÓLAG akkor használható, ha a tényleges teszt-futtatás kimenete idézve van —
valódi Postgres ellen. A loop fájl léte ≠ működik — csak a tényleges futtatás bizonyít.

## Definition Of Done

- [ ] polling loop implementálva, a MEGLÉVŐ `run_projection_batch()`/
      `run_indexing_batch()`-et hívja, fájl:sor hivatkozással
- [ ] `--max-iterations` (vagy ekvivalens) paraméter létezik és tesztelhető
- [ ] systemd unit/cron deployment artifact dokumentálva, EXPLICIT "nincs production-ben
      futtatva" kijelentéssel
- [ ] többiterációs, valódi backlog-lecsapolási teszt lefuttatva, iterációnkénti
      haladás idézve
- [ ] üres backlog teszt lefuttatva, kimenet idézve
- [ ] reachability `grep -rn` eredmény idézve, `file:line` hivatkozással, a "létezik/
      tesztelt" és a "production-ben fut" állítás KÜLÖN kezelve
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a loop fájl létezése ≠ bizonyított működés — csak a tényleges, idézett teszt-futtatás
- egyetlen iterációs teszt, ami mindent egyszerre dolgoz fel — ez NEM bizonyítja a
  loop-jelleget, csak azt, hogy a meglévő batch-függvények működnek (ezt korábbi jobok már
  bizonyították)
- "a systemd unit fájl megírása = deploy-olva van" — TILOS összemosni; a fájl léte
  dokumentáció, nem futó production-szolgáltatás
- a `turn_projector`/`chunk_indexer` batch-logikájának újraírása a loop-on belül —
  ÚJRAHASZNÁLD a meglévő függvényeket

## Git instrukciók

Push a `feature/session-worker-scheduler-001` branch-re, KIZÁRÓLAG a `cic-mcp-session`
célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni, elég a lokális
commit). Main-re az agent NEM pushol. A teszteléshez használt Docker konténert a munka
végén állítsd le és töröld. **NE módosítsd a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/teszt-nevek angolul.
