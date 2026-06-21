# Job: session-source-refs-extractor-001

## Kontextus

A `session_core` schema 4 táblájából 3 már fel van töltve (`sessions`, `turns`, `chunks` —
`turn_projector`/`chunk_indexer` által) — egyedül `session_core.source_refs` üres. Ez a
tábla provenance-referenciákat tárol egy chunk-hoz (fájl, URL, tool-hívás), amik a chunk
forrás-envelope payload-jából vagy a chunk szövegéből deríthetők ki.

**Fontos architekturális döntés**: ez NEM egy ÚJ outbox job_type/trigger — a
`source_refs.chunk_id` FK megköveteli, hogy a chunk MÁR létezzen, tehát a kinyerés a
MEGLÉVŐ `chunk_indexer` `index_turn` per-row tranzakción BELÜL történik, közvetlenül a
chunk létrehozása UTÁN, ugyanabban a tranzakcióban — NE hozz létre új outbox-mechanizmust
ehhez.

## Target

- target repo: `cic-mcp-session`
- target path: az agent válassza meg (új függvény(ek) a `session_store/chunk_indexer.py`-ban,
  vagy egy új, importált modul, pl. `session_store/source_refs.py` — döntsd el és
  idézd a választást)
- change_type: `enhancement`
- status_after_merge: `experimental`
- status indoklás: determinisztikus, de korlátozott kulcs-/regex-illesztés — `candidate`-hez
  kellene valós session-adaton mérni, mennyi tényleges referenciát talál meg/hagy ki
  (recall-elemzés), ez a job ezt nem méri

## Sources

- `${WORKDIR}/.cic-context/factory-docs/job-slices.yaml` — `session-source-refs-extractor-001`
  bejegyzés — NORMATÍV
- **KÖTELEZŐ elsődleges forrás (mind már a `cic-mcp-session` `main`-en van):**
  - `cic-mcp-session/output/session-postgres-schema.sql` — `session_core.source_refs` DDL
    (`source_ref_id`, `chunk_id` FK, `ref_kind`, `ref_value`, `content_hash`)
  - `cic-mcp-session/session_store/chunk_indexer.py` — `_index_one_job()` (a per-row
    tranzakció, amibe a kinyerést be kell illesztened, KÖZVETLENÜL a `_insert_chunk()`
    hívás UTÁN), `_fetch_turn()` (jelenleg csak `turn_id, session_id, content`-et
    SELECT-el — bővítened kell `role`-lal is, mert a `session_core.turns.role` mező
    (amit `turn_projector.map_role()` már kiszámolt és elmentett) a determinisztikus
    szignál a "ez egy tool-hívásból származó turn" detektáláshoz, NEM kell újra
    elérned az eredeti `provider_event_name`-et)
  - `cic-mcp-session/session_store/turn_projector.py` — `map_role()` — csak referenciaként,
    hogy lásd milyen `role` értékek léteznek (`tool`, `assistant`, `user`, `system`,
    `manual`, `event`)

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti KÖTELEZŐ forrásokat, MIELŐTT bármilyen kódot írnál

## Feladat

### 1. Valódi Postgres teszt-instance + teljes lánc alkalmazása

Indíts egy valódi Postgres instance-t (`pgvector/pgvector:pg16`, lokálisan cache-elve), és
alkalmazd EGYMÁS UTÁN az összes meglévő SQL fájlt (mind az 5: schema + 4 migráció).
**Egyfordulós végrehajtási fegyelem**: fejezd be a teljes munkát egyetlen menetben.

### 2. Determinisztikus kinyerési szabályok (döntsd el és dokumentáld)

Implementálj egy függvényt (pl. `extract_source_refs(role: str, content, text: str) ->
list[tuple[str, str]]`, visszaadva `(ref_kind, ref_value)` páreket), KÖVETKEZŐ
szabályokkal:
- **`ref_kind='tool_call'`**: ha `role == 'tool'` ÉS a `content` (JSONB, dict) tartalmaz
  egy ismert tool-név kulcsot (pl. `tool_name`) → egy sor a tool nevével
- **`ref_kind='file'`**: ha a `content` (vagy annak egy ismert beágyazott kulcsa, pl.
  `tool_input`) tartalmaz egy ismert fájlútvonal-kulcsot (pl. `file_path`, `path`,
  `notebook_path`) → egy sor minden talált útvonalra
- **`ref_kind='url'`**: a CHUNK SZÖVEGÉBEN (nem a raw payload-ban) keresve egy fix regex
  mintával (pl. `https?://\S+`) → egy sor minden talált URL-re

Ez NEM lehet AI/LLM-döntés — csak kulcs-/regex-illesztés. Indokold a választott
kulcsneveket/regex-mintát a "Decisions Proposed"-ben.

### 3. Integráció a meglévő `_index_one_job()`-ba

Bővítsd `_fetch_turn()`-t, hogy a `role`-t is SELECT-elje. Hívd meg
`extract_source_refs()`-et minden chunk létrehozása UTÁN (a SAJÁT per-row tranzakción
belül), és írj be egy `session_core.source_refs` sort minden visszaadott
`(ref_kind, ref_value)` párra, `content_hash`-sel (sha256 az `ref_value`-ból, vagy
indokold másik választásodat).

### 4. Négy-eseti teszt-fixture a VALÓDI láncon keresztül

Hozz létre legalább 4 envelope-ot a VALÓDI `insert_envelope()` lánccal:
- **Eset A**: tool-hívás alakú payload (`role` végül `'tool'`-ra fog feloldódni,
  `content` tartalmaz `tool_name`-et)
- **Eset B**: fájlútvonalat tartalmazó payload (pl. `tool_input.file_path`)
- **Eset C**: olyan szöveget tartalmazó turn, amiben van egy URL
- **Eset D**: semmi kinyerhető (kontroll eset — 0 `source_refs` sor, nincs hiba)

### 5. Bizonyítás: a 4 eset helyesen jelenik meg `session_core.source_refs`-ben

Lekérdezéssel bizonyítsd mind a 4 esetet — idézd a tényleges SQL-eredményt mindegyikre,
beleértve a D esetet (0 sor, nincs kivétel).

### 6. Regresszió-ellenőrzés

Futtasd le a TELJES meglévő `tests/test_session_store/` suite-ot, bizonyítva hogy a
`chunk_indexer`/`turn_projector`/`worker_loop`/`session_api`/`vector_search`/
`hybrid_search` tesztek NEM regresszáltak.

## Nem cél

- `session_idx.ranking_features` feltöltése
- recall-/pontosság-mérés valós session-adaton (mennyi referenciát hagy ki a kinyerés)
- AI/LLM-alapú entitás-felismerés vagy kinyerés
- az MCP szerver átírása, hogy ezt a táblát olvassa
- `session_api` réteg bővítése `source_refs` lekérdezésére (külön, jövőbeli job)

## Required Output Files

- `output/session-source-refs-extractor-report.md`

## Required Report Sections

```markdown
# session-source-refs-extractor-001 Output

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
`proven` KIZÁRÓLAG akkor használható, ha a tényleges SQL-lekérdezés kimenete idézve van —
valódi Postgres ellen. A függvény léte ≠ működik — csak a tényleges futtatás bizonyít.

## Definition Of Done

- [ ] kinyerési szabályok definiálva, indokolva, NEM AI/LLM-alapúak
- [ ] `extract_source_refs()` (vagy hasonló) létezik, fájl:sor hivatkozással
- [ ] `_fetch_turn()` bővítve `role`-lal, fájl:sor hivatkozással
- [ ] az integráció a MEGLÉVŐ `_index_one_job()` per-row tranzakcióján belül történik
      (NEM új outbox job_type), kódidézettel bizonyítva
- [ ] mind a 4 teszt-eset (tool_call, file, url, semmi) lefuttatva, tényleges SQL-eredmény
      idézve mindegyikre
- [ ] `content_hash` minden sorban kitöltve, a hash-függvény dokumentálva
- [ ] teljes meglévő teszt-suite lefuttatva, regresszió-mentesség bizonyítva
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- AI/LLM-alapú kinyerés a determinisztikus kulcs-/regex-illesztés helyett — TILOS
- új outbox job_type/trigger bevezetése ehelyett, amikor a meglévő `index_turn`
  tranzakción belül a `chunk_id` már elérhető
- `content_hash` üresen hagyása indoklás nélkül
- csak azt bizonyítani, hogy a függvény hibátlanul fut — mind a 4 esetre KONKRÉT,
  idézett SQL-eredmény kell

## Git instrukciók

Push a `feature/session-source-refs-extractor-001` branch-re, KIZÁRÓLAG a
`cic-mcp-session` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni, elég
a lokális commit). Main-re az agent NEM pushol. A teszteléshez használt Docker konténert a
munka végén állítsd le és töröld. **NE módosítsd a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/teszt-nevek angolul.
