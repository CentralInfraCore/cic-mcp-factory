# Job: session-docs-comment-audit-001

## Kontextus

Egy független orchestrátor-review (a `session-mcp-venv-fix-001` lezárása után, egy külső
elemzés ellenőrzése közben) konkrét dokumentáció-drift hibákat talált a `cic-mcp-session`
repóban: a `README.md`, `CLAUDE.md`, `docs/hu/architecture.md` és `docs/en/architecture.md`
"Jelenlegi állapot"/"Current status" szekciói MÉG azt írják, hogy a repo egy üres
`base-repo` bootstrap scaffold, "nincs még implementálva" a session adatfolyam — miközben a
TELJES session pipeline (envelope ingest, raw event store, worker loop, turn projector,
chunk indexer, vector/hybrid/FTS search, session_api, 7 tool-os MCP szerver, host-natív
`.venv-host` indítás) ~17 capability-jobon keresztül MÁR megépült és bizonyítva van. A
`MANIFEST.sha256` is 14 fájlra mismatch-et ad (`sha256sum -c MANIFEST.sha256` futtatva).

Ez egy DOKUMENTÁCIÓ/KOMMENT javító job — NEM funkcionális kódváltozás. A cél: a
dokumentáció és a kód-szintű kommentek tényleges állapota EGYEZZEN a repo valódi,
bizonyított implementációs állapotával.

## Target

- target repo: `cic-mcp-session`
- target path: `README.md`, `CLAUDE.md`, `docs/hu/architecture.md`,
  `docs/en/architecture.md` + bármely a 2. lépésben talált további stale fájl
- change_type: `fix`
- status_after_merge: `experimental`
- status indoklás: dokumentáció-fix, nincs futtatható kód-változás, nincs hozzá új teszt —
  `candidate`-hez nem releváns ez a job típusa (sosem lesz "candidate" egy doc-fix, ez
  `experimental`-ban marad, amíg a következő funkcionális job nem zárja le másra)

## Sources

- `${WORKDIR}/.cic-context/factory-docs/architecture.md` — "cic-mcp-session" szekció
- `${WORKDIR}/.cic-context/factory-docs/execution-phases.md` — "Phase 3" szekció
- **KÖTELEZŐ elsődleges forrás (a `cic-mcp-session` repo `main`-jén):**
  - `README.md`, `CLAUDE.md`, `docs/hu/architecture.md`, `docs/en/architecture.md` — a
    "Jelenlegi állapot"/"Current status" szekciók (a konkrét stale szövegrész)
  - `output/session-*-report.md` — az ÖSSZES korábbi capability-job riportja a repóban
    (~17 fájl) — ezekből KELL idézni, ami bizonyítja mi épült meg, NEM a saját
    emlékezetből/általános tudásból kell újraírni a "mi van implementálva" állítást
  - `session_store/*.py`, `hooks/log-event.py`, `mcp-server/session_server.py`,
    `mk/infra.mk`, `Makefile` — modul-szintű docstring-ek/kommentek

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. A 4 már ismert stale szekció javítása

Írd át a `README.md`, `CLAUDE.md`, `docs/hu/architecture.md`, `docs/en/architecture.md`
"Jelenlegi állapot"/"Current status" szekcióit úgy, hogy pontosan leírják a TÉNYLEGES
implementált állapotot. MINDEN állításhoz idézd a konkrét `output/session-*-report.md`
fájlt vagy kódfájlt, ami bizonyítja — NE a saját általános tudásodból írd újra, hogy "mi
van implementálva", hanem a riportokból/kódból szó szerint idézve.

### 2. Szisztematikus, grep-alapú komment-audit

A 4 ismert fájlon TÚL, futtass egy szisztematikus keresést a többi forrásfájlban is stale
kommentekre/docstring-ekre:

```
grep -rn "not yet implemented\|nincs még implementálva\|TODO\|placeholder\|scaffold" \
  session_store/ hooks/ mcp-server/ mk/ Makefile --include="*.py" --include="*.mk" \
  -- Makefile 2>/dev/null | grep -v test_
```

(vagy ekvivalens, fájltípusonként). MINDEN találatot egyenként ítélj meg: `stale` (a
megjegyzés téves a jelenlegi kód mellett — javítsd) vagy `accurate`/`not applicable` (a
megjegyzés még helyes, vagy nem releváns kontextusban van, pl. egy MÁSIK fájlra/jövőbeli
tervre utal). Idézd a teljes grep-kimenetet ÉS minden találat egysoros ítéletét.

### 3. `MANIFEST.sha256` regenerálás

```
make manifest-update
make manifest-verify
```

Mindkét parancs kimenetét idézd. A `manifest-verify`-nak utána HIBA NÉLKÜL kell lefutnia.

### 4. Regresszió-ellenőrzés

Mivel ez egy dokumentáció/komment-fix, NEM funkcionális kódváltozás: bizonyítsd, hogy a
meglévő teszt-suite (`tests/test_session_store/`) a változások után is változatlanul fut —
idézd a tényleges futtatási kimenetet (pass/fail számok), NE csak feltételezd hogy a
doc-fix nem érintette a kódot.

## Nem cél

- funkcionális kódváltozás (session_store/*.py, hooks/log-event.py, mcp-server/*.py
  logikájának módosítása) — KIZÁRÓLAG docstring/komment szintű javítás engedélyezett
- új teszt írása
- a `.mcp.json.tpl`/`mk/infra.mk`/`Makefile` FUNKCIONÁLIS tartalmának módosítása (csak a
  bennük lévő kommentek, ha stale-nek bizonyulnak)
- `cic-mcp-factory`/`cic-mcp-gateway`/más repó módosítása

## Required Output Files

- `output/session-docs-comment-audit-report.md`

## Required Report Sections

```markdown
# session-docs-comment-audit-001 Output

## Scope
## Inputs Read
## Fixed Sections — Before/After Diff

(mind a 4 ismert fájlra, teljes diff idézve)

## Systematic Comment Scan

(teljes grep-kimenet + minden találat egysoros ítélete: stale / accurate / not applicable)

## Findings
## Claim-Evidence Matrix

| Claim | Status | Evidence | Verification Method | Risk |
|---|---|---|---|---|

## MANIFEST Regeneration

(`make manifest-update` + `make manifest-verify` kimenet idézve)

## Regression Check

(teszt-suite kimenet idézve)

## Decisions Proposed
## Rejected / Out Of Scope
## Risks
## Definition Of Done Check
## Next Jobs
```

Elfogadott `Status` értékek: `proven`, `partial`, `missing`, `rejected`, `unknown`.
`proven` egy "X szekció javítva, pontos" állításra KIZÁRÓLAG akkor használható, ha a
before/after diff idézve van ÉS a javított szöveg konkrét file:line hivatkozást ad a
bizonyító riportra/kódra — a szöveg megváltozása önmagában ≠ implemented, csak a citált
forrás-egyezés bizonyít.

## Definition Of Done

- [ ] mind a 4 ismert fájl "Jelenlegi állapot"/"Current status" szekciója javítva,
      file:line hivatkozással a bizonyító forrásra
- [ ] szisztematikus grep-scan lefuttatva a többi fájlra, minden találat egyenként
      megítélve
- [ ] `make manifest-update` + `make manifest-verify` lefuttatva, hibamentes,
      kimenet idézve
- [ ] regresszió-ellenőrzés (teszt-suite) lefuttatva, kimenet idézve
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a "Jelenlegi állapot" szekciók átírása forrás-idézet nélkül, csak általános tudásból
- a szisztematikus grep-scan kihagyása, csak a 4 már ismert fájl javítása
- bármilyen funkcionális kódváltozás docs/komment-fix ürüggyel

## Git instrukciók

Push a `feature/session-docs-comment-audit-001` branch-re, KIZÁRÓLAG a `cic-mcp-session`
célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni, elég a lokális commit).
Main-re az agent NEM pushol. **NE módosítsd a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/fájlnevek angolul.
