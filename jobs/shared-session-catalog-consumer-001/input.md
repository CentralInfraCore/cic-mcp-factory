# Job: shared-session-catalog-consumer-001

## Kontextus

Phase 4 ELSŐ jobja a `cic-mcp-shared` repóban. A `cic-mcp-shared` jelenleg a `base-repo`
MCP-template generikus scaffoldját tartalmazza, `source/` üres, NINCS még
shared-specifikus implementáció (`CLAUDE.md` "Jelenlegi állapot": `experimental`, nincs
shared-specifikus kód). Ez a job NEM implementáció — KONTRAKTUS-szintű riport, amely
definiálja, HOGYAN fogyasztaná a `cic-mcp-shared` a `cic-mcp-session` session-katalógust,
anélkül hogy maga válna az ELSŐ igazságforrássá a session-adatra.

**Kritikus határ** (a job-slices.yaml `forbidden_shortcuts`-ja szerint): a
`cic-mcp-shared` SOSEM lehet a session-adat első igazságforrása, és SOSEM promote-olhat
tartalmat canonical-ra emberi review nélkül — ez a `CLAUDE.md` trust modelljének
(`trust: mixed/candidate/reviewed_shared`, `canonical: false` by default) megőrzése
miatt kötelező határ.

**Prerequisite-ellenőrzés KÖTELEZŐ ELSŐ LÉPÉS**: a job-slices.yaml előírja, hogy a
riport vagy megerősíti hogy a `session-ingress-envelope-contract-001` prerequisite
KÉSZ, vagy NO-GO-t jelez. Ezt a `jobs/index.yaml`-ban/`jobs/session-ingress-envelope-
contract-001/meta.yaml`-ban kell ellenőrizni (a `cic-mcp-factory` klónban) — NEM
feltételezni.

## Target

- target repo: `cic-mcp-shared`
- target path: `output/shared-session-catalog-consumer.md`
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: kontraktus-riport, nincs futtatható adapter/aggregátor kód —
  `candidate`-hez egy tényleges implementáció (a riport "Next Jobs" szekciójában
  javasolt) és legalább egy valós, futtatott bizonyíték kellene (a
  `gateway-session-adapter-contract-001` → `session-context-pack-v1-001` mintát követve)

## Sources

- `${WORKDIR}/.cic-context/factory-docs/architecture.md` — "cic-mcp-shared" + "Fő
  határok" szekció
- `${WORKDIR}/.cic-context/factory-docs/execution-phases.md` — "Phase 4" szekció
- **KÖTELEZŐ elsődleges forrás (a `cic-mcp-factory` repo `main`-jén, MÁR ott van):**
  - `${WORKDIR}/jobs/index.yaml` — ellenőrizd, hogy `session-ingress-envelope-
    contract-001` státusza `done`
  - `${WORKDIR}/jobs/session-ingress-envelope-contract-001/output/session-ingress-
    envelope.schema.yaml` — a TELJES `SessionIngressEnvelope` schema
  - `${WORKDIR}/jobs/session-ingress-envelope-contract-001/output/session-ingress-
    envelope-contract.md` — a kontraktus indoklása
- **KÖTELEZŐ MÁSODIK forrás (a `cic-mcp-session` repo, KLÓNOZVA ehhez a jobhoz,
  KIZÁRÓLAG OLVASÁSRA — NE módosítsd):**
  - `cic-mcp-session/mcp-server/session_server.py` — a 7 MCP tool TÉNYLEGES
    szignatúrája — idézz `file:line` hivatkozást MINDEN tool-hívásra amit a
    shared-konzument felhasznál
  - `cic-mcp-session/CLAUDE.md` — trust modell (`canonical: false`,
    `default_scope: session_id`, `cross_session: false`)
- **HARMADIK forrás (a `cic-mcp-shared` repo, a target):**
  - `cic-mcp-shared/CLAUDE.md` — "Fő határok", "Trust modell" szekció

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. Prerequisite-ellenőrzés

Grep-pel erősítsd meg a `session-ingress-envelope-contract-001` job állapotát:

```
grep -A3 'job_id: "session-ingress-envelope-contract-001"' jobs/index.yaml
```

Idézd a kimenetet. Ha a státusz NEM `done`, a riport legyen NO-GO és a "Decisions
Proposed" szekció jelezze ezt — NE folytasd a többi feladatot.

### 2. Session MCP API surface — mit fogyaszt a shared

Először GREP-pel erősítsd meg, mely tool-ok valóban `@mcp.tool()`-ként regisztráltak a
`cic-mcp-session` klónban (teszt-fájlok kizárva):

```
grep -rn "@mcp.tool()" -A 1 mcp-server/session_server.py | grep -v test_
```

Idézd a teljes kimenetet. Dokumentáld, mely tool(oka)t hívná a `cic-mcp-shared`
konzument-adapter, milyen paraméterekkel — KIZÁRÓLAG az MCP tool-határon keresztül,
SOHA nem direkt SQL/tábla-hozzáféréssel (a `gateway-session-adapter-contract-001`
mintáját követve, ami már bizonyította ezt a határt betarthatónak).

### 3. Mit perzisztál a shared vs. mit kérdez le élőben a session-től

Definiáld EXPLICIT, mezőszintű döntéssel: a `cic-mcp-shared` réteg cross-session
aggregátumokat (klaszterek, visszatérő fogalmak, súlyozott jelöltek) PERZISZTÁL saját
tárban, DE a session-szintű RAW tartalmat NEM duplikálja — minden session-szintű
részlet-lekérdezés a `cic-mcp-session` MCP API-n keresztül megy LIVE, igény szerint.
Indokold: miért nem volna helyes a teljes session-tartalmat shared-oldali táblákba
másolni (lásd `cic-mcp-shared` CLAUDE.md "Nem": "raw hook ingestion első
igazságforrása" — ha a shared másolatot tartana, KÉT igazságforrás keletkezne).

### 4. Trust-állítás — `mixed`/`candidate`/`reviewed_shared`, sosem `canonical` automatikusan

Térképezd fel: egy `cic-mcp-session`-ből származó, shared-oldalon aggregált jelölt
milyen `trust` értéket kapna (`mixed`/`candidate`/`reviewed_shared` — a `cic-mcp-shared`
CLAUDE.md enum-ja szerint), és miért NEM kaphat `canonical: true`-t automatikus
promotion nélkül. Hivatkozz a `cic-mcp-shared` CLAUDE.md "Trust modell" szekciójára.

### 5. Konkrét adapter-kontraktus vázlat

Írj egy táblát: `cic-mcp-session` MCP tool → shared-oldali felhasználás → trust-
besorolás → perzisztált vagy live-query. (NEM teljes implementáció, csak a leképezés.)

## Nem cél

- tényleges adapter/aggregátor kód implementálása
- a `SessionIngressEnvelope` schema módosítása
- `cic-mcp-session` repo módosítása (KIZÁRÓLAG olvasásra klónozva)
- `shared-cross-session-search-001`/`shared-weighting-model-001` (a Phase 4 másik két
  jobja)
- canonical promotion folyamat/review-flow részletes kidolgozása (csak annak ÁLLÍTÁSA,
  hogy az emberi review-t igényel, kötelező)

## Required Output Files

- `output/shared-session-catalog-consumer.md`

## Required Report Sections

```markdown
# shared-session-catalog-consumer-001 Output

## Scope
## Inputs Read
## Prerequisite Check

(grep kimenet idézve, GO/NO-GO döntés)

## Session MCP API Surface

(a felhasznált tool-ok, file:line szignatúrával idézve)

## Persisted vs. Live-Queried Split
## Trust Mapping
## Adapter Contract Table
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
`proven` egy "a shared ezt a tool-t hívja X paraméterekkel" állításra KIZÁRÓLAG akkor
használható, ha a `mcp-server/session_server.py` tényleges sora idézve van — a fájl
léte ≠ implemented, a tool neve megemlítve a riportban nem bizonyítja a tényleges
szignatúrát, csak a fájl konkrét sorának idézése bizonyít.

## Definition Of Done

- [ ] prerequisite (`session-ingress-envelope-contract-001`) állapota grep-pel
      megerősítve, GO/NO-GO döntés indokolva
- [ ] minden felhasznált session MCP tool-hoz `file:line` szignatúra idézve
- [ ] explicit perzisztált-vs-live-query mezőszintű döntés, indoklással
- [ ] trust-mapping definiálva (`mixed`/`candidate`/`reviewed_shared`), `canonical:
      false` explicit kimondva
- [ ] adapter-kontraktus tábla kész
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a `cic-mcp-shared` lesz a session-adat ELSŐ igazságforrása (a teljes raw tartalom
  shared-oldali másolása ezt jelentené — TILOS)
- a shared automatikus canonical promotiont végez emberi review nélkül
- a session-adat direkt SQL/tábla-hozzáférése — KIZÁRÓLAG az MCP tool-határon keresztül
- tool-szignatúra idézése a `mcp-server/session_server.py` konkrét sorának ellenőrzése
  nélkül

## Git instrukciók

Push a `feature/shared-session-catalog-consumer-001` branch-re, KIZÁRÓLAG a
`cic-mcp-shared` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni, elég
a lokális commit; a `cic-mcp-session` klónba SEMMIT nem szabad commitolni/pusholni, az
kizárólag olvasásra van). Main-re az agent NEM pushol. **NE módosítsd a `meta.yaml`
`status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek angolul.
