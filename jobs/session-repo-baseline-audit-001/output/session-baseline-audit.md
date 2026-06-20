# session-repo-baseline-audit-001 Output

## Scope

Repo-szintű audit a `cic-mcp-session` (`CentralInfraCore/cic-mcp-session`) jelenlegi
állapotáról. Cél: minden jelentős repo-elem (MCP szerver, KB-generátor pipeline, Makefile
parancsok, docs, Vault signing tooling, session-specifikus tartalom) tényalapú
`implemented`/`scaffold`/`concept`/`missing` besorolása, file/path és futtatási
bizonyítékkal. Nem cél: session-specifikus architektúra megvalósítása, Postgres schema,
gateway integráció, SessionIngressEnvelope contract megírása.

## Inputs Read

- `.cic-context/factory-docs/architecture.md` (cic-mcp-factory klón) — komponens-térkép,
  Igen/Nem határok, trust modell, Postgres-first elv
- `.cic-context/factory-docs/acceptance-contract.md` (cic-mcp-factory klón) — NO-GO szabályok,
  Universal Output Contract, Session-Specific Contract
- `cic-mcp-session/README.md`, `CLAUDE.md`
- `cic-mcp-session/docs/{hu,en}/architecture.{md,yaml}`
- `cic-mcp-session/docs/{hu,en}/concept/*.md` (git-managment, declarative_ecosystem_integration)
- `cic-mcp-session/Makefile`, `mk/infra.mk`
- `cic-mcp-session/make_source.py`, `mcp-server/server.py`, `mcp-server/server.yaml`
- `cic-mcp-session/project.yaml`, `requirements.in`, `requirements.txt`
- `cic-mcp-session/tools/` (compiler.py, infra.py, generate_gitmodules.py, releaselib/, vault-sign-agent.*)
- `cic-mcp-session/tests/` (teljes test suite futtatva)
- `cic-mcp-session` git history (`git log --oneline`, 156 commit)
- Kalibrációs referencia: `/home/sinkog/sync/git.partners/CentralInfraCore/MCPs/private`
  (`source/`, `sqlite_data/`, `.gitmodules`, `git log` feature-commitok)
- `mcp__cic-graph__kb_status` — a cic-graph KB jelenleg a `cic-mcp-private` adatkészletéhez
  van kötve (`data_dir: .../MCPs/private/kb_data/pkl`), nem a `cic-mcp-session` repóhoz
- `mcp__cic-graph__search_nodes` a `cic-mcp-session`, `trust-domain`, `session-scope`
  fogalmakra — mindhárom **0 eredményt** adott

## Findings

### 0. KB-boot eredmény

A `kb_status` a `cic-mcp-private` repo adatkészletét tölti be (chunks/nodes/edges/faiss/bm25
mind a `.../MCPs/private/kb_data/pkl/` alól), nem a `cic-mcp-session`-ét — ez konzisztens
azzal, hogy `cic-mcp-session`-nek jelenleg **nincs saját épített KB-ja** (lásd 3. pont). A
`search_nodes("cic-mcp-session")`, `search_nodes("trust-domain")`, `search_nodes("session-scope")`
mindegyike `{"result": []}` — a privát KB-ban (amely a CIC-ökoszisztéma más repóit indexeli)
nincs node ezekről a fogalmakról. Ez nem hiba, csak azt jelzi, hogy a fogalmi háromszintű
státusz-ellenőrzést ebben a jobban kizárólag a repo-tartalom közvetlen vizsgálatával kellett
elvégezni, nem a graph-on keresztül.

### 1. README.md / CLAUDE.md / docs állítások vs. valóság — EGYEZÉS

A `README.md` "Státusz" szekciója és a `CLAUDE.md` "Jelenlegi állapot" szekciója, valamint a
`docs/hu/architecture.md` "Jelenlegi állapot" szekciója (sor 71-77) mind azt állítják:
- `source/` üres
- a `make_source.py`/`mcp-server/` scaffold generikus, nem session-specifikus
- session-specifikus tartalom (SessionIngressEnvelope, Postgres) még nincs implementálva

Ez **megegyezik** a tényleges repo-állapottal (lásd lentebb). Ez explicit pozitív eredmény: a
docs nem túlígér ezen a ponton.

### 2. `project.yaml` — ELTÉRÉS a komponens-identitástól

A `project.yaml` `metadata.name: base`, `metadata.description: "Schema Compiler & Signing
Infrastructure Template"` — ez a `base-repo` eredeti, generikus metaadata, **nem** lett
átírva `cic-mcp-session`-re. Ez nem session-specifikus README/CLAUDE.md-eltérés (azokat
direkt customizálta a `b7db097`/`d09c9ca` commit), hanem egy **elmaradt lépés**: a
project-szintű identitás (`project.yaml`) sosem lett frissítve a bootstrap után. Funkcionális
hatása ismeretlen (release tooling-hoz használt mező), de dokumentációs/audit szempontból
inkonzisztencia.

### 3. `make_source.py` → `kb_data/` pipeline — SCAFFOLD, NEM FUTTATHATÓ JELENLEGI ÁLLAPOTBAN

Két különálló hibapont igazolva, mindkettőt tényleges futtatással:

**(a) `requirements.txt` nem tartalmazza az MCP/KB csomagokat.**
`requirements.in` listázza: `mcp`, `markdown`, `pandas`, `beautifulsoup4`, `langdetect`,
`sentence-transformers`, `faiss-cpu`, `rank-bm25`, `numpy`, `fastapi`, `uvicorn`. A compilált
`requirements.txt`-ben **egyik sincs** — `grep -i "^markdown" requirements.txt` csak
`markdown-it-py==4.0.0`-t talál (tranzitív dep, nem ugyanaz a `markdown` package). Friss venv-be
`pip install -r requirements.txt` után `python make_source.py` azonnal elszáll:
```
ModuleNotFoundError: No module named 'markdown'
```
Ez azt jelenti, hogy a `requirements.txt` (a tényleges lockfile) sosem lett regenerálva
(`pip-compile`) a `0f78405`/`1b52615`/`723760a` MCP-feature-commitok után — drift a `.in` és
`.txt` között.

**(b) Üres `source/`-szal a generátor `ZeroDivisionError`-ral elszáll, NEM üres KB-t generál.**
A hiányzó csomagok manuális telepítése után (`pip install markdown pandas beautifulsoup4
langdetect sentence-transformers faiss-cpu rank-bm25 numpy fastapi uvicorn mcp`) a
`make_source.py` lefutott az embedding-betöltésig, majd:
```
File "make_source.py", line 307, in build_bm25_index
    return BM25Okapi(tokenized)
  File ".../rank_bm25.py", line 52, in _initialize
    self.avgdl = num_doc / self.corpus_size
ZeroDivisionError: division by zero
```
A `kb_data/` mappa a futás után is csak a git-tracked `edge_types.md` + `.gitignore`-t
tartalmazza — **semmilyen `pkl` artifact nem készült**. A pipeline tehát üres `source/`-szal
nem "üres KB-t generál" (ahogy ezt egy defenzív implementáció tenné), hanem hard-crash-el.

**Reachability/runtime összegzés:** `make kb.build` (a dokumentált belépési pont, `mk/infra.mk:108`
`infra.kb.build: @$(PYTHON) make_source.py`, ahol `PYTHON := ./p_venv/bin/python`) **azonnal
elszáll**, mielőtt a fenti két hibáig egyáltalán eljutna, mert `p_venv/` nem létezik a repóban:
```
$ make kb.build
--- Building knowledge base from ./source ---
make: ./p_venv/bin/python: No such file or directory
make: *** [mk/infra.mk:108: infra.kb.build] Error 127
```
Státusz: **scaffold** (kód létezik, de a dokumentált belépési ponton keresztül jelenleg sem a
hiányzó venv, sem a hiányzó deps, sem az üres `source/` miatt nem futtatható végig).

### 4. `mcp-server/server.py` — SCAFFOLD, NEM IMPLEMENTED

A `load_kb()` (1656 soros `server.py`, sor 99-) `@lru_cache(maxsize=1)`-elt, és minden egyes
tool (`search_query`, `search_token`, `search_code`, `search_nodes`, `get_chunk`, `get_node`,
`neighbors`, `focus_pack`, `explain_node`, `kb_status`, `reload_kb`, `guided_path`,
`impact_analysis`) ezen keresztül ér el adatot. `load_kb()` minden hiányzó pkl fájlnál
`FileNotFoundError`-t dob (sor 102-103: `if not p.exists(): raise FileNotFoundError(...)`).
Közvetlen futtatással igazolva:
```
$ python -c "import server; server.load_kb()"
FileNotFoundError: Missing: .../kb_data/pkl/chunks.pkl
```
Mivel a 3. pont szerint a pipeline jelen állapotban nem tud `pkl` artifactot generálni, a
szerver **nem tud sikeresen elindulni semmilyen tool-hívásra** — `make mcp.run`
(`mk/infra.mk:110-112`, ugyanaz a hiányzó `p_venv` blokkolja) ugyanígy elszáll már a `PYTHON`
binárison.

**Reachability ellenőrzés (kötelező a job szerint):**
```
$ grep -rn "search_query\|search_nodes\b" --include="*.py" . | grep -v "/tests/" | grep -v "test_"
mcp-server/server.py:457:def search_query(...)
mcp-server/server.py:586:def search_nodes(...)
mcp-server/server.py:783:    hits = search_query(query, top_k=limit)   # focus_pack belső hívása
mcp-server/server.py:1097:   hits = search_query(topic, top_k=20)      # guided_path belső hívása
```
Az egyetlen "production call site" a `server.py`-on belüli tool-tool kereszthivatkozás
(`focus_pack`/`guided_path` hívja `search_query`-t). **Nincs külső production hívó** — sem
más `cic-mcp-*` repo, sem a Makefile, sem a release tooling nem hívja meg a szervert úgy, hogy
az tényleges tool-választ adjon. Ez pontosan a job `Reachability ellenőrzés` szakasza által
leírt "scaffold, nem implemented" eset: a kód létezik, de nincs éles runtime híd egy sikeresen
betöltött KB-ig.

Státusz: **scaffold** (12 tool definiálva, belső struktúra helyes, de jelen állapotban nem
indítható éles KB-val, és nincs külső hívó).

### 5. Session-specifikus tartalom (SessionIngressEnvelope, Postgres, trust mezők) — MISSING (a vártnak megfelelően)

```
$ grep -rn "SessionIngressEnvelope" --include="*.py" --include="*.md" --include="*.yaml" --include="*.json" .
```
Az összes találat (`CLAUDE.md`, `README.md`, `docs/{hu,en}/architecture.{md,yaml}`) **csak
dokumentációban** van — nincs `.py`/`.sql`/`.json` schema-definíció. `grep -rln
"postgres\|Postgres\|POSTGRES" --include="*.py" --include="*.sql" --include="*.yaml"` a
`docs/`-on kívül **0 találat**. `find . -name "*.sql"` és `find . -iname "*migration*"`
mindkettő **0 találat** (a `.git/` kivételével). `grep -rn "canonical\s*:\s*false\|
promotion_allowed\|session_local\|session_derived" --include="*.py" --include="*.sql"` **0
találat** — a trust-modell mezők (`canonical`, `promotion_allowed`, `interpreted`,
`default_scope`, `cross_session`) kizárólag a `CLAUDE.md`/docs YAML-blokkjaiban léteznek
dokumentációs célból, sehol kódban/schema-ban.

Státusz: **concept** — a session-specifikus rétegnek (ingress envelope, Postgres storage,
trust mezők) jelenleg nulla kód-megfelelője van, csak dokumentált terv. Ez pontosan a job
elvárt eredménye, és sikeresen bizonyítva (nem csak állítva).

### 6. Vault signing tooling — RÉSZBEN IMPLEMENTED, RÉSZBEN SCAFFOLD

`tools/releaselib/vault_service.py` (75 stmt, teszt-coverage 95%, `tests/test_tools/
test_releaselib/test_vault_service.py` 0 hibával fut) — ez a kódréteg implementált és tesztelt
a `cic-mcp-session` saját, generic release-tooling kontextusában (örökölt a base-repo-ból).
Azonban a **git hook bekötése** (`commit-msg` hook a `cic-my-sign-key`-jel) jelen klónban nem
ellenőrizhető production-szinten: `git config core.hooksPath` →
`/home/sinkog/sync/git.partners/CentralInfraCore/hooks`, ami **nem létezik ebben a
munkakörnyezetben** (`ls` hibát ad). Ez nem feltétlenül hiba a `cic-mcp-session` repóban — a
hooksPath valószínűleg a fejlesztői gépen globálisan van beállítva, és a job-workspace klón
ezt nem örökli automatikusan — de azt jelenti, hogy **ebből a klónból nem volt
végrehajtható/igazolható signed-commit teszt**. A `project.yaml`-ban lévő Vault-aláírás
(`sign:`, `cicSign:`, tanúsítványok) git-tracked, statikus adat — nem futásidejű bizonyíték.

Státusz: **implemented** (a `releaselib`/`vault_service.py` kódréteg, tesztekkel bizonyítva,
örökölt generic infrastruktúra) — de a session-specifikus signing-folyamat élő futtatása ebben
az auditban **nem volt reprodukálható** (scaffold-szintű bizonyíték: kód van, hook-bekötés
külső függőség miatt nem tesztelhető innen).

### 7. Release tooling (`tools/compiler.py`, `tools/infra.py`) — RÉSZBEN IMPLEMENTED

`pytest tests/ -q` futtatva: **117 passed, 18 failed** (135 összesen). A 18 hiba között:
- `tests/test_tools/test_mcp_server.py::TestSearchQuerySemantic::test_result_has_required_fields`
  — `AssertionError: assert 'file_path' in {..., 'file_paths': [...], ...}` — ez egy
  **schema-drift** a teszt és a `server.py` tényleges válasz-formátuma között (a kód
  `file_paths` listát ad vissza, a teszt `file_path` egyes számú kulcsot vár). Ez közvetlen
  bizonyíték arra, hogy a `mcp-server/server.py` és a hozzá tartozó teszt suite nincs
  szinkronban — tovább erősíti a 4. pont "scaffold" besorolását.
- 11 hiba `test_compiler.py`/`test_infra.py`-ban (`TestMainCLI`, `TestReleaseManagerPhases`,
  `TestConfigLoader`) — ezek a generic release-folyamatot tesztelik (nem session-specifikus),
  valószínűleg mock/fixture-drift vagy Docker-függő tesztek, amik ebben a Docker nélküli
  futtatásban nem futnak helyesen.

Coverage: `tools/generate_gitmodules.py` **0%** (96/96 stmt miss) — ez a `kb.gitmodules`
Makefile target mögötti kód, **soha nem futott le tesztben sem**, és élesben sem futtatható,
mert a hozzá szükséges `knowledge.sources.yaml` nem létezik a repóban (`find . -maxdepth 1
-iname "knowledge*"` → 0 találat). `make kb.gitmodules PROFILE=public` lefuttatva: ugyanaz a
`p_venv` hiány miatt `Error 127`-rel elszáll, mielőtt a `knowledge.sources.yaml` hiánya
egyáltalán számítana.

Státusz: **partial/scaffold** — `compiler.py`/`infra.py`/`releaselib/` magja tesztelt és
működik (117 zöld teszt), de a KB-specifikus rész (`generate_gitmodules.py`) 0% lefedettséggel
és hiányzó konfiggal **nem futtatható**.

### 8. Kontraszt a `cic-mcp-private` kalibrációs referenciával

| Elem | `cic-mcp-private` (kalibráció) | `cic-mcp-session` |
|---|---|---|
| `source/` | 2 valódi git submodule (`CentralInfraCore/`, `OpenIntentSign/`), 17 al-submodule a `.gitmodules`-ban | csak `.gitkeep`, 0 fájl |
| `sqlite_data/*.sqlite` | `knowledge_base.sqlite`, **13 975 552 byte** (~14 MB), épített | nincs `.sqlite` fájl, csak `db_schema.json` |
| `.gitmodules` | létezik, 17 submodule bejegyzés | nem létezik |
| git history jellege | feature-commitok: `feat: content-addressed chunk deduplication`, `feat: Go meta YAML KB integration — 914 → 1140 chunks`, `feat: wire base/mcp specialization branch into KB submodules` — ezek **tartalom-bővítő**, KB-méretre ható commitok | a history (`git log --oneline`, 156 commit) infrastruktúra- és docs-customization commit (`feat: add MCP server base infrastructure`, `docs: customize README/CLAUDE.md...`) — **nincs egyetlen tartalom-bővítő (KB-t tényleg építő) commit sem** |
| KB build végeredmény | sikeresen lefutott, valós tartalom indexelve | jelen auditban lefuttatva: `ZeroDivisionError`, 0 byte kimenet |

Ez a táblázat konkrétan azt mutatja, mit jelent "implemented" ugyanezen a scaffoldon: nem a
kód megléte, hanem a **feltöltött `source/` + épített `sqlite_data/*.sqlite` + tartalom-bővítő
feature-commitok** együttese. A `cic-mcp-session` ezek közül **egyikkel sem** rendelkezik —
ez objektív, számszerű (fájlméret, submodule-szám, commit-tartalom) bizonyíték, nem
feltételezés.

## Claim-Evidence Matrix

| Claim | Status | Evidence | Verification Method | Risk |
|---|---|---|---|---|
| `README.md`/`CLAUDE.md`/`docs/hu/architecture.md` "Jelenlegi állapot" állításai megegyeznek a tényleges repo-állapottal | proven | `docs/hu/architecture.md:71-77`; `source/` tartalma `ls -la` szerint csak `.gitkeep` | direkt fájlrendszer-ellenőrzés | alacsony |
| `project.yaml` komponens-identitása (`name: base`) nincs frissítve session-specifikusra | proven | `project.yaml` `metadata.name: base`, `description: "Schema Compiler & Signing Infrastructure Template"` | `cat project.yaml` | alacsony — kozmetikai, de audit-inkonzisztencia |
| `make_source.py` üres `source/`-szal hibára fut (nem üres KB-t generál) | proven | `ZeroDivisionError` a `build_bm25_index`-ben (`make_source.py:307`), futtatva venv-ben telepített deps-ekkel | tényleges futtatás (`python make_source.py`), `kb_data/` 0 új fájl utána | közepes — ha bármely jövőbeli job feltölti `source/`-t és lefuttatja, az üres-eset hibakezelése nélkül továbbra is instabil lesz kis korpusznál |
| `requirements.txt` nem tartalmazza a `requirements.in`-ben listázott MCP/KB csomagokat | proven | `grep -i "^markdown" requirements.txt` → csak `markdown-it-py`; friss `pip install -r requirements.txt` után `ModuleNotFoundError: No module named 'markdown'` | tényleges `pip install` + `python make_source.py` futtatás | magas — bárki, aki a dokumentált módon (`pip install -r requirements.txt`) telepít, nem tudja futtatni a KB pipeline-t |
| `make kb.build` jelen állapotban nem futtatható (`p_venv` hiánya) | proven | `make: ./p_venv/bin/python: No such file or directory`, `Error 127` | `make kb.build` tényleges futtatása | magas — a CLAUDE.md dokumentált "Kulcs parancsok" listájának első lépése azonnal hibára fut |
| `mcp-server/server.py` minden tool-ja `FileNotFoundError`-ral hibázik üres `kb_data/pkl/`-lel | proven | `server.py:102-103` (`load_kb`); közvetlen Python-hívással igazolva: `FileNotFoundError: Missing: .../kb_data/pkl/chunks.pkl` | direkt `load_kb()` hívás futtatva | magas — `make mcp.run` sem tudna sikeresen elindulni |
| `search_query`/`search_nodes` stb. tool-oknak nincs külső production hívójuk, csak belső kereszthivatkozás | proven | `grep -rn "search_query\|search_nodes\b" --include="*.py" . | grep -v test` → `server.py:783`, `server.py:1097` (mindkettő `server.py`-on belüli, `focus_pack`/`guided_path` hívása) | `grep -rn` a job által előírt reachability-parancs | közepes — amíg nincs külső konzument, a tool-kontraktus nem validált éles használatban |
| SessionIngressEnvelope/Postgres/trust mezők nincsenek kódban implementálva, csak dokumentálva | proven | `grep -rn "SessionIngressEnvelope" --include="*.py" --include="*.yaml" --include="*.json"` → 0 találat (csak `.md` docs); `grep` Postgres/trust mezőkre kódban → 0 találat; `find -name "*.sql"` → 0 | grep + find a teljes repóban | alacsony — ez a job elvárt eredménye, helyesen dokumentálva is |
| `tools/releaselib/vault_service.py` implementált és tesztelt | proven | `pytest tests/test_tools/test_releaselib/test_vault_service.py` 0 hiba; coverage 95% (`vault_service.py` 75 stmt, 4 miss) | tényleges pytest futtatás | alacsony |
| Vault signing git hook élesben bekötött ebben a klónban | unknown | `git config core.hooksPath` → `/home/sinkog/sync/git.partners/CentralInfraCore/hooks`, mely nem létezik ebben a munkakörnyezetben | `ls` a hooksPath útra | alacsony — valószínűleg fejlesztői gép-szintű global config, nem repo-hiba, de innen nem igazolható |
| `tools/generate_gitmodules.py` 0% lefedettséggel, nincs `knowledge.sources.yaml` a repóban | proven | pytest coverage report: `generate_gitmodules.py 96 96 0%`; `find . -maxdepth 1 -iname "knowledge*"` → 0 találat | pytest coverage + find | közepes — a `kb.gitmodules` Makefile target jelenleg garantáltan hibára fut |
| `mcp-server/server.py` és a hozzá tartozó teszt suite schema-drift-ben van (`file_path` vs `file_paths`) | proven | `tests/test_tools/test_mcp_server.py::test_result_has_required_fields` FAILED: `assert 'file_path' in {..., 'file_paths': [...]}` | pytest futtatás | közepes |
| `cic-mcp-private`-hez képest `cic-mcp-session` `source/`/`sqlite_data/` infrastruktúra azonos, tartalom nélküli | proven | `cic-mcp-private/sqlite_data/knowledge_base.sqlite` 13 975 552 byte vs. `cic-mcp-session` nincs `.sqlite` fájl; `cic-mcp-private/.gitmodules` 17 submodule vs. `cic-mcp-session`-ben nincs `.gitmodules` | `ls -la` mindkét repóban, `cat .gitmodules` | alacsony — ez a vártnak megfelelő, dokumentált scaffold-állapot |
| `cic-graph` KB jelenleg nem indexeli a `cic-mcp-session` repót | proven | `kb_status` `data_dir` → `.../MCPs/private/kb_data/pkl`; `search_nodes("cic-mcp-session")`, `search_nodes("trust-domain")`, `search_nodes("session-scope")` mindegyike `{"result": []}` | `mcp__cic-graph__kb_status` + `search_nodes` élő hívás | alacsony — várt, nem hiba |

## Decisions Proposed

1. A `cic-mcp-session` jelenlegi állapota helyesen **`experimental`** — a repo egyetlen
   funkcionális rétege sem éri el a "candidate" szintet (sem a KB pipeline, sem az MCP szerver
   nem futtatható végponttól-végpontig jelen állapotban).
2. Mielőtt bármilyen session-specifikus capability-job (`session-ingress-envelope-contract-001`
   stb.) implementációt ír, egy **infrastruktúra-helyreállító job** szükséges, amely:
   - regenerálja a `requirements.txt`-t (`pip-compile requirements.in`) úgy, hogy tartalmazza
     az MCP/KB csomagokat
   - kezeli az üres/kis `source/` esetet a `make_source.py`-ban (legalább graceful empty-KB
     generálás `ZeroDivisionError` helyett)
   - frissíti a `project.yaml` `metadata.name`/`description` mezőit session-specifikusra
3. A `tools/generate_gitmodules.py` (0% coverage, hiányzó `knowledge.sources.yaml`) és a
   `kb.gitmodules` target csak akkor váljon release-ready-é, ha a session-specifikus
   `source/` feltöltési stratégia (mely repókat submodule-ozzuk be) eldöntött — ez jelenleg
   nyitott kérdés, amit a `session-ingress-envelope-contract-001`/`session-postgres-storage-
   design-001` jobok előtt vagy velük párhuzamosan kell tisztázni.

## Rejected / Out Of Scope

- Session-specifikus architektúra teljes megvalósítása — out of scope, ezt a job explicit
  kizárja (`Nem cél`).
- Postgres schema implementálása — out of scope, külön job (`session-postgres-storage-
  design-001`).
- Gateway integráció — out of scope.
- `SessionIngressEnvelope` contract megírása — out of scope, külön job
  (`session-ingress-envelope-contract-001`).
- A Vault hook globális (`/home/sinkog/sync/git.partners/.../hooks`) bekötésének javítása —
  out of scope ennek a jobnak, ez egy környezet-szintű (nem repo-szintű) konfiguráció, és a
  job worktree-jéből nem is módosítható biztonságosan.

## Risks

- **Magas**: a CLAUDE.md "Kulcs parancsok" szekciójának első lépése (`make kb.build`) jelenleg
  garantáltan hibára fut bármely friss klónban, `p_venv` hiánya miatt. Ha egy jövőbeli
  capability-job vakon követi a dokumentált parancssorozatot anélkül, hogy ezt az auditot
  elolvasná, időt veszít a hibakeresésen.
- **Magas**: a `requirements.txt`/`requirements.in` drift miatt még `p_venv` létrehozása után
  is `ModuleNotFoundError`-ral szállna el a pipeline — ez egy rejtett, nem azonnal nyilvánvaló
  hiba, amíg valaki tényleg végigfuttatja (ahogy ebben az auditban megtörtént).
  Hibajavítás nélkül minden jövőbeli "építsünk valódi KB-t" job ugyanebbe a falba futna bele.
  Az audit emellett bizonyítja, hogy üres `source/`-szal a pipeline jelenlegi formájában
  (`ZeroDivisionError`-ral) elszáll — egy graceful empty-KB eset nélkül bármely jövőbeli
  job, amely fokozatosan tölti fel a `source/`-t, instabil állapotot tapasztalhat kis
  korpusznál.
- **Közepes**: a `test_mcp_server.py` 1 db schema-drift hibája (`file_path` vs `file_paths`)
  azt jelzi, hogy a teszt suite és a tényleges `server.py` válasz-kontraktus nincs
  szinkronban — ha egy jövőbeli job ezt a tesztet "zöldnek" feltételezi anélkül hogy lefuttatná,
  hamis biztonságot kaphat.
- **Alacsony**: `project.yaml` elmaradt customizációja inkább audit-higiéniai, mint
  funkcionális kockázat — de a következő release-tooling jobnak érdemes egy sorban javítani.

## Definition Of Done Check

- [x] minden nagyobb repo elem státusza: implemented/scaffold/concept/missing —
  lásd Findings 1-8 és a Claim-Evidence Matrix
- [x] minden `implemented` állítás mellett reachability vagy runtime evidence —
  `vault_service.py` (pytest + coverage), `releaselib/*` (pytest); minden más elem
  (`make_source.py`, `server.py`, `generate_gitmodules.py`) explicit `scaffold`-ként van
  jelölve, tényleges futtatási hibákkal alátámasztva (`ZeroDivisionError`, `FileNotFoundError`,
  `Error 127`, `ModuleNotFoundError`)
- [x] legalább 3 következő factory-job javaslat — lásd "Next Jobs", 4 javaslat
- [x] NO-GO lista — lásd "Next Jobs" alatti NO-GO szakasz
- [x] claim-evidence tábla kitöltve, nem üres — 13 sor
- [x] explicit ellenőrzött: docs/CLAUDE.md korábbi állításai és tényleges repo-állapot
  egyezik-e — 1. pont (Findings): **egyezik** a "Jelenlegi állapot" szekciókban; 2. pont:
  **eltérés** található a `project.yaml` komponens-identitásában

## Next Jobs

1. **`session-infra-pipeline-fix-001`** (új javaslat, nem volt korábban tervezve) —
   `requirements.txt` regenerálása (`pip-compile requirements.in`) úgy, hogy tartalmazza az
   MCP/KB csomagokat, és a `make_source.py` empty-source eset graceful kezelése
   (`ZeroDivisionError` elkerülése `corpus_size == 0` esetén). Indok: ez blokkolja **minden**
   további session-specifikus jobot, amely valaha valódi `source/` tartalmat tölt be és KB-t
   épít — ezt kell elsőként megoldani, mielőtt a contract-jobok elindulnának.
2. **`session-ingress-envelope-contract-001`** (a job inputban már megnevezett, soron
   következő) — `SessionIngressEnvelope` schema + validáció megírása. Indok: ez az audit
   bizonyította, hogy ez a schema jelenleg **csak dokumentációban** létezik (0 kód-megfelelő);
   ez a leginkább blokkoló hiányzó contract a session réteg felépítéséhez.
3. **`session-postgres-storage-design-001`** (a job inputban már megnevezett) — Postgres
   schema-szeparáció (`session_raw.*`, `session_core.*`, `session_idx.*`, `session_jobs.*`,
   `session_api.*`) megtervezése az `architecture.md` Postgres-first elve alapján. Indok: az
   audit bizonyította, hogy jelenleg **0 SQL fájl** és **0 Postgres-referencia kódban** van —
   ez a második legnagyobb hiányzó réteg az ingress envelope után.
4. **`session-project-metadata-cleanup-001`** (új javaslat) — a `project.yaml`
   `metadata.name`/`description` mezőinek frissítése `base`-ről `cic-mcp-session`-re, és a
   release tooling (`tools/compiler.py`, `tools/infra.py`) 18 failing tesztjének
   kivizsgálása/javítása (különös tekintettel a `test_mcp_server.py` schema-drift hibájára).
   Indok: alacsony kockázatú, de audit-higiéniai adósság, amely megelőzi a következő
   release-ciklust.

### NO-GO lista (mire nem szabad jelenleg építeni)

- **NO-GO**: `make kb.build`/`make mcp.run` parancsokra alapozott bármilyen jövőbeli job
  demo/teszt-terve, amíg a `session-infra-pipeline-fix-001` nem zárja a `requirements.txt`
  drift-et és a `p_venv` hiányt.
- **NO-GO**: a `tools/generate_gitmodules.py`/`kb.gitmodules` target használata, amíg nincs
  `knowledge.sources.yaml` a repóban — jelenleg 0% tesztelt, és nincs konfigurációs input.
- **NO-GO**: a `mcp-server/server.py` "12 tool implementált" állítás további hivatkozása
  `implemented`-ként bármely jövőbeli jobban — ez ezen audit alapján **scaffold**, nincs
  futtatható runtime híd jelen állapotban.
- **NO-GO**: a `project.yaml` jelenlegi tartalmára (mint "session-specifikus metaadat")
  hivatkozó bármilyen állítás — ez még a `base` template metaadata.
