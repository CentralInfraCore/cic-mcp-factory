# Job: shared-promotion-candidate-logic-001

## Kontextus

A `shared-cross-session-aggregator-implementation-001` job (mergelve) megírta a
`shared_core/aggregator.py`-t, amely minden aggregációs futás után BESZÚR egy
`shared_core.candidates` sort, `trust = 'candidate'` FELTÉTEL NÉLKÜL beírva
(`_insert_candidate()`, a `"candidate"` string literál hardkódolva). A
`PROMOTION_WEIGHT_THRESHOLD`/`PROMOTION_MIN_RECURRENCE` konstansok DEKLARÁLVA
vannak a modulban, DE SOHA nem kerülnek felhasználásra — ezt az a job maga is
explicit, transzparensen jelezte a saját riportjában ("Findings" 4. pont), és
javasolt egy követő jobot ennek a hiánynak a zárására. EZ a job az.

A `shared-weighting-model-001` riport (290-298. sor) a `promotion_candidate
(trust: candidate)` állapotot EGY AND-feltételhez köti:
`recurrence_count >= 2 AND weight_score >= THRESHOLD`. Jelenleg ez a feltétel
SOSEM kerül kiértékelésre — minden aggregált sor `trust = 'candidate'`-ot kap,
függetlenül attól, hogy a feltétel teljesül-e.

**KRITIKUS HATÁR**: ez a job KIZÁRÓLAG az `trust = 'candidate'` VAGY
`trust = 'mixed'` közötti döntést implementálja BESZÚRÁSKOR. A `reviewed_shared`/
`canonical` állapotba kerülés MINDIG emberi review-folyamat
(`cic-mcp-shared/CLAUDE.md` "Trust modell", a schema saját CHECK constraint-je
is kikényszeríti ezt) — ezt a job NEM érinti, NEM automatizálja.

## Target

- target repo: `cic-mcp-shared`
- target path: `output/shared-promotion-candidate-logic.md` + a
  `shared_core/aggregator.py` módosítása (NEM új fájl — a MEGLÉVŐ
  `_insert_candidate()` hívási helyén döntsd el a `trust` értékét) + a hozzá
  tartozó teszt-frissítés
- change_type: `fix`
- status_after_merge: `candidate`
- status indoklás: TÉNYLEGES, futtatható kód-javítás + valós Postgres-teszt,
  amely bizonyítja mindkét ágat (`candidate` ÉS `mixed` is tényleg bekerül a
  táblába a megfelelő bemenetre)

## Sources

- **KÖTELEZŐ elsődleges forrás (a `cic-mcp-factory` repo `main`-jén, MÁR ott van):**
  - `${WORKDIR}/jobs/index.yaml` — prerequisite-ellenőrzéshez `- id: "<job-id>"`
    kulccsal (NEM `job_id:`)
  - `${WORKDIR}/jobs/shared-weighting-model-001/output/shared-weighting-model.md` —
    290-298. sor: `promotion_candidate (trust: candidate)` feltétel:
    `recurrence_count >= 2 AND weight_score >= THRESHOLD` — EZ a kontraktus,
    amit a kódnak ténylegesen ki kell értékelnie
  - `${WORKDIR}/jobs/shared-cross-session-aggregator-implementation-001/output/
    shared-cross-session-aggregator-implementation.md` — "Findings" 4. pont:
    a `PROMOTION_WEIGHT_THRESHOLD`/`PROMOTION_MIN_RECURRENCE` deklarálva, de
    NEM felhasznált állapot leírása, és a "Next Jobs" szekció, ami EZT a jobot
    javasolja
- **MÁSODIK forrás (a `cic-mcp-shared` repo, a target, KLÓNOZVA):**
  - `shared_core/aggregator.py` — `PROMOTION_WEIGHT_THRESHOLD`/
    `PROMOTION_MIN_RECURRENCE` konstansok (kb. 78-79. sor) ÉS
    `_insert_candidate()` (kb. 360-410. sor), KÜLÖNÖSEN a hardkódolt
    `"candidate"` string literál a `cur.execute()` paraméter-tuple-ban — EZT
    a konkrét helyet kell módosítani
  - `tests/test_shared_core/test_aggregator.py` — a MEGLÉVŐ fixture-minta
    (`_seed_session()`, `two_synthetic_sessions`) — EZT a mintát bővítsd, NEM
    újra feltalálni
  - `shared_core/shared_storage_schema` referenciaként: a `trust` mező CHECK
    constraint-je (`'mixed', 'candidate', 'reviewed_shared'`) — csak a
    MEGENGEDETT értékek megerősítésére, NEM módosítandó

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. Prerequisite-ellenőrzés

```
grep -n '\- id: "shared-cross-session-aggregator-implementation-001"' -A 3 jobs/index.yaml
```

Idézd a kimenetet, erősítsd meg `status: "done"`. Ha NEM, NO-GO és állj meg.

### 2. Jelenlegi hardkódolt érték megtalálása — grep + audit

```
grep -rn "PROMOTION_WEIGHT_THRESHOLD\|PROMOTION_MIN_RECURRENCE\|\"candidate\"" --include="*.py" . | grep -v test_
```

Idézd a kimenetet. Erősítsd meg, hogy a `"candidate"` string ténylegesen
feltétel nélkül kerül a `cur.execute()` paraméter-tuple-ba (NEM csak
megemlítve van egy kommentben).

### 3. Gating-döntés implementáció

Hozz létre egy ÖNÁLLÓ, tisztán tesztelhető függvényt (pl.
`decide_trust_level(weight_score: float, recurrence_count: int) -> str`),
amely:
- `"candidate"`-ot ad vissza, HA `recurrence_count >= PROMOTION_MIN_RECURRENCE
  AND weight_score >= PROMOTION_WEIGHT_THRESHOLD` (a `shared-weighting-
  model-001` 290-298. sorának PONTOS AND-feltétele)
- `"mixed"`-et ad vissza EGYÉBKÉNT (a schema CHECK constraint megengedett
  legalacsonyabb trust-szintje egy automatikusan generált sorra — NEM
  `"reviewed_shared"`, az emberi review nélkül SOSEM)

Vezesd be ezt a függvényt a `_insert_candidate()` hívási helyén (vagy a hívó
oldalon, ÁTADVA a kiszámolt értéket) — a hardkódolt `"candidate"` literált
CSERÉLD ki a függvény visszatérési értékére. NE módosítsd a `weight_score`/
`recurrence_count` SAJÁT kiszámítási logikáját (az MÁR helyes és bizonyított,
ezt a jobot ez nem érinti).

### 4. Valós, futtatott bizonyíték — mindkét ág

Bővítsd a MEGLÉVŐ `test_aggregator.py` fixture-mintáját (vagy adj hozzá egy
új, hasonló szintetikus session-pár tesztet) úgy, hogy VALÓS Postgres +
VALÓS MCP subprocess ellen bizonyítsd:
1. egy szintetikus bemenet, amely TELJESÍTI az AND-feltételt → a beírt sor
   `trust = 'candidate'`
2. egy szintetikus bemenet, amely NEM teljesíti (pl. csak 1 session-ben van
   találat, `recurrence_count < 2`) → a beírt sor `trust = 'mixed'`

Idézd a TÉNYLEGES psql/pytest kimenetet mindkét esetre.

## Nem cél

- `reviewed_shared`/`canonical` állapotba automatikus átmenet (MINDIG emberi
  review, lásd "Kritikus határ")
- a `weight_score`/`recurrence_count` kiszámítási formula módosítása (ÉPÍTS
  a meglévőre, NE írd újra)
- már beírt sorok trust-értékének utólagos frissítése/re-evaluálása (a
  jelenlegi aggregátor minden futásnál ÚJ sort szúr be, nincs UPSERT-pattern
  — ezt a jobot ez nem érinti, ne vezess be UPSERT-et)
- a `PROMOTION_WEIGHT_THRESHOLD`/`PROMOTION_MIN_RECURRENCE` numerikus
  értékének módosítása (a `shared-weighting-model-001` szerint ez
  implementációs döntés volt, MÁR eldöntve az előző jobban — ne változtasd)

## Required Output Files

- `output/shared-promotion-candidate-logic.md`
- a módosított `shared_core/aggregator.py`
- a hozzá tartozó teszt-frissítés

## Required Report Sections

```markdown
# shared-promotion-candidate-logic-001 Output

## Scope
## Inputs Read
## Prerequisite Check
## Hardcoded Value — Found And Confirmed
## Gating Decision Implementation
## Real Postgres + Real MCP Subprocess Proof — Both Branches
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
`proven` egy "a gating helyesen dönt" állításra KIZÁRÓLAG akkor használható, ha
a TÉNYLEGES, futtatott teszt mindkét ágra (candidate ÉS mixed) a tényleges
beírt `trust` értékkel idézve van — a függvény leírása a kódban nem bizonyítja,
hogy helyesen fut.

## Definition Of Done

- [ ] a prerequisite `id:` kulccsal megerősítve, GO/NO-GO döntés indokolva
- [ ] a jelenlegi hardkódolt `"candidate"` érték file:line hivatkozással
      megtalálva és idézve
- [ ] ÖNÁLLÓ `decide_trust_level()` (vagy ekvivalens) függvény, a PONTOS
      AND-feltétellel, file:line hivatkozással
- [ ] valós Postgres + valós MCP subprocess teszt MINDKÉT ágra (candidate ÉS
      mixed), a tényleges beírt `trust` értékekkel bizonyítva
- [ ] claim-evidence tábla kitöltve, nem üres
- [ ] a riport NEM állítja, hogy `reviewed_shared`/`canonical` automatikus
      átmenet implementálva lett

## Forbidden Shortcuts

- a `"candidate"` hardkódolt érték megemlítése/leírása anélkül, hogy a
  TÉNYLEGES kódban kicserélődne
- csak EGY ág (csak `candidate` VAGY csak `mixed`) tesztelése — MINDKETTŐ
  kötelező
- `reviewed_shared`/`canonical` automatikus beállítása bármilyen heurisztika
  alapján
- UPSERT-pattern bevezetése (a "Nem cél" explicit kizárja)
- a fájl/kód léte ≠ implemented (ez egyetlen soron) — a futtatott teszt
  kimenete bizonyít, a kód megírása nem

## Git instrukciók

Push a `feature/shared-promotion-candidate-logic-001` branch-re, KIZÁRÓLAG a
`cic-mcp-shared` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell
pusholni, elég a lokális commit). Main-re az agent NEM pushol. **NE módosítsd
a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek/kód angolul.
