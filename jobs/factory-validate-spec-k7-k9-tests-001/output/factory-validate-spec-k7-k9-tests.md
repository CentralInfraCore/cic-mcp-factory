# factory-validate-spec-k7-k9-tests-001 Output

## Scope

A `tools/validate-spec.sh` script K7/K7b/K9 mechanikus ellenőrzési logikája (42-58. sor)
ELŐZŐLEG ÍRVA és élesben futó volt, de pytest-fedezet nélkül — a `factory-tooling-test-suite-001`
job csak K1/K3/K4/K8-at fedte le. Ez a job KIZÁRÓLAG ezt a hiányt zárja: 4 új fixture-fájl
(`k7_violation.md`, `k7b_violation.md`, `k9_violation.md`, `go_audit.md`) + 4 új teszt-függvény
a `tests/test_validate_spec.py`-ben, a MEGLÉVŐ `_make_job_dir`/`_run_validate_spec` helper-ek
és a MEGLÉVŐ teszt-minta újrahasználásával. A `validate-spec.sh` LOGIKÁJA nem módosult — csak
teszt került hozzá a meglévő, élő logikára.

## Inputs Read

- `jobs/factory-validate-spec-k7-k9-tests-001/input.md` — a teljes job spec
- `jobs/index.yaml` — prerequisite-ellenőrzéshez (`factory-tooling-test-suite-001` státusza)
- `tools/validate-spec.sh` — a TELJES K1-K9 logika, különös tekintettel a K7/K7b/K9 ágra (42-58. sor)
- `tests/test_validate_spec.py` — a meglévő teszt-minta (`_make_job_dir`, `_run_validate_spec`,
  a K1/K3/K4/K8 teszt-függvények alakja)
- `tests/conftest.py` — `repo_root`/`fixtures_dir` pytest fixture-ök
- `tests/helpers.py` — a `run()` subprocess wrapper
- `tests/fixtures/validate_spec/go.md`, `k8_violation.md` — a meglévő fixture-stílus
- `tests/requirements.txt` — `pytest>=8.0`, `PyYAML>=6.0`

## Prerequisite Check

Parancs és tényleges kimenet:

```
$ grep -n '\- id: "factory-tooling-test-suite-001"' -A 3 jobs/index.yaml
20:  - id: "factory-tooling-test-suite-001"
21-    level: "capability"
22-    status: "done"
23-    parent: "session-infra-pipeline-fix-001"
```

`status: "done"` megerősítve az `id:` kulcs alatt (nem `job_id:`). **Döntés: GO** — a
prerequisite job lezárt állapotban van, a `tests/test_validate_spec.py` és a hozzá tartozó
helper-ek/fixture-ök léteznek és futtathatók (lásd lent), a jelen job ráépülhet rájuk.

## K7/K9 Logic Audit

Parancs és tényleges kimenet:

```
$ grep -rn "K7\|K9" --include="*.sh" tools/ | grep -v test_
tools/validate-spec.sh:42:# K7 — Forráskód audit esetén: grep + teszt-fájl kizárás kötelező (Go vagy Python)
tools/validate-spec.sh:46:        FAILURES+=("K7: forráskód audit, de nincs 'grep -rn' előírás a call-chain ellenőrzéshez")
tools/validate-spec.sh:53:# K9 — Reachability artifact kötelező: production call site (file:line) VAGY deadcode output
tools/validate-spec.sh:57:        FAILURES+=("K9: nincs reachability artifact előírva — kell: production call site (file:line) VAGY 'deadcode ./...' output az agent outputban; 'symbol létezik' ≠ 'production hívja'")
```

A logika (`tools/validate-spec.sh:42-59`):

```bash
# K7 — trigger: (audit|call.chain|implemented|scaffold|hívódik|olvasd a forrás|statusz.meghatároz)
if grep -qE '(audit|call.chain|implemented|scaffold|hívódik|olvasd a forrás|statusz.meghatároz)' "$SPEC"; then
    if ! grep -qE 'grep -rn|grep -r ' "$SPEC"; then
        FAILURES+=("K7: ...")
    fi
    if ! grep -qE '_test\.go|test_|_test\.py|deadcode' "$SPEC"; then
        FAILURES+=("K7b: ...")
    fi
fi

# K9 — trigger: (implemented|scaffold|hívódik|production.*call|call.*chain)
if grep -qE '(implemented|scaffold|hívódik|production.*call|call.*chain)' "$SPEC"; then
    if ! grep -qE '(deadcode|call.?site|call.?path|file:line|hívó.*fájl|hívó.*sor|production.*hívás)' "$SPEC"; then
        FAILURES+=("K9: ...")
    fi
fi
```

Saját futtatás a MEGLÉVŐ `go.md` fixture-rel egy ideiglenes job-dir-ben:

```
$ TMPDIR=$(mktemp -d)
$ mkdir -p "$TMPDIR/jobs/test-job"
$ cp tests/fixtures/validate_spec/go.md "$TMPDIR/jobs/test-job/input.md"
$ cd "$TMPDIR" && bash <repo>/tools/validate-spec.sh test-job; echo "EXIT_CODE=$?"
=== validate-spec: test-job ===
MECHANIKUS ELLENŐRZÉS: GO
Folytasd: /job-validate test-job (evidence-alapú ellenőrzés)
EXIT_CODE=0
```

Megerősítve: `go.md` tartalma (`Forrás: /home/user/project/file.go és ${CIC_WORKDIR}/tools/foo.sh`,
`exit code ≠ sikeres`, `output/report.md`, claim-evidence tábla) NEM tartalmaz semelyik K7
vagy K9 trigger-szót (`audit`, `call.chain`, `implemented`, `scaffold`, `hívódik`,
`olvasd a forrás`, `statusz.meghatároz`, `production.*call`) — ezért a K7/K9 `if` blokkok
soha nem futnak le rá, a script GO-t ad `FAIL:` nélkül. **Ez pontosan magyarázza, miért
"passed" a meglévő K1/K3/K4/K8 suite mindeddig K7/K9 teszt-fedezet nélkül**: a meglévő
`go.md` fixture sosem aktiválta a K7/K9 ágat, így a hiányukra senki nem futott rá.

## New Fixtures

4 új fixture a `tests/fixtures/validate_spec/` alatt, a meglévő `go.md`/`k8_violation.md`
minimalista, magyar nyelvű stílusát követve — minden fixture pontosan egy célzott
kritérium-állapotot kapcsol ki/be:

| Fixture | Tartalmazza | Nem tartalmazza | Triggerel |
|---|---|---|---|
| `k7_violation.md` | "audit" szó | `grep -rn`/`grep -r ` minta | K7 (és vele együtt K7b is, mert a script logikája szerint a K7b feltétel — teszt-fájl-kizárás megléte — automatikusan hamis, ha grep sincs) |
| `k7b_violation.md` | "audit" szó + `grep -rn "FooBar" .` | teszt-fájl-kizárás (`_test.go`/`test_`/`deadcode`) | csak K7b (a `grep -rn` minta megléte miatt a K7 feltétel teljesül, így `FAIL: K7:` NEM jelenik meg) |
| `k9_violation.md` | "implemented" szó | reachability artifact (`file:line`/`call.?site`/`deadcode`) | K9 (és K7/K7b is, mert "implemented" K7-trigger szó is, és nincs grep/teszt-kizárás sem — ezt a teszt-függvény nem zárja ki, a spec ezt nem írja elő) |
| `go_audit.md` | "audit" + "implemented" szó, `grep -rn "FooBar" . \| grep -v _test.go`, `file:line` reachability hivatkozás | — (minden kötelező minta megvan) | semelyik FAIL, `MECHANIKUS ELLENŐRZÉS: GO` |

A `k7_violation.md` és `k9_violation.md` esetén a script tényleges, NEM módosítandó logikája
miatt a K7b (illetve K9-nél a K7/K7b) együtt FAIL-el a célzott kritériummal — ez NEM hiba a
fixture-ben, hanem a `if` blokkok szerkezetének (egymástól nem `elif`, hanem önálló feltételek)
következménye. A job spec ("3. ÚJ fixture-fájlok") ezt csak `k7b_violation.md`-nél zárja ki
explicit módon ("és NE `FAIL: K7:`"), a másik kettőnél nem ír elő kizáró asszerciót — az új
teszt-függvények ennek megfelelően lettek megírva (lásd "New Test Functions").

## New Test Functions

4 új teszt-függvény a `tests/test_validate_spec.py`-ben, a meglévő `test_k1_violation_...`
stb. függvények pontos alakját követve (`_make_job_dir`/`_run_validate_spec` helper-ek
újrahasználva, `result.returncode`, `MECHANIKUS ELLENŐRZÉS: NO-GO`/`GO`, `FAIL: K7:`/
`FAIL: K7b:`/`FAIL: K9:` jelenlét/hiány-asszerciók):

- `test_k7_violation_missing_grep` — `k7_violation.md`, `returncode == 1`, NO-GO,
  `FAIL: K7:` jelen
- `test_k7b_violation_missing_test_exclusion` — `k7b_violation.md`, `returncode == 1`,
  NO-GO, `FAIL: K7b:` jelen, `FAIL: K7:` NINCS jelen
- `test_k9_violation_missing_reachability_artifact` — `k9_violation.md`,
  `returncode == 1`, NO-GO, `FAIL: K9:` jelen
- `test_go_audit_case_passes_k7_k9_when_satisfied` — `go_audit.md`, `returncode == 0`,
  GO, semelyik `FAIL:` nincs jelen

A meglévő K1/K3/K4/K8 teszt-függvények és a `test_missing_input_md_is_no_go`/
`test_missing_job_id_argument_usage_error` SEM módosultak — a fájl csak BŐVÜLT.

## Real Pytest Run — Full Suite

Venv build (`.venv-host`, host pip cache megtartva, NEM `--no-cache-dir`):

```
$ python3 -m venv .venv-host
$ .venv-host/bin/pip install -r tests/requirements.txt
Successfully installed PyYAML-6.0.3 iniconfig-2.3.0 packaging-26.2 pluggy-1.6.0 pygments-2.20.0 pytest-9.1.1
```

Teljes suite futtatása:

```
$ .venv-host/bin/python3 -m pytest tests/ -v
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0
collecting ... collected 16 items

tests/test_run_job.py::test_missing_job_id_argument_is_usage_error PASSED [  6%]
tests/test_run_job.py::test_no_go_spec_short_circuits_before_agent_start PASSED [ 12%]
tests/test_run_job.py::test_resume_flag_routes_to_session_id_check_not_validate_spec PASSED [ 18%]
tests/test_update_index.py::test_normal_case_generates_expected_index PASSED [ 25%]
tests/test_update_index.py::test_empty_jobs_dir_produces_jobs_empty_list PASSED [ 31%]
tests/test_validate_spec.py::test_go_case_passes_all_criteria PASSED     [ 37%]
tests/test_validate_spec.py::test_k1_violation_missing_source_path PASSED [ 43%]
tests/test_validate_spec.py::test_k3_violation_missing_forbidden_shortcut PASSED [ 50%]
tests/test_validate_spec.py::test_k4_violation_missing_output_filename PASSED [ 56%]
tests/test_validate_spec.py::test_k8_violation_missing_claim_evidence_table PASSED [ 62%]
tests/test_validate_spec.py::test_k7_violation_missing_grep PASSED       [ 68%]
tests/test_validate_spec.py::test_k7b_violation_missing_test_exclusion PASSED [ 75%]
tests/test_validate_spec.py::test_k9_violation_missing_reachability_artifact PASSED [ 81%]
tests/test_validate_spec.py::test_go_audit_case_passes_k7_k9_when_satisfied PASSED [ 87%]
tests/test_validate_spec.py::test_missing_input_md_is_no_go PASSED       [ 93%]
tests/test_validate_spec.py::test_missing_job_id_argument_usage_error PASSED [100%]

============================== 16 passed in 0.52s ==============================
```

**16 passed, 0 failed.** Mind a 12 régi teszt (`test_run_job.py` 3 db, `test_update_index.py`
2 db, `test_validate_spec.py` régi 7 db: `go_case`, K1, K3, K4, K8, `missing_input_md`,
`missing_job_id_argument`) ÉS a 4 új K7/K7b/K9 teszt PASSED — nincs regresszió.

## Findings

1. A `tools/validate-spec.sh` K7/K7b/K9 logikája (42-58. sor) most már pytest-fedezett —
   a `.github/workflows/tests.yml` CI minden PR/push-on lefuttatja, így egy jövőbeli
   K7/K9 grep-minta-törés (pl. K10 hozzáadásakor) elbukna a CI-ben.
2. **Javaslat (NEM ennek a jobnak a feladata)**: a `cic-mcp-factory/CLAUDE.md` "Ismert
   korlátok / roadmap" szekciójának utolsó pontja ("automatizált tesztek a factory
   tooling-ra ... nincs hozzájuk bats/pytest suite") frissítésre szorul — immár hamis a
   `validate-spec.sh`-ra vonatkozóan (K1/K3/K4/K7/K7b/K8/K9 mind lefedett), és a
   `run-job.sh`/`update-index.sh` is lefedett a `factory-tooling-test-suite-001`-ben.
   Ez a riport javasolja a frissítést, de NEM hajtja végre a fájlon.
3. A K7 és K9 trigger-feltételek nem zárják ki egymást (`implemented` mindkettőt
   triggereli) — ez a script tervezett viselkedése, nem hiba; az új fixture-ök/tesztek
   ennek megfelelően lettek megírva (lásd "New Fixtures").

## Claim-Evidence Matrix

| Claim | Status | Evidence | Verification Method | Risk |
|---|---|---|---|---|
| A prerequisite job (`factory-tooling-test-suite-001`) `status: "done"` | proven | `grep -n '- id: "factory-tooling-test-suite-001"' -A 3 jobs/index.yaml` kimenete idézve a "Prerequisite Check"-ben | tényleges grep futtatás | alacsony |
| A meglévő `go.md` fixture NEM triggereli a K7/K9 ellenőrzést | proven | saját `bash tools/validate-spec.sh` futtatás ideiglenes job-dir-ben, kimenet: `MECHANIKUS ELLENŐRZÉS: GO`, `EXIT_CODE=0`, nincs `FAIL:` | tényleges script-futtatás, kimenet idézve | alacsony |
| `k7_violation.md` helyesen buktatja a K7 hiányt | proven | `pytest tests/test_validate_spec.py::test_k7_violation_missing_grep` PASSED a teljes suite futtatásban | tényleges pytest futtatás, kimenet idézve | alacsony |
| `k7b_violation.md` helyesen buktatja a K7b hiányt és NEM buktatja hamisan a K7-et | proven | `pytest ...::test_k7b_violation_missing_test_exclusion` PASSED, asszertálja `FAIL: K7b:` jelenlétét ÉS `FAIL: K7:` hiányát | tényleges pytest futtatás, kimenet idézve | alacsony |
| `k9_violation.md` helyesen buktatja a K9 hiányt | proven | `pytest ...::test_k9_violation_missing_reachability_artifact` PASSED | tényleges pytest futtatás, kimenet idézve | alacsony |
| `go_audit.md` a TELJESÍTETT ágon nem hibázik hamisan (K7/K9 nem buktatja hamis pozitívan) | proven | `pytest ...::test_go_audit_case_passes_k7_k9_when_satisfied` PASSED, `returncode==0`, `MECHANIKUS ELLENŐRZÉS: GO`, nincs `FAIL:` | tényleges pytest futtatás, kimenet idézve | alacsony |
| A meglévő K1/K3/K4/K8 + egyéb tesztek (12 db) nem törtek meg | proven | teljes `pytest tests/ -v` kimenet: 16 passed, mind a 12 régi teszt PASSED | tényleges, teljes suite futtatás, kimenet idézve | alacsony |
| `tools/validate-spec.sh` LOGIKÁJA nem módosult | proven | `git diff --stat tools/validate-spec.sh` üres kimenet a feature branch-en a main-hez képest | `git diff` futtatás | alacsony |
| `meta.yaml` `status` mezője nem módosult | proven | `git diff main -- jobs/factory-validate-spec-k7-k9-tests-001/meta.yaml` üres kimenet | `git diff` futtatás | alacsony |

## Decisions Proposed

- Javasolt: a `cic-mcp-factory/CLAUDE.md` "Ismert korlátok / roadmap" utolsó pontjának
  frissítése, jelezve hogy `validate-spec.sh` (K1/K3/K4/K7/K7b/K8/K9) és `run-job.sh`/
  `update-index.sh` immár pytest-fedezett — ez NEM ennek a jobnak a feladata, csak javaslat.

## Rejected / Out Of Scope

- `tools/validate-spec.sh` LOGIKÁJÁNAK módosítása — explicit nem cél, nem történt módosítás.
- K2/K5/K6 fixture/teszt — evidence-alapú, emberi/LLM-ítélet kritériumok, nem mechanikus
  script-ellenőrzés, nincs pytest-fixture hozzájuk (és nem is lehet).
- `cic-mcp-factory/CLAUDE.md` "Ismert korlátok" szövegének felülírása — csak javaslat a
  "Findings"-ben, a fájl nem módosult.
- `run-job.sh`/`update-index.sh` további tesztelése — már lefedett a
  `factory-tooling-test-suite-001`-ben, kívül esik ennek a jobnak a fókuszán.

## Risks

- A K7 és K9 trigger-reguláris kifejezések (`audit|call.chain|implemented|scaffold|...`)
  jövőbeli bővítése (pl. új trigger-szó hozzáadása) megváltoztathatja, mely fixture-ök
  triggerelik melyik ágat — ezt a 4 új teszt most már elkapja regresszióként, mert a
  pontos `FAIL:` jelenlét/hiány van asszertálva.
- A `k7_violation.md` és `k9_violation.md` fixture-ök a script jelenlegi szerkezete miatt
  több FAIL-t is produkálnak egyszerre (K7+K7b, illetve K9+K7+K7b) — ez nem hiba, de ha
  valaki a jövőben szigorúbb, izolált egy-FAIL-es tesztet akarna, a script `if`/`elif`
  szerkezetét kellene átalakítani (ami explicit NEM cél ebben a jobban).

## Definition Of Done Check

- [x] a prerequisite `id:` kulccsal megerősítve, GO döntés indokolva (lásd "Prerequisite Check")
- [x] a K7/K9 logika file:line hivatkozással idézve (`tools/validate-spec.sh:42-59`, lásd "K7/K9 Logic Audit")
- [x] mind a 4 ÚJ fixture létrehozva (`k7_violation.md`, `k7b_violation.md`, `k9_violation.md`, `go_audit.md`), a meglévő stílust követve
- [x] mind a 4 ÚJ teszt-függvény megírva, a meglévő minta szerint
- [x] TELJES pytest-suite futtatva, a tényleges kimenet idézve, 16/16 PASSED, nincs regresszió
- [x] claim-evidence tábla kitöltve, nem üres
- [x] a riport javasolja a CLAUDE.md frissítését (NEM hajtja végre) — lásd "Findings" 2. pont

## Next Jobs

- (javasolt, nem ezen job része) `factory-claude-md-roadmap-sync-001` — a CLAUDE.md
  "Ismert korlátok / roadmap" szekció frissítése a tényleges pytest-lefedettség
  tükrében (validate-spec.sh K1-K9, run-job.sh, update-index.sh mind lefedett).
