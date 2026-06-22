# Job: session-context-pack-v1-001

## Kontextus

A `gateway-session-adapter-contract-001` job KONTRAKTUS-szinten definiálta, hogyan
fordítaná a gateway a `cic-mcp-session` MCP API válaszait egy `GatewayContextEnvelope`-ba
— de a riport saját "Next Jobs" #3 pontja explicit kimondja: "ez a job
(`session-context-pack-v1-001`) lenne az első, ami `experimental`-ből `candidate`-be
tudná emelni ezt a kontraktust", mert addig NEM volt valódi, futtatott bizonyíték arra,
hogy a kontraktus TÉNYLEG implementálható.

Ez a job az ELSŐ VALÓDI `compile_context()` implementáció a `cic-mcp-gateway` repóban —
NEM újabb kontraktus-vázlat. Ez egy implementációs job, MAGASABB bizonyítási mércével,
mint a Phase 1B/eddigi Phase 2 jobok:

- a `cic-mcp-session` MCP szervert ÖNÁLLÓ subprocess-ként kell elindítani és VALÓDI
  stdio MCP handshake-kel (`list_tools()` + `call_tool()`) hívni — UGYANAZ a bizonyítási
  mérce, amit a `session-mcp-venv-fix-001` már bizonyított használhatónak (in-process
  Python hívás NEM elég)
- a teszteléshez használt session-adatot a `cic-mcp-session` SAJÁT, VALÓDI ingest
  pipeline-ján KELL átfuttatni (`insert_envelope()` → `run_projection_batch()` →
  `run_indexing_batch()`) — NEM egy kézzel írt SQL INSERT-tel becsempészve. Ennek a
  pontos receptjét a `cic-mcp-session/tests/test_session_store/test_session_api.py`
  fájl MÁR dokumentálja (160-169. sor körül) — EZT a mintát kövesd, ne találd ki
  újra.

## Target

- target repo: `cic-mcp-gateway`
- target path: a `compile_context()` függvény pontos modul-elhelyezése (pl.
  `gateway_core/compile_context.py` vagy ekvivalens — ÚJ könyvtár, mivel a repóban
  jelenleg NINCS gateway-specifikus Python modul, csak a generikus `base-repo`
  KB-template) RÁD VAN BÍZVA — indokold a választást a riportban
- change_type: `new_capability`
- status_after_merge: `candidate`
- status indoklás: ELLENTÉTBEN a korábbi Phase 1B/2 kontraktus-jobokkal, ITT
  `candidate`-et célzunk, mert ez az ELSŐ valódi, futtatott, end-to-end bizonyíték —
  ha a "Required Evidence" pontok mindegyike TÉNYLEGESEN teljesül (valódi subprocess
  handshake, valódi pipeline-on átfutott adat, schema-validált envelope, zöld teszt),
  a `candidate` indokolt; ha BÁRMELYIK csak részben sikerül, maradj `experimental`-on
  és jelezd a riportban PONTOSAN melyik pont hiányzik

## Sources

- `${WORKDIR}/.cic-context/factory-docs/execution-phases.md` — "Phase 2" szekció
- `${WORKDIR}/.cic-context/factory-docs/architecture.md` — "Fő határok" szekció
- **KÖTELEZŐ elsődleges forrás (a `cic-mcp-gateway` repo `main`-jén):**
  - `cic-mcp-gateway/output/gateway-context-envelope.schema.yaml` — a TELJES schema,
    minden kötelező mezővel
  - `cic-mcp-gateway/output/gateway-session-adapter-contract.md` — a "Session MCP API
    Surface", "Adapter Input/Output Contract", "Trust Mapping",
    "Unavailable-Session Behavior" szekciók — EZ a kontraktus, amit implementálsz
- **KÖTELEZŐ MÁSODIK forrás (a `cic-mcp-session` repo, KLÓNOZVA ehhez a jobhoz,
  KIZÁRÓLAG OLVASÁSRA — NE módosítsd, NE commitolj bele):**
  - `cic-mcp-session/mcp-server/session_server.py` — a tényleges MCP tool-ok (legalább
    a `get_session_context_pack` és `get_session_status` tool-t KELL hívnod)
  - `cic-mcp-session/tests/test_session_store/test_session_api.py` — 160-169. sor körül,
    a VALÓDI ingest-pipeline minta (`insert_envelope` → `run_projection_batch` →
    `run_indexing_batch`) — EZZEL szedd fel a teszt session-adatot
  - `cic-mcp-session/session_store/envelope_writer.py`,
    `cic-mcp-session/session_store/turn_projector.py`,
    `cic-mcp-session/session_store/chunk_indexer.py` — a pipeline tényleges függvényei
  - `cic-mcp-session/output/session-mcp-venv-fix-report.md` — a stdio MCP handshake
    bizonyítási mintája (hogyan indul a szerver subprocess-ként, hogyan néz ki a
    `mcp.client.stdio` kliens-kód)

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármilyen kódot írnál

## Feladat

### 1. Teszt-session adat felépítése a VALÓDI pipeline-on

Indíts egy friss Postgres tesztkonténert, alkalmazd az összes SQL migrációt, majd a
`test_session_api.py` mintáját követve hívd MEG (ne reimplementáld) a
`insert_envelope()` → `run_projection_batch()` → `run_indexing_batch()` láncot legalább
egy session-re, legalább néhány turn/chunk-kal. Idézd a tényleges Python-hívásokat és a
DB-ben eredményül kapott sorszámokat (pl. `SELECT count(*) FROM session_core.chunks`).

### 2. `compile_context(session_id)` implementáció

Írd meg a függvényt, amely:
1. egy ÖNÁLLÓ subprocess-ként elindítja a `cic-mcp-session` MCP szervert
   (`.venv-host/bin/python mcp-server/session_server.py` vagy ekvivalens, lásd
   `session-mcp-venv-fix-report.md` mintáját) és valódi `mcp.client.stdio`-val
   csatlakozik
2. meghívja a `get_session_status(session_id)` tool-t (a "session nem elérhető" eset
   ellenőrzéséhez — lásd a `gateway-session-adapter-contract.md` "Unavailable-Session
   Behavior" szekcióját)
3. ha a session létezik, meghívja a `get_session_context_pack(session_id, max_chunks)`
   tool-t, és a választ a kontraktusban dokumentált leképezés szerint
   `session_derived_notes[]`/`refs[]`-be fordítja
4. egy teljes, a `gateway-context-envelope.schema.yaml` szerint érvényes
   `GatewayContextEnvelope` dict/objektumot ad vissza

### 3. Schema-validáció

Validáld a TÉNYLEGES `compile_context()` kimenetét a `gateway-context-envelope.schema.yaml`
ellen — programozottan (pl. egy egyszerű, a `required`/`properties` listát bejáró
ellenőrző script, NEM csak vizuális átolvasás). Idézd a validáció kimenetét.

### 4. "Session nem elérhető" eset valódi futtatása

Hívd meg a `compile_context()`-et egy SZÁNDÉKOSAN nem létező `session_id`-vel, és idézd
a tényleges visszatérési értéket — bizonyítva, hogy a `proof_requirements[]`-alapú
jelzés (a kontraktus szerint) TÉNYLEG megjelenik, nem csak elméletben van leírva.

### 5. Automatizált teszt

Írj legalább egy pytest tesztet, amely a TELJES end-to-end utat lefuttatja (valódi
subprocess, valódi DB, valódi pipeline-on átfutott adat) — idézd a teszt-futtatás
kimenetét.

## Nem cél

- a `GatewayContextEnvelope`/source-registry schema-fájlok MÓDOSÍTÁSA
- a `cic-mcp-session` repo MÓDOSÍTÁSA (kizárólag olvasásra van klónozva)
- a Phase 2 másik két jobja (`factory-session-bridge-001`,
  `gateway-session-adapter-contract-001` — ez utóbbi már lezárva)
- SSE-mód, autentikáció, multi-session/multi-instance kezelés
- a `trust_summary`/`conflicts` mezők teljes kitöltése minden elméleti esetre — elég a
  kontraktusban már definiált 2 eset (elérhető + nem elérhető session)

## Required Output Files

- `output/session-context-pack-v1-report.md`

## Required Report Sections

```markdown
# session-context-pack-v1-001 Output

## Scope
## Inputs Read
## Test Session Data Setup

(a valódi pipeline-hívások + DB-sorszámok idézve)

## compile_context() Implementation Summary
## Real Stdio MCP Handshake Evidence

(a tényleges subprocess + list_tools/call_tool kimenet idézve)

## Schema Validation Result
## Unavailable-Session Case — Real Output
## Automated Test Evidence

(a pytest kimenet idézve)

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
`proven` egy "a `compile_context()` valódi MCP handshake-kel működik" állításra
KIZÁRÓLAG akkor használható, ha a tényleges subprocess+stdio kimenet idézve van — a
függvény léte ≠ implemented, csak a tényleges futtatási kimenet idézése bizonyít.
Hasonlóan: a hívó fájl és sor (`file:line`) idézése kötelező minden tool-hívásra.

## Definition Of Done

- [ ] teszt-session adat a VALÓDI `insert_envelope`/`run_projection_batch`/
      `run_indexing_batch` pipeline-on átfuttatva, DB-sorszámokkal bizonyítva
- [ ] `compile_context()` implementálva, ÖNÁLLÓ subprocess + valódi stdio MCP
      handshake-kel hívja a `cic-mcp-session` szervert
- [ ] a kimenet programozottan validálva a `gateway-context-envelope.schema.yaml`
      ellen, kimenet idézve
- [ ] "session nem elérhető" eset valódi futtatással bizonyítva, kimenet idézve
- [ ] legalább 1 automatizált teszt zöld, kimenet idézve
- [ ] claim-evidence tábla kitöltve, nem üres
- [ ] ha BÁRMELYIK fenti pont nem teljesül teljesen, a "Decisions Proposed" szekció
      explicit jelzi és a `status_after_merge`-et `experimental`-ra módosítja
      (NEM a meta.yaml-ban — csak a riport saját szövegében jelezve az
      orchestrátor felé, a meta.yaml `capability.status_after_merge` mezőjét NE
      módosítsd, az orchestrátor dönt a tényleges záráskor)

## Forbidden Shortcuts

- mock-olt vagy kézzel összerakott `GatewayContextEnvelope` a tényleges
  `compile_context()`-hívás helyett
- a stdio MCP handshake működésének állítása anélkül, hogy TÉNYLEGESEN subprocess-ként
  futtatnád
- a teszt-adat kézzel írt SQL INSERT-tel becsempészése a valódi
  `insert_envelope`/`run_projection_batch`/`run_indexing_batch` pipeline megkerülésével
- `candidate` állítás a "session nem elérhető" eset valódi futtatása nélkül

## Git instrukciók

Push a `feature/session-context-pack-v1-001` branch-re, KIZÁRÓLAG a `cic-mcp-gateway`
célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni, elég a lokális
commit; a `cic-mcp-session` klónba SEMMIT nem szabad commitolni/pusholni). Main-re az
agent NEM pushol. A teszteléshez használt Docker konténert a munka végén állítsd le és
töröld. **NE módosítsd a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek angolul.
