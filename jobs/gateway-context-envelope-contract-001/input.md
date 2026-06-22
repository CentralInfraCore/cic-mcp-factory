# Job: gateway-context-envelope-contract-001

## Kontextus

A `gateway-repo-baseline-or-bootstrap-001` audit job megerősítette: a `cic-mcp-gateway`
repo `scaffold` állapotban van (bootstrap kész, dokumentáció-réteg gateway-specifikus, de
nulla domain-logika kód), és javasolta ezt a jobot, mint a logikailag első contract-jobot —
a source registry (egy KÖVETKEZŐ job) értelmetlen lenne anélkül, hogy tudnánk, MILYEN
formátumba kell egy forrásnak (`cic-mcp-session`/`cic-mcp-shared`/`cic-mcp-knowledge`)
illeszkednie.

Ez a job a `GatewayContextEnvelope` ELSŐ formális schema-kontraktusát definiálja — azt a
trust-jelölt kontextus-csomagot, amit a gateway agent-facing API-ja visszaad. A
`cic-mcp-gateway/docs/{hu,en}/architecture.md` "Tervezett adatfolyam" szekciója MÁR
javasolt egy mezőlistát (`answer_type`, `query_intent`, `scope`, `sources_used`,
`trust_summary`, `canonical_facts`, `workdir_facts`, `session_derived_notes`,
`shared_memory_notes`, `conflicts`, `proof_requirements`, `refs`) — ez a job EBBŐL indul ki
és formalizálja YAML schema-ként, az előző audit "GatewayContextEnvelope — Initial Boundary"
hármas-bontására épülve (honnan jött / mi a tartalom / milyen trust-jelölés van rajta).

A `cic-mcp-session` `SessionIngressEnvelope` schema-ja
(`cic-mcp-session/output/session-ingress-envelope.schema.yaml`) ennek az ökoszisztémának a
schema-írási konvencióját mutatja (`apiVersion`/`kind`/`metadata`/`required`/`properties`,
minden mezőhöz `description`) — EZT a stílust kövesd, NE találj ki új konvenciót.

**Fontos elhatárolás**: ez a job KIZÁRÓLAG a `GatewayContextEnvelope` (a gateway KIMENETI,
agent-facing csomagja) schema-ját definiálja. NEM a source registry-t (az egy KÖVETKEZŐ
job, `gateway-source-registry-contract-001`), és NEM a tényleges routing/adapter kódot
(`gateway-session-adapter-contract-001` és társai).

## Target

- target repo: `cic-mcp-gateway`
- target path: `output/gateway-context-envelope-contract.md` +
  `output/gateway-context-envelope.schema.yaml` (ÚJ fájlok)
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: ez egy schema-kontraktus job, nincs futtatható validátor-kód, nincs
  teszt rá — `candidate`-hez egy tényleges JSON-Schema/YAML validátor implementáció és
  legalább egy valódi gateway-adapter job (`gateway-session-adapter-contract-001`) kellene,
  ami a schema-t tényleg használja

## Sources

- `${WORKDIR}/.cic-context/factory-docs/architecture.md` — "cic-mcp-gateway" szekció
  (Igen/Nem határok) — NORMATÍV
- `${WORKDIR}/.cic-context/factory-docs/execution-phases.md` — "Phase 1B" szekció —
  NORMATÍV
- `${WORKDIR}/.cic-context/corpus/normalized/thead-review-2026-06-20.yaml` —
  `dec-thead-0005` ("cic-mcp-gateway is a trust-domain aware context compiler, not a
  generic search proxy")
- **KÖTELEZŐ elsődleges forrás:**
  - `cic-mcp-gateway/output/gateway-baseline.md` — az előző audit job riportja, a
    "GatewayContextEnvelope — Initial Boundary" + "Decisions Proposed" + "Risks" szekció
    (a doc/kód divergencia kockázat) — EBBŐL indulj ki, NE kezdd nulláról
  - `cic-mcp-gateway/docs/hu/architecture.md` és `docs/en/architecture.md` — "Tervezett
    adatfolyam" szekció (a mezőlista-javaslat forrása)
  - `cic-mcp-gateway/CLAUDE.md` — trust modell (`gateway_role: trust_domain_context_compiler`,
    `owns_raw_storage: false`, `owns_embedding_store: false`, `returns_trust_envelope: true`)
  - **Stílus-referencia** (NE a tartalmát vedd át, csak a YAML schema-írási konvenciót):
    `cic-mcp-session/output/session-ingress-envelope.schema.yaml` — ez a repo NINCS
    klónozva ehhez a jobhoz; ha a Sources-ban felsorolt fájlt nem éred el, a konvenciót az
    alábbi "Schema stílus-konvenció" szekcióból vedd át.

## Schema stílus-konvenció (mivel a cic-mcp-session repo nincs klónozva)

```yaml
apiVersion: cic.gateway/v1
kind: GatewayContextEnvelope
metadata:
  schema_id: "cic_mcp.gateway.context_envelope_contract"
  status: experimental
  created_at: "<ISO8601>"
  source_job: "gateway-context-envelope-contract-001"
  description: >
    <rövid leírás>

required:
  - apiVersion
  - kind
  - <stb.>

properties:
  apiVersion:
    type: string
    const: "cic.gateway/v1"
    description: >
      <miért const, mit kell a consumer-nek tennie eltérő verzióval>
  # ... minden mezőhöz hasonló blokk, description-nel
```

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. `GatewayContextEnvelope` YAML schema

Formalizáld a doc-tervből + az előző audit "GatewayContextEnvelope — Initial Boundary"
szekciójából a teljes schema-t, a "Schema stílus-konvenció" szerint. KÖTELEZŐ mezők
(`acceptance_gates` szerint, ez a minimum, bővíthető a doc-terv többi mezőjével is):

- `sources_used` — melyik `source_id`-kből épült a válasz (lista)
- `trust_summary` — a tartalom trust-szintjének összefoglalása (pl. melyik rész
  canonical/session/shared eredetű, milyen megbízhatósággal)
- `conflicts` — ismert konfliktusok a forrásrétegek között (lehet üres lista, de a mező
  KÖTELEZŐ — ha nincs konfliktus, explicit üres listát ad vissza, nem hiányzó mezőt)
- `proof_requirements` — mit kell még bizonyítani/ellenőrizni, mielőtt a válasz canonical
  igazságként kezelhető
- `refs` — a forrás-tartalmakra mutató referenciák (pl. chunk-id, session_id, file:line)

A schema-nak EXPLICIT meg kell különböztetnie a tartalom-mezőkben: `canonical_facts`
(cic-mcp-knowledge eredetű), `workdir_facts` (cic-factory/workdir eredetű),
`session_derived_notes` (cic-mcp-session eredetű), `shared_memory_notes` (cic-mcp-shared
eredetű) — ezek property-szinten elkülönült mezők legyenek, NEM egy közös "facts" mező
trust-tag-gel, mert a forrásréteg-eredet strukturális, nem csak metaadat.

A schema-nak tartalmaznia kell egy mezőt/jelölést is ami kimondja: a gateway maga NEM
tárol raw adatot és NEM tárol embedding-et — ezt vagy egy `metadata`/`description` szintű
megjegyzésként, vagy egy invariáns-leírásként rögzítsd (NEM kell hozzá futtatható kód,
csak a schema dokumentációja mondja ki explicit).

### 2. Kontraktus-report

Írd meg a `output/gateway-context-envelope-contract.md` riportot, ami:
- elmagyarázza a schema mezőit és a 4 tartalom-kategória (`canonical_facts`/`workdir_facts`/
  `session_derived_notes`/`shared_memory_notes`) elkülönítésének indokát
- EXPLICIT kimondja: a gateway nem tárol raw storage-ot, nem tárol embedding store-ot (ez a
  `cic-mcp-gateway/CLAUDE.md` trust modelljéből származó tétel, ide szintetizálva)
- EXPLICIT elválasztja a `GatewayContextEnvelope`-ot a forrás-specifikus MCP API-któl (pl.
  a `cic-mcp-session` 7 MCP tool-ja — `search_session_context`, `get_session_timeline` stb.
  — a gateway NEM ezeket a nyers válaszokat adja vissza, hanem a `GatewayContextEnvelope`-ba
  becsomagolt, trust-jelölt verziót)
- legalább **2 VALID** és **2 INVALID** envelope-példát tartalmaz (konkrét YAML/JSON
  blokkok, nem csak leírás) — az invalid példáknál EXPLICIT meg kell mondani MIÉRT
  invalid (pl. "hiányzik a `trust_summary`", "a `conflicts` mező hiányzik teljesen, nem
  csak üres lista", "nyers vektor-similarity hit van visszaadva trust-csomagolás nélkül —
  ez pont a forbidden shortcut")

## Nem cél

- source registry definiálása vagy implementálása (ez `gateway-source-registry-contract-001`)
- tényleges routing logika, MCP tool, vagy session/shared adapter kód írása (ez
  `gateway-session-adapter-contract-001` és társai)
- JSON-Schema validátor FUTTATHATÓ kódjának megírása (csak a YAML schema-fájl maga, leíró
  szinten — validátor implementáció egy következő jobé)
- `cic-mcp-session`/`cic-mcp-shared`/`cic-mcp-knowledge` repók módosítása

## Required Output Files

- `output/gateway-context-envelope-contract.md`
- `output/gateway-context-envelope.schema.yaml`

## Required Report Sections

```markdown
# gateway-context-envelope-contract-001 Output

## Scope
## Inputs Read
## Schema Summary
## Findings
## Claim-Evidence Matrix

| Claim | Status | Evidence | Verification Method | Risk |
|---|---|---|---|---|

## Valid Envelope Examples

(legalább 2, teljes YAML/JSON blokk)

## Invalid Envelope Examples

(legalább 2, teljes YAML/JSON blokk + miért invalid)

## Separation From Source-Specific MCP APIs
## Decisions Proposed
## Rejected / Out Of Scope
## Risks
## Definition Of Done Check
## Next Jobs
```

Elfogadott `Status` értékek: `proven`, `partial`, `missing`, `rejected`, `unknown`.
`proven` egy "a schema tartalmazza X mezőt" állításra KIZÁRÓLAG akkor használható, ha a
schema-fájl konkrét sora/property-blokkja idézve van — a mező EMLÍTÉSE a report
narratívájában ≠ a mező tényleges jelenléte a schema-fájlban, csak a tényleges
`output/gateway-context-envelope.schema.yaml` fájl-tartalom idézése bizonyít.

## Definition Of Done

- [ ] `output/gateway-context-envelope.schema.yaml` létrehozva, a stílus-konvenció szerint
- [ ] a schema tartalmazza: `sources_used`, `trust_summary`, `conflicts`,
      `proof_requirements`, `refs`
- [ ] a schema elkülöníti: `canonical_facts`, `workdir_facts`, `session_derived_notes`,
      `shared_memory_notes`
- [ ] a report explicit kimondja: gateway nem tárol raw storage-ot, nem tárol embedding
      store-ot
- [ ] a report legalább 2 valid + 2 invalid envelope példát tartalmaz, indoklással
- [ ] a report elválasztja a `GatewayContextEnvelope`-ot a forrás-specifikus MCP API-któl
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a gateway nyers vector-hit-eket ad vissza trust-envelope csomagolás nélkül — minden
  válasznak a `GatewayContextEnvelope`-on KELL átmennie, nincs "gyors út" közvetlen
  forrás-válasz visszaadásra
- a `conflicts`/`proof_requirements` mező opcionálisként kezelése — KÖTELEZŐ mezők, akkor
  is jelen kell lenniük (üres listaként), ha nincs aktuális konfliktus
- a 4 tartalom-kategória (`canonical_facts`/`workdir_facts`/`session_derived_notes`/
  `shared_memory_notes`) egy közös "facts" mezőbe összevonása trust-tag-gel — ez elveszti
  a forrásréteg-eredet strukturális garanciáját

## Git instrukciók

Push a `feature/gateway-context-envelope-contract-001` branch-re, KIZÁRÓLAG a
`cic-mcp-gateway` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni, elég a
lokális commit). Main-re az agent NEM pushol. **NE módosítsd a `meta.yaml` `status`
mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a schema mezőnevek/YAML kulcsok/kódrészletek angolul.
