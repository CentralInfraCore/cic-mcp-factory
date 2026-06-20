# Claude Job Authoring Guide

Ez a guide azt rogziti, hogyan kell a fenti architekturat Claude/factory jobokra bontani ugy, hogy ne egye meg a context windowt es ne romoljon a kivitelezes minosege.

## Fo szabaly

Egy job egyetlen konkret capability-szeletet oldjon meg.

Nem jo:

```text
Tervezd meg a sessiont, gatewayt, sharedet es implementald Postgresben.
```

Jo:

```text
Tervezd meg a SessionIngressEnvelope schema elso verziojat a cic-mcp-session repohoz.
Output: schema + claim-evidence report.
```

## Context budget

Egy agent job inputban maximalisan:

- 1 celkomponens
- 1 fazis
- 1 target repo
- 1-2 review artifact
- 1 output kovetelmeny lista
- 1 DoD

Kerulendo:

- teljes thead fajlok beadása
- tobb repo teljes feltérképezése egyszerre
- session + gateway + shared egy jobban
- schema + runtime + tests + importer egy jobban

## Input.md szerkezet

```text
# Job: <job-id>

## Kontextus
Rovid, 10-20 soros magyar osszefoglalo.

## Target
- target repo
- target path, ha ismert
- change type
- status_after_merge

## Forrasok
- konkret fajlok/pathok
- review artifactok
- tilos teljes raw thead feldolgozas, hacsak nem indokolt

## Feladat
Pontosan mit kell megtervezni/megvalositani.

## Nem cel
Mit ne csinaljon az agent.

## Output
Konkret output fajlok.

## Claim-evidence tabla
Kotelezo formatum.

## Definition of Done
Ellenorizheto pontok.

## Tiltott roviditesek
Explicit "X != Y" szabalyok.
```

## Factory validaciohoz illeszkedo kotelezo elemek

Minden job input tartalmazzon:

- konkret source path vagy review artifact
- legalabb egy explicit tiltott rovidites
- konkret output fajlnev
- claim-evidence tabla kovetelmeny
- ellenorizheto DoD
- reachability artifact, ha runtime/tool capabilityrol van szo

Minden job input hivatkozzon erre:

```text
.cic-context/factory-docs/acceptance-contract.md
```

Az acceptance contract relevans reszei MUST bekeruljenek az `input.md`-be. Nem eleg csak linkelni, ha az agent nem latja a fajlt a target workspace-ben.

## Claim-evidence tabla

Minden outputban:

```markdown
| Allitas | Statusz | Bizonyitek | Verifikacios modszer | Kockazat |
|---|---|---|---|---|
```

Statusz lehet:

- proven
- partial
- scaffold
- concept
- rejected
- unknown

## Minimal input.md sablon

```markdown
# Job: <job-id>

## Context

Ez a job a <target repo> repo <capability> szeletet kezeli.

## Target

- target repo: `<repo>`
- target path: `<path vagy "repo root">`
- change_type: `<new_capability|enhancement|fix>`
- status_after_merge: `<experimental|candidate|canonical>`
- status indoklas: `<miert ez>`

## Sources

- `<konkret path vagy review artifact>`
- `<konkret path vagy review artifact>`

## Task

<Egy mondatban a konkret feladat.>

## Not A Goal

- <mit ne csinaljon>
- <mit ne csinaljon>

## Required Output Files

- `output/<report>.md`
- `output/<schema-or-sql>.yaml|sql` ha kell

## Required Report Sections

Must follow `.cic-context/factory-docs/acceptance-contract.md` Universal Output Contract.

## Definition Of Done

- [ ] <ellenorizheto pont>
- [ ] <ellenorizheto pont>
- [ ] claim-evidence table kitoltve

## Forbidden Shortcuts

- `<X> != <Y>`
- `<X> != <Y>`
```

## Context-size vedelmi szabalyok

Ha egy job tul nagy:

- bontsd contract/design/implementation/test szeletekre
- eloszor csak audit
- utana csak schema
- utana csak minimal runtime
- utana csak integration

Pelda:

```text
session-postgres-storage-design-001
  csak DDL es trigger/outbox hatar

session-raw-event-store-001
  csak session_raw ingest + idempotency

session-turn-projector-001
  csak raw -> turns projection

session-search-api-001
  csak FTS/vector/hybrid read API
```

## Agent minosegi elvaras

Az agent ne kitalalja a repo mintat. Elobb nezze meg:

- README/CLAUDE.md
- schema/migrations/tooling
- meglévő API mintak
- teszt mintak

De az input ne adja oda az egesz vilagot. Csak irja elo, mit kell feltarni.

## Stop rule

Ha az agent alapveto architekturális hibat talal:

- ne implementaljon tovabb
- irjon `output/blockers.md` vagy a kotelezo reportban "NO-GO" szekciot
- adjon konkret uj job javaslatot

## Canonical tiltás

Session/gateway/shared korai jobban tilos:

```yaml
canonical: true
promotion_allowed: true
```

Kivetel csak akkor, ha a job kifejezetten reviewed knowledge promotionrol szol.
