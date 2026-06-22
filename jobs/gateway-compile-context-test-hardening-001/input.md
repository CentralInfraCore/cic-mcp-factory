# Job: gateway-compile-context-test-hardening-001

## Kontextus

A `session-context-pack-v1-001` job (`cic-mcp-gateway` PR #7, mergelve) implementálta az
ELSŐ valódi `compile_context()` függvényt és `candidate` státuszt kapott. Az
orchestrátor FÜGGETLEN újra-ellenőrzése (saját, friss Postgres-konténerrel, a már
mergelt `main` ágon) egy KONKRÉT, reprodukált hiányosságot talált, amely a `candidate`
indoklását gyengíti:

**A talált hiba**: a `requirements.in` tartalmazza a `sentence-transformers` (és
`markdown`, `faiss-cpu`) csomagokat, de a commitolt `requirements.txt` NEM — ezt a
deszinkront a `session-context-pack-v1-001` riport saját "Findings" #6 pontja már
dokumentálta, de NEM kötötte össze azzal a következménnyel, hogy emiatt a SAJÁT ÚJ
tesztje (`tests/test_gateway_core/test_compile_context.py`) egy TISZTA klónon/venv-en
CSENDBEN DEGRADÁLVA fut le: a `seeded_session_id` fixture a `cic-mcp-session`
`session_store.chunk_indexer.run_indexing_batch()`-ot hívja (sys.path injektálással,
de a GATEWAY saját `.venv-host`-jának interpreterével) — ha ott nincs telepítve a
`sentence-transformers`, az `embed_texts()` hívás `ModuleNotFoundError`-t dob, amit a
`chunk_indexer._index_one_job()` egy SZÁNDÉKOS, tág `except Exception` blokk elnyel
(failed/dead_letter outbox-eredménnyé alakítva) — ez a `with conn.transaction():`
blokkon belül van, ezért a chunk-beszúrás is VISSZAGÖRGETŐDIK. A teszt mégis ZÖLDEN fut
le, mert az `assert len(envelope["session_derived_notes"]) >= 1` asszerció a
`get_session_status()`-ból mindig hozzáadott összegző note-tal is teljesül — a
context_pack-eredetű tartalom HIÁNYÁT a teszt NEM kapja el.

**Független reprodukció (orchestrátor, friss Docker Postgres-konténerrel, mind a
6 migráció lefuttatva, `cic-mcp-gateway/.venv-host`-ban `sentence-transformers` NÉLKÜL)**:
`2 passed`, de `SELECT count(*) FROM session_core.chunks` → `0`. Manuális
`pip install sentence-transformers` UTÁN, azonos teszt: `2 passed`, és
`session_core.chunks` → valódi sorszámmal (a 2-turn fixture-höz illeszkedő).

Ez NEM logikai hiba a `compile_context()`-ben (az implementáció VALÓDI adattal
bizonyítottan helyesen működik — lásd a riport "Real Stdio MCP Handshake Evidence"
szekcióját, 6 valódi `session_derived_notes` egy manuális futtatásból) — ez egy
**dependency-lock + teszt-asszertáció hiányosság**, amely azt jelenti, hogy a
`candidate` állítás ("legalább 1 automatizált teszt zöld, valódi pipeline-on átfutott
adatra") egy tiszta klónon NEM reprodukálható megbízhatóan.

## Target

- target repo: `cic-mcp-gateway`
- target path: `requirements.txt` (regenerálva) + `tests/test_gateway_core/test_compile_context.py`
  (asszertáció szigorítva)
- change_type: `fix`
- status_after_merge: `candidate`
- status indoklás: ez a job NEM új capability, hanem a már mergelt
  `cic_mcp.gateway.compile_context_v1` `candidate` státuszának VALÓDI alátámasztása —
  a `candidate` csak akkor marad indokolt, ha mindkét DoD pont (lásd lent) teljesül; ha
  NEM, a riportban jelezd és javasold `experimental`-ra visszaminősítést

## Sources

- **KÖTELEZŐ elsődleges forrás (a `cic-mcp-gateway` repo `main`-jén):**
  - `requirements.in` — a "MCP Server & Knowledge Base" blokk (`mcp`, `markdown`,
    `pandas`, `sentence-transformers`, `faiss-cpu`, ...)
  - `requirements.txt` — a JELENLEGI, deszinkronizált, commitolt állapot
  - `docker-compose.yml` — a `setup` service `command`-ja (23-25. sor körül):
    `pip-compile --cache-dir /app/.pip-cache -o requirements.txt requirements.in &&
    pip install --no-cache-dir -r requirements.txt --target /app/p_venv` — EZ a
    kanonikus módja a `requirements.txt` regenerálásának, NE futtass kézzel `pip freeze`-t
    vagy ekvivalens ad-hoc módszert
  - `mk/infra.mk:69-71` (`infra.deps:` target) — ez hívja a `docker compose run --rm setup`-ot
  - `gateway_core/compile_context.py`, `gateway_core/validate_envelope.py` — a
    `session-context-pack-v1-001`-ben implementált kód, NEM módosítandó funkcionálisan
  - `tests/test_gateway_core/test_compile_context.py` — a meglévő teszt, amelynek
    asszertációját szigorítani kell
  - `output/session-context-pack-v1-report.md` — a "Findings" #6 és "Risks" #5 pontja
    (a deszinkron már dokumentált, ELŐZETES állapot)

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit módosítanál

## Feladat

### 1. `requirements.txt` regenerálása a kanonikus módon

Futtasd `make infra.deps`-t (vagy közvetlenül `docker compose run --rm setup`-ot, ha a
Make target nem elérhető a job-futtatási környezetben) — ez `pip-compile`-lal
regenerálja a `requirements.txt`-t a TELJES `requirements.in`-ből. Idézd a diff-et
(`git diff requirements.txt` előtte/utána, rövidítve a leglényegesebb hozzáadott sorokra:
`sentence-transformers`, `markdown`, `faiss-cpu` és tranzitív függőségeik).

Ha a Docker-alapú `pip-compile` NEM elérhető a job-futtatási környezetben (pl. nincs
Docker-hozzáférés), dokumentáld ezt EXPLICIT a "Findings"-ban és "Risks"-ben, és jelezd
hogy ez blokkolja a `candidate`-megerősítést — NE generálj kézzel/heurisztikusan
`requirements.txt`-t.

### 2. `.venv-host` újraépítése a regenerált `requirements.txt`-ből

```
rm -rf .venv-host
python3 -m venv .venv-host
.venv-host/bin/pip install --no-cache-dir -r requirements.txt
```

Idézd a `sentence-transformers`/`markdown`/`faiss-cpu` telepítésének sikeres kimenetét.

### 3. Teszt-asszertáció szigorítása

A jelenlegi `tests/test_gateway_core/test_compile_context.py`
`test_compile_context_available_session_end_to_end` tesztje csak
`assert len(envelope["session_derived_notes"]) >= 1`-et követel — ez akkor is teljesül,
ha a `get_session_context_pack()` 0 sort ad vissza (mert a `get_session_status()`
összegző note-ja önmagában is `>= 1`-et eredményez). Szigorítsd az asszertációt ÚGY,
hogy az KIFEJEZETTEN megkövetelje a context_pack-eredetű tartalmat is, pl.:

```python
assert envelope["answer_type"] == "history_recall"
chunk_refs = [n for n in envelope["session_derived_notes"] if ":chunk:" in n["ref"]]
assert len(chunk_refs) >= 1, "context_pack tartalom hiányzik a session_derived_notes[]-ból"
```

(a pontos implementáció rád van bízva, de az elv kötelező: a teszt bukjon, ha a
context_pack-tartalom hiányzik, NE csak a státusz-note meglétét ellenőrizze)

### 4. Teljes regressziós futtatás

Futtasd le a TELJES `tests/` mappát (NEM csak `test_gateway_core/`-t) a regenerált
`requirements.txt`/`.venv-host`-tal — ellenőrizd, hogy a `test_make_source.py`/
`test_mcp_server.py` collection-hibái (a riport "Findings" #6-ban dokumentált,
`markdown`/`faiss` hiánya miatt) MOST megszűntek-e. Idézd a teljes `tests/` futtatás
kimenetét (összesítő sor: hány passed/failed).

### 5. `compile_context` teszt újrafuttatása valódi friss Postgres-konténerrel

Indíts egy FRISS Postgres-konténert, alkalmazd a `cic-mcp-session` migrációkat (a
`session-context-pack-v1-001` riport "Test Session Data Setup" szekciója szerint), majd
futtasd le a szigorított `test_compile_context.py`-t. Idézd a kimenetet ÉS a
`session_core.chunks` táblában keletkezett sorok számát (`psql`/`docker exec` direkt
lekérdezéssel) — ez bizonyítja, hogy a teszt MOST valóban valódi chunk-tartalmat
exercise-el, nem csak a státusz-note-ot.

## Nem cél

- a `compile_context()`/`validate_envelope.py` FUNKCIONÁLIS módosítása
- a `gateway-context-envelope.schema.yaml` módosítása
- a `cic-mcp-session` repo módosítása
- a `ReleaseManager`/`compiler` API-inkonzisztencia javítása (a riport "Findings" #6-ban
  külön említett, nem ehhez a job-hoz tartozó hiba — ha a teljes `tests/` futtatás után
  is megmarad, csak DOKUMENTÁLD, NE javítsd)
- új `.venv-host`/`make deps.local` Makefile target hozzáadása a `cic-mcp-gateway`-hez
  (NEM kötelező ehhez a jobhoz, bár ha természetesen adódik, megteheted)

## Required Output Files

- `output/gateway-compile-context-test-hardening-report.md`

## Required Report Sections

```markdown
# gateway-compile-context-test-hardening-001 Output

## Scope
## Inputs Read
## requirements.txt Regeneration Result

(diff idézve)

## .venv-host Rebuild Result
## Test Assertion Hardening

(a pontos diff a test_compile_context.py-ban)

## Full Test Suite Regression Result

(a teljes tests/ futtatás kimenete, előtte/utána összevetve a session-context-pack-v1
riport "Automated Test Evidence" szekciójának 17 failed + 2 collection error állapotával)

## Hardened Test Re-run With Real Chunks

(a szigorított teszt kimenete + DB chunk-sorszám idézve)

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
`proven` egy "a teszt most valódi chunk-tartalmat exercise-el" állításra KIZÁRÓLAG akkor
használható, ha a tényleges DB chunk-sorszám és a teszt-kimenet egyaránt idézve van —
a teszt zöld állapota önmagában NEM bizonyítja a tartalom valódiságát (ez pontosan az
a hiba, amit ez a job javít).

## Definition Of Done

- [ ] `requirements.txt` regenerálva `pip-compile`-lal, tartalmazza `sentence-transformers`/
      `markdown`/`faiss-cpu`-t, diff idézve
- [ ] `.venv-host` újraépítve a regenerált `requirements.txt`-ből, telepítés-kimenet idézve
- [ ] a teszt-asszertáció szigorítva, hogy a context_pack-tartalom hiánya esetén BUKJON
- [ ] a szigorított teszt friss Postgres-konténerrel lefuttatva, ZÖLD, ÉS a DB-ben
      tényleges chunk-sorszám igazolja a valódi tartalmat
- [ ] a teljes `tests/` mappa regressziós futtatása idézve (javult-e a collection-hiba)
- [ ] ha BÁRMELYIK pont nem teljesül, a riport explicit jelzi és javasolja
      `experimental`-ra visszaminősítést a `cic_mcp.gateway.compile_context_v1`
      capability-re

## Forbidden Shortcuts

- a "2 passed" pytest exit code ≠ sikeres bizonyíték — a tényleges DB chunk-sorszámot is idézni kell, a zöld teszt önmagában nem elég
- kézzel/heurisztikusan írt `requirements.txt` a `pip-compile` kimenete helyett
- a teszt-asszertáció "lazítása" úgy, hogy az MÉG KÖNNYEBBEN passzoljon (csak
  SZIGORÍTÁS megengedett)
- a "zöld teszt" állítás a tényleges DB chunk-tartalom ellenőrzése nélkül

## Git instrukciók

Push a `feature/gateway-compile-context-test-hardening-001` branch-re, KIZÁRÓLAG a
`cic-mcp-gateway` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni, elég
a lokális commit). Main-re az agent NEM pushol. A teszteléshez használt Docker
konténert a munka végén állítsd le és töröld. **NE módosítsd a `meta.yaml` `status`
mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek angolul.
