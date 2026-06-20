# Job: session-repo-baseline-audit-001

## Kontextus

A `cic-mcp-session` repo 2026-06-20-án lett bootstrapelve a `base-repo` `mcp/main`
specializációs branch-éből (FastMCP-szerver scaffold, `make_source.py` KB-generátor,
`p_venv`, Vault signing tooling). A README.md/CLAUDE.md és a `docs/{hu,en}/architecture.{md,yaml}`
már komponens-specifikusra van írva (session réteg: Igen/Nem határok, trust modell,
tervezett Postgres-first adatfolyam) — de ez eddig csak a mi (orchestrátor) állítása, nincs
agent által végzett, repo-szintű audit-bizonyíték arról, hogy a scaffold tényleg azt
tartalmazza, amit a docs mond, és hogy semmi nincs benne implementálva a session-specifikus
rétegből.

Ez a job ezt az audit-hiányt oldja meg: tényekkel (file/path, git history, futtatható
parancsok) ellenőrzi, mi van valójában a repóban, és minden elemet
implemented/scaffold/concept/missing státuszba sorol.

## Target

- target repo: `cic-mcp-session`
- target path: repo root
- change_type: `enhancement`
- status_after_merge: `experimental`
- status indoklás: az audit önmagában nem termel kódot vagy contractot a target repóban —
  a `status_after_merge: experimental` ennek az auditnak a *eredményeként javasolt következő
  capability-jobokra* vonatkozik, nem ennek a jobnak a saját artifactjára (ami egy report,
  nem capability-implementáció).

## Sources

- `.cic-context/factory-docs/architecture.md` — `cic-mcp-session` szekció (komponens-térkép, Igen/Nem határok)
- `.cic-context/factory-docs/execution-phases.md` — Phase 1A
- `.cic-context/factory-docs/acceptance-contract.md` — NORMATÍV, releváns részek lent beidézve
- `.cic-context/corpus/normalized/thead-review-2026-06-20.yaml`
- a `cic-mcp-session` repo saját tartalma (README.md, CLAUDE.md, docs/, Makefile, mk/infra.mk,
  tools/, mcp-server/, source/, kb_data/, sqlite_data/, project.yaml)
- **Kalibrációs referencia (csak olvasásra, NE módosítsd):**
  `/home/sinkog/sync/git.partners/CentralInfraCore/MCPs/private` — ez a `cic-mcp-private`
  repo ugyanabból a `base-repo` `mcp/main` scaffold-ból indult, de nála a `source/` valódi
  git submodule-okkal feltöltve (`CentralInfraCore/`, `OpenIntentSign/`), `sqlite_data/knowledge_base.sqlite`
  épített (~14 MB), és valódi feature-commitok vannak rajta (pl. `feat: content-addressed
  chunk deduplication`, `feat: Go meta YAML KB integration`). Ezt használd kontraszt-
  referenciaként: ami `cic-mcp-private`-ben implementált, ugyanaz a mechanizmus
  `cic-mcp-session`-ben jelenleg `scaffold` (üres `source/`, nincs `sqlite_data/*.sqlite`)
  — ez konkrét, idézhető bizonyítékot ad az "implemented infrastruktúra, de session-specifikus
  tartalom nélkül" állításhoz, nem csak feltételezést.

## Boot sequence (kötelező, mielőtt szakmai állítást teszel)

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. `search_nodes` a `cic-mcp-session`, `trust-domain`, `session-scope` fogalmakra — van-e
   már node ezekről, ha van, milyen státuszban
3. Ezután nézd át a `cic-mcp-session` repo tényleges tartalmát (klónozva lesz, lásd
   "Munkakörnyezet" a futtatáskor) — README.md, CLAUDE.md, docs/, Makefile, source/, kb_data/

**Ne előre tervezd meg a választ.** Azt kell feltárnod, mi van *valójában* a repóban — a
docs/CLAUDE.md amit korábban írtunk lehet, hogy túlígér valamit (pl. azt állítja egy
funkcióról hogy "tervezett", miközben a kód már részben létezik, vagy fordítva).

## Feladat

Auditáld a `cic-mcp-session` repo jelenlegi állapotát. Minden jelentősebb elemet
(MCP szerver, KB-generátor pipeline, Makefile parancsok, docs, Vault signing tooling,
session-specifikus tartalom) sorolj `implemented` / `scaffold` / `concept` / `missing`
státuszba, file/path bizonyítékkal.

Különösen vizsgáld meg:
- a `make_source.py` → `kb_data/` → `mcp-server/server.py` pipeline tényleg futtatható-e
  jelen állapotban (üres `source/`-szal mit csinál — hibára fut, vagy üres KB-t generál?)
- van-e bármilyen session-specifikus tartalom (SessionIngressEnvelope schema, Postgres
  migráció, trust mezők) — a várt válasz: **nincs**, de ezt bizonyítsd, ne csak állítsd
- a `docs/{hu,en}/architecture.{md,yaml}` és a `CLAUDE.md` állításai ("Jelenlegi állapot"
  szekciók) megfelelnek-e a tényleges repo-tartalomnak
- vesd össze a `cic-mcp-private` kalibrációs referenciával (lásd Sources): mit jelent
  ugyanezen a scaffold-on, hogy egy komponens `implemented` (`source/` feltöltve,
  `sqlite_data/*.sqlite` épített, feature-commitok) — ehhez képest pontosan mi hiányzik a
  `cic-mcp-session`-ből. Idézd a konkrét fájl/parancs különbséget, ne csak állítsd.

### Reachability ellenőrzés (kötelező minden `implemented`/`scaffold` állításhoz)

Egy Python szimbólum/fájl létezése a repóban NEM elég `implemented` státuszhoz — azt is
bizonyítsd, hogy production kódból tényleg hívódik:

```bash
grep -rn "<FuncOrClassName>" --include="*.py" . | grep -v "test_" | grep -v "/tests/"
```

Ha a `grep -rn` eredmény csak teszt-fájlokban vagy a definíció helyén talál hivatkozást
(nincs production call site), a státusz **NEM** `implemented` — legfeljebb `scaffold`.
Minden `implemented` állításhoz idézd a production hívó fájl:sor-t a `grep -rn` outputból
(file:line formátumban). Ha nincs ilyen hívó (pl. `mcp-server/server.py` sosem indul el
semmilyen Makefile target által, vagy a `make_source.py` sosem fut le sikeresen üres
`source/`-szal), ezt explicit írd le `scaffold`-ként, nem `implemented`-ként.

## Nem cél

- session-specifikus architektúra teljes megvalósítása
- Postgres schema implementálása
- gateway integráció
- SessionIngressEnvelope contract megírása (ez egy külön, soron következő job:
  `session-ingress-envelope-contract-001`)

## Required Output Files

- `output/session-baseline-audit.md`

## Required Report Sections

A report MUST kövesse az `.cic-context/factory-docs/acceptance-contract.md`
"Universal Output Contract" szakaszát:

```markdown
# session-repo-baseline-audit-001 Output

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

Elfogadott `Status` értékek a Claim-Evidence Matrix-ban: `proven`, `partial`, `scaffold`,
`concept`, `missing`, `rejected`, `unknown`.

## Definition Of Done

- [ ] minden nagyobb repo elem státusza: implemented/scaffold/concept/missing
- [ ] minden `implemented` állítás mellett reachability vagy runtime evidence (pl. tényleg
      lefuttatva a `make kb.build`/`make mcp.run` parancs, és az eredmény idézve)
- [ ] legalább 3 következő factory-job javaslat (pl. `session-ingress-envelope-contract-001`,
      `session-postgres-storage-design-001` ezek közül lehetnek, de indokold miért pont ezek
      a következők)
- [ ] NO-GO lista azokról, amikre még nem szabad építeni
- [ ] claim-evidence tábla kitöltve, nem üres
- [ ] explicit ellenőrzött: a `docs/`/`CLAUDE.md` korábbi állításai és a tényleges
      repo-állapot egyezik-e (ha eltérés van, jelöld)

## Forbidden Shortcuts

- `file existence != implemented` — egy fájl létezése a repóban nem jelenti hogy az a
  funkció implementált
- `README claim != runtime capability` — a README/CLAUDE.md korábbi állítása nem bizonyíték,
  a tényleges futtatás/kód az

## Git instrukciók

Push csak a `feature/session-repo-baseline-audit-001` branch-re. Main-re NEM.

## Nyelvi szabály

A report magyarul készüljön (dokumentáció), a esetleges kódrészletek/parancsok angolul
maradnak, ahogy a repo konvenciója is mondja.
