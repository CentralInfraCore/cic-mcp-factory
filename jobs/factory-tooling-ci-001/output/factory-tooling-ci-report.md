# factory-tooling-ci-001 Output

## Scope

A `cic-mcp-factory` repo (saját maga) kap egy GitHub Actions workflow-t (`.github/workflows/tests.yml`),
ami a `factory-tooling-test-suite-001` jobban létrehozott 12 tesztből álló pytest suite-ot futtatja
`pull_request` (bármely branch → `main`) és `push` (`main`) eseményekre. Ez az első CI-bekötés a
`cic-mcp-*` családban — `status_after_merge: experimental`.

A jobnak nemcsak a yaml fájlt kellett létrehoznia, hanem bizonyítania is, hogy egy VALÓDI Actions
run lefutott és SUCCESS-szal zárult ugyanazon a commit-on, amit a feature branch-re pusholtam.

## Inputs Read

- `jobs/factory-tooling-ci-001/input.md` (ez a job spec, tartalmazza a Universal Output Contract
  szakaszlistát is, közvetlenül innen, nem külön `acceptance-contract.md`-ből)
- `jobs/factory-tooling-test-suite-001/output/factory-tooling-test-suite-report.md`
- `tests/requirements.txt`
- `tests/` teljes suite: `conftest.py`, `helpers.py`, `test_run_job.py`, `test_update_index.py`,
  `test_validate_spec.py`, `fixtures/`
- `tools/update-index.sh` (a CI hiba diagnosztizálásához)
- `CLAUDE.md` (job/agent lifecycle szabályok — push vs. PR vs. merge jogosultság)

## Findings

1. **Lokális pytest zöld volt, de hamis biztonságot adott.** Lokálisan egy tiszta venv-ben
   (`pytest>=8.0` telepítve a `tests/requirements.txt`-ből) mind a 12 teszt PASSED. Az ok: a
   `tools/update-index.sh` belül `python3 -` heredoc-ot hív, ami `import yaml`-t használ — ez
   a **rendszer python3-at** hívja, nem a venv python3-at, és a dev gépen `python3-yaml` apt
   csomag már telepítve volt. Ez elfedte, hogy a `tests/requirements.txt` valójában hiányos.

2. **Az első valódi CI run elbukott, és ez bizonyította a hiányt.** A `.github/workflows/tests.yml`
   első push-a után (commit `3ec205b`) megnyitottam PR #8-at
   (`feature/factory-tooling-ci-001` → `main`), hogy a `pull_request` trigger lefusson — a
   `push` trigger csak `main`-re van kötve a spec szerint, így önmagában a feature branch push
   nem indít runt. Az így keletkezett run (`27882226294`) **FAILED**, 2/12 teszt elbukott:
   `ModuleNotFoundError: No module named 'yaml'` — pontosan a fenti gyanú, csak GitHub Actions
   runneren reprodukálva, ahol nincs előtelepítve `python3-yaml`.

3. **Javítás: `PyYAML>=6.0` hozzáadva a `tests/requirements.txt`-hez** (commit `66a77a2`). Ezt
   előbb lokálisan is megerősítettem egy tiszta venv-vel, ahol a venv bin-t a PATH elejére
   tettem (hogy a subprocess `python3` hívás is a venv-re mutasson, ne a rendszerre) — 12/12
   PASSED. Push után a CI run (`27882265563`), UGYANAZON a commit-on (`66a77a2`), **SUCCESS**,
   12/12 PASSED.

4. **`push` trigger (`branches: main`) szándékosan nem tesztelt ebben a jobban.** A spec
   ("Main-re az agent NEM pushol") és a CLAUDE.md lifecycle ("Push `main`-re kizárólag az
   orchestrátor joga") miatt nincs mód arra, hogy az agent valódi push-csal main-re tesztelje
   ezt az ágat — ez csak az első tényleges merge-nél fog lefutni. Ezt limitációként jelölöm,
   nem proven állításként.

5. **PR #8 nyitva maradt.** A PR-t kizárólag azért nyitottam meg, hogy a `pull_request` trigger
   egyáltalán lefusson (a `push` trigger csak `main`-re van kötve, így a feature branch push
   önmagában zéró runt produkál). Nem mergeltem — a merge legitimáció kizárólag az
   orchestrátoré. A PR két on-topic commitot tartalmaz (workflow + requirements fix), és
   alkalmas arra, hogy a `/job-close` lépés újrahasználja vagy lezárja.

## Claim-Evidence Matrix

| Claim | Status | Evidence | Verification Method | Risk |
|---|---|---|---|---|
| `.github/workflows/tests.yml` létezik, `pull_request` (bármely branch → main) + `push` (main) triggerrel | proven | fájl tartalom, commit `3ec205b` | fájl olvasás | low |
| `pull_request`-triggerelt CI run tényleg lefutott ezen a branch-en/commit-on | proven | `gh run list --repo CentralInfraCore/cic-mcp-factory --branch feature/factory-tooling-ci-001`: run `27882265563`, conclusion=success, event=pull_request, headSha=`66a77a29c48f28878fe0b219c9926e00b494fde5` == `git rev-parse HEAD` | `gh run list` / `gh run view --json headSha,conclusion,event` | low |
| Mind a 12 teszt lefutott és zöld volt a CI-ben (nem csak a workflow maga) | proven | `gh run view 27882265563 --log`: `collecting ... collected 12 items` → 12× `PASSED` sor → `============================== 12 passed in 0.34s ==============================` | `gh run view --log` | low |
| Lokális pytest futás is zöld (külön bizonyíték a CI-től) | proven | lokális venv futás, PATH-prioritizált subprocess python3-mal: `12 passed in 0.34s` | lokális `pytest tests/ -v` futtatás | low |
| A `PyYAML` hiány valódi hiba volt, nem csak feltételezés | proven | run `27882226294` (commit `3ec205b`, PR #8 első push): conclusion=failure, `gh run view --log-failed`: `ModuleNotFoundError: No module named 'yaml'`, `2 failed, 10 passed` | `gh run view --log-failed` az első, hibás futáson | low |
| Egyetlen Python verzió (3.12) használt, nincs mátrix build | proven | workflow fájl: `python-version: "3.12"`, egyetlen `jobs:` blokk | fájl tartalom | low |
| `push` (`branches: main`) trigger tényleg lefut sikeresen | unknown | nincs tesztelve — valódi push `main`-re csak az orchestrátor jogköre, ez a job nem tudja előidézni | nincs — deklarált limitáció | medium (alacsony bukási eséllyel, ugyanaz a job-definíció mint a `pull_request` ágon, de tényszerűen igazolatlan az első merge-ig) |

## Decisions Proposed

- A `feature/factory-tooling-ci-001` branch (PR #8, már megnyitva) mergelése `main`-be a
  `/job-close` review után, `status_after_merge: experimental` jelöléssel, a spec indoklása
  szerint (nincs előzmény, 2-3 PR kell `candidate`-hez).
- A `push:main` trigger első valódi tesztje legyen az első tényleges merge — ezt nem kell
  külön jobnak nyitni, elég ha az orchestrátor a `/job-close`/merge után egy `gh run list
  --branch main` paranccsal megerősíti.

## Rejected / Out Of Scope

- Mátrix build több Python verzióra — explicit nem cél a spec szerint.
- A 3 shell tool (`run-job.sh`, `update-index.sh`, `validate-spec.sh`) funkcionális módosítása —
  csak a `tests/requirements.txt` (teszt-függőség manifeszt) változott, a tool-ok logikája nem.
- CI bekötés más `cic-mcp-*` repóba — explicit külön jövőbeli job, a spec szerint csak ha ez itt
  bizonyítottan működik.
- `run-job.sh` git/agent-integrációs tesztje — explicit külön job, az előző job "Next Jobs"-ja
  szerint.
- PR #8 lezárása/mergelése — a merge legitimáció kizárólag az orchestrátoré a CLAUDE.md
  lifecycle szerint, ezért nyitva maradt.

## Risks

- A `push:main` trigger-ág igazolatlan ebben a jobban (lásd Claim-Evidence Matrix) — alacsony
  bukási eséllyel, mert ugyanazokat a step-eket futtatja mint a `pull_request` ág, de technikailag
  nem bizonyított az első merge-ig.
- A `PyYAML>=6.0` verziópin lazán van rögzítve — `experimental` státusznál ez alacsony kockázat,
  de ha reprodukálhatósági gond adódna, érdemes lehet pontosabb pin-re váltani.
- PR #8 két commitot tartalmaz (workflow létrehozás + requirements fix) — mindkettő on-topic és
  a hiba-felfedezés/javítás folyamatát dokumentálja, de az orchestrátor squash-elheti egybe, ha
  a `/job-close` egy commitot vár.

## Definition Of Done Check

- [x] `.github/workflows/tests.yml` létrejön, `pull_request` + `push` trigger `main`-re —
  lásd `.github/workflows/tests.yml`, commit `3ec205b`
- [x] a feature branch push UTÁN legalább egy VALÓDI Actions run elindul ÉS SUCCESS-szal zárul
  ugyanezen a commit-on — run `27882265563`, headSha `66a77a29c48f28878fe0b219c9926e00b494fde5`
  == `git rev-parse HEAD`, run URL:
  `https://github.com/CentralInfraCore/cic-mcp-factory/actions/runs/27882265563`
- [x] a CI log-ban látható, hogy mind a 12 teszt lefutott és zöld volt — idézve fent
  (`collected 12 items`, 12× `PASSED`, `12 passed in 0.34s`)
- [x] claim-evidence tábla kitöltve, minden `proven` állításhoz tényleges `gh run` kimenet idézve

## Next Jobs

- Az első tényleges `main`-re merge után `gh run list --repo CentralInfraCore/cic-mcp-factory
  --branch main`-nel megerősíteni, hogy a `push:main` trigger-ág is lefut és zöld (nem külön
  job, beépíthető a `/job-close` review-ba).
- (örökölve az előző jobtól) `run-job.sh` git/agent-integrációs teszt job.
- (örökölve) CI kiterjesztése más `cic-mcp-*` repókra, 2-3 sikeres PR után, ha ez a job
  `candidate`-re lép.
