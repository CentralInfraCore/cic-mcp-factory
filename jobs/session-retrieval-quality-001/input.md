# Job: session-retrieval-quality-001

## Kontextus

Két outbox-worker már megírva és mergelve:
- `session-turn-projector-001`: `session_raw.envelopes` → `session_core.sessions`/`turns`
- `session-chunk-indexer-001`: `session_core.turns` → `session_core.chunks` +
  `session_idx.chunk_fts` + `session_idx.chunk_embeddings`

A `session-postgres-schema.sql` emellett már TARTALMAZ egy `session_api` schema-t 4
stabil SQL függvénnyel (`search_context`, `get_timeline`, `get_context_pack`,
`session_status`) — ezeket EDDIG SOHA senki nem hívta meg valódi adaton. Ez a job az
ELSŐ, ami a teljes láncot (write-path → mindkét worker → read-path) végponttól végpontig
teszteli.

**Két konkrét, gyanús integrációs rés, amit ennek a jobnak EXPLICIT meg kell vizsgálnia
(NEM feltételezni, hanem tényleges futtatással eldönteni)**:

1. **FTS nyelvi konfiguráció eltérés**: a `chunk_indexer.py` a chunk szöveget
   `to_tsvector('simple', ...)`-vel indexeli (lásd `session_store/chunk_indexer.py`,
   keresd a `to_tsvector` hívást), de a `session_api.search_context()` függvény
   `plainto_tsquery('english', p_query)`-vel kérdez (lásd `session-postgres-schema.sql`
   kb. 326-345. sor). A `'simple'` konfiguráció NEM stemmel (csak lowercase+tokenizál),
   az `'english'` konfiguráció IGEN (pl. "running" → "run"). Ha egy chunk szövege
   "running"-ot tartalmaz, és a query "run", a `tsv @@ plainto_tsquery('english', 'run')`
   feltétel lehet, hogy NEM talál egyezést, mert a tsvector oldal nem lett stemmelve.
   **Ezt tényleges beszúrással + lekérdezéssel kell bizonyítani, nem kikövetkeztetni.**
2. **`session_status()` `pending_jobs` aluszámolás gyanúja**: a függvény (lásd
   `session-postgres-schema.sql` kb. 381-399. sor) a `pending_jobs`-t úgy számolja, hogy
   `o.payload->>'event_id' IN (SELECT e.event_id::text FROM session_raw.envelopes ...)`.
   A `project_envelope` job_type outbox-sorok payload-ja TARTALMAZ `event_id`-t (lásd
   `session_raw.enqueue_projection_job()` trigger), de az `index_turn` job_type sorok
   payload-ja (`session-chunk-indexer-migration.sql`-ben bevezetett trigger) CSAK
   `session_id`/`turn_seq`-et tartalmaz, `event_id`-t NEM. Ha ez igaz, a `pending_jobs`
   SOHA nem számolja be a függő `index_turn` job-okat. **Ezt is tényleges `index_turn`
   outbox-sor létrehozásával + a függvény lekérdezésével kell ellenőrizni.**

Mindkét esetben: ha a gyanú igazolódik és VALÓDI, nemkívánt hibás működést okoz, egy
minimális, additív migrációval (hasonlóan a `session-chunk-indexer-migration.sql`
mintájához) javítsd ki, és indokold a választást a "Decisions Proposed"-ben. Ha a gyanú
NEM igazolódik (a tényleges teszt szerint működik), dokumentáld ezt is — ne találd ki,
melyik az igaz, derítsd ki.

## Target

- target repo: `cic-mcp-session`
- target path: tesztek a meglévő `tests/test_session_store/` mintát követve (pl.
  `tests/test_session_store/test_session_api.py`), MIGRÁCIÓ (ha szükséges) egy ÚJ
  fájlban (pl. `output/session-retrieval-quality-migration.sql`), additív, NEM a meglévő
  fájlok felülírása
- change_type: `enhancement`
- status_after_merge: `experimental`
- status indoklás: ez egy validációs/javító job, nem egy önálló capability — a 4
  `session_api` függvény MAGA már a `session-postgres-schema.sql` (lezárt, `done` állapotú
  job) része volt; ez a job a meglévő funkciókat teszteli/javítja, de a chunk-méret/
  retrieval-hangolás (lásd `session-chunk-indexer-001` "Risks") továbbra sem értékelt itt
  — `candidate`-hez kellene egy nagyobb, valós-session-mennyiségű kiértékelés

## Sources

- `${WORKDIR}/.cic-context/factory-docs/job-slices.yaml` — `session-retrieval-quality-001`
  bejegyzés — NORMATÍV
- **KÖTELEZŐ elsődleges forrás (mind már a `cic-mcp-session` `main`-en van):**
  - `cic-mcp-session/output/session-postgres-schema.sql` — `session_api.*` 4 függvény
    TELJES definíciója (kb. 320-400. sor)
  - `cic-mcp-session/session_store/turn_projector.py`,
    `cic-mcp-session/session_store/chunk_indexer.py`,
    `cic-mcp-session/session_store/envelope_writer.py` — a teljes write-path lánc, amit
    a teszt-fixture-nek VALÓDIBAN kell végighívnia (NEM kézi INSERT a
    session_core/session_idx táblákba)
  - `cic-mcp-session/output/session-chunk-indexer-migration.sql` — az `index_turn`
    trigger payload-formátuma (`session_id`/`turn_seq`, NINCS `event_id`)
  - `cic-mcp-session/tests/test_session_store/test_chunk_indexer.py` és
    `test_turn_projector.py` — a meglévő teszt-fixture minta (Postgres-konténer indítás,
    `_pg_config`, truncate-fixture), amit kövess

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti KÖTELEZŐ forrásokat, MIELŐTT bármilyen kódot írnál

## Feladat

### 1. Valódi Postgres teszt-instance + teljes lánc alkalmazása

Indíts egy valódi Postgres instance-t (`pgvector/pgvector:pg16`, lokálisan cache-elve),
és alkalmazd EGYMÁS UTÁN: `session-postgres-schema.sql`, majd
`session-chunk-indexer-migration.sql`. **Egyfordulós végrehajtási fegyelem**: fejezd be a
teljes munkát egyetlen menetben.

### 2. Realisztikus, kétnyelvű teszt-fixture a VALÓDI láncon keresztül

Hozz létre egy fixture-t, ami TÉNYLEGESEN meghívja:
`envelope_writer.insert_envelope()` (több envelope, ugyanahhoz a session-hez) →
`turn_projector.run_projection_batch()` → `chunk_indexer.run_indexing_batch()`.
A beszúrt tartalom legyen kifejezetten kétnyelvű (magyar + angol szöveg), és tartalmazzon
legalább egy angol szót KÉT alakban (pl. "running" egy chunk-ban, és a query-ben "run"
fog szerepelni) — ez kell az 1. gyanú teszteléséhez.

### 3. `session_api.search_context()` teszt + FTS nyelvi konfiguráció ellenőrzés

- query egy egzakt szóra (pl. egy szó, ami pontosan szerepel a chunk szövegében) →
  asszertáld hogy a várt `chunk_id` visszajön
- query a stemming-érzékeny alakra (pl. "run", miközben a chunk "running"-ot tartalmaz)
  → dokumentáld a TÉNYLEGES eredményt (talál/nem talál), ne feltételezd
- ha a stemming-teszt hibás/nemkívánt eredményt ad, implementálj egy additív migrációt,
  ami összhangba hozza a `to_tsvector`/`tsquery` konfigurációkat (döntsd el melyik
  irányba — indokold a kétnyelvű korpusz fényében, hogy melyik konfiguráció a
  védhetőbb), és teszteld újra, hogy a javítás után a teszt átmegy

### 4. `session_api.get_timeline()` és `get_context_pack()` teszt

Valódi multi-turn fixture-rel: asszertáld a helyes `turn_seq`/`chunk_seq` sorrendet a
visszaadott sorokban.

### 5. `session_api.session_status()` teszt + pending_jobs ellenőrzés

- hozz létre egy `index_turn` outbox sort `pending` állapotban (a meglévő trigger-rel,
  egy valódi turn beszúrásával, MIELŐTT a chunk-indexer worker lefutna rajta)
- hívd meg `session_status()`-t, és vizsgáld meg, hogy a `pending_jobs` érték TARTALMAZZA-e
  ezt a sort
- ha NEM (a gyanú igazolódik), implementálj egy additív migrációt, ami javítja a
  `pending_jobs` számítást úgy, hogy minden outbox `job_type`-ra helyesen működjön
  (ne csak `project_envelope`-ra), és teszteld újra

### 6. Reachability / integrációs lánc dokumentálása

Nincs külön reachability-grep ehhez a jobhoz (a `session_api.*` függvények SQL-ben élnek,
nem Python-hívási láncban) — helyette dokumentáld `file:line` hivatkozással MINDEN
`session_api.*` függvény definíciójának helyét a `session-postgres-schema.sql`-ben, és
minden olyan helyet, ahol a migráció (ha készült) ezt módosította.

## Nem cél

- ÚJ vektor-keresési SQL függvény írása (`session_idx.chunk_embeddings`-et lekérdező
  hibrid/cosine-similarity API) — ez egy külön, jövőbeli job
  (`session-vector-search-api-001`)
- `session_core.source_refs`/`session_idx.ranking_features` feltöltése
- nagy mennyiségű, valós session-adaton végzett retrieval-minőség benchmark
  (`candidate`-hez kellene, ez a job csak korrektségi/integrációs validáció)
- az MCP szerver (`mcp-server/server.py`) átírása, hogy ezeket a függvényeket hívja

## Required Output Files

- `output/session-retrieval-quality-report.md`
- `output/session-retrieval-quality-migration.sql` (CSAK ha a 3. vagy 5. pont fixet
  igényelt — ha mindkét gyanú alaptalan, ez a fájl elmaradhat, de a report ezt explicit
  mondja ki, nem csak hallgat róla)

## Required Report Sections

```markdown
# session-retrieval-quality-001 Output

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

Elfogadott `Status` értékek: `proven`, `partial`, `scaffold`, `missing`, `rejected`,
`unknown`. `proven` KIZÁRÓLAG akkor használható, ha a tényleges SQL-függvény-hívás
kimenete idézve van — valódi Postgres ellen.

## Definition Of Done

- [ ] kétnyelvű, valódi-láncon-átmenő fixture létrehozva és dokumentálva
- [ ] `search_context()` egzakt-szó teszt lefuttatva, kimenet idézve
- [ ] `search_context()` stemming-érzékeny teszt lefuttatva, kimenet idézve, a TÉNYLEGES
      eredmény (talál/nem talál) explicit kimondva
- [ ] ha a stemming-teszt hibásnak bizonyult: additív migráció implementálva és
      újra-tesztelve, kimenet idézve; ha NEM bizonyult hibásnak: ez is explicit kimondva
- [ ] `get_timeline()`/`get_context_pack()` teszt lefuttatva, helyes sorrend asszertálva,
      kimenet idézve
- [ ] `session_status()` `pending_jobs` teszt lefuttatva `index_turn` outbox-sorral,
      a TÉNYLEGES eredmény (helyesen számol/aluszámol) explicit kimondva
- [ ] ha az aluszámolás igazolódott: additív migráció implementálva és újra-tesztelve,
      kimenet idézve; ha NEM igazolódott: ez is explicit kimondva
- [ ] minden `session_api.*` függvény `file:line` hivatkozása dokumentálva
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a `session_api` függvények SQL-kódjának elolvasása ÉS abból a működés
  KIKÖVETKEZTETÉSE ≠ bizonyíték — mindkét gyanús pontot TÉNYLEGES futtatással kell
  eldönteni, valódi Postgres ellen
- kézzel beszúrt `session_core`/`session_idx` sorok a teszt-fixture-höz — TILOS, a
  fixture-nek a VALÓDI `insert_envelope`/`run_projection_batch`/`run_indexing_batch`
  láncon kell átmennie
- "a `session_status()` valószínűleg jól működik, mert a `project_envelope` esetben jó" ≠
  elfogadható — az `index_turn` esetet KÜLÖN, explicit tesztelni kell
- ha egy migráció készül, és nincs hozzá teszt ami bizonyítja hogy a fix működik (a hiba
  reprodukálva ELŐTTE, eltűnt UTÁNA) ≠ elfogadható

## Git instrukciók

Push a `feature/session-retrieval-quality-001` branch-re, a `cic-mcp-session` célrepóban.
Main-re az agent NEM pushol. A teszteléshez használt Docker konténert a munka végén
állítsd le és töröld.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/teszt-nevek angolul.
