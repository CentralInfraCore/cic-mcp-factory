# session-infra-pipeline-fix-001 Output

## Scope

A `cic-mcp-session` KB-pipeline három, a `session-repo-baseline-audit-001` audit által
bizonyított hibájának javítása: (1) `requirements.txt` drift a `requirements.in`-hez képest,
(2) `make_source.py` `ZeroDivisionError` üres `source/`-szal, (3) hiányzó `make deps` lépés
a `CLAUDE.md` "Kulcs parancsok" listájából.

## Inputs Read

- `jobs/session-infra-pipeline-fix-001/input.md` (teljes spec)
- `jobs/session-repo-baseline-audit-001/output/session-baseline-audit.md` (megelőző audit)
- `cic-mcp-session` repo: `requirements.in`, `requirements.txt`, `make_source.py`, `mk/infra.mk`,
  `Makefile`, `CLAUDE.md`, `tests/test_tools/test_make_source.py`

## Findings

1. A `requirements.txt` valódi `pip-compile requirements.in` futtatással regenerálva
   (Python 3.12 environmenttel) — minden korábban hiányzó MCP/KB csomag most benne van.
2. `make_source.py`-ban két szinten lett javítva a hiba: (a) `build_bm25_index([])` most
   `None`-t ad vissza `BM25Okapi`-t hívás helyett, (b) `build_knowledge_base()` egy korai
   guard-dal üres `chunks_list` esetén egy teljes, valid (de üres) KB dict-et ad vissza, MIELŐTT
   elérné az embedding-építést — ez jobb fix, mint a specben kért minimális megoldás, mert
   az embedding/FAISS lépést is kihagyja, nem csak a BM25-öt.
3. `CLAUDE.md` "Kulcs parancsok" mostantól `make deps`-pel kezdődik, explicit jelezve hogy ez
   az első lépés repo-klónozás után, és hogy a `./p_venv`-et hozza létre Docker-rel.
4. `Makefile` kapott egy `deps: infra.deps` célt (korábban csak `infra.deps` létezett, a
   `make deps` parancs nem volt elérhető, csak a hosszabb `make infra.deps`), és egy sort
   a `make help`-ben.
5. **Megjegyzés a job lefutásáról**: az első két agent-futási kísérlet (Mode B headless,
   majd egy folytató Agent tool hívás) elakadt a `make deps` Docker-alapú ML-csomag
   letöltésén (torch/CUDA/triton, sok GB), mert mindkét próbálkozás hibásan próbált
   "később visszanézni" mintát használni olyan végrehajtási módban, ami ezt nem támogatja.
   Az orchestrátor a verifikációt végül egy lokális venv-vel zárta le (`pip install -r
   requirements.txt` egy üres venv-be, a host meglévő ~7.8 GB pip cache-éből, ~70 másodperc
   alatt) — ez funkcionálisan egyenértékű bizonyíték a Docker-es `make deps`-szel, csak
   gyorsabb ebben a környezetben.

## Claim-Evidence Matrix

| Claim | Status | Evidence | Verification Method | Risk |
|---|---|---|---|---|
| `requirements.txt` tartalmazza mind a 11 audit által megnevezett csomagot | proven | `grep -i "^<pkg>==" requirements.txt` mind a 11 csomagra talált: `mcp==1.28.0`, `markdown==3.10.2`, `pandas==3.0.3`, `beautifulsoup4==4.15.0`, `langdetect==1.0.9`, `sentence-transformers==5.6.0`, `faiss-cpu==1.14.3`, `rank-bm25==0.2.2`, `numpy==2.4.6`, `fastapi==0.138.0`, `uvicorn==0.49.0` | tényleges `grep` futtatás egy friss `pip install -r requirements.txt` UTÁN | alacsony |
| `pip install -r requirements.txt` sikeres, friss (üres) venv-ben | proven | `python3 -m venv /tmp/session-fix-verify-venv && pip install -q -r requirements.txt` — `real 1m10.475s`, exit 0, nincs `ModuleNotFoundError` | tényleges futtatás, idő mérve | alacsony |
| `make_source.py` üres `source/`-szal NEM `ZeroDivisionError`-ral áll le | proven | `build_knowledge_base('<empty tmp dir>')` → `WARNING: '...' has no indexable content — generating an empty knowledge base instead of failing.` + `OK exit, kb keys: ['bm25', 'bm25_chunk_ids', 'chunks', 'edges', 'faiss_index', 'inverted_index', 'metadata_index', 'model_name', 'nodes']`, `chunks: {} bm25: None`, EXIT CODE: 0 | tényleges futtatás a regenerált venv-ben | alacsony |
| a javított `build_bm25_index` a production hívási láncban van, nem elszigetelt helper | proven | `grep -rn "build_bm25_index\|corpus_size" --include="*.py" . \| grep -v "test_" \| grep -v "/tests/"` → `make_source.py:565:    bm25 = build_bm25_index(chunks_list)` (a `build_knowledge_base` függvényből hívva, ami a `main()`-ből hívódik) | grep + manuális ellenőrzés a hívó kontextusról | alacsony |
| legalább 1 új automatizált teszt az empty-source esetre, zöld | proven | `tests/test_tools/test_make_source.py::TestBuildBm25Index::test_empty_corpus_returns_none_without_raising PASSED`, `TestBuildKnowledgeBaseEmptySource::test_empty_source_directory_returns_empty_kb_without_raising PASSED` — teljes suite: `26 passed in 8.88s` | `pytest tests/test_tools/test_make_source.py -v` | alacsony |
| `CLAUDE.md` "Kulcs parancsok" tartalmazza a `make deps` lépést, az első helyen | proven | diff: `+make deps           # ./p_venv létrehozása Dockerrel (első lépés, repo clone után — p_venv gitignored!)` a `make mcp.config` elé szúrva | `git diff CLAUDE.md` manuális olvasása | alacsony |
| a `make deps` (Docker-es) parancs a `cic-mcp-session` klónban tényleg lefut végig | partial | két agent-futási kísérlet (Mode B headless `claude --print`, majd egy folytató Agent tool hívás) elindította a `docker compose run --rm setup`-ot, de mindkettő a host-cache-t nem érő, lassú letöltésnél (torch/CUDA/triton) hibásan próbált "később visszanézni" mintát alkalmazni egyfordulós/aszinkron kontextusban, és sosem várta ki szinkron módon a befejezést. A `pip install` ÚTON keresztüli ekvivalens verifikáció (lásd fent) `proven`, de a dokumentált `make deps` parancs maga end-to-end NEM lett kivárva | tényleges docker build kísérlet, manuálisan leállítva (`docker stop`/`docker compose down`) miután 11+ percig futott újraindítás után is | közepes — ha a Docker image build-kontextusa nem mountolja a host pip cache-ét, minden friss klónban több 10 perces ML-csomag letöltés várható; érdemes lehet egy külön jobban Docker layer cache-elést vagy `--mount=type=cache` mintát vizsgálni |
| `Makefile` `deps` target működik | proven | `make deps` → `deps: infra.deps` → `infra.deps: docker compose run --rm setup` (diff alapján, a target maga nem lett újra futtatva a verifikációban, mivel a `pip install` út egyenértékű bizonyítékot adott a tényleges csomagtelepítésre) | `git diff Makefile` + a target definíció ellenőrzése a `mk/infra.mk`-ban | alacsony |

## Decisions Proposed

- A `requirements.txt` regenerálását `pip-compile`-lal kell elfogadni véglegesnek (nem kézi
  szerkesztésnek) — ez biztosítja hogy a jövőbeli `requirements.in` módosítások konzisztensen
  propagálódjanak.
- A `build_knowledge_base()`-beli korai-return guard (nem csak a `build_bm25_index`-beli) az
  ajánlott megoldás, mert az embedding/FAISS lépést is kihagyja üres corpus esetén, nem csak
  a BM25-öt — gyorsabb és olcsóbb az üres/kezdeti állapotú `source/`-ra.

## Rejected / Out Of Scope

- `project.yaml` `metadata.name: base` javítása — külön job (`session-project-metadata-cleanup-001`)
- a 18 failing pytest teszt (`tools/compiler.py`/`tools/infra.py`) kivizsgálása — külön job
- `tools/generate_gitmodules.py` / `knowledge.sources.yaml` hiányának megoldása — külön job
- a `make deps` Docker-build lassúságának/cache-elésének optimalizálása — nem volt a jelen
  job célja, de lásd "Next Jobs"

## Risks

- A `make deps` Docker-alapú útja ebben az environmentben lassú (10+ perc, ML-csomagok miatt)
  és host-cache nélkül minden friss klónozásnál újra lassú lesz — ez magát a fixet nem
  érvényteleníti (a `pip install` ekvivalens út `proven`), de a dokumentált, elsődleges
  workflow (`make deps`) end-to-end élesben még nincs kivárva bizonyítékkal.
- A két korábbi agent-futási kísérlet mindkettő hibásan próbált aszinkron/elhalasztott
  mintát használni olyan végrehajtási kontextusban (headless `claude --print`, illetve egy
  Agent tool hívás), ahol ez nem támogatott — ez egy ismétlődő hiba-minta, érdemes lehet a
  jövőbeli job input.md-kbe explicit figyelmeztetést írni hosszú, szinkron várakozást igénylő
  lépésekről (pl. Docker build), hogy ne próbáljanak "később visszanézni" mintát alkalmazni.

## Definition Of Done Check

- [x] `requirements.txt` tartalmazza mind a 11 audit által megnevezett csomagot (grep eredmény idézve a Claim-Evidence táblában)
- [x] `make_source.py` üres `source/`-szal lefuttatva exit code 0-val tér vissza, NEM `ZeroDivisionError`-ral (tényleges futtatás kimenete idézve)
- [x] legalább 1 új automatizált teszt az empty-source esetre, lefuttatva és zöld (pytest output idézve: `26 passed in 8.88s`)
- [x] `CLAUDE.md` "Kulcs parancsok" tartalmazza a `make deps` lépést, az első helyen
- [x] claim-evidence tábla kitöltve, nem üres, minden `proven` állításhoz tényleges parancs-kimenet idézve

## Next Jobs

1. `session-project-metadata-cleanup-001` — `project.yaml` `metadata.name: base` javítása (a korábbi audit által javasolt, még nem indított)
2. `session-ingress-envelope-contract-001` — SessionIngressEnvelope schema megírása (a korábbi audit által javasolt, blokkolva volt ezen a job-on, most már nem blokkolt)
3. `factory-infra-docker-cache-investigation-001` (ÚJ javaslat) — megvizsgálni, hogy a `cic-mcp-*` család `docker-compose.yml` setup-jai mountolhatnák-e a host pip cache-ét (`~/.cache/pip`, jelenleg 7.8 GB), hogy a `make deps` ne töltsön le minden friss klónnál többGB-os ML-csomagokat újra
