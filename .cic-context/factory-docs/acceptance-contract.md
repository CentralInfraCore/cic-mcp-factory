# Factory Acceptance Contract

Ez a dokumentum a `factory-docs` csomag normativ resze.

A szavak jelentese:

- MUST: kotelezo. Hianya NO-GO.
- SHOULD: erosen ajanlott. Hianya indoklast igenyel.
- MAY: opcionális.

## Global NO-GO Rules

Egy factory job nem indithato, ha az `input.md` nem tartalmazza:

1. konkret target repo nev
2. konkret forras path vagy review artifact
3. konkret output fajlnev
4. claim-evidence tabla kovetelmeny
5. legalabb egy explicit tiltott rovidites
6. ellenorizheto Definition of Done
7. `status_after_merge` indoklas

## Universal Output Contract

Minden job output report MUST tartalmazza ezeket a szekciokat:

```markdown
# <job-id> Output

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

Elfogadott `Status` ertekek:

- `proven`
- `partial`
- `scaffold`
- `concept`
- `missing`
- `rejected`
- `unknown`

## Artifact Contract

Ha a job schema-t ad, akkor MUST:

- kulon schema fajl
- report, amely magyarazza a schema donteseket
- legalabb 2 pozitiv es 2 negativ validacios pelda
- idempotency es trust mezok explicit kezelese

Ha a job SQL-t ad, akkor MUST:

- kulon `.sql` fajl
- schema nevekkel tagolt DDL
- index strategia
- trigger/outbox hatar
- rollback/drop vagy migration note
- `what stays in worker` szekcio

Ha a job MCP tool contractot ad, akkor MUST:

- tool name
- input schema
- output schema
- error cases
- trust fields
- source refs
- reachability/registration plan

## Context Budget Contract

Egy job input MUST NOT tartalmazhat:

- teljes `thead01.txt`, `thead02.txt`, `thead04.txt`
- session + gateway + shared teljes implementaciot egyszerre
- historical importer feladatot ingress/storage contract elott

Egy job input SHOULD tartalmazzon:

- legfeljebb 5 forrast
- 1 target repot
- 1 output reportot
- 0-1 schema/SQL extra artifactot

## Session-Specific Contract

Session jobok MUST betartani:

```yaml
canonical: false
promotion_allowed: false
interpreted: false # ingress/raw szinten
default_scope: session_id
cross_session: false
```

Session jobok MUST NOT:

- shared memoryt epiteni
- canonical knowledge-t gyartani
- hook oldalon decision/claim extractiont vegezni
- globalis live `chunks.pkl` store-t tervezni

## Gateway-Specific Contract

Gateway jobok MUST betartani:

```yaml
gateway_role: trust_domain_context_compiler
owns_raw_storage: false
owns_embedding_store: false
returns_trust_envelope: true
```

Gateway jobok MUST NOT:

- session tablakat kozvetlenul hasznalni stabil adapter/API nelkul
- raw vector talalatokat trust envelope nelkul visszaadni
- generic proxykent definialni magukat

## PostgreSQL Contract

Postgres design jobok MUST kulon valaszolni:

1. melyik resz DB determinisztikus projection
2. melyik resz trigger
3. melyik resz outbox/job queue
4. melyik resz worker
5. melyik resz MCP read API
6. milyen index kell
7. milyen partitioning/inheritance allaspont van

Trigger MUST NOT:

- LLM-et hivni
- HTTP-t hivni
- embeddinget generalni
- hosszu batch feldolgozast vegezni

Trigger MAY:

- content hash-t ellenorizni
- generated/search mezot frissiteni
- outbox jobot enqueuelni
- notify-t kuldeni
- lightweight status mezot allitani

## Review Gate

Egy job output akkor tekintheto `GO` allapotunak, ha:

- minden kotelezo artifact letezik
- claim-evidence tabla nem ures
- legalabb egy negativ/tiltott rovidites ellenorzott
- DoD pontonkent PASS/PARTIAL/FAIL jelolve
- minden `implemented` allitasnak van runtime/reachability bizonyiteka

Ha barmelyik hianyzik:

```text
NO-GO: revise job input or rerun agent.
```
