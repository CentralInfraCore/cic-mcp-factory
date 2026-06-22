# Job: session-mcp-venv-fix-001

## Kontextus

A `session-mcp-config-wiring-001` job független verifikációja során megerősítve:
a `.mcp.json.tpl` `command` mezője (`{{REPO_ROOT}}/p_venv/bin/python`) SOSEM létezik
egy `make deps` futás után, mert a `docker-compose.yml` `setup` service-e
`pip install --target /app/p_venv`-et használ (lapos package-könyvtár, a `builder`
service `PYTHONPATH=/app:/app/p_venv`-alapú workflow-jához), NEM egy valódi
venv-et `bin/python` symlinkkel. Ez a hiba a `.mcp.json.tpl` MINDKÉT bejegyzését
érinti — a MEGLÉVŐ `cic-graph`-ot ÉPPÚGY, mint az újabb `cic-session`-t.

Ez a job a GYÖKÉROKOT javítja — NEM csak az egyik bejegyzést.

**Fontos elhatárolás**: a `docker-compose.yml` `setup`/`builder` service-ek
MEGLÉVŐ, Docker-alapú workflow-ja (`make deps`, `make up`, `make shell`, `make build`)
NEM törhet el. A `p_venv` `PYTHONPATH`-alapú használata a `builder` service-ben
MARADJON működő — ezt a jobot a HOST-natív (nem Docker) indítási recept javítására
hoztuk létre, nem a Docker build-pipeline megváltoztatására.

## Target

- target repo: `cic-mcp-session`
- target path: a pontos mechanizmus (lásd "Feladat 1") rád van bízva — `.mcp.json.tpl`,
  `Makefile`/`mk/infra.mk`, és/vagy egy ÚJ script/target, attól függően melyik
  megoldást választod és indokolod
- change_type: `fix`
- status_after_merge: `experimental`
- status indoklás: a javítás bizonyítva tényleges subprocess+stdio handshake-kel
  mindkét szerverre, de SEMMILYEN éles session nincs rámutatva — `candidate`-hez egy
  tényleges, hosszabb-életű lokális/dev használat kellene

## Sources

- `${WORKDIR}/.cic-context/factory-docs/job-slices.yaml` —
  `session-mcp-venv-fix-001` bejegyzés — NORMATÍV
- **KÖTELEZŐ elsődleges forrás (mind már a `cic-mcp-session` `main`-en van):**
  - `cic-mcp-session/docker-compose.yml` — a `setup` service (`pip install --target
    /app/p_venv`) és a `builder` service (`PYTHONPATH=/app:/app/p_venv`) — ÉRTSD MEG
    a meglévő tervezési szándékot, MIELŐTT bármit módosítanál
  - `cic-mcp-session/Dockerfile` — `python:3.11-slim` alap image
  - `cic-mcp-session/.mcp.json.tpl` — mindkét bejegyzés (`cic-graph`, `cic-session`)
  - `cic-mcp-session/mk/infra.mk` — `infra.mcp.config`, `infra.deps`,
    `infra.mcp.run`, `infra.mcp.run.session`
  - `cic-mcp-session/Makefile` — a `.PHONY` lista és a meglévő alias-ok
  - `cic-mcp-session/output/session-mcp-config-wiring-report.md` — a korábbi job
    riportja, ami EZT a hibát elsőként azonosította (lásd "Risks" szekció)

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti KÖTELEZŐ forrásokat, MIELŐTT bármilyen kódot írnál

## Feladat

### 1. Mechanizmus-választás és indoklás

Két fő irány lehetséges (vagy egy harmadik, általad indokolt):
- **(A)** Hagyd a `setup`/`builder` Docker-workflow-t TELJESEN érintetlenül, és
  igazítsd a `.mcp.json.tpl` `command`/`env` mezőit ahhoz, AHOGY a `p_venv` TÉNYLEG
  működik (pl. `command: "{{REPO_ROOT}}/.venv-host/bin/python"` egy ÚJ,
  HOST-natív, `python3 -m venv`-vel épített venv-hez, VAGY system `python3` +
  `PYTHONPATH={{REPO_ROOT}}/p_venv` env-változó)
- **(B)** Adj egy ÚJ, host-natív venv build target-et (pl. `make deps.local` /
  `infra.deps.local`), ami `python3 -m venv` + `pip install -r requirements.txt`-vel
  épít egy VALÓDI venv-et egy ÚJ könyvtárban (NE a `p_venv`-be, hogy ne keveredjen a
  Docker-alapú flow-val), és a `.mcp.json.tpl` ERRE az új könyvtárra mutasson

Válassz EGYET, indokold a "Decisions Proposed"-ben, és KÖVETKEZETESEN alkalmazd MIND
A KÉT `.mcp.json.tpl` bejegyzésre (`cic-graph` ÉS `cic-session`) — ez NEM
csak a `cic-session`-re szóló javítás.

### 2. A meglévő Docker-workflow regresszió-mentessége

Bizonyítsd, hogy a MEGLÉVŐ `make deps`/`make up`/`make shell`/`make build`
Docker-alapú workflow A JAVÍTÁS UTÁN IS működik, változatlanul — idézd a tényleges
parancs-kimenetet.

### 3. Tényleges subprocess + stdio MCP handshake — MINDKÉT szerverre

A `session-mcp-config-wiring-001` mintáját követve (NEM in-process Python hívás):
indíts egy valódi Postgres tesztkonténert, futtasd `make mcp.config`-ot, és egy MCP
kliens-könyvtárral (`mcp.client.stdio`) csatlakozz ÖNÁLLÓ subprocess-ként ELŐSZÖR a
`cic-session` szerverhez (`list_tools()` → 7 tool), MAJD a `cic-graph` szerverhez
(`list_tools()` → a meglévő KB-tool-ok) — idézd mindkét kimenetet.

### 4. Regresszió-ellenőrzés

Futtasd le a TELJES meglévő `tests/test_session_store/` suite-ot.

## Nem cél

- a `cic-graph`/`cic-session` tool-ok logikájának módosítása
- a Docker `builder`/`setup` service-ek `PYTHONPATH`-alapú dependency-resolution
  viselkedésének megváltoztatása
- bármilyen éles session/`.claude/settings.json` módosítása
- SSE-mód, autentikáció, multi-instance kezelés

## Required Output Files

- `output/session-mcp-venv-fix-report.md`

## Required Report Sections

```markdown
# session-mcp-venv-fix-001 Output

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

Elfogadott `Status` értékek: `proven`, `partial`, `missing`, `rejected`, `unknown`.
`proven` KIZÁRÓLAG akkor használható, ha a tényleges subprocess+stdio handshake
kimenet idézve van — mindkét szerverre. A `.mcp.json.tpl`-ben lévő bejegyzés léte ≠
működik — csak a tényleges futtatás bizonyít.

## Definition Of Done

- [ ] mechanizmus-választás indokolva a "Decisions Proposed"-ben
- [ ] MINDKÉT `.mcp.json.tpl` bejegyzés (cic-graph + cic-session) a javított
      mechanizmust használja
- [ ] a meglévő Docker `make deps`/`make up`/`make shell`/`make build` workflow
      regresszió-mentessége bizonyítva, kimenet idézve
- [ ] TÉNYLEGES subprocess + stdio MCP handshake bizonyítva MINDKÉT szerverre,
      kimenet idézve mindkettőre
- [ ] teljes meglévő teszt-suite lefuttatva, regresszió-mentesség bizonyítva
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- csak a `cic-session` bejegyzés javítása, a `cic-graph` azonos, meglévő hibáját
  érintetlenül hagyva
- a Docker `builder` service `PYTHONPATH`-alapú dependency-resolution
  viselkedésének megtörése a javítás melléhatásaként
- azt állítani, hogy a stdio handshake működik anélkül, hogy TÉNYLEGESEN subprocess-
  ként futtatnád (in-process Python hívás NEM elég, a
  `session-mcp-config-wiring-001` saját bizonyítási mércéje szerint)

## Git instrukciók

Push a `feature/session-mcp-venv-fix-001` branch-re, KIZÁRÓLAG a `cic-mcp-session`
célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni, elég a lokális
commit). Main-re az agent NEM pushol. A teszteléshez használt Docker konténert a
munka végén állítsd le és töröld. **NE módosítsd a `meta.yaml` `status` mezőjét**
sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/teszt-nevek angolul.
