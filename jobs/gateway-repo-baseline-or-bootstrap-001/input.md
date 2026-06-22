# Job: gateway-repo-baseline-or-bootstrap-001

## Kontextus

Ez a `cic-mcp-gateway` réteg ELSŐ factory capability-jobja (Phase 1B). A repo bootstrap-ja
("base-repo" `mcp/main` branch-ből, docs/CLAUDE.md gateway-specifikus customizálása)
out-of-band, factory job nélkül MÁR megtörtént (`bootstrap_status:
done_out_of_band_2026-06-20` a `job-slices.yaml`-ban) — a `cic-mcp-gateway` repo `main`-jén
a `CLAUDE.md` és a `docs/{hu,en}/architecture.{md,yaml}` már gateway-specifikus szöveget
tartalmaz. EZ a job NEM a bootstrap-ot végzi el (az már megvolt), hanem AUDITÁLJA és
DOKUMENTÁLJA az eredményt egy formális factory output-ban (`output/gateway-baseline.md`),
és kijelöli a gateway minimális felelősségi körét + a következő gateway contract jobot —
implementáció (routing logika, MCP tool-ok, GatewayContextEnvelope tényleges kódja) NEM cél.

A `cic-mcp-session` réteg (Phase 3) ezzel a job-bal lezárva (`session-mcp-venv-fix-001` —
mindkét MCP szerver host-natív indítása javítva, teljes pipeline bizonyítva). A gateway a
KÖVETKEZŐ réteg, ami a session-source-ot (és később shared/knowledge-et) adapterként fogja
fogyasztani — de előbb saját, session-független kontraktusra van szüksége
(`GatewayContextEnvelope`, source registry), hogy ne a session API-világához igazodva nőjön.

## Target

- target repo: `cic-mcp-gateway`
- target path: `output/gateway-baseline.md` (ÚJ fájl — a repo gyökerében nincs még `output/`
  könyvtár, létre kell hozni)
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: ez egy audit + kontraktus-vázlat job, nincs futtatható kód, nincs teszt —
  `candidate`-hez egy tényleges `gateway-context-envelope-contract-001` implementáció kellene

## Sources

- `${WORKDIR}/.cic-context/factory-docs/architecture.md` — "cic-mcp-gateway" szekció (Igen/Nem
  határok) — NORMATÍV
- `${WORKDIR}/.cic-context/factory-docs/execution-phases.md` — "Phase 1B - cic-mcp-gateway
  Baseline" szekció — NORMATÍV
- `${WORKDIR}/.cic-context/corpus/normalized/thead-review-2026-06-20.yaml` — `dec-thead-0005`
  ("cic-mcp-gateway is a trust-domain aware context compiler, not a generic search proxy")
  és `architecture_summary.gateway_layer`
- **KÖTELEZŐ elsődleges forrás (a `cic-mcp-gateway` repo `main`-jén, MÁR ott van):**
  - `cic-mcp-gateway/CLAUDE.md` — a már customizált gateway-scope dokumentáció (Igen/Nem
    határok, trust modell, tiltott rövidítések) — ÉRTSD MEG, MIELŐTT bármit írnál, NE
    ismételd meg szó szerint, SZINTETIZÁLD a saját auditodba
  - `cic-mcp-gateway/docs/hu/architecture.md` és `cic-mcp-gateway/docs/en/architecture.md`
  - `cic-mcp-gateway/source/` — ellenőrizd hogy tényleg üres-e (csak `.gitkeep`)

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. Repo státusz audit — grep-alapú, nem csak "elolvastam"

Határozd meg: a `cic-mcp-gateway` repo jelenlegi állapota `exists` / `scaffold` /
`bootstrap-required` (a `required_evidence` szerinti pontos kategorizálás). A döntésedet
GREP-pel bizonyítsd, NE csak narratívával:

```
grep -rn "gateway" --include="*.py" cic-mcp-gateway/ | grep -v test_ | grep -v "/tools/" | grep -v "/p_venv/"
```

(vagy ekvivalens — a cél: bizonyítani, hogy a `mcp-server/server.py`/`make_source.py` a
generikus `base-repo` KB-template kódja, NEM gateway-specifikus implementáció — tehát a
repo könyvtárszerkezetének léte ≠ gateway capability implementálva.)

Az eredményt (file:sor szintű találatok VAGY a "0 gateway-specifikus találat" tény) idézd
az outputban.

### 2. Minimális gateway felelősségi kör (kontraktus-vázlat, NEM kód)

Szintetizáld (ne csak idézd) az `architecture.md` "cic-mcp-gateway" Igen/Nem listáját +
a `cic-mcp-gateway/CLAUDE.md` trust modelljét egy rövid, saját szavaiddal írt
összefoglalóba: mit fog a gateway csinálni, mit NEM (raw event store, embedding store,
factory runner, canonical promotion — ezek explicit "Nem" tételek).

### 3. Source registry kezdeti határ (vázlat)

Vázold fel (mezőlista/YAML-skeleton szinten, NEM implementáció): mi egy "source" a gateway
szempontjából (pl. `cic-mcp-session`, `cic-mcp-shared`, `cic-mcp-knowledge`, `workdir` mint
trust-domain-ek), és milyen minimális metaadatot kell egy source registry bejegyzésnek
tartalmaznia (pl. `source_id`, `trust_domain`, `owns_raw_storage: bool`,
`returns_trust_envelope: bool`).

### 4. `GatewayContextEnvelope` kezdeti határ (vázlat)

Vázold fel (mezőlista szinten, NEM teljes schema, NEM implementáció) a
`GatewayContextEnvelope` minimális mezőit — legalább: honnan jött a kontextus
(`source_id`/`trust_domain`), mi a tartalom, milyen trust-jelölés van rajta. Ez egy
KÖVETKEZŐ job (`gateway-context-envelope-contract-001`) bemenete lesz, NEM ennek a jobnak
kell teljes schemát szállítania.

### 5. Következő gateway contract job javaslata

Javasolj egy konkrét következő job-id-t + 2-3 mondatos indoklást (az
`execution-phases.md` "Phase 1B" listája alapján, de a saját auditod eredményével
indokolva — NE csak átmásolva).

## Nem cél

- routing logika, MCP tool-ok, vagy bármilyen tényleges gateway-kód implementálása
- `cic-mcp-session`/`cic-mcp-shared`/`cic-mcp-knowledge` repók módosítása
- a `CLAUDE.md`/`docs/architecture.md` MEGÍRÁSA vagy átírása (már megtörtént, out-of-band)
  — csak audit, ne duplikáld a customizációt
- teljes `GatewayContextEnvelope` vagy source registry SCHEMA leszállítása (ez egy
  következő jobé)

## Required Output Files

- `output/gateway-baseline.md`

## Required Report Sections

```markdown
# gateway-repo-baseline-or-bootstrap-001 Output

## Scope
## Inputs Read
## Repo Status Audit

(grep eredmény idézve, file:sor vagy "0 találat" + indoklás)

## Findings
## Claim-Evidence Matrix

| Claim | Status | Evidence | Verification Method | Risk |
|---|---|---|---|---|

## Minimal Gateway Responsibility
## Source Registry — Initial Boundary
## GatewayContextEnvelope — Initial Boundary
## Decisions Proposed
## Rejected / Out Of Scope
## Risks
## Definition Of Done Check
## Next Jobs
```

Elfogadott `Status` értékek: `proven`, `partial`, `missing`, `rejected`, `unknown`.
`proven` KIZÁRÓLAG akkor használható egy "nincs gateway-specifikus implementáció" jellegű
állításra, ha a grep-kimenet (file:sor VAGY "0 találat") idézve van — a repo könyvtárszerkezetének
léte ≠ implementált gateway capability, csak a tényleges grep-eredmény bizonyít.

## Definition Of Done

- [ ] repo státusz (`exists`/`scaffold`/`bootstrap-required`) megállapítva, grep-bizonyítékkal
- [ ] explicit kijelentve, hogy a gateway NEM generikus proxy (`route_query != search_all`)
- [ ] explicit kijelentve, hogy a gateway NEM tárol session raw adatot
- [ ] minimális gateway felelősségi kör szintetizálva (nem csak idézve)
- [ ] source registry kezdeti határ felvázolva
- [ ] `GatewayContextEnvelope` kezdeti határ felvázolva
- [ ] következő gateway contract job javasolva, indoklással
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- `route_query == search_all` — a gateway NEM lehet "keresd meg mindenhol" proxy
- a gateway session raw adatot tárol — ez a `cic-mcp-session` réteg felelőssége, a gateway
  Nem-listájában explicit szerepel
- a repo könyvtárstruktúrájának/template-fájljainak léte alapján "gateway implementálva"
  állítás grep-bizonyíték nélkül

## Git instrukciók

Push a `feature/gateway-repo-baseline-or-bootstrap-001` branch-re, KIZÁRÓLAG a
`cic-mcp-gateway` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni, elég a
lokális commit). Main-re az agent NEM pushol. **NE módosítsd a `meta.yaml` `status`
mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek angolul.
