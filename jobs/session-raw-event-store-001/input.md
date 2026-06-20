# Job: session-raw-event-store-001

## Kontextus

Eddig két DESIGN job zárult le a session rétegben: a `SessionIngressEnvelope` schema
(`session-ingress-envelope-contract-001`) és a Postgres DDL draft
(`session-postgres-storage-design-001`, `output/session-postgres-schema.sql`). Az
orchestrátor a DDL-t független módon lefuttatta egy valódi `pgvector/pgvector:pg16`
konténeren — minden schema/tábla/index/function/trigger hiba nélkül létrejött, a trigger
helyesen ír outbox-sort, a `canonical: true` insert helyesen elutasítva.

**Ez az ELSŐ valódi kód-implementációs job a session rétegben.** Nincs még semmilyen
Python kód, ami a `SessionIngressEnvelope`-ot tényleg beírná a `session_raw.envelopes`
táblába egy futó Postgres-en. Ez a job ezt írja meg: a write-path.

## Target

- target repo: `cic-mcp-session`
- target path: az agent válassza meg a modul helyét a repo konvenciójának megfelelően
  (pl. `session_store/` vagy `tools/session_store.py`), és idézze a választott path-ot a
  reportban
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: ez az első write-path implementáció, valódi Postgres-teszttel, de nincs
  még éles forgalom/worker-projekció rá épülve — `candidate`-hez kellene legalább a
  `session-turn-projector-001` worker, ami tényleg konzumálja az outbox-ot

## Sources

- `${WORKDIR}/.cic-context/factory-docs/job-slices.yaml` — `session-raw-event-store-001`
  bejegyzés (phase 3, acceptance_gates, required_evidence, forbidden_shortcuts) — NORMATÍV
- `${WORKDIR}/.cic-context/factory-docs/architecture.md` — "## Postgres-first elv" szekció
- **KÖTELEZŐ elsődleges forrás (mindkettő már a `cic-mcp-session` `main`-en van):**
  - `cic-mcp-session/output/session-postgres-schema.sql` — a DDL, amit a write-path
    feltételez (alkalmazd a teszt-Postgres instance-on, MIELŐTT bármilyen insert-kódot
    írnál)
  - `cic-mcp-session/output/session-ingress-envelope.schema.yaml` — a
    `SessionIngressEnvelope` schema, amit a write-path bemenetként fogad

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a `session-postgres-schema.sql`-t és a
   `session-ingress-envelope.schema.yaml`-t, MIELŐTT bármilyen kódot írnál

## Feladat

### 1. Valódi Postgres teszt-instance

Indíts egy valódi Postgres instance-t teszteléshez — Docker-rel. **A `pgvector/pgvector:pg16`
image már lokálisan cache-elve van ezen a gépen** (egy korábbi job ezt már lehúzta és
használta), tehát ennek elindítása gyors kell legyen (nem kell hosszú image-letöltésre
várni). Futtasd:

```bash
docker run -d --name session-raw-event-store-test -e POSTGRES_PASSWORD=test -e POSTGRES_DB=testdb pgvector/pgvector:pg16
```

**FONTOS — egyfordulós végrehajtási fegyelem**: ez egy gyors (másodperces) konténer-indítás,
NEM egy hosszú ML-csomag letöltés. Várd ki szinkron módon (`pg_isready` pollozással, max
20 másodperc), NE próbálj semmit "később visszanézni" vagy ütemezni — fejezd be a teljes
munkát ebben az egyetlen menetben.

Alkalmazd a `session-postgres-schema.sql`-t a konténeren, és ellenőrizd hogy mind az 5
schema hiba nélkül létrejön (idézd a kimenetet).

### 2. Write-path implementáció

Írj egy Python függvényt/modult, ami:
- bemenetként egy `SessionIngressEnvelope`-alakú dict/objektumot fogad
- validálja a kötelező mezőket (a schema YAML szerint) INSERT előtt
- beírja a `session_raw.envelopes` táblába
- a DB-kapcsolat paramétereit konfigurálhatóvá teszi (env var vagy config, NE hardcode-olt
  connection string)

Válassz egy Postgres driver csomagot (pl. `psycopg2-binary` vagy `psycopg[binary]`), vedd
fel a `requirements.in`-be, regeneráld a `requirements.txt`-t (`pip-compile`, ahogy a
`session-infra-pipeline-fix-001` jobban is történt — ha nincs `pip-compile`, manuálisan
told be a csomagot és idézd a verziót, amit használtál).

### 3. Idempotencia

A write-path-nak NEM szabad duplikált sort létrehoznia vagy kezeletlen kivételt dobnia, ha
ugyanazt az `idempotency_key`-t kétszer próbálja beírni — használj `ON CONFLICT
(idempotency_key) DO NOTHING` (vagy egyenértékű) mintát, és teszteld is.

### 4. canonical/interpreted elutasítás kezelése

Teszteld, hogy a `canonical: true` vagy `interpreted: true` mezővel érkező envelope-ot a
write-path NEM engedi át hibátlanul — vagy alkalmazás-szintű validációval előre elutasítja,
vagy a DB CHECK constraint hibáját kezeli le graceful módon (nem nyers stacktrace-szel
crashel). Mindkét megközelítés elfogadható, válassz egyet és indokold.

### 5. Tesztek

Írj pytest teszteket, amik a VALÓDI Postgres konténer ellen futnak (nem mock-olt
kapcsolattal):
- sikeres insert (érvényes envelope)
- idempotencia (kétszer ugyanaz az `idempotency_key`, nincs duplikáció, nincs kivétel)
- `canonical: true` elutasítás
- `interpreted: true` elutasítás

A teszteket dokumentáld úgy, hogy egy másik fejlesztő/agent reprodukálhassa (pontos
parancssor a konténer-indítástól a `pytest` futtatásig).

## Nem cél

- a `session_jobs.outbox`-ot konzumáló worker megírása (külön job:
  `session-turn-projector-001`)
- embedding-generálás (külön job: `session-chunk-indexer-001`)
- `mcp-server/server.py` átírása, hogy ezt a write-path-ot hívja (ez egy read-path
  komponens, ez a job csak write-path)
- éles Postgres-instance üzemeltetés/migrációs framework bekötése

## Required Output Files

- `output/session-raw-event-store-report.md`

## Required Report Sections

A report MUST kövesse az `.cic-context/factory-docs/acceptance-contract.md`
"Universal Output Contract" szakaszát:

```markdown
# session-raw-event-store-001 Output

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

Elfogadott `Status` értékek: `proven`, `partial`, `missing`, `rejected`, `unknown`. Itt
`proven` KIZÁRÓLAG akkor használható, ha a tényleges teszt-futtatás kimenete idézve van —
valódi Postgres ellen, nem mock-olt kapcsolattal.

## Definition Of Done

- [ ] a `session-postgres-schema.sql` hiba nélkül alkalmazva egy valódi Postgres
      konténeren, idézve a kimenetet
- [ ] write-path függvény/modul létezik, fájl:sor hivatkozással a reportban
- [ ] sikeres insert teszt VALÓDI Postgres ellen, lefuttatva, kimenet idézve
- [ ] idempotencia teszt (kétszer ugyanaz az idempotency_key) lefuttatva, kimenet idézve,
      bizonyítva hogy nincs duplikáció és nincs kezeletlen kivétel
- [ ] `canonical: true` elutasítás teszt lefuttatva, kimenet idézve
- [ ] `interpreted: true` elutasítás teszt lefuttatva, kimenet idézve
- [ ] a teszt-futtatás reprodukálható egy dokumentált paranccsal (konténer-indítástól
      pytest-ig)
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- mock-olt DB-kapcsolat ≠ működő write-path bizonyítéka — minden `proven` állításhoz VALÓDI
  Postgres ellen futtatott teszt kimenete kell
- "az UNIQUE constraint kezeli, nem kell rá teszt" ≠ elfogadható — az idempotencia tesztet
  KÖTELEZŐ lefuttatni és a kimenetet idézni, nem elég a constraint létezésére hivatkozni
- "a kód logikailag helyes kellene legyen" ≠ bizonyíték — minden write-path-állítást
  tényleges futtatással kell igazolni

## Git instrukciók

Push a `feature/session-raw-event-store-001` branch-re, a `cic-mcp-session` célrepóban.
Main-re az agent NEM pushol. A teszteléshez használt Docker konténert a munka végén
állítsd le és töröld (`docker rm -f session-raw-event-store-test`), hogy ne maradjon árva
erőforrás.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/teszt-nevek angolul.
