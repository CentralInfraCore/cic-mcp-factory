# Job: factory-session-bridge-001

## Kontextus

Phase 2 második jobja. A `factory-systems-review-2026-06-20.yaml` (fac-0001–fac-0006,
risk-fac-0004) megállapította: a factory job-lifecycle (`meta.yaml`, `jobs/index.yaml`)
MÁR tartalmaz session-identitáshoz közeli mezőket (`agent.session_id`,
`timestamps.started/completed`, `job_id`), de a `workdir/tools/hooks/log-event.py` jelenlegi
`events.jsonl` kimenete SZÁNDÉKOSAN könnyűsúlyú összefoglaló, nem a teljes raw payload —
"Do not use current events.jsonl as the final session source-of-truth" (risk-fac-0004
explicit ajánlása). Ez a job definiálja a HIDAT: a factory job-lifecycle saját
metaadatai HOGYAN fordíthatók le egy `SessionIngressEnvelope`-ba, amit a `cic-mcp-session`
be tud tölteni — KONTRAKTUS-szinten, NEM implementáció (nincs tényleges collector-kód).

**Önreferens eset**: a target repo EBBEN a jobban `cic-mcp-factory` MAGA — nincs külön
target-repo klón, a riport a `cic-mcp-factory` saját `jobs/factory-session-bridge-001/output/`
mappájába kerül, push a `feature/factory-session-bridge-001` branch-re KÖZVETLENÜL a
`cic-mcp-factory`-ban (nem egy másik repóba).

## Target

- target repo: `cic-mcp-factory` (önmaga — lásd "Önreferens eset" fent)
- target path: `output/factory-session-bridge.md`
- change_type: `enhancement`
- status_after_merge: `experimental`
- status indoklás: kontraktus-riport, nincs futtatható bridge/collector kód —
  `candidate`-hez egy tényleges implementáció (a riport "Next Jobs" szekciójában
  javasolt) és legalább egy valós job-on átfutó próba kellene

## Sources

- `${WORKDIR}/.cic-context/corpus/normalized/factory-systems-review-2026-06-20.yaml` —
  TELJES egészében — NORMATÍV (fac-0001–fac-0006, risk-fac-0001–0004,
  recommended_next_jobs)
- `${WORKDIR}/.cic-context/factory-docs/architecture.md` — "Factory legitimacio" szekció
- **KÖTELEZŐ elsődleges forrás (a `cic-mcp-factory` repo `main`-jén, MÁR ott van):**
  - `${WORKDIR}/jobs/.schema/meta.yaml` — a TELJES `meta.yaml` mező-séma (minden mező,
    kommentekkel) — ez a tényleges forrása annak, mit "tud" egy factory job session-
    szempontból
  - `${WORKDIR}/jobs/index.yaml` — a generált index struktúrája (`tools/update-index.sh`
    állítja elő) — milyen mezőket aggregál jobonként
  - `${WORKDIR}/tools/run-job.sh` — hol kerül be az `agent.session_id` a meta.yaml-ba,
    hogyan kapcsolódik a feature branch-hez
  - `${WORKDIR}/.cic-context/factory-docs/job-slices.yaml` — a `factory-session-bridge-001`
    saját bejegyzése (acceptance_gates, required_evidence, forbidden_shortcuts) — ez
    NORMATÍV a job elvárásaira
- **Másodlagos, NEM ehhez a repóhoz tartozó referencia** (NE klónozd, NE módosítsd —
  csak a `factory-systems-review-2026-06-20.yaml`-ban van RÓLA szó, a tényleges fájl egy
  MÁSIK, nem klónozott repóban él): `workdir/tools/hooks/log-event.py` — a jelenlegi
  könnyűsúlyú hook-logging mintája, amit a riportban CSAK a corpus-fájl idézeteiből
  szabad jellemezni, nem egy közvetlenül megnyitott fájlból

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. Mely `meta.yaml`/session mezők szükségesek a session-katalógushoz

Először GREP-pel szedd ki a `jobs/.schema/meta.yaml` TELJES mezőlistáját (a teszt-fájlok
nem relevánsak itt, de a kizárás konzisztens maradjon a mintával):

```
grep -rn "^[a-z_]*:" jobs/.schema/meta.yaml | grep -v test_
```

Idézd a teljes kimenetet. Ebből KONKRÉTAN listázd fel, mely mezők (file:line
hivatkozással) közvetlenül megfelelnek egy `SessionIngressEnvelope`/session-katalógus
mezőnek (pl. `job_id` → `provider_session_id`-szerű azonosító, `agent.session_id` → a
tényleges Claude Code session, `timestamps.*` → `occurred_at`/`ingested_at`). Mely
MEGLÉVŐ mező HIÁNYZIK, amit a session-katalógushoz fel kellene venni?

### 2. Miért nem elég a jelenlegi `events.jsonl`

Szintetizáld (ne csak idézd) a `factory-systems-review-2026-06-20.yaml` risk-fac-0004 +
fac-0005 megállapításait: miért nem alkalmas a jelenlegi könnyűsúlyú hook-event-log
végső session source-of-truth-nak.

### 3. Bridge-javaslat: factory job-lifecycle → `SessionIngressEnvelope`

Vázolj egy konkrét mezőleképezést (tábla formátumban: factory `meta.yaml` mező →
`SessionIngressEnvelope` mező → megjegyzés) — NEM teljes implementáció, csak a leképezés
maga. Jelöld explicit, ahol egy ÚJ mezőt kellene a `meta.yaml` schema-hoz adni (és hol
NEM — pl. ha egy meglévő mező már elég).

### 4. Migrációs/kompatibilitási terv a meglévő jobokra

A `jobs/` alatt MÁR ~25+ lezárt job van a régi `meta.yaml` formátummal. Definiáld:
ezeknek KELL-e retroaktívan bridge-elve lenniük, vagy a bridge csak ÚJ jobokra
vonatkozik mostantól — indokold a választást.

## Nem cél

- tényleges collector/bridge kód implementálása
- a `jobs/.schema/meta.yaml` SCHEMA módosítása (ha új mezőt javasolsz, JELEZD a
  riportban, NE módosítsd csendben a séma-fájlt)
- `cic-mcp-session`/`cic-mcp-gateway` repók módosítása
- a `workdir/tools/hooks/log-event.py` tényleges megnyitása/módosítása (az egy MÁSIK,
  nem klónozott repóban él — csak a corpus-fájl idézeteiből jellemezhető)

## Required Output Files

- `output/factory-session-bridge.md`

## Required Report Sections

```markdown
# factory-session-bridge-001 Output

## Scope
## Inputs Read
## Existing meta.yaml Fields Mapped

(file:line idézve a jobs/.schema/meta.yaml-ból minden felhasznált mezőre)

## Why events.jsonl Is Not Enough
## Bridge Proposal — Field Mapping Table
## Migration/Compatibility Plan
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
`proven` egy "a `meta.yaml` tartalmazza X mezőt" állításra KIZÁRÓLAG akkor használható,
ha a `jobs/.schema/meta.yaml` konkrét sora idézve van — a mező megemlítése a riportban
nem bizonyítja a tényleges fájl-tartalmat, a fájl léte ≠ implemented, csak a tényleges
sor idézése bizonyít.

## Definition Of Done

- [ ] a `meta.yaml` session-releváns mezői file:line-nal felsorolva
- [ ] az `events.jsonl` elégtelenségének indoklása szintetizálva (nem csak idézve)
- [ ] mezőleképezési tábla (factory mező → SessionIngressEnvelope mező) kész
- [ ] migrációs/kompatibilitási döntés indoklással
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a jelenlegi `events.jsonl`-t végső session source-of-truth-ként kezelni (ez a
  job-slices.yaml explicit tiltott rövidítése)
- a `jobs/.schema/meta.yaml` séma csendes módosítása
- collector/bridge FUTTATHATÓ kódjának megírása

## Git instrukciók

Ez egy ÖNREFERENS job — a target repo MAGA a `cic-mcp-factory`. Push a
`feature/factory-session-bridge-001` branch-re KÖZVETLENÜL a `cic-mcp-factory`-ban (NINCS
külön target-repo klón ehhez a jobhoz). **NE módosítsd a `meta.yaml` `status` mezőjét**
sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/mezőnevek angolul.
