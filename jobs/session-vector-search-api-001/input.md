# Job: session-vector-search-api-001

## Kontextus

A `session-chunk-indexer-001` job óta `session_idx.chunk_embeddings` minden chunk-hoz egy
384-dimenziós embedding vektort tárol (`paraphrase-multilingual-MiniLM-L12-v2`), és van rá
egy HNSW index is (`idx_session_idx_chunk_embeddings_hnsw`). **Ezt az embedding-et eddig
SOHA senki nem olvasta** — a `session_api.search_context()` (a `session-retrieval-quality-001`
által javított, `'simple'`-alapú FTS) kizárólag szöveges keresést végez, vektor-hasonlóságot
nem.

Ez a job megírja az ELSŐ SQL függvényt, ami tényleg lekérdezi a `chunk_embeddings`-et:
cosine-similarity alapú vektor-keresés, a meglévő HNSW index használatával.

**Fontos architekturális döntés**: a query-szöveget VALAHOL embedding-gé kell alakítani,
mielőtt a SQL függvény meghívható — ez NEM történhet SQL/plpgsql-ben (nincs lokális
embedding-modell-hívás SQL-ből). Tehát:
- a SQL függvény egy KÉSZ `VECTOR(384)` paramétert fogad (NEM szöveget)
- egy Python helper-függvény végzi a szöveg→vektor átalakítást, a `chunk_indexer.py`-ban
  MÁR LÉTEZŐ `embed_texts()`/`_get_embedding_model()` ÚJRAHASZNÁLÁSÁVAL (NE írj új
  modell-betöltő kódot, importáld/hívd a meglévőt)

## Target

- target repo: `cic-mcp-session`
- target path: a Python helper helye az agent választása (pl.
  `session_store/vector_search.py`, ami importálja `chunk_indexer.embed_texts`-et), a
  migráció egy ÚJ SQL fájlban (pl. `output/session-vector-search-api-migration.sql`),
  additív, NEM a meglévő fájlok felülírása
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: ez az első vektor-keresési kód, valódi multi-topic fixture-rel
  bizonyítva, de nincs még valós-méretű (sok session/sok chunk) teljesítmény-/
  index-használati teszt — `candidate`-hez kellene ez, plusz egy hibrid (FTS+vektor)
  ranking-stratégia kiértékelése

## Sources

- `${WORKDIR}/.cic-context/factory-docs/job-slices.yaml` — `session-vector-search-api-001`
  bejegyzés — NORMATÍV
- **KÖTELEZŐ elsődleges forrás (mind már a `cic-mcp-session` `main`-en van):**
  - `cic-mcp-session/output/session-postgres-schema.sql` — `session_idx.chunk_embeddings`
    DDL, `idx_session_idx_chunk_embeddings_hnsw` index definíció, a meglévő
    `session_api.search_context()` minta (kb. 320-345. sor)
  - `cic-mcp-session/output/session-retrieval-quality-migration.sql` — a legutóbbi
    `session_api` migráció mintája (hogyan írj additív `CREATE OR REPLACE FUNCTION`-t)
  - `cic-mcp-session/session_store/chunk_indexer.py` — `embed_texts()`,
    `_get_embedding_model()`, `EMBEDDING_MODEL`, `EXPECTED_EMBEDDING_DIM` — EZEKET
    ÚJRAHASZNÁLD, ne írj új embedding-betöltő/hívó kódot
  - `cic-mcp-session/tests/test_session_store/test_session_api.py` — a meglévő
    valódi-láncon-átmenő fixture minta, amit kövess (insert_envelope →
    turn_projector → chunk_indexer)

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti KÖTELEZŐ forrásokat, MIELŐTT bármilyen kódot írnál

## Feladat

### 1. Valódi Postgres teszt-instance + teljes lánc alkalmazása

Indíts egy valódi Postgres instance-t (`pgvector/pgvector:pg16`, lokálisan cache-elve), és
alkalmazd EGYMÁS UTÁN: `session-postgres-schema.sql`, `session-chunk-indexer-migration.sql`,
`session-retrieval-quality-migration.sql`, majd az ÚJ migrációdat. **Egyfordulós
végrehajtási fegyelem**: fejezd be a teljes munkát egyetlen menetben.

### 2. Additív SQL függvény: vektor-keresés

Írj egy `session_api` SQL függvényt (pl. `search_context_vector`), ami:
- paraméterei: `p_session_id UUID`, `p_query_embedding VECTOR(384)`, `p_limit INTEGER
  DEFAULT 20`
- visszaadja a `session_core.chunks` sorokat (`chunk_id`, `turn_id`, `text`,
  `similarity`), a `session_idx.chunk_embeddings.embedding`-hez a `<=>` (cosine distance)
  operátorral rendezve, a `p_session_id`-ra szűrve
- a meglévő `idx_session_idx_chunk_embeddings_hnsw` indexet kell, hogy tudja használni

### 3. Python query-embedding helper (ÚJRAHASZNÁLVA a meglévő modellt)

Írj egy Python függvényt (pl. `embed_query(text: str) -> list[float]`), ami a
`chunk_indexer.embed_texts()`-et hívja meg EGYETLEN query string-gel, és visszaadja a
kapott vektort, amit a SQL függvénynek lehet paraméterezni (psycopg-n keresztül,
`pgvector` Python adapter vagy nyers `VECTOR` literál string formázás — döntsd el és
dokumentáld). NEM szabad külső LLM/HTTP embedding API-t hívni.

### 4. Realisztikus, két-témájú teszt-fixture a VALÓDI láncon keresztül

Hozz létre egy fixture-t, ami a VALÓDI láncon (insert_envelope → turn_projector →
chunk_indexer) legalább 2, szemantikailag JÓL ELKÜLÖNÜLŐ témájú turn-öt épít fel (pl. egy
turn egy adatbázis-migrációról, egy másik egy frontend CSS-stílusról szól — válassz olyan
témapárt, ami a multilingual MiniLM modellnél is jól elkülönül).

### 5. Tesztek — szemantikai relevancia + index-használat ellenőrzés

- query-szöveg az 1. témáról → asszertáld, hogy a `search_context_vector()` az 1. témájú
  chunk-ot rangsorolja ELŐSZÖR (nem csak hogy visszaad valamit)
- query-szöveg a 2. témáról → asszertáld a 2. témájú chunk elsőségét
- futtass `EXPLAIN` (vagy ekvivalens) a függvény lekérdezésére, és dokumentáld, hogy
  HNSW index scan-t használ-e, VAGY ha a kis sorszám miatt a planner sequential scan-t
  választ, ezt explicit dokumentáld várt/elfogadott jelenségként a kis fixture-méretnél
  (NE hallgass róla, NE feltételezd index-használatot ellenőrzés nélkül)
- teszteld, hogy a `embed_query()` TÉNYLEGES kimeneti dimenziója (lekérdezve, nem
  feltételezve) megegyezik a `chunk_embeddings.embedding` deklarált dimenziójával (384)

### 6. Reachability ellenőrzés (kötelező)

```bash
grep -rn "<helper_function_name>" --include="*.py" . | grep -v "test_" | grep -v "/tests/"
```

Minden találatnál add meg a hívó fájl és sor pontos hivatkozását (`file:line`). Ha 0
KÜLSŐ hívó van, dokumentáld `deadcode`/`scaffold`-ként. A SQL függvény oldalát (nincs
Python reachability) a `session_api.*` minta szerint `file:line`-nal dokumentáld.

## Nem cél

- hibrid (FTS+vektor) ranking-stratégia kidolgozása vagy kiértékelése — külön, jövőbeli job
- `session_core.source_refs`/`session_idx.ranking_features` feltöltése
- nagy mennyiségű, valós session-adaton végzett teljesítmény-/index-skálázódási teszt
- az MCP szerver (`mcp-server/server.py`) átírása, hogy ezt a függvényt hívja
- permanens futtatási infrastruktúra

## Required Output Files

- `output/session-vector-search-api-report.md`
- `output/session-vector-search-api-migration.sql`

## Required Report Sections

```markdown
# session-vector-search-api-001 Output

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
`proven` KIZÁRÓLAG akkor használható, ha a tényleges SQL-függvény-hívás kimenete idézve
van — valódi Postgres ellen. A függvény léte a migrációs fájlban ≠ működik — csak a
tényleges futtatás bizonyít.

## Definition Of Done

- [ ] additív migráció (`output/session-vector-search-api-migration.sql`) alkalmazva,
      kimenet idézve
- [ ] `embed_query()` helper létezik, a meglévő `chunk_indexer.embed_texts()`-et hívja
      (NEM új modell-betöltő kód), fájl:sor hivatkozással
- [ ] `embed_query()` TÉNYLEGES kimeneti dimenziója lekérdezve, megegyezik 384-gyel
- [ ] két-témájú, valódi-láncon-átmenő fixture létrehozva
- [ ] mindkét témára lefuttatott szemantikai-relevancia teszt, kimenet idézve, a várt
      chunk elsősége asszertálva
- [ ] `EXPLAIN` kimenet idézve, az index-használat (vagy annak hiánya kis méretnél)
      explicit kimondva
- [ ] reachability `grep -rn` eredmény idézve, `file:line` hivatkozással
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- query embedding generálása külső LLM/HTTP API-val — TILOS, csak a meglévő lokális
  modell (`chunk_indexer.embed_texts()`) újrahasználata
- csak azt tesztelni, hogy a függvény hibátlanul visszaad SOK sort — a szemantikai
  relevanciát (a releváns chunk az élen van) KÜLÖN, explicit kell bizonyítani
- HNSW index-használat feltételezése `EXPLAIN` ellenőrzés nélkül
- a `chunk_indexer.py` embedding-betöltő/hívó kódjának duplikálása — ÚJRAHASZNÁLD, ne
  írd újra

## Git instrukciók

Push a `feature/session-vector-search-api-001` branch-re, a `cic-mcp-session`
célrepóban. Main-re az agent NEM pushol. A teszteléshez használt Docker konténert a munka
végén állítsd le és töröld.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/teszt-nevek angolul.
