# Job: gateway-context-pack-production-wiring-001

## Kontextus

Phase 6 ("Wiring") negyedik kódjobja. A `gateway_core/compile_context.py`
`compile_context()` függvény (`session-context-pack-v1-001`, megerősítve
`gateway-compile-context-test-hardening-001`-ben) MÁR létezik, MÁR tesztelt valós
Postgres ellen — DE jelenleg **NULLA production caller** van rá: KIZÁRÓLAG a saját
modulja és a `tests/test_gateway_core/test_compile_context.py` hívja. A
`cic-mcp-gateway` repo MÉG NEM rendelkezik semmilyen gateway-specifikus
"agent-facing context API"-val (`architecture.md` "cic-mcp-gateway" "Igen" lista) —
a repóban jelenleg KIZÁRÓLAG a `base-repo` öröklött, generikus `mcp-server/server.py`
KB-szerver létezik (cic-graph stílusú, nem gateway-specifikus).

Ez a job EZT a hiányt zárja: létrehoz egy ÚJ, gateway-specifikus MCP szervert
(`mcp-server/gateway_server.py`, a `cic-mcp-session`-ben már bevált
`mcp-server/session_server.py` szétválasztási minta szerint — KÜLÖN modul, NEM a
generikus KB-szerver módosítása), amely EGY `@mcp.tool()` tool-t exponál, ami
TÉNYLEGESEN hívja a `compile_context()`-et. Ez a TÉNYLEGES "production call site".

**Kritikus határ**: NEM kell valós, tartós production Postgres-instance — a wiring
bizonyítása egy disposable teszt-Postgres ellen történik (ugyanaz a bizonyítási szint,
mint a `gateway-compile-context-test-hardening-001`-ben). A cél a CALL CHAIN
megléte és bizonyítása, NEM a deployment.

## Target

- target repo: `cic-mcp-gateway`
- target path: `output/gateway-context-pack-production-wiring.md` + ÚJ
  `mcp-server/gateway_server.py` fájl + a hozzá tartozó teszt
- change_type: `enhancement`
- status_after_merge: `candidate`
- status indoklás: TÉNYLEGES, futtatható kód + valós Postgres-teszt a TELJES láncon
  (MCP tool → `compile_context()` → session subprocess → Postgres) — megfelel a
  `gateway-session-adapter-contract-001` → `session-context-pack-v1-001` mintának

## Sources

- **KÖTELEZŐ elsődleges forrás (a `cic-mcp-factory` repo `main`-jén, MÁR ott van):**
  - `${WORKDIR}/jobs/index.yaml` — prerequisite-ellenőrzéshez `- id: "<job-id>"`
    kulccsal (NEM `job_id:`)
  - `${WORKDIR}/.cic-context/factory-docs/architecture.md` — "cic-mcp-gateway"
    "Igen" lista (56-65. sor körül): "agent-facing context API"
- **MÁSODIK forrás (a `cic-mcp-gateway` repo, a target, KLÓNOZVA):**
  - `gateway_core/compile_context.py` — `compile_context()` (354. sor körül),
    TELJES szignatúra és docstring (`session_id`, `repo_root`, `max_chunks`,
    `python_executable` paraméterek)
  - `tests/test_gateway_core/test_compile_context.py` — a TELJES teszt-harness
    (`pg_config`, `seeded_session_id`, `session_repo_root` fixture-ök, 53-200. sor
    körül) — EZT A MINTÁT kell követni az új teszthez, NEM újra feltalálni
  - `mcp-server/server.py` — a generikus KB-szerver (CSAK referenciaként, hogy lásd
    a FastMCP-induló mintát — EZT NE módosítsd)
  - `CLAUDE.md` — "Jelenlegi állapot" (jelenleg "nincs még gateway-specifikus
    implementáció" — ezt a riportodban frissítendő állításként kezeld, ha az ÚJ tool
    megépül)
- **HARMADIK forrás (a `cic-mcp-session` repo, KLÓNOZVA a `workplace.repos` révén,
  KIZÁRÓLAG OLVASÁSRA):**
  - `mcp-server/session_server.py` — a docstring TOP-je (1-20. sor körül): a
    "KÜLÖN modul, NEM a generikus KB-szerver módosítása" szétválasztási minta,
    amit a gateway-ben is követni kell

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. Prerequisite-ellenőrzés

```
grep -n '\- id: "session-context-pack-v1-001"' -A 3 jobs/index.yaml
grep -n '\- id: "gateway-compile-context-test-hardening-001"' -A 3 jobs/index.yaml
```

Idézd a kimenetet, erősítsd meg mindkettő `status: "done"`. Ha NEM, NO-GO és állj meg.

### 2. ÚJ gateway-specifikus MCP szerver — call site

Először GREP-pel erősítsd meg a `compile_context()` tényleges szignatúráját és a
meglévő teszt-harness fixture-öket (teszt-fájlok kizárva, bár ezen a két fájlon ez
részben no-op, mert maguk a tesztek a referencia):

```
grep -n "^def compile_context" -A 15 gateway_core/compile_context.py
grep -n "^def pg_config\|^def seeded_session_id\|^def session_repo_root" -A 3 tests/test_gateway_core/test_compile_context.py
```

Idézd a kimenetet. Hozz létre egy ÚJ `mcp-server/gateway_server.py` fájlt (KÜLÖN
modul, NE módosítsd a meglévő `mcp-server/server.py`-t), amely:
- létrehoz egy SAJÁT FastMCP instance-t (pl. `"cic-gateway"` néven, NEM `"cic-graph"`)
- exponál EGY `@mcp.tool()` tool-t, pl. `get_gateway_context_pack(session_id: str,
  session_repo_root: str, max_chunks: int = 50) -> dict`, amely KÖZVETLENÜL hívja a
  `gateway_core.compile_context.compile_context()`-et (importálva, NEM
  reimplementálva)

### 3. Valós, futtatott bizonyíték — TELJES lánc

Írj egy tesztet (pl. `tests/test_mcp_server/test_gateway_server.py`), amely a
`test_compile_context.py` MEGLÉVŐ fixture-mintáját követve (`pg_config`,
`seeded_session_id`, `session_repo_root`):
- indítja az ÚJ `mcp-server/gateway_server.py`-t VALÓS subprocess-ként (stdio MCP
  handshake, a `compile_context.py`-ban már bevált `StdioServerParameters` minta
  szerint)
- meghívja a `get_gateway_context_pack` tool-t egy VALÓS, seedelt session-re
- bizonyítja, hogy a visszakapott `GatewayContextEnvelope`-ban VAN legalább egy
  `:chunk:`-ref note (NEM csak egy összegző status-note — UGYANAZ a szigorítási
  mérce, mint a `gateway-compile-context-test-hardening-001`-ben)

Idézd a TÉNYLEGES pytest-futás kimenetét.

## Nem cél

- valós, tartós production Postgres-instance felállítása vagy deploy-olása
- a `compile_context()` függvény módosítása (ÉPÍTS rá, ne írd újra)
- a meglévő `mcp-server/server.py` (generikus KB-szerver) módosítása
- `shared_memory_notes`/cic-mcp-shared bekötése a gateway-be (külön job tárgya)

## Required Output Files

- `output/gateway-context-pack-production-wiring.md`
- `mcp-server/gateway_server.py`
- a hozzá tartozó teszt-fájl

## Required Report Sections

```markdown
# gateway-context-pack-production-wiring-001 Output

## Scope
## Inputs Read
## Prerequisite Check
## New Gateway MCP Server — Call Site
## Real Postgres + Real Subprocess Proof
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
`proven` egy "a tool TÉNYLEGESEN hívja a `compile_context()`-et" állításra
KIZÁRÓLAG akkor használható, ha a TÉNYLEGES `file:line` hívás-hely idézve van ÉS egy
valós, futtatott teszt bizonyítja a teljes láncot — a függvény importálása/
megemlítése nem bizonyítja a tényleges hívást.

## Definition Of Done

- [ ] mindkét prerequisite `id:` kulccsal megerősítve, GO/NO-GO döntés indokolva
- [ ] ÚJ `mcp-server/gateway_server.py`, KÜLÖN modulként (NEM a generikus KB-szerver
      módosítása), `compile_context()`-et TÉNYLEGESEN hívó tool-lal, file:line idézve
- [ ] valós, futtatott teszt: subprocess + stdio MCP handshake + valós Postgres,
      legalább egy `:chunk:`-ref note bizonyítva (nem csak status-note)
- [ ] claim-evidence tábla kitöltve, nem üres
- [ ] a riport NEM állítja, hogy valós production Postgres-instance létezik

## Forbidden Shortcuts

- a `compile_context()` megemlítése/importálása file:line hívás-hely és valós teszt
  nélkül "bekötöttnek" állítva
- a meglévő `mcp-server/server.py` (generikus KB-szerver) módosítása az ÚJ tool
  hozzáadásához (KÜLÖN modul kell)
- valós, tartós production Postgres-instance létezésének állítása
- a fájl/kód léte ≠ implemented (ez egyetlen soron) — a futtatott teszt kimenete
  bizonyít, a kód megírása nem

## Git instrukciók

Push a `feature/gateway-context-pack-production-wiring-001` branch-re, KIZÁRÓLAG a
`cic-mcp-gateway` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni,
elég a lokális commit; a `cic-mcp-session` klónba SEMMIT nem szabad
commitolni/pusholni — KIZÁRÓLAG olvasásra van). Main-re az agent NEM pushol. **NE
módosítsd a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek/kód angolul.
