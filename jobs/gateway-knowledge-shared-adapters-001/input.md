# Job: gateway-knowledge-shared-adapters-001

## Kontextus

A `GatewayContextEnvelope` trust-domain modellje (lásd `cic-mcp-gateway/
CLAUDE.md` "Trust modell") több forrásréteget feltételez (session, shared,
knowledge), de a gateway JELENLEG KIZÁRÓLAG a session-adaptert hívja
(`gateway_core/compile_context.py`) — knowledge canonical keresés és shared
candidate/reviewed_shared keresés NINCS bekötve.

Ez a job ezt a hiányt zárja, DE a két forrás eltérő érettségű:
- `cic-mcp-knowledge` MÁR rendelkezik egy MCP szerverrel
  (`mcp-server/server.py`, `search_query`/`search_nodes` tool-okkal) — a
  gateway ezt a MEGLÉVŐ tool-kontraktust hívja, a session-adapter mintáját
  követve (subprocess + `mcp.client.stdio`).
- `cic-mcp-shared`-nek NINCS dedikált candidate-search MCP tool-ja — a
  `mcp-server/server.py` ott a generikus, byte-azonos KB-szerver (ugyanaz,
  amit a write-confinement fix jobban javítottunk), NEM a
  `shared_core.candidates` táblát keresi. Ehhez ez a job egy MINIMÁLIS,
  KIZÁRÓLAG OLVASÁSRA szolgáló, közvetlen Postgres-lekérdező függvényt
  definiál (NEM egy új MCP szervert — az egy KÜLÖN, nagyobb job lenne).

## Target

- target repo: `cic-mcp-gateway`
- workplace: `cic-mcp-knowledge` (a meglévő MCP tool-kontraktus
  ellenőrzéséhez), `cic-mcp-shared` (a `shared_core.candidates` schema
  ellenőrzéséhez) — ezeket a repókat ez a job NEM módosítja, csak olvassa
- target path: `gateway_core/` alá egy `knowledge_adapter.py` és
  `shared_adapter.py` (vagy hasonló elnevezés) + `compile_context()`
  bekötése + `output/gateway-knowledge-shared-adapters.md`
- change_type: `enhancement`
- status_after_merge: `candidate`
- status indoklás: valós, multi-source subprocess/DB teszt bizonyítja, hogy
  az envelope tényleg tartalmaz mindkét forrásból eredő, helyesen
  trust-jelölt elemet

## Sources

- **KÖTELEZŐ elsődleges forrás:**
  - `gateway_core/compile_context.py` — a session-adapter MINTÁJA (hogyan
    indít subprocess-t, hogyan hívja az MCP tool-t), amit a knowledge-
    adapter KÖVET
  - `cic-mcp-knowledge/mcp-server/server.py` — a `search_query`/
    `search_nodes` tool-kontraktus (a write-confinement fix UTÁNI állapot)
  - `cic-mcp-shared/output/shared-core-storage-schema.sql` — a
    `shared_core.candidates` TELJES schema, amit a shared-adapter
    OLVASÁSRA (NEM írásra) használ

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Ellenőrizd, hogy `gateway-query-context-api-001` `done` állapotban van-e
   — ha NEM, állítsd a jobot NO-GO-ra, és állj meg
3. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. Pre-change állapot — grep + idézet

```
grep -rn "knowledge\|shared_core" gateway_core/*.py | grep -v test_
```

Idézd a kimenetet — bizonyítsd hogy JELENLEG SEMMI nincs bekötve ezekhez a
forrásokhoz, file:line szinten (vagy 0 találat, ha úgy van).

### 2. Knowledge adapter

A session-adapter mintáját követve (subprocess + `mcp.client.stdio`), hívd
meg a `cic-mcp-knowledge` MCP szerverének `search_query` tool-ját egy adott
query-re. Valós, futtatott subprocess teszttel bizonyítsd, hogy egy ismert
tartalmú knowledge-fixture-re a hívás tényleges, releváns találatot ad
vissza.

### 3. Shared adapter

Egy MINIMÁLIS, csak-olvasó Python függvény, ami KÖZVETLENÜL csatlakozik a
`cic-mcp-shared` Postgres-éhez (NEM MCP-n keresztül — nincs hozzá tool), és
egy query/keyword alapján visszaadja a releváns `shared_core.candidates`
sorokat (`trust IN ('candidate', 'reviewed_shared')` — `mixed` sorokat NE
adjon vissza, azok még nem elég megbízhatóak). Valós Postgres teszttel
bizonyítsd.

### 4. Envelope-összeállítás trust-megőrzéssel

Bővítsd a `compile_context()`-et (vagy az azt hívó réteget), hogy EGY
query-re LEGALÁBB egy knowledge-eredetű ÉS egy shared-eredetű elemet
tartalmazó envelope-ot adjon vissza, ahol MINDEN elem MEGTARTJA a saját
forrás-trust-jelölését (egy knowledge-elem NEM keveredik össze egy
shared `candidate`-elemmel azonos trust-szintként). Valós, multi-source
teszttel bizonyítsd, idézve az envelope tényleges, per-elem trust-mezőit.

## Nem cél

- a `gateway-query-context-api-001` query/intent logikájának módosítása
  (csak HASZNÁLJA, nem bővíti)
- új MCP szerver építése a `shared_core.candidates`-hez (ez egy KÜLÖN,
  nagyobb job lenne — ez a job egy minimális, közvetlen DB-olvasó
  függvénnyel old meg)
- a `cic-mcp-knowledge` vagy `cic-mcp-shared` repó MÓDOSÍTÁSA — ez a job
  KIZÁRÓLAG a `cic-mcp-gateway` oldali adaptert építi
- `mixed` trust-szintű shared sorok visszaadása az envelope-ban

## Required Output Files

- `output/gateway-knowledge-shared-adapters.md`
- a knowledge adapter + shared adapter modulok
- a hozzá tartozó teszt-fájl(ok)

## Required Report Sections

```markdown
# gateway-knowledge-shared-adapters-001 Output

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

Elfogadott `Status` értékek: `proven`, `partial`, `scaffold`, `concept`,
`missing`, `rejected`, `unknown`.

## Definition Of Done

- [ ] pre-change állapot grep-pel bizonyítva (knowledge/shared NINCS
      bekötve)
- [ ] knowledge adapter valós subprocess teszttel bizonyítva
- [ ] shared adapter valós Postgres teszttel bizonyítva, KIZÁRÓLAG
      `candidate`/`reviewed_shared` trust-szintet ad vissza
- [ ] envelope multi-source teszt: legalább 1 knowledge + 1 shared elem,
      MINDEGYIK megtartja a saját trust-jelölését, TÉNYLEGES kimenettel
      bizonyítva
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- az adapter modul léte ≠ implemented — a futtatott teszt kimenete
  bizonyít, a kód megírása nem
- knowledge és shared eredmények összeolvasztása úgy, hogy elveszik melyik
  forrásból/milyen trust-szinttel jött egy elem
- `mixed` trust-szintű shared sor bekerülése az envelope-ba
- a `cic-mcp-knowledge`/`cic-mcp-shared` repó forráskódjának módosítása
  (ez a job KIZÁRÓLAG a gateway oldalt épíi)

## Git instrukciók

Push a `feature/gateway-knowledge-shared-adapters-001` branch-re,
KIZÁRÓLAG a `cic-mcp-gateway` célrepóban (a `cic-mcp-knowledge`/
`cic-mcp-shared` klónok csak OLVASÁSRA vannak, nem módosulnak, nem kell
rájuk pusholni; a `cic-mcp-factory` saját klónjában is elég a lokális
commit). Main-re az agent NEM pushol. **NE módosítsd a `meta.yaml` `status`
mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek/kód angolul.
