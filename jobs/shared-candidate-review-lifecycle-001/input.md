# Job: shared-candidate-review-lifecycle-001

## Kontextus

A `shared_core.candidates` schema MÁR DB-szinten kikényszeríti, hogy
`canonical = TRUE` KIZÁRÓLAG `trust = 'reviewed_shared'`-nél lehetséges
(`candidates_canonical_requires_reviewed_shared` CHECK constraint, valós
Postgres-szel bizonyítva — lásd `shared-core-storage-implementation-001`
"Canonical Constraint - Real Postgres Proof"). A `shared-promotion-
candidate-logic-001` job pedig már implementálta a `mixed → candidate`
automatikus átmenetet (recurrence/weight alapján).

Ami HIÁNYZIK: egy tényleges, operátor által hívható eszköz, ami a
`candidate → reviewed_shared` átmenetet (vagy `→ superseded`/`→ rejected`)
VÉGREHAJTJA, és minden átmenetről audit-naplót vezet. Jelenleg ez a
döntés csak közvetlen, kézi SQL UPDATE-tel lenne kivitelezhető — nincs rá
felület, és nincs audit trail.

Ez a job EZT az operátor-felületet építi: egy CLI vagy MCP tool, ami egy
adott `candidate_id`-t `reviewed_shared`-re (vagy `superseded`/elvetett
állapotba) léptet, és minden átmenetet naplóz.

## Target

- target repo: `cic-mcp-shared`
- target path: egy review CLI/tool modul (pl. `shared_core/review_
  lifecycle.py`) + egy `shared_audit.candidate_transitions` audit-tábla
  migráció + a hozzá tartozó teszt + `output/shared-candidate-review-
  lifecycle.md`
- change_type: `new_capability`
- status_after_merge: `candidate`
- status indoklás: valós Postgres teszt bizonyítja a teljes átmenet-utat ÉS
  egy elutasított, érvénytelen átmenet-kísérletet, audit-log sorral
  mindkettőre

## Sources

- **KÖTELEZŐ elsődleges forrás:**
  - `output/shared-core-storage-schema.sql` — a `shared_core.candidates`
    TELJES schema, KÜLÖNÖSEN a `trust`/`canonical` CHECK constraint-ek
  - `jobs/shared-promotion-candidate-logic-001/output/shared-promotion-
    candidate-logic.md` — a már implementált `mixed → candidate` logika,
    amit ez a job NEM módosít, csak a KÖVETKEZŐ lépést (candidate →
    reviewed_shared) teszi kezelhetővé
  - `cic-mcp-shared/CLAUDE.md` "Trust modell" szekció

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Ellenőrizd, hogy `shared-promotion-candidate-logic-001` `done`
   állapotban van-e — ha NEM, állítsd a jobot NO-GO-ra, és állj meg
3. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 0. Pre-change állapot megerősítése

```
grep -rn "promote_to_reviewed_shared\|promote_to_canonical\|candidate_transitions" --include="*.py" shared_core/ | grep -v test_
```

Idézd a kimenetet (várhatóan 0 találat) — ez bizonyítja, hogy ez a
review-felület jelenleg NEM létezik.

### 1. Audit-tábla

Hozz létre egy `shared_audit.candidate_transitions` táblát (migrációként):
`transition_id`, `candidate_id` (FK), `from_trust`, `to_trust`,
`from_canonical`, `to_canonical`, `actor` (ki hajtotta végre — pl. egy
operátor-azonosító string), `reason` (szöveges indoklás), `created_at`.

### 2. Review-eszköz

Implementálj egy függvényt/CLI parancsot (pl.
`promote_to_reviewed_shared(candidate_id: str, actor: str, reason: str)`),
ami:
- ellenőrzi, hogy a candidate JELENLEG `trust IN ('candidate', 'mixed')`-e
  (ha már `reviewed_shared`, no-op vagy hiba, indokolva)
- frissíti a `trust`-ot `reviewed_shared`-re
- ÍR egy sort a `shared_audit.candidate_transitions`-be
- **NEM állítja `canonical = TRUE`-ra automatikusan** — a `canonical`
  beállítása EGY KÜLÖN, explicit hívás (pl.
  `promote_to_canonical(candidate_id, actor, reason)`), ami a DB CHECK
  constraint-et MEGELŐZŐEN saját validációval is ellenőrzi (`trust ==
  'reviewed_shared'`), majd a TÉNYLEGES DB constraint marad a végső
  kikényszerítő erő — ez a tool NEM bypassolja, csak előzetesen validál

Hasonló módon egy `reject_candidate(candidate_id, actor, reason)` és/vagy
`mark_superseded(candidate_id, superseded_by_id, actor, reason)` is kell.

### 3. Valós, futtatott bizonyíték

Valós Postgres teszttel bizonyítsd:
1. EGY teljes, érvényes átmenet-út: `mixed/candidate → reviewed_shared →
   canonical`, minden lépés után a sor TÉNYLEGES állapotát újraolvasva
2. EGY érvénytelen kísérlet: `promote_to_canonical()` hívása egy
   `trust='candidate'` sorra (NEM `reviewed_shared`) — a tool SAJÁT
   validációja elutasítja, ÉS (külön bizonyítva) ha valaki megkerülné a
   tool-t és direkt SQL-lel próbálná, a DB CHECK constraint is elutasítja
3. mindkét esethez a TÉNYLEGES `shared_audit.candidate_transitions` sor
   (vagy annak hiánya az elutasított esetnél, indokolva)

## Nem cél

- a `mixed → candidate` logika módosítása (`shared-promotion-candidate-
  logic-001`, MÁR kész, nem ennek a jobnak a hatóköre)
- a scoring-formula módosítása (`shared-scoring-rework-001`, KÜLÖN job)
- BÁRMILYEN automatikus (nem-operátor-hívott) `reviewed_shared`/`canonical`
  átmenet — ez a tool KIZÁRÓLAG explicit, ember által hívott művelet

## Required Output Files

- `output/shared-candidate-review-lifecycle.md`
- a review lifecycle modul
- az audit-tábla migráció
- a hozzá tartozó teszt-fájl

## Required Report Sections

```markdown
# shared-candidate-review-lifecycle-001 Output

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

- [ ] `shared_audit.candidate_transitions` tábla migrációként létrehozva
- [ ] `promote_to_reviewed_shared()`, `promote_to_canonical()`,
      `reject_candidate()`/`mark_superseded()` implementálva
- [ ] teljes érvényes átmenet-út valós Postgres teszttel bizonyítva,
      minden lépés újraolvasott állapotával
- [ ] érvénytelen átmenet-kísérlet elutasítva MIND a tool saját
      validációja, MIND a DB CHECK constraint szintjén, mindkettő
      bizonyítva
- [ ] audit-log sorok TÉNYLEGESEN megjelennek a táblában, mindkét esetre
      (érvényes és — ha releváns — elutasított kísérletre is)
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a review-eszköz léte ≠ implemented — a futtatott Postgres teszt
  kimenete bizonyít, a kód megírása nem; minden átmenet-állítást a
  tényleges UPDATE hívás file:line hivatkozásával kell alátámasztani
- bármilyen kód, ami `canonical = TRUE`-t állít a DB CHECK constraint
  megkerülésével (pl. constraint disable, raw UPDATE a tool validációja
  nélkül)
- automatikus (nem explicit operátor-hívott) promóció bármilyen heurisztika
  alapján
- audit-log kihagyása "egyszerű" vagy "alacsony kockázatú" átmeneteknél

## Git instrukciók

Push a `feature/shared-candidate-review-lifecycle-001` branch-re,
KIZÁRÓLAG a `cic-mcp-shared` célrepóban (a `cic-mcp-factory` saját
klónjában NEM kell pusholni, elég a lokális commit). Main-re az agent NEM
pushol. **NE módosítsd a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek/kód angolul.
