# Job: factory-tooling-ci-001

## Kontextus

A `factory-tooling-test-suite-001` job (lásd
`jobs/factory-tooling-test-suite-001/output/factory-tooling-test-suite-report.md`) létrehozott
egy 12 tesztből álló pytest suite-ot a `cic-mcp-factory` saját lifecycle-tooling-jára
(`tools/run-job.sh`, `tools/update-index.sh`, `tools/validate-spec.sh`). Ez a teszt-suite
jelenleg KIZÁRÓLAG manuálisan futtatható — nincs CI, ami minden PR-en automatikusan
lefuttatná. Ez a job ezt a hiányt zárja: a `cic-mcp-factory` repo (és csak ez) az ELSŐ
a `cic-mcp-*` családban, ami GitHub Actions workflow-t kap.

## Target

- target repo: `cic-mcp-factory` (önmaga)
- target path: `.github/workflows/`
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: ez az első CI-bekötés a `cic-mcp-*` családban — nincs még előzmény vagy
  konvenció, amihez "candidate"-ként viszonyítani lehetne. `candidate`-re lépéshez legalább
  2-3 további PR-en kellene bizonyítania hogy megbízhatóan, hamis-pozitív/negatív nélkül fut.

## Sources

- `${WORKDIR}/jobs/factory-tooling-test-suite-001/output/factory-tooling-test-suite-report.md`
  — a teszt-suite tartalma, hogy mit kell CI-ben futtatni
- `${WORKDIR}/tests/requirements.txt` — a teszt-függőségek
- `${WORKDIR}/tests/` — a teljes teszt-suite, amit a workflow-nak futtatnia kell

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Futtasd le lokálisan `pytest tests/ -v`-t, MIELŐTT a workflow-t megírod, hogy lásd a
   pontos elvárt kimenetet (12 teszt, melyik fájlokban)

## Feladat

1. Hozz létre `.github/workflows/<valami>.yml`-t, ami `pull_request` (bármely branch-ről
   `main`-re) ÉS `push` (`main`-re) eseményekre triggerel, és lefuttatja:
   - `pip install -r tests/requirements.txt`
   - `pytest tests/ -v`
   Egyetlen Python verzió elég induláshoz (pl. 3.12, ami megegyezik a fejlesztői
   környezettel) — nincs szükség mátrix build-re ennél a státusznál.

2. **Push-old a feature branch-et, és bizonyítsd hogy a workflow tényleg lefutott és
   SUCCESS-szal zárult EZEN a commit-on** — ez a kötelező reachability-bizonyíték, nem a
   yaml fájl megléte. Ehhez:
   ```bash
   git push -u origin feature/factory-tooling-ci-001
   gh run list --repo CentralInfraCore/cic-mcp-factory --branch feature/factory-tooling-ci-001 --limit 5
   gh run view <run-id> --repo CentralInfraCore/cic-mcp-factory --log | tail -60
   ```
   Idézd a `gh run list` kimenetét (run id, status, conclusion, branch, commit sha) és a
   `gh run view --log` releváns részét, ami megerősíti hogy mind a 12 teszt lefutott és zöld
   volt a CI futásban (nem csak lokálisan).

3. Ha a workflow első futása hibázik (pl. YAML syntax, path hiba, függőség hiánya), javítsd
   és pusholj újra, AMÍG nem kapsz egy valódi SUCCESS futást ezen a branch-en — egy
   YAML fájl, ami sosem futott le sikeresen, NEM teljesíti ezt a jobot.

## Nem cél

- Mátrix build több Python verzióra
- A 3 shell tool funkcionális módosítása
- Más `cic-mcp-*` repóba CI bekötése (ez külön job lenne, ha ez itt bizonyítottan működik)
- A `run-job.sh` git/agent-integrációs tesztje (külön job, lásd a megelőző job "Next Jobs"-ját)

## Required Output Files

- `output/factory-tooling-ci-report.md`

## Required Report Sections

A report MUST kövesse az `.cic-context/factory-docs/acceptance-contract.md`
"Universal Output Contract" szakaszát:

```markdown
# factory-tooling-ci-001 Output

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

Elfogadott `Status` értékek (teszt-lefedettségi/működési állítás, nem
forráskód-reachability-besorolás): `proven`, `partial`, `missing`, `rejected`, `unknown`.

## Definition Of Done

- [ ] `.github/workflows/<name>.yml` létrejön, `pull_request` + `push` trigger `main`-re
- [ ] a feature branch push UTÁN legalább egy VALÓDI Actions run elindul ÉS SUCCESS-szal
      zárul ugyanezen a commit-on — `gh run list`/`gh run view` kimenet idézve, run URL-lel
- [ ] a CI log-ban látható, hogy mind a 12 teszt lefutott és zöld volt (nem csak a workflow
      maga zöld, a teszt-eredmény részletei is idézve)
- [ ] claim-evidence tábla kitöltve, minden `proven` állításhoz tényleges `gh run`
      parancs-kimenet idézve, NE csak a yaml fájl tartalma

## Forbidden Shortcuts

- workflow yaml fájl létezik ≠ CI lefutott — egy syntaktikusan helyes yaml fájl, ami sosem
  futott sikeresen, nem bizonyítja hogy a CI működik
- "a yaml helyes, biztos lefut" ≠ tényleges `gh run` kimenet idézve — minden `proven`
  állításhoz a VALÓDI Actions run eredményét kell idézni, nem feltételezést
- lokális `pytest` futás zöld ≠ CI-ben is zöld — a kettő külön bizonyíték, mindkettő kell

## Git instrukciók

Push a `feature/factory-tooling-ci-001` branch-re, a `cic-mcp-factory` repóban (ez egyben
a target repo is). Main-re az agent NEM pushol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/workflow YAML angolul.
