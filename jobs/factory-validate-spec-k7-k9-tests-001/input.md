# Job: factory-validate-spec-k7-k9-tests-001

## Kontextus

A `factory-tooling-test-suite-001` job (mergelve) megírta a `tests/test_validate_spec.py`
pytest-suite-ot `tools/validate-spec.sh`-hoz — DE csak a K1/K3/K4/K8 kritériumokra van
fixture+teszt (`tests/fixtures/validate_spec/{k1,k3,k4,k8}_violation.md` + `go.md`). A
`tools/validate-spec.sh` MAGA viszont K7/K7b/K9 kritériumokat is gépi kényszerként
ellenőrzi (42-58. sor) — ezekre EGYÁLTALÁN NINCS teszt, és ezt a JELEN orchestrátor-
session aktívan, ismételten kihasználta minden egyes capability-job spec validálásánál
(`bash tools/validate-spec.sh <job-id>` minden jobnál K1-K9-et ellenőrizte, de a K7/K9
szabályok SOHA nem voltak saját teszttel fedve, miközben a script logikájuk MÁR rég
megírt és élesben futott).

**Ez egy valós regresszió-kockázat**: ha valaki módosítja a K7/K9 grep-mintát
`validate-spec.sh`-ban (pl. egy jövőbeli K10 hozzáadásakor véletlenül összetöri a
meglévő feltételes logikát), SEMMILYEN teszt nem buktatná el a CI-t — pont az a
védelem hiányzik, amit a `factory-tooling-ci-001` egyébként már be is kötött
(`.github/workflows/tests.yml`, minden PR/push-on lefut).

A `cic-mcp-factory/CLAUDE.md` "Ismert korlátok / roadmap" szekciója jelenleg ELAVULTAN
azt állítja, hogy "nincs hozzájuk bats/pytest suite" — ez RÉSZBEN igaz (K7/K9-re), de a
K1/K3/K4/K8-ra már hamis (azok lefedettek). Ez a job NEM a teljes szöveg felülírása,
csak a tényleges, fennmaradó hiány (K7/K9) zárása — a CLAUDE.md frissítése a riport
"Findings" szekciójában javasolt, NEM ennek a jobnak kell elvégeznie.

## Target

- target repo: `cic-mcp-factory` (EZ a repo — a `capability.target_repo` mező
  speciális esete, ahol a target_repo EGYBEESIK a `cic-mcp-factory` automatikusan
  klónozott klónjával, NEM külön klón — lásd "Git instrukciók")
- target path: `output/factory-validate-spec-k7-k9-tests.md` + a
  `tests/fixtures/validate_spec/` ÚJ fixture-fájljai + a `tests/test_validate_spec.py`
  bővítése
- change_type: `enhancement`
- status_after_merge: `candidate`
- status indoklás: TÉNYLEGES, futtatható pytest-tesztek a MEGLÉVŐ, élesben futó
  `tools/validate-spec.sh` K7/K9 logikája ellen, a meglévő CI (`tests.yml`) alá esve

## Sources

- **KÖTELEZŐ elsődleges forrás (a `cic-mcp-factory` repo `main`-jén, MÁR ott van):**
  - `${WORKDIR}/jobs/index.yaml` — prerequisite-ellenőrzéshez `- id: "<job-id>"`
    kulccsal (NEM `job_id:`)
  - `${WORKDIR}/tools/validate-spec.sh` — a TELJES K7/K7b/K9 logika (42-58. sor):
    a feltételes triggerelés (`audit|call.chain|implemented|scaffold|hívódik|...`),
    a `grep -rn|grep -r ` előírás (K7), a teszt-fájl-kizárás előírás (K7b), a
    reachability artifact előírás (K9)
  - `${WORKDIR}/tests/test_validate_spec.py` — a MEGLÉVŐ teszt-minta (`_make_job_dir`,
    `_run_validate_spec`, a K1/K3/K4/K8 teszt-függvények alakja) — EZT a mintát kell
    követni, NEM újra feltalálni
  - `${WORKDIR}/tests/fixtures/validate_spec/go.md` és `k8_violation.md` — a MEGLÉVŐ
    fixture-stílus (rövid, magyar nyelvű, minimális tartalom, ami pontosan egy
    kritériumot sért/teljesít)

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. Prerequisite-ellenőrzés

```
grep -n '\- id: "factory-tooling-test-suite-001"' -A 3 jobs/index.yaml
```

Idézd a kimenetet, erősítsd meg `status: "done"`. Ha NEM, NO-GO és állj meg.

### 2. K7/K9 logika audit — grep + saját futtatás

```
grep -rn "K7\|K9" --include="*.sh" tools/ | grep -v test_
```

Idézd a kimenetet. Futtasd le SAJÁT KEZŰLEG a `tools/validate-spec.sh`-t a MEGLÉVŐ
`go.md` fixture-rel egy ideiglenes job-dir-ben, és erősítsd meg, hogy a K7/K9
ELLENŐRZÉS jelenleg NEM aktiválódik rá (mert `go.md` nem tartalmaz audit-trigger
szót) — ez magyarázza, miért "passed" mostanáig a meglévő suite K7/K9 hiánnyal is.

### 3. ÚJ fixture-fájlok — K7, K7b, K9 mindhárom ága

Hozz létre a `tests/fixtures/validate_spec/` alá:
- `k7_violation.md` — tartalmaz egy K7-triggerelő szót (pl. "audit"), de NINCS benne
  `grep -rn`/`grep -r ` minta → várt: `FAIL: K7:` jelenjen meg
- `k7b_violation.md` — tartalmaz K7-triggerelő szót ÉS `grep -rn` mintát, de NINCS
  benne teszt-fájl-kizárás minta (`_test.go`/`test_`/`_test.py`/`deadcode`) → várt:
  `FAIL: K7b:` jelenjen meg (és NE `FAIL: K7:`, mert az első K7-feltétel teljesül)
- `k9_violation.md` — tartalmaz egy K9-triggerelő szót (pl. "implemented"), de NINCS
  benne reachability artifact minta (`file:line`/`call.?site`/`deadcode`/stb.) →
  várt: `FAIL: K9:` jelenjen meg
- `go_audit.md` — EGYSZERRE tartalmaz minden K7/K7b/K9-triggerelő ÉS -teljesítő
  mintát (audit-szó, `grep -rn`, teszt-fájl-kizárás, file:line reachability) → várt:
  `MECHANIKUS ELLENŐRZÉS: GO`, BIZONYÍTVA, hogy K7/K9 a TELJESÍTETT ágon sem hibázik
  hamisan

A fixture-stílus kövesse a MEGLÉVŐ `go.md`/`k8_violation.md` minimalista, magyar
nyelvű mintáját — NE adj hozzá felesleges tartalmat egy fixture-höz, ami nem
szükséges a célzott kritérium ki/be kapcsolásához.

### 4. ÚJ teszt-függvények

Bővítsd a `tests/test_validate_spec.py`-t a MEGLÉVŐ `_make_job_dir`/
`_run_validate_spec` helper-eket újrahasználva, a MEGLÉVŐ teszt-függvények
(`test_k1_violation_missing_source_path` stb.) PONTOS alakját követve (return code,
`MECHANIKUS ELLENŐRZÉS: NO-GO`/`GO` jelenléte, a várt `FAIL: K7:`/`FAIL: K7b:`/
`FAIL: K9:` jelenléte, a NEM várt FAIL-ek hiánya):
- `test_k7_violation_missing_grep`
- `test_k7b_violation_missing_test_exclusion`
- `test_k9_violation_missing_reachability_artifact`
- `test_go_audit_case_passes_k7_k9_when_satisfied`

### 5. Valós, futtatott bizonyíték

```
cd <repo-root> && python3 -m pytest tests/ -v
```

Idézd a TÉNYLEGES pytest kimenetet — MINDEN teszt (a régi K1/K3/K4/K8 ÉS az új
K7/K7b/K9 tesztek) PASSED kell legyen, ÚJ regresszió nélkül.

## Nem cél

- `tools/validate-spec.sh` LOGIKÁJÁNAK módosítása (ÉPÍTS a meglévőre, csak tesztet
  írsz hozzá, NE változtasd meg a K7/K9 grep-mintákat)
- K2/K5/K6 (evidence-alapú, `/job-validate`-nél emberi/LLM-ítélet, NEM mechanikus
  script-ellenőrzés — ezekhez NEM kell/lehet pytest-fixture)
- a `cic-mcp-factory/CLAUDE.md` "Ismert korlátok" szövegének felülírása (csak
  JAVASOLD a "Findings"-ben, NE módosítsd a fájlt)
- `run-job.sh`/`update-index.sh` további tesztelése (azok MÁR lefedettek a
  `factory-tooling-test-suite-001`-ben, ez a job KIZÁRÓLAG a `validate-spec.sh`
  K7/K9 hiányára fókuszál)

## Required Output Files

- `output/factory-validate-spec-k7-k9-tests.md`
- `tests/fixtures/validate_spec/k7_violation.md`
- `tests/fixtures/validate_spec/k7b_violation.md`
- `tests/fixtures/validate_spec/k9_violation.md`
- `tests/fixtures/validate_spec/go_audit.md`
- a bővített `tests/test_validate_spec.py`

## Required Report Sections

```markdown
# factory-validate-spec-k7-k9-tests-001 Output

## Scope
## Inputs Read
## Prerequisite Check
## K7/K9 Logic Audit
## New Fixtures
## New Test Functions
## Real Pytest Run — Full Suite
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
`proven` egy "a teszt helyesen buktatja a K7/K9 hiányt" állításra KIZÁRÓLAG akkor
használható, ha a TÉNYLEGES, futtatott pytest kimenet idézve van — a teszt-fájl
megírása nem bizonyítja, hogy helyesen fut.

## Definition Of Done

- [ ] a prerequisite `id:` kulccsal megerősítve, GO/NO-GO döntés indokolva
- [ ] a K7/K9 logika file:line hivatkozással idézve (`tools/validate-spec.sh`-ból)
- [ ] mind a 4 ÚJ fixture létrehozva (k7, k7b, k9 violation + go_audit), a MEGLÉVŐ
      stílust követve
- [ ] mind a 4 ÚJ teszt-függvény megírva, a MEGLÉVŐ minta szerint
- [ ] TELJES pytest-suite futtatva, a TÉNYLEGES kimenet idézve, MINDEN teszt PASSED
      (régi + új, nincs regresszió)
- [ ] claim-evidence tábla kitöltve, nem üres
- [ ] a riport javasolja a CLAUDE.md frissítését (NEM hajtja végre)

## Forbidden Shortcuts

- `tools/validate-spec.sh` K7/K9 LOGIKÁJÁNAK módosítása ahelyett, hogy csak tesztet
  írnál hozzá
- csak EGY-KÉT ág tesztelése a 3 violation + 1 go_audit közül — MIND A NÉGY kötelező
- fájl létezése ≠ implemented: a fixture/teszt-fájl léte NEM bizonyítja, hogy a teszt
  helyesen fut — a futtatott pytest kimenetét olvasd, ne a fájl megírását
- a meglévő K1/K3/K4/K8 tesztek megtörése/módosítása (csak BŐVÍTED a fájlt, nem
  írod át a meglévő teszteket)

## Git instrukciók

**FONTOS — ez egy önreferenciális job**: a `target_repo` (`cic-mcp-factory`) EGYBEESIK
a mindig-automatikusan-klónozott `cic-mcp-factory` klónnal — NINCS külön második klón.
Minden módosítást (fixture-fájlok, teszt-fájl, output) EBBEN az EGY klónban végezz, a
`feature/factory-validate-spec-k7-k9-tests-001` branch-en, és EZT pushold. NE módosítsd
a `meta.yaml` `status` mezőjét sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek/kód angolul (a
fixture `.md` tartalma lehet magyar, a MEGLÉVŐ fixture-ök stílusát követve).
