# factory-tooling-test-suite-001 Output

## Scope

Automatizált, nem-mockolt pytest teszt-suite a `cic-mcp-factory` saját lifecycle-tooling-jára:
`tools/validate-spec.sh`, `tools/update-index.sh`, `tools/run-job.sh`. A teszt-suite a `tests/`
mappában él, a valódi shell scripteket hívja `subprocess`-en keresztül fixture input/output
adatokkal — nincs mock-olt git/claude hívás. `run-job.sh`-nál a feladatleírás explicit korlátozta
a kört: csak hálózat- és agent-mentes, determinisztikus viselkedés tesztelhető, a valódi git
clone/push és `claude --print` hívás NEM (lásd "Risks").

A 3 shell scriptet funkcionálisan NEM módosítottam — a `--resume` flag-parsing logikát sem
kellett külön függvénybe kiemelni, mert a meglévő viselkedés (lásd "Findings") elegendő
megfigyelhető, determinisztikus elágazási pontot adott a teszteléshez refaktor nélkül.

## Inputs Read

- `${CIC_WORKDIR}/tools/validate-spec.sh` — teljes fájl, 76 sor
- `${CIC_WORKDIR}/tools/update-index.sh` — teljes fájl, 67 sor (bash + Python heredoc)
- `${CIC_WORKDIR}/tools/run-job.sh` — teljes fájl, 321 sor
- `${CIC_WORKDIR}/CLAUDE.md` — "Ismert korlátok / roadmap" szekció
- `${CIC_WORKDIR}/jobs/session-infra-pipeline-fix-001/output/session-infra-pipeline-fix-report.md`
  — "Risks" szekció (a job-ot motiváló incidens)
- `${CIC_WORKDIR}/.cic-context/factory-docs/acceptance-contract.md` — "Universal Output Contract"
  szekció (ez a report formátuma)
- `${CIC_WORKDIR}/jobs/.schema/meta.yaml` — meta.yaml mezőszerkezet a fixture-ökhöz

## Findings

1. **`validate-spec.sh` cwd-függő path-feloldás.** A `SPEC="jobs/$JOB_ID/input.md"` relatív
   path-ot a script a HÍVÓ cwd-jéhez képest oldja fel, nem a script saját helyéhez. Ez nem hiba,
   de a teszteléshez azt jelenti, hogy `cwd=<tmp_path>` kell legyen a `subprocess.run` híváskor,
   ahol `<tmp_path>/jobs/<job-id>/input.md` létezik.

2. **`update-index.sh` WORKDIR-feloldása a script saját elérési útjából derive-olódik**
   (`WORKDIR="$(cd "$(dirname "$0")/.." && pwd)"`), NEM a cwd-ből. Ezért a valódi script
   izolált tesztelése a fájl byte-egyenlő másolását igényelte egy ideiglenes `tools/`
   alkönyvtárba — ez nem mock, a script tartalma változatlan, csak a futási helye más.

3. **`run-job.sh` ugyanezt a `dirname($0)` mintát használja WORKDIR-re, de a benne hívott
   `validate-spec.sh`-nak ÁTADOTT cwd a `run-job.sh` HÍVÓJÁNAK cwd-je, nem a kiszámolt
   `$WORKDIR`.** A script sehol nem `cd`-l a saját `$WORKDIR`-jébe a `validate-spec.sh` hívás
   előtt (lásd `run-job.sh:89-94`). Éles használatban ez nem probléma, mert a dokumentált
   indítási minta mindig `./tools/run-job.sh ...`-ként, a repo gyökeréből történik (cwd ==
   WORKDIR), de ez egy implicit, nem-kikényszerített feltevés — ha valaki más cwd-ből hívná
   meg (pl. `bash /abs/path/tools/run-job.sh ...` egy másik könyvtárból), a `validate-spec.sh`
   rossz `jobs/<job-id>/input.md`-t próbálna feloldani. Lásd "Risks".

4. **`run-job.sh` `--resume` flag-parsing helyesen routeol**: `--resume` esetén a script NEM
   hívja meg a `validate-spec.sh`-t (csak friss indításnál, lásd `run-job.sh:89`), hanem
   közvetlenül a `session_id` nem-üres ellenőrzésére megy (`run-job.sh:97`). Ezt a viselkedést
   sikerült refaktor nélkül, determinisztikusan tesztelni egy olyan fixture-rel, ahol az
   `input.md` validate-spec NO-GO-t adna, de `--resume`-mal ez sosem fut le — a teszt ezt a
   tényt (a "validate-spec" string hiányát a kimenetből) ellenőrzi annak bizonyítékaként, hogy
   a flag helyesen `RESUME=1`-re állította a belső állapotot.

## Claim-Evidence Matrix

| Claim | Status | Evidence | Verification Method | Risk |
|---|---|---|---|---|
| `validate-spec.sh` K1-sértést (hiányzó forrás path) helyesen NO-GO-zza, exit 1, `FAIL: K1:` sorral, és csak azt | proven | `tests/test_validate_spec.py::test_k1_violation_missing_source_path` PASSED; valódi futás kimenete: `FAIL: K1: nincs konkrét forrás path vagy KB chunk-id (pl. /home/..., \${CIC_*}, get_chunk, c781)`, exit code 1 | valódi `validate-spec.sh` hívás fixture `input.md`-vel, `pytest` assert | alacsony |
| `validate-spec.sh` K3-sértést (hiányzó tiltott rövidítés) helyesen NO-GO-zza, és csak azt | proven | `tests/test_validate_spec.py::test_k3_violation_missing_forbidden_shortcut` PASSED; kimenet: `FAIL: K3: nincs explicit tiltott rövidítés (...)`, exit code 1 | valódi script hívás, fixture input | alacsony |
| `validate-spec.sh` K4-sértést (hiányzó output fájlnév) helyesen NO-GO-zza, és csak azt | proven | `tests/test_validate_spec.py::test_k4_violation_missing_output_filename` PASSED; kimenet: `FAIL: K4: nincs konkrét output fájlnév (...)`, exit code 1 | valódi script hívás, fixture input | alacsony |
| `validate-spec.sh` K8-sértést (hiányzó claim-evidence tábla) helyesen NO-GO-zza, és csak azt | proven | `tests/test_validate_spec.py::test_k8_violation_missing_claim_evidence_table` PASSED; kimenet: `FAIL: K8: nincs claim-evidence tábla előírva (...)`, exit code 1 | valódi script hívás, fixture input | alacsony |
| Egy minden K1/K3/K4/K8 kritériumot teljesítő spec GO-t kap, `FAIL:` sor nélkül, exit 0 | proven | `tests/test_validate_spec.py::test_go_case_passes_all_criteria` PASSED; kimenet: `MECHANIKUS ELLENŐRZÉS: GO`, exit code 0 | valódi script hívás, fixture input | alacsony |
| Hiányzó `input.md` esetén `validate-spec.sh` NO-GO-t ad stderr-re, exit 1 | proven | `tests/test_validate_spec.py::test_missing_input_md_is_no_go` PASSED; kimenet: `NO-GO: jobs/test-job/input.md not found` | valódi script hívás | alacsony |
| Job-id argumentum nélkül `validate-spec.sh` usage hibát ad, exit 1 | proven | `tests/test_validate_spec.py::test_missing_job_id_argument_usage_error` PASSED; stderr: `Usage: .../validate-spec.sh <job-id>` | valódi script hívás | alacsony |
| `update-index.sh` normál esetben (2 valid + 1 no-meta + 1 dotdir) helyesen csak a 2 valid jobot listázza, pontos mezőkkel | proven | `tests/test_update_index.py::test_normal_case_generates_expected_index` PASSED; generált `index.yaml` 14 soros body pontosan egyezik az elvárt listával (lásd "Findings" 2. pont), `hidden-job` string nem szerepel a kimenetben | valódi script hívás byte-egyenlő másolatban, fixture `jobs/` fa, sor-szintű egyezés assert | alacsony |
| `update-index.sh` üres `jobs/` esetén `jobs: []`-t ír, "0 job(s)" üzenettel | proven | `tests/test_update_index.py::test_empty_jobs_dir_produces_jobs_empty_list` PASSED; generált fájl 2. sora pontosan `jobs: []` | valódi script hívás, üres fixture | alacsony |
| `run-job.sh` job-id argumentum nélkül usage hibával, nem-nulla exit code-dal áll le | proven | `tests/test_run_job.py::test_missing_job_id_argument_is_usage_error` PASSED; stderr tartalmazza: `Adj meg egy job-id-t` | valódi script hívás argumentum nélkül | alacsony |
| `run-job.sh` NO-GO `validate-spec.sh` eredmény esetén nem indítja el az agentet, nem ír `index.yaml`-t, nem hoz létre workspace-t | proven | `tests/test_run_job.py::test_no_go_spec_short_circuits_before_agent_start` PASSED; stdout tartalmazza: `[ERROR] validate-spec.sh NO-GO`, exit code 1, `jobs/index.yaml` és `jobs/no-go-job/workspace` nem létezik a futás után | valódi `run-job.sh` + valódi `validate-spec.sh` hívás izolált fixture WORKDIR-ben, `HOME` env override a fake agent confighoz, fájlrendszer-assertek | alacsony — lásd Risks: a git/claude rész ezen túl nem fedett |
| `--resume` flag helyesen `RESUME=1`-re állítja a belső állapotot (más kódágra routeol, mint a flag nélküli hívás) | proven | `tests/test_run_job.py::test_resume_flag_routes_to_session_id_check_not_validate_spec` PASSED; stdout tartalmazza: `meta.yaml agent.session_id üres`, NEM tartalmazza a `validate-spec` szót, holott a fixture input NO-GO-t adna validate-spec-nél | valódi script hívás `--resume` flaggel, ugyanaz a fixture job-id ami NO-GO-zna validate-spec esetén | alacsony |
| `run-job.sh` valódi git clone/push és `claude --print` integrációja működik | unknown | nincs teszt rá — explicit kizárva a job specifikáció által (hálózat/agent-mentes kör) | nincs — lásd Risks | magas, lásd Risks |
| A teljes teszt-suite egyetlen paranccsal (`pytest tests/`) lefuttatható, mind a 12 teszt zöld | proven | lásd alább, idézett `pytest tests/ -v` kimenet: `12 passed in 0.33s` | tényleges futtatás, idézett kimenet | alacsony |

### Idézett teszt-futás (`pytest tests/ -v`)

```
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0
rootdir: cic-mcp-factory
collecting ... collected 12 items

tests/test_run_job.py::test_missing_job_id_argument_is_usage_error PASSED [  8%]
tests/test_run_job.py::test_no_go_spec_short_circuits_before_agent_start PASSED [ 16%]
tests/test_run_job.py::test_resume_flag_routes_to_session_id_check_not_validate_spec PASSED [ 25%]
tests/test_update_index.py::test_normal_case_generates_expected_index PASSED [ 33%]
tests/test_update_index.py::test_empty_jobs_dir_produces_jobs_empty_list PASSED [ 41%]
tests/test_validate_spec.py::test_go_case_passes_all_criteria PASSED     [ 50%]
tests/test_validate_spec.py::test_k1_violation_missing_source_path PASSED [ 58%]
tests/test_validate_spec.py::test_k3_violation_missing_forbidden_shortcut PASSED [ 66%]
tests/test_validate_spec.py::test_k4_violation_missing_output_filename PASSED [ 75%]
tests/test_validate_spec.py::test_k8_violation_missing_claim_evidence_table PASSED [ 83%]
tests/test_validate_spec.py::test_missing_input_md_is_no_go PASSED       [ 91%]
tests/test_validate_spec.py::test_missing_job_id_argument_usage_error PASSED [100%]

============================== 12 passed in 0.33s ===============================
```

Futtatás módja: `pytest` nem volt telepítve a rendszer Python-ban (`python3 -m pytest` →
`No module named pytest`), ezért egy ideiglenes venv-ben futott (`pytest>=8.0`, lásd
`tests/requirements.txt`). Reprodukció:
```bash
python3 -m venv /tmp/factory-test-venv
/tmp/factory-test-venv/bin/pip install -r tests/requirements.txt
/tmp/factory-test-venv/bin/pytest tests/ -v
```

## Decisions Proposed

1. A 3 shell tool mindegyikéhez tartozó tesztek a `tests/` mappába kerülnek, fixture-ök a
   `tests/fixtures/<tool>/` alá, egy `tests/requirements.txt`-tel (`pytest>=8.0`) —
   `status_after_merge: experimental`, mert ez az első automatizált védelmi réteg a factory
   tooling-on, nincs még előzmény, amihez "candidate"-ként viszonyítani lehetne.
2. A `tools/run-job.sh` `--resume` flag-parsing logikáját NEM kellett kiemelni külön
   függvénybe — a meglévő, beágyazott `case` blokk viselkedése megfigyelhető (proven) a
   session_id-ellenőrzési ág elérésén keresztül, refaktor-kockázat nélkül.
3. Javasolt CI-bekötés (külön job, lásd "Next Jobs") a `pytest tests/` parancs futtatására
   minden PR-en a `cic-mcp-factory` repóban.

## Rejected / Out Of Scope

- A 3 shell script funkcionális átírása/refaktorálása — nem volt rá szükség, a `--resume`
  flag-kiemelés feltétele (tesztelhetőség hiánya) nem állt fent.
- CI pipeline (GitHub Actions) bekötése — explicit kizárva a job specifikációban, külön job.
- `meta.yaml` schema validator és PR-readiness checker tesztelése — ezek nem léteznek még,
  külön jobok (`factory-meta-schema-validator-001`, `factory-pr-readiness-checker-001`).
- `run-job.sh` valódi git clone/push és `claude --print` integrációs tesztje — explicit
  kizárva a job specifikáció által ("instabil, lassú, külső erőforrást igényelne CI-ben").

## Risks

1. **`run-job.sh` git/agent-integrációja NEM fedett tesztekkel.** A következő viselkedések
   csak teljes git+hálózat+Claude CLI integrációval lennének tesztelhetők, és a job
   specifikációja explicit kizárta ezek automatizált tesztelését:
   - a tényleges `git clone` + `checkout -b feature/<job-id>` minden `CLONE_REPOS` tagra
   - a `pending → running` állapotváltás commit+push lépése (`run-job.sh:125-128`)
   - a `claude --print` agent-hívás és az `OUTPUT_FILE`-ba írás
   - a session UUID megtalálási logika (`find ... -newer "$SESSION_MARKER"`)
   - az `evidence_for_repo()` függvény tényleges git-állapot-detekciója (branch/HEAD/dirty/push
     státusz) valódi klónon
   - a `running → agent_done`/`error` állapotváltás záró commit+push lépése
   - az interaktív "Job már fut. Folytatod? (y/N)" / "Job már agent_done. Újrafuttatod? (y/N)"
     promptok ágai (`run-job.sh:101-106`) — ezeket szándékosan nem teszteltem, mert
     `status: "pending"` fixture-ökkel kerültem el az interaktív `read` hívást, ami CI-ben
     blokkolna stdin nélkül.

2. **`run-job.sh` implicit cwd-feltevése** (lásd "Findings" 3. pont): a `validate-spec.sh`
   hívás cwd-je a `run-job.sh` HÍVÓJÁNAK cwd-jéből származik, nem a kiszámolt `$WORKDIR`-ből.
   A dokumentált indítási minta (`./tools/run-job.sh ...` a repo gyökeréből) miatt ez gyakorlatban
   nem okoz problémát, de nincs explicit `cd "$WORKDIR"` védelem, ha valaki más mintával hívná
   meg. Ezt NEM javítottam (nem cél a funkcionális átírás), csak dokumentáltam.

3. **A teszt-suite futtatásához pytest telepítés szükséges**, ami a rendszer Python-jában
   jelenleg nincs telepítve. Amíg nincs CI-bekötés (külön job), a futtatás manuális venv
   létrehozást igényel — ez dokumentált a report "Claim-Evidence Matrix" alatti reprodukciós
   parancsokban és a `tests/requirements.txt`-ben.

## Definition Of Done Check

- [x] legalább 4 teszt `validate-spec.sh`-ra (K1/K3/K4/K8 + 1 GO eset) — valójában 7 teszt
      (a 4 K-sértés + GO eset + hiányzó input.md eset + hiányzó job-id argumentum eset),
      mindegyik valódi script hívás, lefuttatva, zöld
- [x] legalább 2 teszt `update-index.sh`-ra (normál eset + üres `jobs/` eset) — 2 teszt,
      valódi script hívás, lefuttatva, zöld
- [x] legalább 2 teszt `run-job.sh`-ra a megengedett, hálózat-mentes körben — 3 teszt
      (usage-hiba, NO-GO short-circuit, `--resume` routing), lefuttatva, zöld
- [x] a teljes teszt-suite egyetlen paranccsal (`pytest tests/`) lefuttatható, kimenet idézve
- [x] claim-evidence tábla kitöltve, minden `proven` állításhoz tényleges parancs-kimenet
      idézve
- [x] explicit jelzett `run-job.sh` viselkedések listája, amik nem fedettek
      (git/agent-integráció, interaktív promptok, cwd-feltevés) — lásd "Risks"

## Next Jobs

1. **CI pipeline bekötés** (`factory-tooling-ci-001` vagy hasonló) — a `pytest tests/`
   futtatása minden PR-en a `cic-mcp-factory` repóban (GitHub Actions), `tests/requirements.txt`
   alapján.
2. **`run-job.sh` git/agent-integrációs teszt** (külön job, opcionálisan egy lokális bare git
   remote-ot használva valódi `git clone`/`push` ellenőrzéshez, `claude --print` hívás nélkül
   vagy mockolt CLI binárissal) — ez fedné le a "Risks" 1. pontjában listázott hiányt anélkül,
   hogy valódi GitHub remote-ra vagy Claude API hívásra lenne szükség.
3. **`meta.yaml` schema validator** (`factory-meta-schema-validator-001`) és **PR-readiness
   checker** (`factory-pr-readiness-checker-001`) — a `CLAUDE.md` "Ismert korlátok / roadmap"
   szekciójában már megnevezett hiányok, ezekhez is hasonló pytest-alapú teszt-suite ajánlott.
