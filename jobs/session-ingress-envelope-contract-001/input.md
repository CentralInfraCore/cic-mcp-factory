# Job: session-ingress-envelope-contract-001

## Kontextus

A `cic-mcp-session` infra-pipelinje most már futtatható (`session-infra-pipeline-fix-001`
lezárva) — eddig viszont semmilyen session-specifikus contract nincs a repóban, csak az
örökölt MCP-szerver alapváz. Ez a job az
ELSŐ valódi tartalmi session-capability: a `SessionIngressEnvelope` schema formális
definíciója — az a formátum, amibe minden jövőbeli hook/import/provider payload-ot
csomagolni kell, MIELŐTT bármi session-store-ba kerülne.

Ez a job-slices.yaml Phase 1A szelete (`.cic-context/factory-docs/job-slices.yaml`,
`session-ingress-envelope-contract-001` bejegyzés) — innen másold át az acceptance gate-eket,
ne találd ki újra.

**Ez egy DESIGN/CONTRACT job, NEM kód-implementáció.** Az output egy report + egy schema
fájl, nincs futtatható kód, nincs pytest. A "Definition of Done" ennek megfelelően
schema-tartalom-alapú, nem teszt-futtatás-alapú.

## Target

- target repo: `cic-mcp-session`
- target path: `docs/contracts/` (vagy hasonló, az agent válassza meg a repo konvenciójának
  megfelelően, és idézze a választott path-ot)
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: ez egy schema-javaslat, nincs még implementáció ami ellene validálna
  (nincs ingest kód, nincs Postgres tábla) — `candidate`-hez kellene legalább egy működő
  importer/hook-collector job, ami a schema ellen tényleg validál valódi payload-ot.

## Sources

- `${WORKDIR}/.cic-context/factory-docs/job-slices.yaml` — `session-ingress-envelope-contract-001`
  bejegyzés (phase, acceptance_gates, required_evidence, forbidden_shortcuts) — ez NORMATÍV,
  a lenti gate-ek pontosan ebből vannak átemelve
- `${WORKDIR}/.cic-context/factory-docs/architecture.md` — "## Postgres-first elv" és
  "## Trust modell" szekciók, plusz a "### cic-mcp-session" Igen/Nem határ-lista
- `${WORKDIR}/.cic-context/corpus/normalized/thead-review-2026-06-20.yaml` — `dec-thead-0002`
  ("a hook nem interpretálhat szemantikusan, csak egy formális SessionIngressEnvelope-ba
  csomagolhatja a provider payload-ot"), `rag_implications` szekció (chunk metadata mezők)
- `${WORKDIR}/.cic-context/corpus/normalized/factory-systems-review-2026-06-20.yaml` —
  `fac-0005`, `risk-fac-0004` (a jelenlegi hook-logolás miért NEM elég gazdag forrás)
- **Kalibrációs referencia (csak olvasásra, NE módosítsd):**
  `/home/sinkog/sync/claude_factory/CIC/workdir/tools/hooks/log-event.py` — ez a JELENLEG
  létező, élesben futó hook-logoló mechanizmus (Claude Code PostToolUse/Stop eseményeket ír
  JSONL-be). Ez egy KONKRÉT, valódi raw payload minta, amit a schema-nak el kell tudnia
  fogadni/becsomagolni — használd referenciaként a "payload" és "raw preservation" mezők
  tervezéséhez, de NE vedd át a sémáját 1:1-ben (ez egy lightweight, summary-szintű logger,
  a `SessionIngressEnvelope`-nak gazdagabbnak kell lennie, lásd `risk-fac-0004`).

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. `search_nodes` a `SessionIngressEnvelope`, `session-ingress`, `trust-domain` fogalmakra —
   ha van már node, vedd figyelembe, ha nincs (várható, hogy nincs), ezt explicit jelezd

## Feladat

Definiáld a `SessionIngressEnvelope` schemát és validációs szabályait.

### Kötelező schema-mezők (job-slices.yaml acceptance_gates szerint)

- `apiVersion`, `kind`
- event identity (egyedi event azonosító)
- provider identity (`provider`, `provider_session_id`)
- `source` (honnan jött: hook/importer/manual stb.)
- `payload` (a raw provider payload, NEM interpretált)
- trust mezők (lásd `architecture.md` "Trust modell": `trust: session_local` /
  `session_derived`, `canonical: false`)
- raw preservation mező (a payload eredeti, módosítatlan formában megmarad)
- `interpreted: false` — ÁLLANDÓAN false ingress szinten, ezt a schema-nak KIKÉNYSZERÍTENIE
  kell, nem csak dokumentálnia

### Tiltott kombinációk (KÖTELEZŐ kikényszeríteni a schema validációs szabályaiban)

- `canonical: true` ÉS ingress-szintű envelope egyszerre — TILOS, a schema validációnak ezt
  el kell utasítania
- `interpreted: true` ingress szinten — TILOS, a hook/collector nem interpretálhat
  szemantikusan, csak csomagolhat (lásd `dec-thead-0002`)

### Idempotencia

Definiáld az idempotency key felépítését (milyen mezőkből, milyen sorrendben/hash-eléssel
áll össze) — ennek kell garantálnia, hogy ugyanaz a provider event kétszer ingest-elve NE
duplikálódjon a session_raw rétegben.

### Példák

Adj legalább 2 VALID és 2 INVALID envelope példát (JSON/YAML), az invalid példáknál
EXPLICIT írd oda melyik szabályt sértik (pl. "INVALID #1: canonical=true + interpreted=false
egyszerre ingress szinten — ez a kombináció maga nem tiltott, de canonical=true önmagában
TILOS ingress szinten" — legyél pontos, melyik konkrét szabály sérül).

## Nem cél

- Postgres tábla DDL megírása (külön job: `session-postgres-storage-design-001`)
- a hook (`log-event.py`) tényleges átírása/kiterjesztése (külön job:
  `session-hook-collector-001`, ha a job-slices.yaml-ban szerepel, vagy egy új job)
- importer implementáció (pl. ChatGPT `conversations.json` → envelope, külön job:
  `historical-chatgpt-importer-design-001`, lásd job-slices.yaml)
- MCP tool/API definíció a session olvasásra — ez egy következő réteg

## Required Output Files

- `output/session-ingress-envelope-contract.md`
- `output/session-ingress-envelope.schema.yaml`

## Required Report Sections

A report MUST kövesse az `.cic-context/factory-docs/acceptance-contract.md`
"Universal Output Contract" szakaszát:

```markdown
# session-ingress-envelope-contract-001 Output

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

Elfogadott `Status` értékek (schema-tervezési állítás, nem futtatott-kód-bizonyíték):
`proven`, `partial`, `missing`, `rejected`, `unknown`. Itt `proven` azt jelenti: "a schema
fájlban tényleg jelen van és a leírt szabályt tényleg kikényszeríti", NEM azt, hogy
"valódi adaton validálva van" (nincs még implementáció, ami ezt tudná).

## Definition Of Done

- [ ] `output/session-ingress-envelope.schema.yaml` tartalmazza mind a kötelező mezőt
      (apiVersion, kind, event identity, provider identity, source, payload, trust,
      raw preservation), idézve a schema releváns részét a reportban
- [ ] a schema validációs szabályai (vagy a hozzájuk tartozó leírás) EXPLICIT kizárják a
      `canonical: true` + ingress-szintű envelope kombinációt, és az `interpreted: true`
      ingress-szintű állítást — idézve a konkrét szabály-szöveget
- [ ] idempotency key felépítése definiálva, konkrét mezőlistával
- [ ] legalább 2 valid + 2 invalid envelope példa a reportban, az invalid példáknál
      megnevezett konkrét sértett szabállyal
- [ ] claim-evidence tábla kitöltve, nem üres
- [ ] explicit jelzett: a `cic-mcp-private`/jelenlegi `log-event.py` mintával összevetve mi
      hiányzik/bővül (nem kell új grep-bizonyíték, a meglévő `log-event.py` tartalom elég,
      idézd a releváns sorokat)

## Forbidden Shortcuts

- a schema fájl létezése nem bizonyítja, hogy a benne leírt validációs szabály tényleg
  kikényszerítve van — a konkrét enum/pattern/required mezőt kell idézni, nem csak azt
  hogy a fájl megvan
- a hook szemantikusan interpretál döntéseket/állításokat — ez TILOS ingress szinten, a
  schema-nak ezt nem szabad megengednie semmilyen mezőkombinációval
- `canonical: true` megengedett session ingress szinten — TILOS, a schema validációs
  szabályainak ezt explicit ki kell zárnia
- "a mező neve `trust` és van benne valami szöveg" ≠ "a trust modell tényleg kikényszerítve
  van" — a schema-nak enum/validációs szabályt kell adnia, nem csak egy szabad string mezőt
- "ez csak egy YAML fájl, nem kell bizonyíték" ≠ elfogadható — minden `proven` állításhoz a
  schema fájl konkrét, idézett részlete kell, nem csak állítás hogy "benne van"

## Git instrukciók

Push a `feature/session-ingress-envelope-contract-001` branch-re, a `cic-mcp-session`
célrepóban (mivel ott kerül a contract). Main-re az agent NEM pushol.

## Nyelvi szabály

A report magyarul készüljön, a schema mezőnevei/YAML kulcsok és a JSON/YAML példák angolul.
