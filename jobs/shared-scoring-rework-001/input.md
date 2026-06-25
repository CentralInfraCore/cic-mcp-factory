# Job: shared-scoring-rework-001

## Kontextus

Egy korábbi biztonsági/minőségi review (orchestrátor által függetlenül
megerősítve, közvetlen kódolvasással) feltárta, hogy `shared_core/
aggregator.py` `cross_session_score` formulája (268-294. sor) MINDEN
session-enkénti min-max normalizált értéket EGYSZERŰEN ÖSSZEAD
(`sum(sum(per_session_normalized.values()))`) — ez azt jelenti, hogy egy
sok session-ből összegyűlő, de gyengén releváns minta UGYANOLYAN magas (vagy
magasabb) `weight_score`-t kaphat, mint egy kevés, de erősen releváns
session-ből származó minta. Emellett grep-pel megerősítve: az
`aggregator.py`-ban NINCS `ON CONFLICT`/upsert SEHOL — minden aggregációs
futás ÚJ candidate sort szúr be, akkor is, ha ugyanazt a mintázatot már
korábban is észlelte (duplikáció, nincs idempotencia).

Ez a job EZT a két hibát javítja: (1) abszolút minimum relevance threshold +
session-enkénti score CAP (max vagy top-k súlyozott átlag az egyszerű
összegzés helyett) + minimum bizonyítékszám-gate, (2) candidate fingerprint +
idempotens `ON CONFLICT` upsert, hogy ismételt aggregációs futás UGYANAZT a
sort frissítse, ne duplikáljon.

**Ez a job NEM a `trust`/`canonical` DB-gát módosítása** (az MÁR helyesen
van, lásd `shared-core-storage-implementation-001` "Canonical Constraint -
Real Postgres Proof") — KIZÁRÓLAG a scoring-formula és az upsert-hiány
javítása.

## Target

- target repo: `cic-mcp-shared`
- target path: `shared_core/aggregator.py` módosítása + a hozzá tartozó
  teszt + `output/shared-scoring-rework.md`
- change_type: `fix`
- status_after_merge: `candidate`
- status indoklás: valós Postgres teszt bizonyítja MIND az idempotens
  upsertet, MIND a score-cap tényleges hatását

## Sources

- **KÖTELEZŐ elsődleges forrás:**
  - `shared_core/aggregator.py` — a TELJES fájl, KÜLÖNÖSEN a
    `cross_session_score` számítás (268-294. sor) és az `aggregate_cross_
    session()` insert-logika (322. sortól)
  - `output/shared-core-storage-schema.sql` — a `shared_core.candidates`
    TELJES schema (ezt a job NEM módosítja, csak az insert/update logikát
    az aggregator oldalán)
  - `jobs/shared-cross-session-search-001/output/shared-cross-session-
    search.md` (368-376. sor) és `jobs/shared-weighting-model-001/output/
    shared-weighting-model.md` (290-322. sor) — az EREDETI design, amit ez
    a job CÉLZOTTAN javít, NEM ír újra a nulláról

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. Pre-change állapot megerősítése

```
grep -rn "ON CONFLICT" --include="*.py" shared_core/ | grep -v test_
```

Idézd a kimenetet (várhatóan 0 találat) — ez bizonyítja a JELENLEGI
upsert-hiányt. Idézd a `cross_session_score` PONTOS jelenlegi formuláját
(268-294. sor) is.

### 2. Score-formula javítás

Implementáld:
- abszolút minimum relevance threshold (egy normalizált érték alatt a
  session NEM számít bele az aggregátumba)
- session-enkénti CAP: a `sum(sum(...))` helyett `max(...)` VAGY egy
  top-k súlyozott átlag (indokold a választást a "Decisions Proposed"
  szekcióban) — a cél, hogy egyetlen extrém session NE tudja egyedül
  felhúzni az aggregátumot az összegzés miatt
- minimum bizonyítékszám-gate: ha egy candidate-nek a bizonyíték-száma
  (`provenance_refs` hossza) egy minimum alatt van, NE keletkezzen
  candidate sor

### 3. Candidate fingerprint + idempotens upsert

Definiálj egy fingerprint-et (pl. a `keyword_description` és a forrás
session-ek halmazának hash-e — indokold a választást), és módosítsd az
insert-logikát `INSERT ... ON CONFLICT (fingerprint) DO UPDATE`-re, ami
frissíti a `weight_score`/`recurrence_count`/`provenance_refs`-et a MEGLÉVŐ
sornál, NEM szúr be duplikátumot. (A `shared_core.candidates` táblának
jelenleg nincs `fingerprint` oszlopa — adj hozzá egyet, migrációként,
hátrafelé kompatibilis módon, a meglévő sorokat NEM törölve.)

### 4. Valós, futtatott bizonyíték — MINDKÉT javítás

Valós Postgres teszttel bizonyítsd:
1. **Idempotencia**: ugyanazt az aggregációt kétszer futtatva UGYANAZ a
   candidate sor frissül (`candidate_id` változatlan), NEM jön létre második
   sor. Idézd a TÉNYLEGES előtte/utána `SELECT COUNT(*)` eredményt.
2. **Score-cap hatása**: egy fixture-ön, ahol egy session extrém magas,
   a többi alacsony — mutasd meg a RÉGI formula szerinti score-t ÉS az ÚJ
   formula szerinti score-t UGYANAZON a fixture-ön, bizonyítva hogy az új
   formula nem hagyja egyetlen session-nek dominálni az eredményt.

## Nem cél

- a `trust`/`canonical` CHECK constraint módosítása (MÁR helyes, lásd
  Kontextus)
- a candidate review/promote/reject lifecycle (`shared-candidate-review-
  lifecycle-001`, KÜLÖN job)
- a `provenance_refs` JSONB struktúrájának megváltoztatása — az upsertnél
  a meglévő refs-eket KIEGÉSZÍTENI kell, nem felülírni/elveszíteni

## Required Output Files

- `output/shared-scoring-rework.md`
- a módosított `shared_core/aggregator.py`
- a migráció (új `fingerprint` oszlop)
- a hozzá tartozó teszt-fájl

## Required Report Sections

```markdown
# shared-scoring-rework-001 Output

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

- [ ] pre-change `ON CONFLICT`-hiány és a régi formula grep/idézet
      bizonyítva
- [ ] minimum relevance threshold + session-enkénti score CAP + minimum
      bizonyítékszám-gate implementálva
- [ ] candidate fingerprint + `ON CONFLICT` upsert implementálva,
      migrációval
- [ ] idempotens rerun valós Postgres teszttel bizonyítva (COUNT változatlan)
- [ ] score-cap hatása valós, régi-vs-új összehasonlítással bizonyítva
- [ ] `provenance_refs` upsertnél KIEGÉSZÜL, nem törlődik (bizonyítva)
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a fingerprint/upsert kód léte ≠ implemented — a futtatott Postgres
  teszt kimenete bizonyít, a kód megírása nem; minden állítást a tényleges
  insert/update hívás file:line hivatkozásával kell alátámasztani
- a `trust`/`canonical` CHECK constraint módosítása vagy meggyengítése
- olyan upsert, ami a `provenance_refs`-et felülírja a korábbi futás
  refjeinek elvesztésével
- "idempotens" állítás valós, dupla-futtatott Postgres teszt nélkül
- a score-cap hatásának állítása a régi formula tényleges, idézett
  eredménye nélkül (csak az új formula bemutatása nem elég)

## Git instrukciók

Push a `feature/shared-scoring-rework-001` branch-re, KIZÁRÓLAG a
`cic-mcp-shared` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell
pusholni, elég a lokális commit). Main-re az agent NEM pushol. **NE
módosítsd a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek/kód angolul.
