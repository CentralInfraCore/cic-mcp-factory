# Job: factory-tooling-test-suite-001

## Kontextus

A `cic-mcp-factory` saját lifecycle-tooling-jának (`tools/run-job.sh`, `tools/update-index.sh`,
`tools/validate-spec.sh`) jelenleg NINCS automatizált tesztje — ezt a `CLAUDE.md` "Ismert
korlátok / roadmap" szekciója is explicit megnevezi hiányként. Ez a mai napi
`session-infra-pipeline-fix-001` job futtatása során is konkrét problémát okozott: két
agent-futási kísérlet hibásan próbált aszinkron várakozási mintát alkalmazni, és csak
manuális orchestrátor-beavatkozással lehetett feltárni, hogy hol állt el a futás. Egy
tesztelt tooling-réteg korábban elkapta volna a hasonló, a script viselkedésében rejlő
regressziókat.

Ez a job nem ad új session/gateway/shared capability-t — a `cic-mcp-factory` saját
build/maintenance eszközeinek megbízhatóságát növeli.

## Target

- target repo: `cic-mcp-factory` (önmaga — a `tools/` és a teszt-suite ugyanide kerül)
- target path: `tools/`, új `tests/` mappa a repo gyökerében
- change_type: `enhancement`
- status_after_merge: `experimental`
- status indoklás: maga a teszt-suite nem ad új capability-t, "experimental" itt azt
  jelzi, hogy ez az első automatizált védelmi réteg a factory tooling-on — a
  `candidate`/`canonical` szóba sem jöhet, amíg nincs legalább egy teljes capability-job
  lifecycle, ami ezzel a teszt-suite-tal van lefedve (ez ez a job maga lesz az első).

## Sources

- `${WORKDIR}/tools/run-job.sh` — a teljes script, kb. 14 KB
- `${WORKDIR}/tools/update-index.sh` — a teljes script (bash + beágyazott Python heredoc)
- `${WORKDIR}/tools/validate-spec.sh` — a teljes script, kb. 75 sor (K1/K3/K4/K7/K7b/K8/K9
  regex-mintaillesztés)
- `${WORKDIR}/CLAUDE.md` — "Ismert korlátok / roadmap" szekció (a hiány eredeti megnevezése)
- `${WORKDIR}/jobs/session-infra-pipeline-fix-001/output/session-infra-pipeline-fix-report.md`
  "Risks" szekció — a mai napi konkrét incidens, ami ezt a jobot motiválja

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el mind a 3 shell scriptet teljesen, MIELŐTT tesztet írsz — a viselkedésüket a
   kódból derítsd ki, ne feltételezésből

## Feladat

Hozz létre egy automatizált, nem-mockolt teszt-suite-ot a 3 shell tool-ra. Python/pytest
ajánlott (a repóban már van pytest-infrastruktúra mintaként más `cic-mcp-*` repókban,
és nincs szükség új csomag-függőségre — bash-natív `bats` keretrendszer telepítése külön
lépés lenne, ezt csak akkor válaszd, ha indokolod miért jobb a pytest+subprocess
megoldásnál).

### 1. `validate-spec.sh` tesztek

Hozz létre fixture `input.md` fájlokat (ideiglenes könyvtárban vagy `tests/fixtures/`-ban),
mindegyik PONTOSAN egy K-kritériumot sért (K1, K3, K4, K8 — ezek mindig kötelezőek), és
egyet, ami mindegyiket teljesíti. Futtasd a valódi `validate-spec.sh`-t (NEM mock-olva) minden
fixture-re, és ellenőrizd hogy az exit code és a kiírt `FAIL:` sor pontosan egyezik az elvárt
hibával.

### 2. `update-index.sh` tesztek

Hozz létre fixture `jobs/` fa-struktúrát (több `meta.yaml`, különböző `status`/`level`/
`capability` mezőkkel, és egy teljesen üres `jobs/` esetet is). Futtasd a valódi
`update-index.sh`-t egy ideiglenes munkakönyvtárban, és ellenőrizd hogy a generált
`index.yaml` tartalma (job count, mezők, az üres-eset `jobs: []` formátuma) pontosan egyezik
az elvárt kimenettel.

### 3. `run-job.sh` tesztek — KORLÁTOZOTT KÖRBEN

`run-job.sh` valódi git clone/push és `claude --print` hívást csinál — ezeket NE futtasd
éles hálózati/agent-hívással a teszt-suite-ban (ez instabil, lassú, és külső erőforrást
igényelne CI-ben). Tesztelendő, ami hálózat/agent nélkül is determinisztikusan ellenőrizhető:
- hívás job-id argumentum nélkül → usage hibaüzenet, nem-nulla exit code
- ha a `validate-spec.sh` NO-GO-t ad egy fixture jobra, a `run-job.sh` ezt a pontot előtte
  meghívja és nem folytatja az agent-indítást (ezt valódi `validate-spec.sh` hívással
  ellenőrizd, csak az agent-indítási részt mockold/skip-eld)
- `--resume` flag jelenléte/hiánya helyesen állítja be a script belső állapotát (ehhez
  szükség lehet a script kisebb refaktorálására, hogy a flag-parsing logika egy külön,
  tesztelhető függvénybe/blokkba kerüljön — ha ezt megteszed, idézd a diff-et)

Ha valamilyen `run-job.sh` viselkedés csak teljes git/agent integrációval tesztelhető,
ezt EXPLICIT írd le a report "Risks" szekciójában mint nem-fedett területet, NE
hamisíts hozzá egy mock-olt "passed" tesztet.

## Nem cél

- a 3 shell script bármilyen funkcionális átírása/refaktorálása (kivéve a `--resume`
  flag-parsing kiemelését, ha az a tesztelhetőséghez szükséges, lásd fent)
- CI pipeline (GitHub Actions) bekötése — ez egy következő job
- a meta.yaml schema validator vagy a PR-readiness checker (ezek külön jobok,
  `factory-meta-schema-validator-001` / `factory-pr-readiness-checker-001`)

## Required Output Files

- `output/factory-tooling-test-suite-report.md`

## Required Report Sections

A report MUST kövesse az `.cic-context/factory-docs/acceptance-contract.md`
"Universal Output Contract" szakaszát:

```markdown
# factory-tooling-test-suite-001 Output

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

Elfogadott `Status` értékek (ennél a jobnál relevánsak — teszt-lefedettségi állítás, nem
forráskód-reachability-besorolás): `proven`, `partial`, `missing`, `rejected`, `unknown`.

## Definition Of Done

- [ ] legalább 4 teszt a `validate-spec.sh`-ra (K1/K3/K4/K8 megsértése külön-külön + 1 GO eset),
      mindegyik a valódi scriptet hívja, nem mock-olva, lefuttatva és zöld
- [ ] legalább 2 teszt az `update-index.sh`-ra (normál eset + üres `jobs/` eset), a valódi
      scriptet hívva, lefuttatva és zöld
- [ ] legalább 2 teszt a `run-job.sh`-ra a fent megengedett, hálózat-mentes körben
- [ ] a teljes teszt-suite egyetlen paranccsal lefuttatható (pl. `pytest tests/`), és a
      kimenet idézve a reportban
- [ ] claim-evidence tábla kitöltve, nem üres, minden `proven` állításhoz tényleges
      parancs-kimenet idézve
- [ ] explicit jelzett azon `run-job.sh` viselkedések listája, amik nem fedettek
      (git/agent-integráció), `Risks` szekcióban

## Forbidden Shortcuts

- teszt fájl megírva ≠ sikeres futás — minden tesztet tényleg le kell futtatni, a kimenetet
  idézni kell a reportban
- mock-olt git/claude hívás ≠ bizonyítja hogy a script működik — a `validate-spec.sh` és
  `update-index.sh` teszteknek a VALÓDI scriptet kell hívniuk, fixture input/output adatokkal,
  nem egy újraírt/mock-olt verziót
- "a script logikája egyszerű, nem kell tesztelni" ≠ elfogadható indoklás bármelyik kötelező
  teszt kihagyására

## Git instrukciók

Push a `feature/factory-tooling-test-suite-001` branch-re, a `cic-mcp-factory` repóban
(ez egyben a target repo is — nincs külön workplace repo). Main-re az agent NEM pushol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/teszt-nevek angolul.
