# Job: cic-mcp-knowledge-mcp-write-confinement-fix-001

## Kontextus

Egy külső biztonsági review (orchestrátor által függetlenül megerősítve, lásd
"Sources") feltárta, hogy a `mcp-server/server.py` — amely **byte-azonos**
(SHA256-egyezés ellenőrizve) `cic-mcp-session`/`cic-mcp-knowledge`/
`cic-mcp-shared`/`cic-mcp-gateway` mind a négy repójában, a `base-repo`
öröksége — két `@mcp.tool()`-jelölt függvénye (`update_companion()`,
`record_decision()`) egy MCP-klienstől kapott `file_path`/`companion_path`
paramétert ABSZOLÚT útvonalként közvetlenül elfogad, MINDEN
`SOURCE_DIR`-en-belüliség-ellenőrzés NÉLKÜL, majd `p.open("w")`-vel ÍR rá.

Ez egy path-traversal / write-confinement hiba: egy MCP-kliens (bármely
agent, amelynek ez a szerver be van kötve) `file_path="/tetszőleges/elérhető/
fájl.yaml"`-lel hívva felülírhat BÁRMILYEN, a futó processz által írható
fájlt a hoszton, NEM csak a `source/` könyvtáron belüli companion YAML-okat
— miközben a szerver dokumentációja és a `cic-mcp-*/CLAUDE.md` "MCP szerver
tool-ok" táblázata ezt egy ártalmatlan, KB-böngésző eszközként írja le.

**Ez a job EZT a hiányt zárja, EBBEN az egy repóban** — a másik 3 érintett
repóban (`cic-mcp-session`, `cic-mcp-shared`, `cic-mcp-gateway`) PÁRHUZAMOS,
KÜLÖN jobok futnak ugyanezzel a logikával (`cic-mcp-session-mcp-write-
confinement-fix-001` stb.) — ez a job NEM nyúl bele a másik 3 repóba.

A jobban EGY MÁSIK, KIS hatókörű drift-javítás is benne van: a
`project.yaml` `metadata.name: base` mező (mind a 4 repóban azonos,
sosem lett a saját repo-identitásra cserélve) — ez egy KÜLÖN, alacsony
kockázatú dokumentációs javítás, bundle-ölve ebbe a "fix" jobba, mert
ugyanaz a PR review-ja amúgy is érinti a repo metaadatait.

## Target

- target repo: `cic-mcp-knowledge`
- target path: `output/cic-mcp-knowledge-mcp-write-confinement-fix.md` +
  `mcp-server/server.py` módosítása + a hozzá tartozó teszt + `project.yaml`
  egy mezőjének javítása
- change_type: `fix`
- status_after_merge: `candidate`
- status indoklás: TÉNYLEGES, futtatható biztonsági javítás + valós teszt,
  amely bizonyítja MIND a path-traversal elutasítását, MIND a legitim
  companion-írás folytatódását (nincs regresszió)

## Sources

- **KÖTELEZŐ elsődleges forrás:**
  - `mcp-server/server.py` — `SOURCE_DIR` definíció (kb. 1167. sor),
    `update_companion()` (kb. 1486-1553. sor) és `record_decision()` (kb.
    1560-1636. sor) — MINDKETTŐ a sebezhető függvény, MINDKETTŐT javítani
    kell, AZONOS logikával
  - `project.yaml` — `metadata.name: base` (1-3. sor körül) — ez a mező
    SOSEM lett a repo saját nevére cserélve

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. A sebezhetőség megerősítése — grep + saját reprodukció

```
grep -rn "def update_companion\|def record_decision" --include="*.py" mcp-server/ | grep -v test_
```

Idézd a kimenetet. Írj egy ELŐZETES, SAJÁT reprodukciós tesztet (vagy
közvetlen Python-hívást), amely bizonyítja, hogy a JAVÍTÁS ELŐTTI kód
`update_companion(file_path="/tmp/<valami-a-source_dir-on-kívül>.yaml", ...)`
hívásra TÉNYLEGESEN ÍR egy SOURCE_DIR-en kívüli fájlba (vagy legalább
megkísérli — `p.open("w")`-ig eljut). Idézd a TÉNYLEGES kimenetet, ami
bizonyítja a hibát LÉTEZŐKÉNT, MIELŐTT javítanád.

### 2. Confinement-ellenőrzés implementáció

Adj hozzá egy ÚJ helper függvényt (pl. `_resolve_within_source_dir(file_path:
str) -> Path`), a `SOURCE_DIR` definíció közelében, amely:
- felépíti a path-ot UGYANÚGY, mint eddig (abszolút marad abszolút, relatív
  `SOURCE_DIR`-hez lesz illesztve)
- `.resolve()`-ja MINDKÉT oldalt (a kapott path-ot ÉS `SOURCE_DIR`-t)
- `Path.is_relative_to()`-val ELLENŐRZI, hogy a feloldott path TÉNYLEG
  `SOURCE_DIR`-en belül van-e
- HA NEM, dob egy explicit kivételt (pl. `ValueError`), amit a hívó oldal
  elkap és `{"success": False, "message": "path escapes SOURCE_DIR, refused"}`-
  ot ad vissza, ÍRÁS/OLVASÁS MEGKÍSÉRLÉSE NÉLKÜL

Vezesd be ezt MINDKÉT helyre (`update_companion()` ÉS `record_decision()`),
a path-felépítés UTÁN, de a `p.open()` ELŐTT. NE módosíts más függvényt (pl.
`claim_task`/`complete_task`/`fail_task` `_find_promptmaps()`-alapú scope-ja
MÁR biztonságos, nem vesz át kliens-megadott abszolút path-ot — ezt erősítsd
meg grep-pel, NE nyúlj hozzá).

### 3. Valós, futtatott bizonyíték — MINDKÉT eset

Írj egy tesztet (a meglévő `tests/test_tools/test_mcp_server.py` mintáját
követve, `import server as mcp_server` az `mcp-server/` `sys.path`-re
illesztve), amely bizonyítja:
1. `update_companion(file_path="<SOURCE_DIR-en kívüli abszolút path>", ...)`
   → `{"success": False, ...}`, ÉS a célfájl TÉNYLEG NEM jött létre/módosult
2. `update_companion(file_path="<egy LEGITIM, SOURCE_DIR-en BELÜLI companion
   YAML>", ...)` → TOVÁBBRA IS sikeresen frissít (NINCS regresszió a
   legitim use case-en)
3. MINDKÉT eset megismételve `record_decision()`-re is

Idézd a TÉNYLEGES pytest kimenetet.

### 4. `project.yaml` javítás

Cseréld ki `metadata.name: base`-t a repo TÉNYLEGES nevére (`cic-mcp-knowledge`). NE módosíts más mezőt (`description`/`tags`/`version`/`license`/
`owner`/`validatedBy` MARADJON érintetlen — ez egy KÜLÖN, szélesebb döntés,
NEM ennek a jobnak a hatóköre).

## Nem cél

- `claim_task`/`complete_task`/`fail_task` módosítása (MÁR biztonságos,
  csak megerősítendő grep-pel)
- a `project.yaml` `description`/`tags`/`version`/`license`/`owner` mezőinek
  módosítása (KIZÁRÓLAG `metadata.name`)
- a másik 3 repó (`cic-mcp-session`/`cic-mcp-shared`/`cic-mcp-gateway`)
  javítása (KÜLÖN, párhuzamos jobok)
- a generikus KB-szerver (`mcp-server/server.py`) egyéb funkcióinak
  (search/focus_pack/stb.) módosítása
- **a `README.md`/`CLAUDE.md` "base-repo" szövegének átírása** — a
  `cic-mcp-knowledge` repo, a másik 3 (`session`/`shared`/`gateway`)
  repótól ELTÉRŐEN, MÉG SOHA nem ment át egy specializációs/bootstrap jobon
  (`jobs/index.yaml`-ben NINCS egyetlen "knowledge"-et tartalmazó `id:` sem
  — ezt grep-pel erősítsd meg). A README "base-repo" szövege ezért JELENLEG
  TÉNYLEGESEN IGAZ állítás (nincs specializált tartalom, amit leírhatna),
  NEM csak elavult dokumentáció — ezt NE írd át egy fabrikált specializációs
  narratívára. Javasolj a "Next Jobs"-ban egy KÜLÖN, dedikált
  `knowledge-repo-baseline-or-bootstrap-001`-szerű jobot (a `session-repo-
  baseline-or-bootstrap-001`/`gateway-repo-baseline-or-bootstrap-001` mintájára),
  ami ezt a hiányt a megfelelő szinten zárná.

## Required Output Files

- `output/cic-mcp-knowledge-mcp-write-confinement-fix.md`
- a módosított `mcp-server/server.py`
- a hozzá tartozó teszt-fájl
- a módosított `project.yaml`

## Required Report Sections

```markdown
# cic-mcp-knowledge-mcp-write-confinement-fix-001 Output

## Scope
## Inputs Read
## Vulnerability Reproduction (Before Fix)
## Confinement Check Implementation
## Real Test Proof — Rejection AND No-Regression
## project.yaml Fix
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

Elfogadott `Status` értékek: `proven`, `partial`, `missing`, `rejected`,
`unknown`. `proven` egy "a path-traversal elutasítva, a legitim eset
működik" állításra KIZÁRÓLAG akkor használható, ha a TÉNYLEGES, futtatott
teszt kimenete MINDKÉT esetre idézve van — a kód megírása nem bizonyítja,
hogy helyesen fut.

## Definition Of Done

- [ ] a sebezhetőség REPRODUKÁLVA a javítás ELŐTT, TÉNYLEGES kimenettel
- [ ] `_resolve_within_source_dir()` (vagy ekvivalens) implementálva,
      file:line hivatkozással
- [ ] MINDKÉT érintett függvény (`update_companion`, `record_decision`)
      javítva
- [ ] valós teszt: path-traversal ELUTASÍTVA ÉS legitim eset TOVÁBBRA IS
      működik, MINDKÉT függvényre, a TÉNYLEGES pytest kimenettel
- [ ] `claim_task`/`complete_task`/`fail_task` biztonsága megerősítve
      grep-pel (NEM módosítva)
- [ ] `project.yaml` `metadata.name` javítva, más mező érintetlen
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a path-ellenőrzés `str`-alapú prefix-összehasonlítással (pl.
  `str(p).startswith(str(SOURCE_DIR))`) — ez megkerülhető symlink-kel vagy
  `..`-szegmenssel; KIZÁRÓLAG `Path.resolve()` + `Path.is_relative_to()`
  fogadható el
- csak EGY a két érintett függvény (`update_companion` VAGY
  `record_decision`) javítása — MINDKETTŐ kötelező
- csak a rejection vagy csak a no-regression eset tesztelése — MINDKETTŐ
  kötelező, mindkét függvényre
- a fájl/kód léte ≠ implemented (ez egyetlen soron) — a futtatott teszt
  kimenete bizonyít, a kód megírása nem

## Git instrukciók

Push a `feature/cic-mcp-knowledge-mcp-write-confinement-fix-001` branch-re,
KIZÁRÓLAG a `cic-mcp-knowledge` célrepóban (a `cic-mcp-factory` saját
klónjában NEM kell pusholni, elég a lokális commit). Main-re az agent NEM
pushol. **NE módosítsd a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek/kód angolul.
