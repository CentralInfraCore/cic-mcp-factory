# Job: session-infra-pipeline-fix-001

## Kontextus

A `session-repo-baseline-audit-001` audit (`jobs/session-repo-baseline-audit-001/output/session-baseline-audit.md`)
három konkrét, tényleges futtatással bizonyított hibát talált a `cic-mcp-session` KB-pipeline-jában:

1. `requirements.txt` nem tartalmazza a `requirements.in`-ben listázott MCP/KB csomagokat
   (`mcp`, `markdown`, `pandas`, `beautifulsoup4`, `langdetect`, `sentence-transformers`,
   `faiss-cpu`, `rank-bm25`, `numpy`, `fastapi`, `uvicorn`) — friss `pip install -r
   requirements.txt` után `python make_source.py` azonnal `ModuleNotFoundError: No module
   named 'markdown'`-ral elszáll.
2. `make_source.py` üres `source/`-szal `ZeroDivisionError`-ral áll le a `build_bm25_index`
   függvényben (`avgdl = num_doc / self.corpus_size`, `corpus_size == 0`), NEM üres/graceful
   KB-t generál.
3. A `CLAUDE.md` "Kulcs parancsok" szekciója sosem dokumentálja a `make deps`
   (`infra.deps` → `docker compose run --rm setup`, ami a `./p_venv`-et létrehozza) lépést
   mint előfeltételt — emiatt bárki, aki a dokumentált sorrendet követi (`make mcp.config` →
   `make kb.build`), azonnal `make: ./p_venv/bin/python: No such file or directory` hibát kap.
   **Ez nem repo-bug, hanem dokumentációs hiány** — a `p_venv` szándékosan gitignored, minden
   klónban újra kell építeni, de ez a lépés nincs leírva.

Ez a job ezt a három hibát javítja, hogy a `make_source.py` → `kb_data/` → `mcp-server/server.py`
pipeline tényleg végigfuthasson a dokumentált belépési pontokon keresztül — mind valódi
tartalommal, mind (jövőbeli, fokozatos feltöltés közbeni) üres/kis `source/`-szal.

## Target

- target repo: `cic-mcp-session`
- target path: repo root (`requirements.in`/`requirements.txt`, `make_source.py`, `CLAUDE.md`,
  `tests/test_tools/test_make_source.py` vagy hasonló)
- change_type: `fix`
- status_after_merge: `experimental`
- status indoklás: ez infrastruktúra-javítás, nem session-specifikus capability — a repo
  utána is `experimental` marad, mert a SessionIngressEnvelope/Postgres réteg ettől
  függetlenül továbbra is `concept` státuszban van. A `status_after_merge` itt azt jelzi,
  hogy a KB-pipeline *futtatható* lesz, nem azt, hogy a session-rétegnek bármilyen
  candidate-szintű tartalma lenne.

## Sources

- `jobs/session-repo-baseline-audit-001/output/session-baseline-audit.md` — a teljes audit,
  benne a pontos hibák, fájl:sor hivatkozásokkal (Findings 3. és a CLAUDE.md "Kulcs parancsok"
  hiánya a Risks szekcióban)
- `.cic-context/factory-docs/acceptance-contract.md` — NORMATÍV, releváns részek lent beidézve
- a `cic-mcp-session` repo saját tartalma: `requirements.in`, `requirements.txt`,
  `make_source.py`, `mk/infra.mk`, `CLAUDE.md`, `tests/`

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát (a korábbi audit szerint a
   `cic-mcp-session`-re vonatkozó node-ok száma 0 volt — ha ez változott, jelezd)
2. Olvasd el a teljes `session-repo-baseline-audit-001` auditot a "Sources"-ban megadott
   path-on, MIELŐTT bármit módosítasz — ne fedezd fel újra ugyanazt, amit már bizonyítottak

## Feladat

### 1. `requirements.txt` regenerálása

Regeneráld a `requirements.txt`-t a `requirements.in`-ből (`pip-compile requirements.in`,
vagy ha a `pip-compile` nem elérhető a workspace-ben, manuálisan add hozzá a hiányzó
csomagokat verzióval és idézd, melyik forrásból vetted a verziószámot). Bizonyítsd grep-pel,
hogy mind a 11 audit által megnevezett csomag (`mcp`, `markdown`, `pandas`, `beautifulsoup4`,
`langdetect`, `sentence-transformers`, `faiss-cpu`, `rank-bm25`, `numpy`, `fastapi`, `uvicorn`)
benne van a regenerált fájlban.

### 2. `make_source.py` empty-source graceful handling

Javítsd a `build_bm25_index` (vagy ahol a `ZeroDivisionError` tényleg keletkezik — ellenőrizd
a pontos sort, az audit `make_source.py:307`-et említ, de a te futtatásod adja a végső
bizonyítékot) függvényt úgy, hogy `corpus_size == 0` esetén NE crash-eljen, hanem:
- írjon egy érthető log/warning üzenetet ("source/ is empty, generating empty KB" vagy hasonló)
- generáljon egy valid, üres (0 chunk/node/edge) KB artifact-szettet a `kb_data/`-ba
- exit code 0-val térjen vissza, NE stacktrace-szel

Írj hozzá legalább egy automatizált tesztet (`tests/test_tools/test_make_source.py` vagy új
fájl), amely üres `source/`-t szimulál és bizonyítja, hogy a hívás NEM dob kivételt.

### 3. `CLAUDE.md` "Kulcs parancsok" javítása

Vedd fel a `make deps` parancsot a "Kulcs parancsok" listába, ELSŐ lépésként, a `make
mcp.config` elé, egy mondatos magyarázattal (mit csinál: `./p_venv` létrehozása Docker-rel).

## Reachability / végigfuttatás ellenőrzés (kötelező a Definition of Done-hoz)

Az 1+2 pont javítása után **tényleg futtasd le** mindkét forgatókönyvet, és idézd a kimenetet:

```bash
# (a) friss venv, hiányzó deps szimulálva — a javított requirements.txt-vel sikeresnek kell lennie
# (b) üres source/ — a javított make_source.py-nak sikeresnek kell lennie (exit 0), NEM ZeroDivisionError-ral
```

Ezután futtasd:
```bash
grep -rn "build_bm25_index\|corpus_size" --include="*.py" . | grep -v "test_" | grep -v "/tests/"
```
és idézd a hívó fájl:sor-t (file:line formátumban) a `grep -rn` outputból, ami igazolja hogy
a javított függvény tényleg a `make_source.py` main folyamatának production hívási láncában
van, nem egy elszigetelt, sosem hívott helper.

Ha a fix után is van bármilyen maradék hibapont (pl. a `p_venv` Docker-függő `make deps` ebben
a workspace-ben nem futtatható, mert nincs Docker), ezt explicit írd le `partial`-ként a
claim-evidence táblában, NE állítsd `proven`-nek anélkül hogy tényleg futott.

## Nem cél

- a `project.yaml` `metadata.name: base` javítása (külön job:
  `session-project-metadata-cleanup-001`)
- a 18 failing pytest teszt teljes kivizsgálása/javítása a `tools/compiler.py`/`tools/infra.py`-ban
  (külön job, lásd fentebb)
- `tools/generate_gitmodules.py` / `knowledge.sources.yaml` hiányának megoldása
- SessionIngressEnvelope, Postgres schema, gateway integráció — ezek külön jobok

## Required Output Files

- `output/session-infra-pipeline-fix-report.md`

## Required Report Sections

A report MUST kövesse az `.cic-context/factory-docs/acceptance-contract.md`
"Universal Output Contract" szakaszát:

```markdown
# session-infra-pipeline-fix-001 Output

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

Elfogadott `Status` értékek: `proven`, `partial`, `scaffold`, `concept`, `missing`,
`rejected`, `unknown`.

## Definition Of Done

- [ ] `requirements.txt` tartalmazza mind a 11 audit által megnevezett csomagot (grep
      eredmény idézve)
- [ ] `make_source.py` üres `source/`-szal lefuttatva exit code 0-val tér vissza,
      NEM `ZeroDivisionError`-ral (tényleges futtatás kimenete idézve)
- [ ] legalább 1 új automatizált teszt az empty-source esetre, lefuttatva és zöld
      (pytest output idézve)
- [ ] `CLAUDE.md` "Kulcs parancsok" tartalmazza a `make deps` lépést, az első helyen
- [ ] claim-evidence tábla kitöltve, nem üres, minden `proven` állításhoz tényleges
      parancs-kimenet idézve

## Forbidden Shortcuts

- fájl létezése ≠ verified — a `requirements.txt` kézi szerkesztése nem bizonyíték,
  a tényleges `pip install` + `python make_source.py` exit code ≠ sikeres futás amíg nincs
  tényleges futtatás idézve
- `"graceful kezelés hozzáadva" != tesztelt` — kód-változás önmagában nem elég, automatizált
  teszttel kell bizonyítani az empty-source esetet
- `kód létezik != hívási láncban van` — `grep -rn` kötelező annak igazolására, hogy a
  javított kódrész tényleg a main végrehajtási útban van, nem egy nem hívott helper

## Git instrukciók

Push a `feature/session-infra-pipeline-fix-001` branch-re, a `cic-mcp-session` célrepóban
IS (mivel ott történik a tényleges kódváltozás) — külön a `cic-mcp-factory`-tól. Main-re
SEHOL nem pushol az agent.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/commit message-ek angolul.
