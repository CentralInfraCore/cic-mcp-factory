# Job: session-mcp-tools-001

## Kontextus

Minden korábbi `session_api.*` job riportja (vector-search, hybrid-search,
source-refs-api) ugyanazt a hiányt jelezte: a stabil SQL függvény LÉTEZIK és
TESZTELT, de SEMMI nem teszi elérhetővé egy MCP klienshez — a reachability
`missing`/`scaffold` marad.

**Fontos, a repóban már létező, de FÉLREVEZETŐ tény**: a `mcp-server/server.py` fájl
NEM egy session-specifikus MCP szerver — ez a `cic-graph` KB-gráf szerver (token-
keresés, node-lookup, focus_pack stb.), ami EGY EGÉSZEN MÁS, a `session_api`-tól
teljesen független koncepció. **NE módosítsd ezt a fájlt** — ez nem tartozik ehhez a
jobhoz.

Ez a job az ELSŐ session-specifikus MCP szervert hozza létre — egy ÚJ fájlban —, és
ABBAN regisztrálja az ELSŐ session_api MCP tool-t.

## Target

- target repo: `cic-mcp-session`
- target path: ÚJ fájl, pl. `mcp-server/session_server.py` (a meglévő `server.py`
  MELLÉ, nem helyette)
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: egyetlen tool, kis fixture-rel bizonyítva — `candidate`-hez több
  tool és valós session-adaton végzett kiértékelés kellene

## Sources

- `${WORKDIR}/.cic-context/factory-docs/job-slices.yaml` — `session-mcp-tools-001`
  bejegyzés — NORMATÍV
- **KÖTELEZŐ elsődleges forrás (mind már a `cic-mcp-session` `main`-en van):**
  - `cic-mcp-session/mcp-server/server.py` — a `cic-graph` szerver STÍLUSMINTÁJA
    (`FastMCP(...)` inicializálás, `@mcp.tool()` dekorátor-minta, `main()` belépési
    pont) — KÖVESD ezt a mintát, de ÚJ szervernév-vel (pl. `FastMCP("cic-session")`,
    NEM `"cic-graph"`), és NE importálj/módosíts semmit a KB-gráf logikájából
  - `cic-mcp-session/output/session-hybrid-search-api-migration.sql` —
    `session_api.search_context_hybrid(p_session_id UUID, p_query TEXT,
    p_query_embedding VECTOR(384), p_limit INTEGER DEFAULT 20)` — EZT a függvényt
    hívd meg, NE írd újra az RRF-logikát
  - `cic-mcp-session/session_store/vector_search.py` — `embed_query()` (a
    `p_query_embedding` paraméter előállításához), `to_pgvector_literal()`
  - `cic-mcp-session/session_store/envelope_writer.py` — `SessionStoreConfig.from_env()`
    (a DB-kapcsolat forrása — NINCS hardcode-olt connection string)
  - `cic-mcp-session/tests/test_session_store/test_hybrid_search.py` — a 3-chunk-os
    RRF fixture (lexikális-csak egyezés, szemantikai-csak egyezés, irreleváns kontroll)
    — ezt a fixture-t HASZNÁLD FEL ÚJRA, NE alkoss újat
  - `cic-mcp-session/tests/test_tools/test_mcp_server.py` — minta arra, hogy a
    `@mcp.tool()`-dekorált függvény a dekorátor ELLENÉRE simán hívható direktben
    Python-ból (`mcp_server.search_query(...)`) — de EZ a job megköveteli, hogy a
    TÉNYLEGES MCP dispatch-útvonalat (`mcp.list_tools()`, `mcp.call_tool()`) IS
    bizonyítsd, nem csak a direkt függvényhívást

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti KÖTELEZŐ forrásokat, MIELŐTT bármilyen kódot írnál

## Feladat

### 1. Valódi Postgres teszt-instance + teljes lánc alkalmazása

Indíts egy valódi Postgres instance-t (`pgvector/pgvector:pg16`, lokálisan cache-elve), és
alkalmazd EGYMÁS UTÁN az összes meglévő SQL fájlt (mind a 6: schema + 5 migráció).
**Egyfordulós végrehajtási fegyelem**: fejezd be a teljes munkát egyetlen menetben.

### 2. ÚJ MCP szerver modul, EGYETLEN tool-lal

Hozz létre egy ÚJ fájlt (pl. `mcp-server/session_server.py`):
- `FastMCP("cic-session")` (vagy hasonló, EGYEDI névvel, NEM `"cic-graph"`)
- DB-kapcsolat: `SessionStoreConfig.from_env()` — env-vezérelt, nincs hardcode
- EGYETLEN `@mcp.tool()` dekorált függvény (pl. `search_session_context(session_id:
  str, query: str, limit: int = 20) -> list[dict]`), ami:
  - `embed_query(query)`-vel előállítja az embeddinget, `to_pgvector_literal()`-lel
    formázza
  - meghívja `session_api.search_context_hybrid(p_session_id, p_query,
    p_query_embedding, p_limit)`-et psycopg-vel
  - visszaadja a sorokat dict-listaként (`chunk_id`, `turn_id`, `text`, `fused_score`)
- NEM írja újra az RRF-logikát — KIZÁRÓLAG a meglévő SQL függvényt hívja

### 3. Kétszintű reachability bizonyítás (KÖTELEZŐ mindkettő)

- **(a) Direkt függvényhívás**: hívd meg `search_session_context(...)`-et direktben
  Python-ból (a dekorátor ezt nem akadályozza, lásd `test_mcp_server.py` minta), a
  3-chunk-os RRF fixture-rel feltöltött valódi Postgres ellen — idézd a visszaadott
  listát
- **(b) TÉNYLEGES MCP dispatch-útvonal**: bizonyítsd `mcp.list_tools()` (async, pl.
  `asyncio.run(mcp.list_tools())`) kimenetével, hogy a tool TÉNYLEG regisztrálva van,
  ÉS hívd meg `mcp.call_tool(...)`-pal (vagy az ekvivalens async API-val) is — ez az
  ÉLES MCP-dispatch útvonal, nem csak a meztelen Python függvény. Idézd ennek a
  kimenetét is.

Mindkét hívás UGYANAZT a fúzionált rangsort kell visszaadja, mint a
`session-hybrid-search-api-001` riportjában dokumentált eredmény (Chunk A és B Chunk C
fölött).

### 4. Regresszió-ellenőrzés

Futtasd le a TELJES meglévő `tests/test_session_store/` suite-ot, bizonyítva hogy semmi
nem regresszált.

### 5. Explicit "nincs deploy-olva" kijelentés

A riportban EXPLICIT mondd ki: ez a job NEM köti be az új szervert a
`.mcp.json.tpl`-be vagy bármilyen éles Claude Code konfigba — az élesítés/regisztráció
külön, jövőbeli döntés.

## Nem cél

- a `.mcp.json.tpl` bővítése, vagy bármilyen éles MCP-kliens-konfig módosítása
- a meglévő `mcp-server/server.py` (cic-graph KB szerver) módosítása — TELJESEN
  független koncepció, NE nyúlj hozzá
- további session_api függvények (search_context, get_timeline, get_context_pack,
  session_status, search_context_vector, get_source_refs) tool-osítása — ez csak
  `search_context_hybrid`-re szól, a többi jövőbeli job
- multi-tool szerver, autentikáció, rate-limiting

## Required Output Files

- `output/session-mcp-tools-report.md`

## Required Report Sections

```markdown
# session-mcp-tools-001 Output

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
Postgres ellen, ÉS a (b) pontban a tényleges MCP dispatch-útvonalon keresztül. A
függvény léte a fájlban ≠ MCP-n keresztül elérhető — csak a tényleges
`mcp.call_tool()` hívás bizonyít MCP-reachability-t.

## Definition Of Done

- [ ] `mcp-server/session_server.py` létrejött, `FastMCP("cic-session")` (vagy
      egyedi név), fájl:sor hivatkozással
- [ ] `search_session_context()` (vagy hasonló) létezik, a meglévő
      `search_context_hybrid()` SQL függvényt hívja, nem ír újra RRF-logikát
- [ ] direkt függvényhívás bizonyítva, kimenet idézve
- [ ] `mcp.list_tools()` kimenete idézve, a tool regisztrálva látható
- [ ] `mcp.call_tool()` (vagy ekvivalens) tényleges MCP dispatch-hívás bizonyítva,
      kimenet idézve
- [ ] mindkét hívási mód UGYANAZT a fúzionált rangsort adja, mint a
      `session-hybrid-search-api-001` riport
- [ ] a meglévő `mcp-server/server.py` ÉRINTETLEN
- [ ] teljes meglévő teszt-suite lefuttatva, regresszió-mentesség bizonyítva
- [ ] explicit "nincs deploy-olva/`.mcp.json.tpl`-be kötve" kijelentés a riportban
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- csak a meztelen Python függvényt hívni és azt állítani, hogy "az MCP tool működik" —
  a TÉNYLEGES `mcp.list_tools()`/`mcp.call_tool()` dispatch-útvonalat is bizonyítani
  kell
- `search_context_hybrid` RRF-logikájának Python-beli újraírása a meglévő SQL függvény
  hívása helyett
- a meglévő `mcp-server/server.py` (cic-graph KB szerver) módosítása — TILOS, nincs
  köze ehhez a jobhoz
- azt állítani, hogy ez bárhol éles MCP-kliens-konfigba bekötve van, amikor nincs

## Git instrukciók

Push a `feature/session-mcp-tools-001` branch-re, KIZÁRÓLAG a `cic-mcp-session`
célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni, elég a lokális
commit). Main-re az agent NEM pushol. A teszteléshez használt Docker konténert a munka
végén állítsd le és töröld. **NE módosítsd a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/teszt-nevek angolul.
