# Job: session-ingest-hook-sandboxed-001

## Kontextus

A `.cic-context/factory-docs/execution-phases.md` "Phase 6 - Wiring" szekciója
EXPLICIT, dokumentált módon kimondja: "a session-hook tényleges bekapcsolása
egy aktív Claude Code settings.json-ba (privacy/consent döntés: minden
tool-use logolva lenne)" — ez TUDATOSAN KI VAN HAGYVA az agent-job-ok
köréből, mert ez egy ember/operátor döntés, nem agent által eldönthető kérdés.

Ez a job EZT a határt TISZTELI: megépíti és teszteli a 6 Claude Code hook
scriptet (`UserPromptSubmit`, `PostToolUse`, `PostToolUseFailure`, `Stop`,
`SessionStart`, `SessionEnd`), amelyek a `session-transcript-reader-001`
(prerequisite) kimenetét az ingest pipeline-ba juttatnák — DE KIZÁRÓLAG egy
SANDBOXOLT, a job saját workspace-ében létrehozott `settings.json` és
sandboxolt Postgres ellen. **Ez a job SOHA nem ír valódi `~/.claude/
settings.json`-ba vagy `~/.claude-personal/settings*.json`-ba** — az éles
aktiválás egy KÜLÖN, a te explicit jóváhagyásodra váró lépés, amit ez a job
egy "go-live checklist" dokumentummal készít elő, de nem hajt végre.

## Target

- target repo: `cic-mcp-session`
- target path: `hooks/` alá a 6 script (a meglévő `hooks/log-event.py`
  konvencióját követve, ha van ilyen) + `output/session-ingest-hook-
  sandboxed.md` + `output/session-ingest-hook-go-live-checklist.md`
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: a hook scriptek maguk valódi, futtatott teszttel
  bizonyítottak SANDBOXBAN, de az éles bekötés (ami a tényleges
  "production-ready" státuszhoz kellene) explicit, ezen a jobon TÚLI emberi
  döntés — innen `experimental`, nem `candidate`

## Sources

- **KÖTELEZŐ elsődleges forrás:**
  - `.cic-context/factory-docs/execution-phases.md` Phase 6 szekció — a
    "tudatosan kihagyva" lista, amit ez a job tisztel
  - `jobs/session-transcript-reader-001/output/session-transcript-reader.md`
    — a prerequisite kimenete, amit a hook scriptek hívnak
  - `hooks/log-event.py` (ha létezik a `cic-mcp-session` repóban — ellenőrizd
    grep-pel, ez az egyetlen meglévő hook-konvenció referenciapont)

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Ellenőrizd, hogy `session-transcript-reader-001` `done` állapotban van-e
   (`jobs/session-transcript-reader-001/meta.yaml` a cic-mcp-factory
   klónban) — ha NEM, állítsd a jobot NO-GO-ra, és állj meg
3. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. A 6 hook script

Mindegyik hook script:
- olvassa a stdin JSON payload-ot (session_id, transcript_path, cwd,
  hook_event_name, stb. — lásd `session-hook-collector-001` report)
- `Stop` eseménynél hívja a `session-transcript-reader-001` olvasóját az
  adott `transcript_path`-on
- a kinyert turn(ok)at egy SANDBOXOLT outbox/queue-ba írja (NEM a valódi
  production Postgres-be — ez a job saját, eldobható sandbox DB-t használ)
- **failure-isolation**: bármilyen kivétel a hook futása közben EL VAN
  KAPVA és NAPLÓZVA, SOHA nem propagálódik úgy, hogy a user Claude Code
  turnját blokkolja vagy hibásra állítsa

### 2. Sandboxolt teszt-infrastruktúra

Hozz létre egy ELDOBHATÓ `settings.json`-t a job workspace-ében (pl.
`workspace_tmp/sandboxed-settings.json`), ami a 6 hook scriptet a SAJÁT
sandbox-jára köti be. Bizonyítsd:

```
grep -rn "settings.json\|\.claude" --include="*.py" hooks/ | grep -v test_
```

hogy a kódban (a teszteket KIZÁRVA) SEHOL nem szerepel `~/.claude/
settings.json` vagy `~/.claude-personal/settings` írási célként — idézd a
találatok file:line hivatkozását, és mutasd meg hogy mindegyik a
SANDBOXOLT path-ra mutat, nem a valódi felhasználói konfigurációra.

### 3. Failure-isolation — valós teszt

Írj egy tesztet, amely DELIBERATE módon megtöri egy hook bemenetét (pl.
hibás JSON, hiányzó mező, nem-létező transcript_path), és bizonyítja, hogy a
hook ettől NEM dob kivételt kifelé (a hívó folyamat szempontjából a hook
"lágyan" hibázik, naplóz, és visszaadja a vezérlést).

### 4. "Go-live checklist"

Írj egy KÜLÖN dokumentumot (`output/session-ingest-hook-go-live-
checklist.md`), ami PONTOSAN felsorolja, mit kellene NEKED (emberi
operátorként) megtenned, ha úgy döntesz, hogy éles bekötöd ezt:
- melyik settings.json-ba, milyen hook-blokkal
- milyen env-változókat kell beállítani (ld. `session-runtime-env-
  unification-001`, ha addigra elkészült)
- milyen privacy/consent kockázatot vállalsz (minden tool-use logolva lesz)
- hogyan tudod visszavonni, ha úgy döntesz

Ez a dokumentum NEM egy végrehajtási lépés ebben a jobban — csak előkészület.

## Nem cél

- bármilyen írás `~/.claude/settings.json`-ba vagy
  `~/.claude-personal/settings*.json`-ba — ez a LEGFONTOSABB tiltás ebben a
  jobban
- tartós, nem-eldobható Postgres-instance vagy systemd timer telepítése
  (hosting-döntés, külön ember/operátor lépés)
- a `session-transcript-reader-001` modul módosítása (csak hívja, nem
  módosítja)
- a "go-live checklist" VÉGREHAJTÁSA — csak a dokumentum megírása a feladat

## Required Output Files

- `output/session-ingest-hook-sandboxed.md`
- `output/session-ingest-hook-go-live-checklist.md`
- a 6 hook script
- a hozzá tartozó teszt-fájl(ok)

## Required Report Sections

```markdown
# session-ingest-hook-sandboxed-001 Output

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

- [ ] mind a 6 hook script létezik, mindegyik önállóan tesztelve
- [ ] grep -rn bizonyítja: SEHOL nincs írás `~/.claude/settings.json`-ba vagy
      `~/.claude-personal/settings*.json`-ba a kódban vagy a tesztekben
- [ ] failure-isolation valós teszttel bizonyítva (deliberate broken input,
      a hívó nem kap kivételt)
- [ ] "go-live checklist" dokumentum megírva, konkrét, végrehajtható
      lépésekkel
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a hook script léte a repóban ≠ implemented — a futtatott teszt kimenete
  bizonyít, a kód megírása nem
- bármilyen írás vagy módosítás `~/.claude/` vagy `~/.claude-personal/` alatt
  (ez a LEGFONTOSABB tiltott rövidítés ebben a jobban)
- olyan hook, ami blokkolhatja vagy hibásra állíthatja a user tényleges
  Claude Code turnját
- "go-live ready" állítás státuszként — a `status_after_merge` pontosan
  azért `experimental`, mert az aktiválás egy külön emberi döntésre vár

## Git instrukciók

Push a `feature/session-ingest-hook-sandboxed-001` branch-re, KIZÁRÓLAG a
`cic-mcp-session` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell
pusholni, elég a lokális commit). Main-re az agent NEM pushol. **NE
módosítsd a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek/kód angolul.
