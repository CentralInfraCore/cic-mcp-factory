# Job: gateway-source-registry-contract-001

## Kontextus

A `gateway-context-envelope-contract-001` job formalizálta a `GatewayContextEnvelope`
schema-t — ennek `sources_used[].source_id` mezője MÁR egy zárt enum-ra hivatkozik
(`cic-mcp-session`, `cic-mcp-shared`, `cic-mcp-knowledge`, `cic-mcp-workdir`), és a
schema saját description-je explicit kimondja: "the full source registry contract (field
types, capabilities) is defined by gateway-source-registry-contract-001, not here". Ez a
job EZT a hiányzó kontraktust formalizálja — a `gateway-baseline.md` "Source Registry —
Initial Boundary" táblájára épülve (`source_id`, `trust_domain`, `owns_raw_storage`,
`returns_trust_envelope`, `query_capabilities`, `canonical` mezők).

A `gateway-baseline.md` "Risks" szekciója egy NYITOTT kérdést hagyott: a `cic-mcp-workdir`
jelenleg a `cic-factory` szerepét tölti be (`docs/en/architecture.md`: "current
repo/worktree/branch/diff (role filled by cic-factory)") — KÜLÖN source-domain-e, vagy
csak a `cic-factory`-n keresztül érhető el? EZT a jobot KÖTELEZŐ lezárnia, döntéssel és
indoklással, NEM nyitva hagyva.

**Kritikus kényszer**: a `gateway-context-envelope.schema.yaml` `source_id`/`trust_domain`
enum-jai MÁR rögzítve vannak (4 source_id érték, 5 trust_domain érték). Ennek a jobnak a
schema-ja PONTOSAN ugyanezeket az enum-értékeket kell használnia — bármilyen eltérés
kontraktus-törés, amit explicit jelezni kell, NEM csendben módosítani.

## Target

- target repo: `cic-mcp-gateway`
- target path: `output/gateway-source-registry-contract.md` +
  `output/gateway-source-registry.schema.yaml` (ÚJ fájlok)
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: schema-kontraktus job, nincs futtatható registry-betöltő/validátor kód
  — `candidate`-hez egy tényleges `gateway-session-adapter-contract-001` implementáció
  kellene, ami a registry-t valóban használja

## Sources

- `${WORKDIR}/.cic-context/factory-docs/architecture.md` — "cic-mcp-gateway" szekció
- `${WORKDIR}/.cic-context/factory-docs/execution-phases.md` — "Phase 1B" szekció
- **KÖTELEZŐ elsődleges forrás (a `cic-mcp-gateway` repo `main`-jén):**
  - `cic-mcp-gateway/output/gateway-baseline.md` — "Source Registry — Initial Boundary" +
    "Risks" szekció (a `cic-mcp-workdir`/`cic-factory` nyitott kérdés) — EBBŐL indulj ki
  - `cic-mcp-gateway/output/gateway-context-envelope.schema.yaml` — a `sources_used[]`
    property `source_id`/`trust_domain` enum-jai — EZEKKEL kell szinkronban lenned
  - `cic-mcp-gateway/output/gateway-context-envelope-contract.md` — "Next Jobs" szekció
    (mit vár el ettől a jobtól)
  - `cic-mcp-gateway/docs/hu/architecture.md` és `docs/en/architecture.md` — trust modell,
    a `cic-mcp-workdir`/`cic-factory` kapcsolat leírása

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. Enum-szinkron ellenőrzés — grep-alapú, ne csak emlékezetből

Mielőtt megírnád a saját schema-t, GREP-pel/olvasással szedd ki a tényleges
`source_id`/`trust_domain` enum-listát a `gateway-context-envelope.schema.yaml`-ból:

```
grep -n "cic-mcp-session\|cic-mcp-shared\|cic-mcp-knowledge\|cic-mcp-workdir\|session_local\|session_derived\|shared_mixed\|canonical\|workdir_local" \
  output/gateway-context-envelope.schema.yaml | grep -v test_
```

Idézd a találatokat — ez a forrása az enum-listának, NEM az emlékezeted vagy a
`gateway-baseline.md` (amely csak egy KORÁBBI vázlat volt, a tényleges schema lehet ettől
eltérő).

### 2. Source registry YAML schema

`output/gateway-source-registry.schema.yaml` — `apiVersion`/`kind`/`metadata`/`required`/
`properties` stílusban (ugyanaz a konvenció, mint a `gateway-context-envelope.schema.yaml`).
Mezők (minimum, a `gateway-baseline.md` táblája alapján, BŐVÍTHETŐ):
- `source_id` — enum, PONTOSAN az 1. lépésben kiszedett értékekkel
- `trust_domain` — enum, PONTOSAN az 1. lépésben kiszedett értékekkel
- `owns_raw_storage` — bool
- `returns_trust_envelope` — bool
- `query_capabilities` — list[string]
- `canonical` — bool

### 3. `cic-mcp-workdir` vs `cic-factory` döntés

Dönts: a `cic-mcp-workdir` KÜLÖN source-domain-e a registry-ben, vagy a `cic-factory`-n
keresztül érhető el csak (azaz a registry-ben NINCS önálló `cic-mcp-workdir` bejegyzés,
hanem egy `cic-factory`-proxy-bejegyzés van). Indokold a `docs/hu/architecture.md`/
`docs/en/architecture.md` konkrét sorára hivatkozva. A döntésnek KÖVETKEZETESEN illeszkednie
kell az 1. lépésben kiszedett `source_id` enum-mal (mivel a `gateway-context-envelope.schema.yaml`
MÁR rögzíti a `cic-mcp-workdir` source_id-t, a döntésnek ezt a tényt figyelembe kell vennie
— ha a registry-ben mégis `cic-factory`-ként szerepel, ezt a látszólagos ellentmondást
explicit fel kell oldanod/megmagyaráznod, NEM csendben elsiklani fölötte).

### 4. Kontraktus-report

`output/gateway-source-registry-contract.md` — legalább **4 VALID** registry-bejegyzés
(egy minden ismert `source_id`-ra) és legalább **2 INVALID** (konkrét indoklással MIÉRT
invalid, pl. "hiányzik a `trust_domain`", "`owns_raw_storage: true` egy olyan source-on,
ami a gateway saját bejegyzése lenne — tiltott").

## Nem cél

- registry betöltő/validátor FUTTATHATÓ kódjának megírása
- `GatewayContextEnvelope` schema MÓDOSÍTÁSA (ha enum-eltérést találsz, JELEZD a riportban,
  NE módosítsd csendben a már mergelt schema-fájlt)
- tényleges routing logika vagy adapter kód (`gateway-session-adapter-contract-001` és
  társai)
- `cic-mcp-session`/`cic-mcp-shared`/`cic-mcp-knowledge`/`cic-mcp-factory` repók módosítása

## Required Output Files

- `output/gateway-source-registry-contract.md`
- `output/gateway-source-registry.schema.yaml`

## Required Report Sections

```markdown
# gateway-source-registry-contract-001 Output

## Scope
## Inputs Read
## Enum Sync Check

(grep-kimenet a gateway-context-envelope.schema.yaml-ból, idézve)

## Schema Summary
## cic-mcp-workdir vs cic-factory Decision
## Findings
## Claim-Evidence Matrix

| Claim | Status | Evidence | Verification Method | Risk |
|---|---|---|---|---|

## Valid Registry Entries

(legalább 4)

## Invalid Registry Entries

(legalább 2, indoklással)

## Decisions Proposed
## Rejected / Out Of Scope
## Risks
## Definition Of Done Check
## Next Jobs
```

Elfogadott `Status` értékek: `proven`, `partial`, `missing`, `rejected`, `unknown`.
`proven` egy "az enum szinkronban van" állításra KIZÁRÓLAG akkor használható, ha mindkét
schema-fájl (`gateway-context-envelope.schema.yaml` ÉS a saját
`gateway-source-registry.schema.yaml`) konkrét enum-listája egymás mellett, szó szerint
idézve van — az állítás kimondása a riportban ≠ a két fájl tényleges egyezése, csak a
side-by-side idézet bizonyít.

## Definition Of Done

- [ ] `source_id`/`trust_domain` enum-ok PONTOSAN egyeznek a
      `gateway-context-envelope.schema.yaml`-jal, side-by-side idézve
- [ ] `cic-mcp-workdir` vs `cic-factory` kérdés lezárva, döntéssel és forrás-hivatkozással
- [ ] legalább 4 valid + 2 invalid registry-bejegyzés, indoklással
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a `source_id`/`trust_domain` enum eltérése a `GatewayContextEnvelope`-tól indoklás
  nélkül
- a `cic-mcp-workdir`/`cic-factory` kérdés nyitva hagyása
- registry betöltő/validátor FUTTATHATÓ kódjának megírása

## Git instrukciók

Push a `feature/gateway-source-registry-contract-001` branch-re, KIZÁRÓLAG a
`cic-mcp-gateway` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni, elég a
lokális commit). Main-re az agent NEM pushol. **NE módosítsd a `meta.yaml` `status`
mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a schema mezőnevek/YAML kulcsok/kódrészletek angolul.
