# Job: session-mcp-config-wiring-001

## Kontextus

A `session-mcp-tools-001` és `session-mcp-tools-remaining-001` job létrehozta a
`mcp-server/session_server.py` MCP szervert, mind a 7 `session_api.*` tool-lal —
kétszintű reachability-bizonyítással (direkt Python-hívás + in-process
`mcp.list_tools()`/`mcp.call_tool()` dispatch). Mindkét riport EXPLICIT kimondta:
"nincs `.mcp.json.tpl`-be kötve" — ez a job ZÁRJA EZT a hiányt, a LOKÁLIS FEJLESZTŐI
indítási receptet adva hozzá (nem éles deployment-et).

**Fontos elhatárolás**: ez a job NEM regisztrálja és NEM indítja el az új szervert
SEMMILYEN éles orchestrátor/Claude Code session-ben — kizárólag azt bizonyítja, hogy a
`.mcp.json.tpl` + `Makefile` recept FUTHATÓ és MŰKÖDIK, ha valaki (ember) ezt
manuálisan aktiválja a saját lokális session-jében. Ez egy KÜLÖN, jövőbeli, emberi
döntés, NEM ennek a jobnak a feladata.

## Target

- target repo: `cic-mcp-session`
- target path: `.mcp.json.tpl` (bővítés), `mk/infra.mk` + `Makefile` (új target)
- change_type: `enhancement`
- status_after_merge: `experimental`
- status indoklás: a recept futtatva és bizonyítva, de SEMMILYEN éles session nincs
  rámutatva — `candidate`-hez egy tényleges, hosszabb-életű lokális/dev használat
  kellene

## Sources

- `${WORKDIR}/.cic-context/factory-docs/job-slices.yaml` —
  `session-mcp-config-wiring-001` bejegyzés — NORMATÍV
- **KÖTELEZŐ elsődleges forrás (mind már a `cic-mcp-session` `main`-en van):**
  - `cic-mcp-session/.mcp.json.tpl` — a MEGLÉVŐ, TELJES tartalma:
    ```json
    {
      "mcpServers": {
        "cic-graph": {
          "command": "{{REPO_ROOT}}/p_venv/bin/python",
          "args": ["{{REPO_ROOT}}/mcp-server/server.py"],
          "env": {"KB_DATA_DIR": "{{REPO_ROOT}}/kb_data/pkl"}
        }
      }
    }
    ```
    EZT a `cic-graph` bejegyzést NE módosítsd — csak EGY ÚJ `cic-session` bejegyzést
    adj hozzá MELLÉ, ugyanazt a `{{REPO_ROOT}}` placeholder-konvenciót követve.
  - `cic-mcp-session/mk/infra.mk` — `infra.mcp.config` (sed-alapú `{{REPO_ROOT}}`
    helyettesítés), `infra.mcp.run` (a MINTA, amit `infra.mcp.run.session`-nek
    KÖVETNI kell, csak `session_server.py`-ra mutatva)
  - `cic-mcp-session/Makefile` — a `.PHONY` lista és a `mcp.run: infra.mcp.run`
    alias-minta — vedd fel ide is az új target alias-t
  - `cic-mcp-session/mcp-server/session_server.py` — `main()` (jelenleg
    paraméter nélküli `mcp.run()` — ez stdio módot futtat, EZ a mód kell ehhez a
    jobhoz, NEM SSE)
  - `cic-mcp-session/session_store/envelope_writer.py` —
    `SessionStoreConfig.from_env()` — a fallback-lánc (env var → `PG*` env var →
    `localhost`/`postgres` default), amire a "nincs env-blokk a tpl-ben" döntés épül

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti KÖTELEZŐ forrásokat, MIELŐTT bármilyen kódot írnál

## Feladat

### 1. ÚJ `.mcp.json.tpl` bejegyzés — KRITIKUS BIZTONSÁGI MEGSZORÍTÁS

Adj hozzá egy `cic-session` bejegyzést a MEGLÉVŐ `cic-graph` MELLÉ:
```json
"cic-session": {
  "command": "{{REPO_ROOT}}/p_venv/bin/python",
  "args": ["{{REPO_ROOT}}/mcp-server/session_server.py"]
}
```

**KÖTELEZŐ, NEM ALKU KÉPES SZABÁLY**: ez a bejegyzés NEM tartalmazhat `env` blokkot
`SESSION_STORE_PG_PASSWORD`-dal vagy BÁRMILYEN secret-tel — a `.mcp.json.tpl` egy
GIT-TRACKELT fájl. Ha a kapcsolati paramétereket dokumentálni akarod, tedd a
riportba SZÖVEGESEN ("a `cic-session` indításához a hívó shell-ben be kell állítani:
`SESSION_STORE_PG_HOST`, `SESSION_STORE_PG_PORT`, `SESSION_STORE_PG_DB`,
`SESSION_STORE_PG_USER`, `SESSION_STORE_PG_PASSWORD`"), NE a fájlba. Ha ezt a
szabályt megsérted, a job NO-GO, FÜGGETLENÜL minden más bizonyítéktól.

### 2. ÚJ Makefile target

Adj hozzá `mk/infra.mk`-hoz egy `infra.mcp.run.session` target-et, PONTOSAN az
`infra.mcp.run` mintáját követve (csak `session_server.py`-ra mutatva), és a
`Makefile`-hoz egy `mcp.run.session: infra.mcp.run.session` alias sort + `.PHONY`
bejegyzést, a meglévő `mcp.run`/`mcp.run.sse` minta mellé.

### 3. Tényleges `make mcp.config` futtatás

Futtasd le `make mcp.config`-ot, és idézd a kirenderelt `.mcp.json` TELJES tartalmát —
bizonyítva, hogy MINDKÉT bejegyzés (cic-graph + cic-session) helyesen szerepel, a
`{{REPO_ROOT}}` helyesen helyettesítve.

### 4. TÉNYLEGES subprocess + stdio MCP handshake bizonyítás

Ez a job ÚJ bizonyítási szintet igényel a korábbi jobokhoz képest: NEM elég az
in-process Python hívás (`mcp.list_tools()` direktben) — itt azt kell bizonyítani,
hogy a KIRENDERELT `.mcp.json` `command`+`args` párosával ELINDÍTOTT ÖNÁLLÓ
subprocess valódi stdio MCP handshake-en keresztül válaszol. Használj egy MCP
kliens-könyvtárat (a `mcp` Python package már a `requirements.txt`-ben van — nézd meg
a `mcp.client.stdio`/`mcp.client.session` modulokat), indítsd el a session szervert
PONTOSAN a `.mcp.json` `command`/`args` értékeivel (valódi env várakkal a teszt
processz environment-jében, NEM a tpl-ben), és hívj meg legalább egy `list_tools()`
hívást a stdio transport-on át. Idézd a tényleges kimenetet.

### 5. Regresszió-ellenőrzés

Futtasd le a TELJES meglévő `tests/test_session_store/` suite-ot, bizonyítva hogy
semmi nem regresszált.

### 6. Explicit elhatárolás a riportban

A riportban EXPLICIT mondd ki: ez a job NEM regisztrálta/indította el az új szervert
semmilyen éles orchestrátor/Claude Code session-ben — ez a `.mcp.json.tpl` + Makefile
recept BIZONYÍTOTTAN FUTHATÓ, de az aktiválás külön, jövőbeli, emberi döntés.

### 7. Reachability ellenőrzés (kötelező)

```bash
grep -rn "infra.mcp.run.session\|cic-session" --include="Makefile" --include="*.mk" --include="*.tpl" .
```

`file:line` hivatkozással minden találatra. Dokumentáld explicit: a recept LÉTEZÉSE
és FUTÁSA (subprocess-szinten bizonyítva) KÉT KÜLÖNÁLLÓ állítás a "VALAKI TÉNYLEG
EZT HASZNÁLJA egy éles Claude Code session-ben" állítástól — az utóbbi `missing`.

## Nem cél

- a `cic-graph` bejegyzés vagy `mcp-server/server.py` módosítása
- a `search_session_context*`/`get_session_*` tool-ok módosítása
- SESSION_STORE_PG_PASSWORD vagy bármilyen secret a `.mcp.json.tpl`-be írása — TILOS
- bármilyen éles orchestrátor/Claude Code session `.mcp.json`-jának módosítása vagy a
  szerver ottani regisztrálása
- SSE-mód támogatás a session szerverhez (csak stdio, mint a `cic-graph`
  alapesetben)

## Required Output Files

- `output/session-mcp-config-wiring-report.md`

## Required Report Sections

```markdown
# session-mcp-config-wiring-001 Output

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
`proven` KIZÁRÓLAG akkor használható, ha a tényleges `make mcp.config` kimenet ÉS a
tényleges subprocess+stdio handshake kimenet idézve van. A `.mcp.json.tpl`-ben lévő
bejegyzés léte ≠ működik — csak a tényleges subprocess-indítás és stdio-válasz
bizonyít.

## Definition Of Done

- [ ] `.mcp.json.tpl`-ben ÚJ `cic-session` bejegyzés, a `cic-graph` ÉRINTETLEN
- [ ] NINCS secret/jelszó a `.mcp.json.tpl`-ben (kötelező, nem alku képes)
- [ ] `infra.mcp.run.session` target létrejött `mk/infra.mk`-ban, `infra.mcp.run`
      mintáját követve, fájl:sor hivatkozással
- [ ] `Makefile`-ban `mcp.run.session` alias + `.PHONY` bejegyzés
- [ ] `make mcp.config` tényleges kimenete idézve, mindkét bejegyzés látható a
      kirenderelt `.mcp.json`-ban
- [ ] TÉNYLEGES subprocess + stdio MCP handshake bizonyítva (NEM csak in-process
      Python hívás), kimenet idézve
- [ ] teljes meglévő teszt-suite lefuttatva, regresszió-mentesség bizonyítva
- [ ] explicit "nincs éles session-be regisztrálva" kijelentés a riportban
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- secret/jelszó beírása a `.mcp.json.tpl`-be — TILOS, automatikus NO-GO
- csak in-process Python hívást bizonyítani ("`mcp.list_tools()` direktben") és azt
  állítani, hogy "a launch-recept működik" — a TÉNYLEGES subprocess+stdio handshake
  bizonyítása kötelező
- azt állítani, hogy ez bárhol éles orchestrátor/Claude Code session-be regisztrálva
  van, amikor nincs
- a `cic-graph` bejegyzés vagy `mcp-server/server.py` módosítása

## Git instrukciók

Push a `feature/session-mcp-config-wiring-001` branch-re, KIZÁRÓLAG a
`cic-mcp-session` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni,
elég a lokális commit). Main-re az agent NEM pushol. A teszteléshez használt Docker
konténert ÉS bármilyen elindított subprocess-t a munka végén állítsd le. **NE
módosítsd a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/teszt-nevek angolul.
