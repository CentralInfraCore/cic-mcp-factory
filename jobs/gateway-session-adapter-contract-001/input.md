# Job: gateway-session-adapter-contract-001

## Kontextus

Phase 1B (gateway baseline + `GatewayContextEnvelope` schema + source registry schema)
lezárva. Ez az ELSŐ Phase 2 job: definiálja, HOGYAN fordítaná a gateway a
`cic-mcp-session` forrást egy `GatewayContextEnvelope`-ba — KONTRAKTUS-szinten, NEM
implementáció. A `GatewayContextEnvelope.session_derived_notes[]` mező MÁR rögzítve van
(`content`, `trust` ∈ {`session_local`, `session_derived`}, `ref`), és a source registry
MÁR tartalmaz egy `cic-mcp-session` bejegyzést — ez a job EZEKET köti össze a `cic-mcp-session`
TÉNYLEGES MCP API-jával.

**Kritikus határ** (`forbidden_shortcuts` a job-slices.yaml-ban): a gateway-adapter a
`cic-mcp-session` MCP tool-jain KERESZTÜL érné el az adatot (`mcp-server/session_server.py`
7 tool-ja), SOHA nem direkt SQL/tábla-hozzáféréssel — ez a `cic-mcp-session` saját trust
modelljének (`canonical: false`, `default_scope: session_id`) megőrzése miatt kötelező
határ, nem stiláris preferencia.

## Target

- target repo: `cic-mcp-gateway`
- target path: `output/gateway-session-adapter-contract.md` (ÚJ fájl — ELLENTÉTBEN a
  két korábbi Phase 1B jobbal, EBBEN a jobban NINCS külön `.schema.yaml` fájl, csak a
  riport — a job-slices.yaml `output_files` listája egyetlen fájlt ír elő)
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: kontraktus-riport, nincs futtatható adapter-kód — `candidate`-hez egy
  tényleges adapter-implementáció (külön job) és legalább egy valós
  `compile_context`-hívás kellene

## Sources

- `${WORKDIR}/.cic-context/factory-docs/execution-phases.md` — "Phase 2" szekció —
  NORMATÍV
- `${WORKDIR}/.cic-context/factory-docs/architecture.md` — "Fő határok" szekció
- **KÖTELEZŐ elsődleges forrás (a `cic-mcp-gateway` repo `main`-jén):**
  - `cic-mcp-gateway/output/gateway-context-envelope.schema.yaml` — a
    `session_derived_notes[]` property (`content`/`trust`/`ref` mezők, `trust` enum)
  - `cic-mcp-gateway/output/gateway-source-registry.schema.yaml` — a `cic-mcp-session`
    bejegyzés mezői (`query_capabilities`, `returns_trust_envelope` stb.)
  - `cic-mcp-gateway/output/gateway-context-envelope-contract.md` — a "Separation From
    Source-Specific MCP APIs" szekció (a meglévő elv, amit ez a job konkretizál)
- **KÖTELEZŐ MÁSODIK forrás (a `cic-mcp-session` repo, KLÓNOZVA ehhez a jobhoz,
  KIZÁRÓLAG OLVASÁSRA — NE módosítsd):**
  - `cic-mcp-session/mcp-server/session_server.py` — a 7 MCP tool TÉNYLEGES szignatúrája
    (különösen `get_session_context_pack(session_id, max_chunks)`,
    `get_session_status(session_id)`, `get_session_source_refs(...)`) — idézz konkrét
    `file:line` hivatkozást MINDEN tool-hívásra amit az adapter-kontraktus felhasznál
  - `cic-mcp-session/CLAUDE.md` — trust modell (`canonical: false`,
    `default_scope: session_id`, `cross_session: false`)

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. Adapter input/output kontraktus — tényleges MCP tool-hívásokra hivatkozva

Dokumentáld PONTOSAN, mely `cic-mcp-session` MCP tool(oka)t hívná az adapter, milyen
paraméterekkel, és a visszatérési értéket HOGYAN fordítaná
`session_derived_notes[]`/`refs[]` bejegyzésekre. MINDEN állításhoz idézd a
`mcp-server/session_server.py` konkrét `file:line` szignatúráját — NE találd ki a tool
paramétereit emlékezetből.

### 2. Trust mapping

Térképezd fel: a `cic-mcp-session` saját trust-szótára (`session.trust = session_local /
session_derived`, a `CLAUDE.md` trust modellje szerint) HOGYAN kerül a
`session_derived_notes[].trust` mezőbe (amely MÁR pontosan ugyanezt a két értéket
engedi enumként). Mikor `session_local` és mikor `session_derived` egy adott
tool-válasz? (pl. egy nyers chunk-szöveg `session_local`, egy aggregált/projektált
context_pack sor lehet `session_derived` — DÖNTÉSED legyen, indokold.)

### 3. "Session nem elérhető" viselkedés

A `get_session_status(session_id)` tool ÜRES dict-et (`{}`) ad vissza, ha a
`session_id` nem létezik (`mcp-server/session_server.py` dokumentált viselkedése —
idézd a konkrét sort). Definiáld: ebben az esetben a `GatewayContextEnvelope`-nak
EXPLICIT jeleznie kell ezt — a `conflicts[]` vagy `proof_requirements[]` mezőn keresztül
(válassz egyet, indokold), NEM szabad néma/üres `session_derived_notes[]`-szal
"sikeres" választ szimulálni.

### 4. Példa `compile_context` válasz

Írj egy TELJES, konkrét `GatewayContextEnvelope` YAML/JSON példát, amely
`cic-mcp-session` forrást használ (legalább 2 `session_derived_notes[]` bejegyzéssel,
megfelelő `sources_used[]`/`refs[]` kitöltéssel) — ÉS egy másik példát, ami a "session
nem elérhető" esetet mutatja (a 3. lépés döntése szerint kitöltve).

## Nem cél

- tényleges adapter-kód (Python/MCP client) implementálása
- `GatewayContextEnvelope`/source-registry schema MÓDOSÍTÁSA (ha hiányt találsz, JELEZD
  a riportban, NE módosítsd csendben a mergelt schema-fájlokat)
- `cic-mcp-session` repo módosítása (KIZÁRÓLAG olvasásra klónozva)
- `factory-session-bridge-001`/`session-context-pack-v1-001` (a Phase 2 másik két jobja)

## Required Output Files

- `output/gateway-session-adapter-contract.md`

## Required Report Sections

```markdown
# gateway-session-adapter-contract-001 Output

## Scope
## Inputs Read
## Session MCP API Surface

(a felhasznált tool-ok, file:line szignatúrával idézve)

## Adapter Input/Output Contract
## Trust Mapping
## Unavailable-Session Behavior
## Findings
## Claim-Evidence Matrix

| Claim | Status | Evidence | Verification Method | Risk |
|---|---|---|---|---|

## Example compile_context Response — Session Available
## Example compile_context Response — Session Unavailable
## Decisions Proposed
## Rejected / Out Of Scope
## Risks
## Definition Of Done Check
## Next Jobs
```

Elfogadott `Status` értékek: `proven`, `partial`, `missing`, `rejected`, `unknown`.
`proven` egy "az adapter ezt a tool-t hívja X paraméterekkel" állításra KIZÁRÓLAG akkor
használható, ha a `mcp-server/session_server.py` tényleges sora idézve van — a tool
neve megemlítve a riportban nem bizonyítja a tényleges szignatúrát, csak a fájl konkrét
sorának idézése bizonyít.

## Definition Of Done

- [ ] minden felhasznált session MCP tool-hoz `file:line` szignatúra idézve
- [ ] trust mapping (`session_local`/`session_derived`) definiálva, indoklással
- [ ] "session nem elérhető" eset definiálva (`conflicts`/`proof_requirements` mezőn
      keresztül)
- [ ] 2 teljes példa-envelope (elérhető + nem elérhető session eset)
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a gateway session TÁBLÁKAT kérdez le direktben — KIZÁRÓLAG az MCP tool-határon
  keresztül érheti el a session adatot
- tool-szignatúra idézése a `mcp-server/session_server.py` konkrét sorának ellenőrzése
  nélkül
- a "session nem elérhető" eset néma elsiklása (üres, de "sikeresnek" tűnő envelope)

## Git instrukciók

Push a `feature/gateway-session-adapter-contract-001` branch-re, KIZÁRÓLAG a
`cic-mcp-gateway` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni,
elég a lokális commit; a `cic-mcp-session` klónba SEMMIT nem szabad commitolni/pusholni,
az kizárólag olvasásra van). Main-re az agent NEM pushol. **NE módosítsd a `meta.yaml`
`status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek angolul.
