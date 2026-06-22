# Job: session-mcp-tools-remaining-001

## Kontextus

A `session-mcp-tools-001` job létrehozta az ELSŐ session-specifikus MCP szervert
(`mcp-server/session_server.py`, `FastMCP("cic-session")`) EGYETLEN tool-lal
(`search_session_context`, a `session_api.search_context_hybrid()`-et hívja). A
mintát kétszintű reachability-bizonyítással (direkt függvényhívás + tényleges
`mcp.list_tools()`/`mcp.call_tool()` dispatch) validálta.

Ez a job BŐVÍTI a MEGLÉVŐ `session_server.py`-t (NEM új fájl, NEM a meglévő tool
átírása) a `session_api` réteg MARADÉK 6 függvényére, UGYANAZT a vékony wrapper-mintát
követve:
1. `search_context` (FTS-only)
2. `search_context_vector` (vektor-only)
3. `get_timeline`
4. `get_context_pack`
5. `session_status`
6. `get_source_refs`

## Target

- target repo: `cic-mcp-session`
- target path: `mcp-server/session_server.py` (a MEGLÉVŐ fájl bővítése, a meglévő
  `search_session_context` tool ÉRINTETLEN marad)
- change_type: `enhancement`
- status_after_merge: `experimental`
- status indoklás: a meglévő, kis fixture-ökkel bizonyítva — `candidate`-hez valós
  session-adaton végzett kiértékelés kellene minden függvényre

## Sources

- `${WORKDIR}/.cic-context/factory-docs/job-slices.yaml` —
  `session-mcp-tools-remaining-001` bejegyzés — NORMATÍV
- **KÖTELEZŐ elsődleges forrás (mind már a `cic-mcp-session` `main`-en van):**
  - `cic-mcp-session/mcp-server/session_server.py` — a MEGLÉVŐ minta
    (`search_session_context` implementációja) — KÖVESD PONTOSAN ugyanezt a
    struktúrát (psycopg + `SessionStoreConfig.from_env()`, dict-lista visszatérés,
    `@mcp.tool()` dekorátor) mind a 6 ÚJ tool-nál
  - `cic-mcp-session/output/session-retrieval-quality-migration.sql` —
    `session_api.search_context(p_session_id, p_query, p_limit=20)` →
    `chunk_id, turn_id, text, rank`; `session_api.session_status(p_session_id)` →
    `session_id, status, started_at, last_seen_at, pending_jobs`
  - `cic-mcp-session/output/session-postgres-schema.sql` —
    `session_api.get_timeline(p_session_id, p_limit=100)` →
    `turn_id, occurred_at, role, turn_seq`; `session_api.get_context_pack(p_session_id,
    p_max_chunks=50)` → `chunk_id, turn_seq, text`
  - `cic-mcp-session/output/session-vector-search-api-migration.sql` —
    `session_api.search_context_vector(p_session_id, p_query_embedding VECTOR(384),
    p_limit=20)` → `chunk_id, turn_id, text, similarity`
  - `cic-mcp-session/output/session-source-refs-api-migration.sql` —
    `session_api.get_source_refs(p_session_id, p_ref_kind=NULL, p_limit=100)` →
    `source_ref_id, chunk_id, turn_id, ref_kind, ref_value, content_hash`
  - `cic-mcp-session/tests/test_session_store/test_session_api.py` —
    `_call_get_timeline`/`_call_get_context_pack` minta, és a
    `test_get_timeline_returns_turns_in_turn_seq_order`/
    `test_get_context_pack_returns_chunks_in_turn_seq_then_chunk_seq_order`
    fixture-jei (`search_context`/`session_status` fixture-jei is itt vannak) — EZEKET
    HASZNÁLD FEL, NE alkoss új fixture-öket
  - `cic-mcp-session/tests/test_session_store/test_vector_search.py` —
    `search_context_vector` meglévő fixture-je
  - `cic-mcp-session/tests/test_session_store/test_session_source_refs_api.py` —
    `get_source_refs` meglévő, két-session-es fixture-je

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti KÖTELEZŐ forrásokat, MIELŐTT bármilyen kódot írnál

## Feladat

### 1. Valódi Postgres teszt-instance + teljes lánc alkalmazása

Indíts egy valódi Postgres instance-t (`pgvector/pgvector:pg16`, lokálisan cache-elve), és
alkalmazd EGYMÁS UTÁN az összes meglévő SQL fájlt (mind a 6: schema + 5 migráció).
**Egyfordulós végrehajtási fegyelem**: fejezd be a teljes munkát egyetlen menetben.

### 2. Hat ÚJ MCP tool a MEGLÉVŐ session_server.py-ban

Add hozzá MIND A 6 tool-t (a meglévő `search_session_context` MELLÉ, azt nem
módosítva), ugyanazt a vékony wrapper-mintát követve (psycopg hívás a meglévő SQL
függvényre, `SessionStoreConfig.from_env()`, dict-lista visszatérés):
- `search_session_context_fts(session_id, query, limit=20)` → `search_context`
- `search_session_context_vector(session_id, query, limit=20)` →
  `search_context_vector` (a query-t `embed_query()`+`to_pgvector_literal()`-lel
  konvertálva, ÚJRAHASZNÁLVA a meglévő `session_server.py` import-ját)
- `get_session_timeline(session_id, limit=100)` → `get_timeline`
- `get_session_context_pack(session_id, max_chunks=50)` → `get_context_pack`
- `get_session_status(session_id)` → `session_status`
- `get_session_source_refs(session_id, ref_kind=None, limit=100)` → `get_source_refs`

SEMMILYEN SQL-logikát (FTS, vektor, provenance-join) NEM írhatsz újra Python-ban —
KIZÁRÓLAG a meglévő SQL függvényeket hívod.

### 3. Kétszintű reachability bizonyítás MIND A 6 ÚJ tool-ra

Minden ÚJ tool-ra KÖTELEZŐ mindkettő:
- **(a) Direkt függvényhívás**: a megfelelő meglévő teszt-fixture (lásd Sources) ellen,
  valódi Postgres-en — idézd a kimenetet
- **(b) TÉNYLEGES MCP dispatch**: `mcp.list_tools()` mutassa MIND A 7 tool-t
  (a meglévő `search_session_context` + a 6 új), ÉS `mcp.call_tool()` (vagy
  ekvivalens) hívja meg MINDEN ÚJ tool-t — idézd a kimenetet mindegyikre

Minden tool eredménye EGYEZZEN a megfelelő forrás-job riportjában dokumentált
eredménnyel (pl. `get_source_refs`-nél a `session-source-refs-api-001` riport NULL-
filter/kind-filter/session-scoping eseteivel).

### 4. Regresszió-ellenőrzés

Futtasd le a TELJES meglévő `tests/test_session_store/` suite-ot, bizonyítva hogy
semmi nem regresszált, ÉS hogy a meglévő `search_session_context` tool (a
`session-mcp-tools-001` job munkája) változatlanul működik.

### 5. Explicit "nincs deploy-olva" kijelentés

A riportban EXPLICIT mondd ki: ez a job NEM köti be a szervert a `.mcp.json.tpl`-be
vagy bármilyen éles Claude Code konfigba.

### 6. Reachability ellenőrzés (kötelező)

```bash
grep -rn "search_session_context_fts\|search_session_context_vector\|get_session_timeline\|get_session_context_pack\|get_session_status\|get_session_source_refs" --include="*.py" . | grep -v "test_" | grep -v "/tests/"
```

`file:line` hivatkozással minden találatra. Dokumentáld explicit: a tool-ok LÉTEZÉSE a
fájlban és a sikeres `mcp.call_tool()` hívás KÉT KÜLÖNÁLLÓ állítás a "VALAMELYIK
orchestrátor/gateway/kliens TÉNYLEG ezt a szervert indítja production-ben" állítástól —
az utóbbi `missing`, mert a `.mcp.json.tpl`-be nincs bekötve. A tool létezése a
fájlban ≠ működik MCP-n keresztül — csak a tényleges `mcp.call_tool()` hívás bizonyít.

## Nem cél

- a `.mcp.json.tpl` bővítése, vagy bármilyen éles MCP-kliens-konfig módosítása
- a meglévő `mcp-server/server.py` (cic-graph KB szerver) módosítása
- a meglévő `search_session_context` tool átírása/módosítása
- multi-tool szerver autentikáció, rate-limiting
- bármelyik SQL függvény logikájának módosítása/javítása (ez a job KIZÁRÓLAG vékony
  wrapper-eket ad hozzá, a függvények már léteznek és teszteltek)

## Required Output Files

- `output/session-mcp-tools-remaining-report.md`

## Required Report Sections

```markdown
# session-mcp-tools-remaining-001 Output

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
`proven` KIZÁRÓLAG akkor használható, ha a tényleges hívás kimenete idézve van — valódi
Postgres ellen, ÉS a tényleges MCP dispatch-útvonalon keresztül mind a 6 ÚJ tool-ra. A
tool léte a fájlban ≠ MCP-n keresztül elérhető.

## Definition Of Done

- [ ] mind a 6 ÚJ tool létrejött a MEGLÉVŐ `session_server.py`-ban, fájl:sor
      hivatkozással mindegyikre
- [ ] a meglévő `search_session_context` tool ÉRINTETLEN
- [ ] mind a 6 ÚJ tool-ra: direkt függvényhívás bizonyítva, kimenet idézve
- [ ] `mcp.list_tools()` kimenete mutatja MIND A 7 tool-t, idézve
- [ ] mind a 6 ÚJ tool-ra: `mcp.call_tool()` tényleges dispatch-hívás bizonyítva,
      kimenet idézve
- [ ] minden tool eredménye egyezik a forrás-job riportjával
- [ ] a meglévő `mcp-server/server.py` ÉRINTETLEN
- [ ] teljes meglévő teszt-suite lefuttatva, regresszió-mentesség bizonyítva
- [ ] explicit "nincs deploy-olva" kijelentés a riportban
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- csak a meztelen Python függvényeket hívni és azt állítani, hogy "az MCP tool-ok
  működnek" — a TÉNYLEGES `mcp.list_tools()`/`mcp.call_tool()` dispatch-útvonalat
  MINDEGYIKRE bizonyítani kell
- bármelyik SQL függvény logikájának (FTS, vektor, RRF, provenance-join) Python-beli
  újraírása
- új fixture-ök kitalálása, amikor egy korábbi jobból már van bizonyított fixture
  ugyanarra a függvényre
- a meglévő `mcp-server/server.py` vagy a meglévő `search_session_context` tool
  módosítása

## Git instrukciók

Push a `feature/session-mcp-tools-remaining-001` branch-re, KIZÁRÓLAG a
`cic-mcp-session` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni,
elég a lokális commit). Main-re az agent NEM pushol. A teszteléshez használt Docker
konténert a munka végén állítsd le és töröld. **NE módosítsd a `meta.yaml` `status`
mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/teszt-nevek angolul.
