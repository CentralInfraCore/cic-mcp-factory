# Job: shared-cross-session-aggregator-implementation-001

## Kontextus

Phase 6 ("Wiring") harmadik kódjobja. A `cic-mcp-shared` repóban MÁR létezik a
`shared_core.candidates` Postgres-schema (`shared-core-storage-implementation-001`,
mergelve) — valós `canonical` CHECK constraint-tel bizonyítva. Ez a job írja meg az
ELSŐ TÉNYLEGES aggregátor-kódot: lekérdezi a `cic-mcp-session` MCP
`search_session_context` tool-ját N session_id-re egy adott keyword-query-vel, a
`shared-cross-session-search-001` riportban definiált session-enkénti min-max
normalizálással összesít, a `shared-weighting-model-001` formulájával súlyt számol, és
beír egy `shared_core.candidates` sort.

**Kritikus határ**: a `cic-mcp-session` MCP-t VALÓS subprocess-szel kell hívni (a
`cic-mcp-gateway/gateway_core/compile_context.py` `SessionServerLaunchConfig`
mintáját követve, file:line idézve) — NEM mockolt session-válasszal. A teszt-fixture
KIZÁRÓLAG szintetikus session-tartalom lehet (ugyanaz a szabály, mint a
`historical-dedupe-idempotency-001`-ben).

## Target

- target repo: `cic-mcp-shared`
- target path: `output/shared-cross-session-aggregator-implementation.md` + a
  aggregátor-kód (a repo Python-struktúrájának megfelelő helyen — NÉZD MEG a repót,
  NE találj ki új konvenciót)
- change_type: `new_capability`
- status_after_merge: `candidate`
- status indoklás: TÉNYLEGES, futtatható kód + valós subprocess MCP hívás + valós
  Postgres-teszt — megfelel a `gateway-session-adapter-contract-001` →
  `session-context-pack-v1-001` mintának

## Sources

- **KÖTELEZŐ elsődleges forrás (a `cic-mcp-factory` repo `main`-jén, MÁR ott van):**
  - `${WORKDIR}/jobs/index.yaml` — prerequisite-ellenőrzéshez `- id: "<job-id>"`
    kulccsal (NEM `job_id:`)
  - `${WORKDIR}/jobs/shared-cross-session-search-001/output/shared-cross-session-
    search.md` — "Cross-Session Query Shape And Ranking" szekció (270. sor körül),
    KÜLÖNÖSEN a 309. sor: "session-enkénti min-max normalizálás, majd egyszerű
    összegzés"
  - `${WORKDIR}/jobs/shared-weighting-model-001/output/shared-weighting-model.md` —
    290-298. sor: a `weight_score` formula (`cross_session_score +
    factory_linkage_bonus + recency_bonus`) ÉS a `recurrence_count >= 2 AND
    weight_score >= THRESHOLD` AND-feltétel
  - `${WORKDIR}/jobs/shared-core-storage-implementation-001/output/shared-core-
    storage-schema.sql` — a TELJES `shared_core.candidates` schema, KÜLÖNÖSEN a
    `candidate_id` (48. sor), `weight_score` (83. sor), `provenance_refs` (105. sor)
    mezők és a `canonical` constraint (63. sor)
- **MÁSODIK forrás (a `cic-mcp-gateway` repo, KLÓNOZVA — ha nincs a
  `workplace.repos`-ban, klónozd magad, KIZÁRÓLAG OLVASÁSRA):**
  - `gateway_core/compile_context.py` — `SessionServerLaunchConfig` (70. sor körül),
    `StdioServerParameters(...)` hívás (97. sor körül) — a subprocess-launch minta,
    amit a `cic-mcp-session` MCP hívásánál KÖVETNI kell
- **HARMADIK forrás (a `cic-mcp-session` repo, KLÓNOZVA a `workplace.repos` révén,
  KIZÁRÓLAG OLVASÁSRA):**
  - `mcp-server/session_server.py` — `search_session_context(session_id, query,
    limit)` (94-95. sor), `get_session_status` (a session-szűréshez)
- **NEGYEDIK forrás (a `cic-mcp-shared` repo, a target):**
  - `cic-mcp-shared/CLAUDE.md` — "Trust modell", "Fő határok"

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. Prerequisite-ellenőrzés

```
grep -n '\- id: "shared-cross-session-search-001"' -A 3 jobs/index.yaml
grep -n '\- id: "shared-weighting-model-001"' -A 3 jobs/index.yaml
grep -n '\- id: "shared-core-storage-implementation-001"' -A 3 jobs/index.yaml
```

Idézd a kimenetet, erősítsd meg mindhárom `status: "done"`. Ha NEM, NO-GO és állj meg.

### 2. MCP subprocess-launch — grep + minta-követés

```
grep -rn "class SessionServerLaunchConfig\|StdioServerParameters(" --include="*.py" . | grep -v test_
```

(ezt a `cic-mcp-gateway` klónban futtasd) — idézd a kimenetet, és a saját aggregátor
kódodban KÖVESD EZT A MINTÁT a `cic-mcp-session` `mcp-server/session_server.py`
elindítására (subprocess + stdio MCP handshake), NEM mockolt session-választ.

### 3. Aggregátor-implementáció

Írj egy függvényt/modult, amely:
- bemenetként kap egy `keyword_description` query-t és egy `session_id` listát
- minden `session_id`-re HÍVJA a `search_session_context(session_id, query, limit)`
  MCP tool-t (valós subprocess-en keresztül)
- a `shared-cross-session-search-001` 309. sora szerint session-enkénti min-max
  normalizálást végez a kapott pontszámokon, majd összegzi
- a `shared-weighting-model-001` 290-298. sora szerint kiszámolja a `weight_score`-t
  (`cross_session_score + factory_linkage_bonus + recency_bonus`) és a
  `recurrence_count`-ot (hány session-ben volt nem-nulla normalizált relevancia)
- beír egy sort a `shared_core.candidates` táblába (`insert`, a meglévő schema
  mezőivel — `candidate_id` auto-generált, `weight_score`, `recurrence_count`,
  `provenance_refs` JSONB a session/chunk pointerekkel)

### 4. Valós, futtatott bizonyíték

Hozz létre N (legalább 2) SZINTETIKUS session-fixture-t a `cic-mcp-session` Postgres
ellen (KIZÁRÓLAG fabrikált tartalom, ugyanaz a szabály mint a
`historical-dedupe-idempotency-001`-ben), futtasd végig az aggregátort egy valós,
subprocess-szel indított `cic-mcp-session` MCP szerver ellen, és bizonyítsd VALÓS
Postgres-lekérdezéssel, hogy egy `shared_core.candidates` sor létrejött, nem-triviális
`weight_score`-ral és `recurrence_count >= 2`-vel. Idézd a TÉNYLEGES psql/pytest
kimenetet.

## Nem cél

- a `shared_core.candidates` schema módosítása (ÉPÍTS a meglévőre)
- a `weight_score`/`recurrence_count` formula újradefiniálása (idézd, ne találd ki
  újra)
- canonical promotion vagy emberi review-folyamat implementálása
- `historical-import-runner-001` (másik Phase 6 job)

## Required Output Files

- `output/shared-cross-session-aggregator-implementation.md`
- az aggregátor-kód fájlja(i)

## Required Report Sections

```markdown
# shared-cross-session-aggregator-implementation-001 Output

## Scope
## Inputs Read
## Prerequisite Check
## MCP Subprocess Launch Pattern (Real, Not Mocked)
## Aggregator Implementation
## Synthetic Multi-Session Test Fixture
## Real Postgres + Real MCP Subprocess Proof
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
`proven` egy "a `weight_score` helyesen számolódik" állításra KIZÁRÓLAG akkor
használható, ha a TÉNYLEGES, futtatott teszt kimenete (a tényleges számértékkel)
idézve van — a formula leírása a kódban nem bizonyítja, hogy helyesen fut.

## Definition Of Done

- [ ] mindhárom prerequisite `id:` kulccsal megerősítve, GO/NO-GO döntés indokolva
- [ ] az aggregátor VALÓS subprocess-szel hívja a `cic-mcp-session` MCP-t, file:line
      hivatkozással a `SessionServerLaunchConfig` mintára
- [ ] `weight_score`/`recurrence_count` a `shared-weighting-model-001` formuláját
      pontosan követi, file:line hivatkozással
- [ ] szintetikus, fabrikált multi-session fixture, valós tartalom nélkül
- [ ] valós Postgres + valós MCP subprocess teszt: legalább egy `shared_core.
      candidates` sor létrejön, `recurrence_count >= 2`, nem-triviális `weight_score`
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- mockolt/stubbolt `cic-mcp-session` MCP-válasz a valós subprocess helyett
- a súlyozási formula újra-kitalálása a `shared-weighting-model-001` idézése helyett
- valós, személyes session-tartalom használata a teszt-fixture-ökben
- a fájl/kód léte ≠ implemented (ez egyetlen soron) — a futtatott teszt kimenete
  bizonyít, a kód megírása nem

## Git instrukciók

Push a `feature/shared-cross-session-aggregator-implementation-001` branch-re,
KIZÁRÓLAG a `cic-mcp-shared` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell
pusholni, elég a lokális commit; a `cic-mcp-session` klónba SEMMIT nem szabad
commitolni/pusholni — KIZÁRÓLAG olvasásra van). Main-re az agent NEM pushol. **NE
módosítsd a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek/kód angolul.
