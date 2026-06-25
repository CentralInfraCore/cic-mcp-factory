# Job: session-runtime-env-unification-001

## Kontextus

A `cic-mcp-session` worker loop, a session MCP szerver, és a `cic-mcp-gateway`
session-adapter (`gateway_core/compile_context.py`) jelenleg egymástól
függetlenül, eltérő módon olvashatják be a Postgres kapcsolati konfigurációt
(DSN/host/port/dbname) — ez azt a kockázatot hordozza, hogy egy
konfiguráció-változás csak az egyik komponensben érvényesül, és a worker más
DB-t lát, mint az MCP szerver vagy a gateway.

Ez a job EZT a drift-et zárja: egyetlen, közös env-fájl konvenciót vezet be
(pl. `session.env`), amit a worker loop, a session MCP szerver, a leendő
ingest hook (`session-ingest-hook-sandboxed-001`), és a gateway
session-adapter hívási útja EGYFORMÁN tölt be — és egy valós smoke teszttel
bizonyítja, hogy mindegyik ugyanazt a DB-t látja.

## Target

- target repo: `cic-mcp-session` (config-fájl és loader központi helye)
- workplace: `cic-mcp-gateway` is klónozva (a session-adapter hívási útjának
  ellenőrzéséhez/igazításához, de a gateway saját logikáját NEM módosítja ez
  a job — csak a konfig-betöltés egységesítését)
- change_type: `fix`
- status_after_merge: `candidate`
- status indoklás: valós, futtatott smoke teszt bizonyítja, hogy 2+ komponens
  ugyanazt a DB-t látja közös env-fájllal

## Sources

- **KÖTELEZŐ elsődleges forrás:**
  - a worker loop (`session_store/worker_loop.py` vagy ekvivalens) jelenlegi
    config-betöltési kódja
  - `mcp-server/session_server.py` jelenlegi config-betöltési kódja
  - `cic-mcp-gateway/gateway_core/compile_context.py` jelenlegi
    `repo_root`/`python_executable` paraméterezése (354-359. sor körül) — ez
    a hívási út, amin keresztül a gateway eljut a session DB-hez

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. Pre-change leltár — grep + idézet

```
grep -rn "psycopg.connect\|os.environ\[.*DSN\|os.environ\[.*PG\|getenv" --include="*.py" session_store/ mcp-server/ | grep -v test_
```

Idézd a kimenetet — minden helyet, ahol JELENLEG a DB-konfiguráció betöltődik,
file:line hivatkozással. Ez a "mielőtt egységesítenénk, mit egységesítünk"
bizonyíték.

### 2. Közös env-fájl formátum

Definiálj egy env-fájl formátumot (pl. `.env`-stílusú, `KEY=value` soronként:
`SESSION_PG_DSN`, vagy host/port/dbname/user/password külön kulcsokkal —
indokold a választást). Adj hozzá egy `.env.example` template-et (commitolt),
és győződj meg róla, hogy a TÉNYLEGES env-fájl `.gitignore`-olt.

### 3. Loader egységesítés

Módosítsd a worker loopot ÉS a session MCP szervert, hogy ugyanazt a
loader-függvényt használják a config betöltésére. A gateway oldalán (a
`cic-mcp-gateway` klónban) igazítsd a hívási utat úgy, hogy ugyanazt az
env-fájlt töltse be, amikor a session-adapteren keresztül kapcsolódik.

### 4. Valós, multi-consumer smoke teszt

Indíts el LEGALÁBB 2 konzumert (pl. a worker loop egy egyszeri futása ÉS a
session MCP szerver egy lekérdezése) UGYANAZZAL az env-fájllal, és
bizonyítsd EGY EGYEDI MARKER SORRAL (amit egyik konzumer ír, a másik
olvas), hogy ugyanazt a DB-instance-t látják. Idézd a tényleges kimenetet.

## Nem cél

- a worker loop vagy az MCP szerver ÜZLETI LOGIKÁJÁNAK módosítása — csak a
  config-betöltés egységesítése
- a gateway query-API bővítése (`gateway-query-context-api-001`, KÜLÖN job)
- secrets/jelszavak commitolása — KIZÁRÓLAG `.env.example` template
  kerülhet git-be, a valódi env-fájl `.gitignore`-olt marad

## Required Output Files

- `output/session-runtime-env-unification.md`
- a közös config-loader modul
- `.env.example`
- a hozzá tartozó teszt-fájl (smoke teszt)

## Required Report Sections

```markdown
# session-runtime-env-unification-001 Output

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
`missing`, `rejected`, `unknown`. `proven` a "mindegyik konzumer ugyanazt a
DB-t látja" állításra KIZÁRÓLAG akkor használható, ha a TÉNYLEGES,
futtatott smoke teszt kimenete idézve van.

## Definition Of Done

- [ ] pre-change config-betöltési helyek grep-pel feltérképezve, file:line
      idézve
- [ ] közös env-fájl formátum + `.env.example` definiálva
- [ ] a valódi env-fájl `.gitignore`-olt (bizonyítva)
- [ ] worker loop ÉS session MCP szerver ugyanazt a loadert használja
- [ ] gateway session-adapter hívási útja igazítva, ugyanazt az env-fájlt
      tölti be
- [ ] valós, multi-consumer smoke teszt egyedi marker-sorral, TÉNYLEGES
      kimenettel
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a loader modul léte ≠ implemented — a futtatott smoke teszt kimenete
  bizonyít, a kód megírása nem
- "egységesítve" állítás valós, multi-consumer smoke teszt nélkül
- bármilyen secret/jelszó/DSN commitolása (kizárólag `.env.example`
  template-ben, placeholder értékekkel)
- a worker/MCP/gateway üzleti logikájának módosítása ürügyként a
  config-egységesítéshez

## Git instrukciók

Push a `feature/session-runtime-env-unification-001` branch-re a
`cic-mcp-session` ÉS a `cic-mcp-gateway` célrepóban is (mindkettő módosul).
A `cic-mcp-factory` saját klónjában NEM kell pusholni, elég a lokális
commit. Main-re az agent NEM pushol. **NE módosítsd a `meta.yaml` `status`
mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek/kód angolul.
