# Job: session-chunk-indexer-001

## Kontextus

A `session-turn-projector-001` job megírta az első outbox-worker-t: `session_raw.envelopes`
sorokat projektál `session_core.sessions`/`session_core.turns`-ba, és lezárja a
`project_envelope` outbox-job-okat. A `session_core.turns.content` (JSONB, az envelope
payload-ja 1:1) viszont eddig nincs sehol megbontva chunk-okra, és nincs sem full-text,
sem vektor-kereshető.

Ez a job megírja a MÁSODIK outbox-worker-t: `session_core.turns` sorokat darabol
`session_core.chunks`-ra, FTS-indexeli (`session_idx.chunk_fts.tsv`), és embedding-eli
(`session_idx.chunk_embeddings`). Ehhez egy ÚJ outbox job_type-ot kell bevezetni
(`index_turn`), amit egy ÚJ, additív trigger enqueue-l a `session_core.turns` táblán —
ugyanazt a mintát követve, amit a `trg_session_raw_envelopes_enqueue` már bevezetett a
`session_raw.envelopes`-on.

**A `session-postgres-schema.sql` saját kommentje ezt a döntést EXPLICIT ide utalja**:

```sql
-- Embedding dimensionality is a placeholder (1536, matching common
-- text-embedding models) — pinning the actual model/dimension is an open
-- decision for the worker job that implements embedding generation
-- (see session-chunk-indexer-001 in execution-phases.md Phase 3).
```

Tehát a `VECTOR(1536)` placeholder megváltoztatása (ha a választott modell mást ad) NEM
egy önkényes schema-módosítás, hanem egy ELŐRE ENGEDÉLYEZETT, ehhez a jobhoz tartozó döntés.

**Meglévő konvenció az embedding-modellre**: a repo MÁR használ egy lokális
sentence-transformers modellt a KB-rétegben:

```
make_source.py:17: EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
```

Ezt a modellt (vagy egy ettől explicit eltérő, indokolt választást) használd a chunk
embedding-ekhez is — konzisztencia kedvéért, de NEM kötelező ugyanazt választani, ha van jó
indok másra. A választott modell TÉNYLEGES kimeneti dimenzióját (NEM feltételezve, hanem
egy tényleges `model.encode(...)` hívással lekérdezve) kell dokumentálni, és ha ez eltér
1536-tól, a migrációnak `ALTER TABLE session_idx.chunk_embeddings ALTER COLUMN embedding
TYPE VECTOR(<N>)`-t kell végeznie (vagy a táblát újra kell létrehoznia a helyes típussal,
ha az `ALTER ... TYPE` pgvector-ral nem triviális — döntsd el és indokold).

## Target

- target repo: `cic-mcp-session`
- target path: az agent válassza meg (pl. `session_store/chunk_indexer.py`, konzisztensen
  az előző két job modul-elhelyezésével), és idézze a választott path-ot a reportban
- migráció helye: egy ÚJ SQL fájl (pl. `output/session-chunk-indexer-migration.sql`), NEM
  a meglévő `session-postgres-schema.sql` felülírása — a meglévő fájl változatlanul marad,
  ez egy additív migráció, amit MÁSODIK lépésként alkalmazol ugyanazon az instance-on
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: a chunking determinisztikus, de a "helyes" chunk-méret/átfedés
  hangolása, és a retrieval-minőség (mennyire jók a visszakapott chunk-ok egy valódi
  `session_api.search_context()` hívásnál) nincs ebben a jobban kiértékelve —
  `candidate`-hez kellene egy retrieval-minőség teszt valós session-adatokon

## Sources

- `${WORKDIR}/.cic-context/factory-docs/job-slices.yaml` — `session-chunk-indexer-001`
  bejegyzés (phase 3, acceptance_gates, required_evidence, forbidden_shortcuts) — NORMATÍV
- `${WORKDIR}/.cic-context/factory-docs/architecture.md` — "## Schema szeparacio" szekció
- **KÖTELEZŐ elsődleges forrás (mindhárom már a `cic-mcp-session` `main`-en van):**
  - `cic-mcp-session/output/session-postgres-schema.sql` — `session_core.chunks`,
    `session_idx.chunk_fts`, `session_idx.chunk_embeddings`, `session_jobs.outbox` DDL,
    és a `trg_session_raw_envelopes_enqueue` trigger MINTÁJA (ugyanezt a mintát kövesd az
    új `index_turn` trigger-nél)
  - `cic-mcp-session/session_store/turn_projector.py` — a per-row-tranzakciós
    outbox-feldolgozási minta (`_project_one_job`, `run_projection_batch` szerkezete),
    amit ÚJRAHASZNÁLJ a chunk-indexer worker szerkezetében (NE találd ki újra a
    hibakezelés/retry/dead_letter logikát, kövesd ugyanazt a mintát)
  - `cic-mcp-session/make_source.py` (kb. 280-300. sorok) — a meglévő
    `SentenceTransformer`/`create_embeddings` minta, amit a chunk-embedding generáláshoz
    referenciaként használj

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti 3 KÖTELEZŐ forrást, MIELŐTT bármilyen kódot írnál

## Feladat

### 1. Valódi Postgres teszt-instance + additív migráció

Indíts egy valódi Postgres instance-t (`pgvector/pgvector:pg16`, lokálisan cache-elve),
alkalmazd ELŐSZÖR a meglévő `session-postgres-schema.sql`-t, MAJD MÁSODIK lépésként az
ÚJ migrációs SQL fájlt (`output/session-chunk-indexer-migration.sql`), ami:
- létrehoz egy trigger-funkciót + trigger-t a `session_core.turns` táblán (AFTER INSERT),
  ami egy `session_jobs.outbox` sort enqueue-l `job_type='index_turn'`-vel,
  `source_id = turn_id`-vel (kövesd a meglévő `trg_session_raw_envelopes_enqueue` mintáját)
- (ha szükséges) módosítja a `session_idx.chunk_embeddings.embedding` oszlop típusát a
  tényleges modell-dimenzióra

**Egyfordulós végrehajtási fegyelem**: fejezd be a teljes munkát egyetlen menetben.

### 2. Chunking-stratégia (determinisztikus, döntsd el és dokumentáld)

Készíts egy determinisztikus szöveg-darabolási stratégiát, ami a `session_core.turns.content`
(JSONB) tartalmából 1 vagy több `session_core.chunks` sort hoz létre:
- a `content` JSONB-ből vonj ki szöveget (a payload szerkezete provider-/event-függő —
  dokumentáld a kinyerési logikát: pl. ismert kulcsok keresése, fallback a teljes JSON
  string-szerializációjára, ha nincs ismert szöveg-mező)
- darabold fix méret/karakterhatár szerint (pl. ~1000-2000 karakteres darabok, dokumentált
  átfedéssel vagy anélkül) — ez NEM lehet AI/LLM döntés a határokról, csak determinisztikus
  szabály (fix méret VAGY mondat-/sorhatár-regex)
- minden darabhoz `chunk_seq` (sorszám a turn-en belül, `UNIQUE (turn_id, chunk_seq)`-nek
  megfelelően) és `token_count` (egyszerű, dokumentált becslés, pl. whitespace-split hossz)

### 3. Worker implementáció

Írj egy Python worker-t, ami a `turn_projector.py` szerkezetét követve:
- beolvassa a `session_jobs.outbox` `pending`/`failed` (`job_type='index_turn'`) sorait
- minden sorhoz: beolvassa a hozzá tartozó `session_core.turns` sort
- létrehozza a `session_core.chunks` sorokat (2. pont szerint)
- minden chunk-hoz beír egy `session_idx.chunk_fts` sort (`to_tsvector('simple', text)`
  vagy egy indokolt nyelv-konfiguráció — dokumentáld a választást)
- minden chunk-hoz generál egy embedding-et a választott LOKÁLIS modellel, és beírja a
  `session_idx.chunk_embeddings` sort (`embedding_model` mezővel)
- siker esetén az outbox sort `done`-ra állítja; hiba esetén `attempts`/`last_error`/
  `failed`/`dead_letter` ugyanúgy, mint a `turn_projector.py`-ban

### 4. Hibakezelés teszt

Hozz létre egy `index_turn` outbox sort, ami egy NEM LÉTEZŐ `turn_id`-ra hivatkozik — a
workernek `failed`/`dead_letter`-re kell állítania, NEM szabad kivételt dobnia kezeletlenül.

### 5. Tesztek — end-to-end, VALÓDI Postgres ellen

Pytest tesztek a VALÓDI Postgres konténer ellen (nem mock-olva):
- egy `session_core.turns` sor beszúrása (felhasználva a meglévő
  `envelope_writer.insert_envelope()` + `turn_projector.run_projection_batch()` láncot, hogy
  valódi turn keletkezzen) → trigger létrehoz egy `index_turn` outbox sort → a chunk-indexer
  worker futtatása → `session_core.chunks`/`session_idx.chunk_fts`/
  `session_idx.chunk_embeddings` sorok ellenőrzése → outbox `done` ellenőrzése
- a hibakezelés teszt (4. pont)
- legalább egy teszt, ami egy hosszú `content`-et ad (több chunk-ra bomlik) és ellenőrzi a
  `chunk_seq` helyes sorozatát
- egy teszt, ami ellenőrzi, hogy a generált embedding TÉNYLEGES dimenziója megegyezik a
  `chunk_embeddings.embedding` oszlop deklarált dimenziójával (nem csak hogy az INSERT nem
  dob hibát — kérdezd le explicit a `vector_dims(embedding)` SQL függvénnyel vagy
  ekvivalenssel, és assertáld a várt számra)

### 6. Reachability ellenőrzés (kötelező)

```bash
grep -rn "<worker_function_name>" --include="*.py" . | grep -v "test_" | grep -v "/tests/"
```

Minden találatnál add meg a hívó fájl és sor pontos hivatkozását (`file:line` formátumban,
pl. `session_store/chunk_indexer.py:142`) — ha 0 KÜLSŐ hívó van (csak a saját CLI/teszt),
ezt explicit `deadcode`-ként/`scaffold`-ként dokumentáld, NE csak azt írd hogy "a függvény
létezik". Ugyanúgy kezeld a `scaffold`/`proven` megkülönböztetést, mint az előző két
jobban: a CLI létezése/futtathatósága elkülönítve a "valaki tényleg rendszeresen futtatja"
állítástól (a production hívási lánc állapotát is `file:line` hivatkozással dokumentáld, ha
van).

## Nem cél

- `session_core.source_refs` feltöltése (külön job)
- `session_idx.ranking_features` feltöltése (külön job)
- `session_api.search_context()`/retrieval-minőség kiértékelése (a `candidate` státusz egyik
  hiányzó eleme, de ez a job nem méri)
- konkurens, multi-worker-instance lock-olás/claim-mechanizmus (ugyanaz a single-worker
  feltétel, mint a `turn_projector`-nál)
- permanens futtatási infrastruktúra (cron/supervisor/systemd timer)
- külső LLM/HTTP embedding API (OpenAI, Anthropic, stb.) — KIZÁRÓLAG lokális modell

## Required Output Files

- `output/session-chunk-indexer-report.md`
- `output/session-chunk-indexer-migration.sql`

## Required Report Sections

```markdown
# session-chunk-indexer-001 Output

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

Elfogadott `Status` értékek: `proven`, `partial`, `scaffold`, `missing`, `rejected`,
`unknown`. `proven` KIZÁRÓLAG akkor használható, ha a tényleges teszt-futtatás kimenete
idézve van — valódi Postgres ellen.

## Definition Of Done

- [ ] migráció (`output/session-chunk-indexer-migration.sql`) alkalmazva egy valódi
      Postgres instance-en, a meglévő `session-postgres-schema.sql` UTÁN, hiba nélkül,
      kimenet idézve
- [ ] chunking-stratégia definiálva és indokolva (determinisztikus, NEM AI/LLM-alapú)
- [ ] worker függvény/modul létezik, fájl:sor hivatkozással
- [ ] a választott embedding modell neve + TÉNYLEGES (lekérdezett, nem feltételezett)
      dimenziója dokumentálva, és ha eltér 1536-tól, a migráció ezt kezeli, indoklással
- [ ] end-to-end teszt (turn → outbox(index_turn) → worker → chunks/chunk_fts/
      chunk_embeddings sorok → outbox done) lefuttatva, kimenet idézve
- [ ] hibakezelés teszt (nem létező turn_id) lefuttatva, kimenet idézve
- [ ] többszörös chunk-keletkezés tesztelve (hosszú content → 2+ chunk, helyes `chunk_seq`)
- [ ] embedding-dimenzió teszt (`vector_dims(embedding)` vagy ekvivalens) lefuttatva,
      kimenet idézve
- [ ] reachability `grep -rn` eredmény idézve, `scaffold`/`proven` megkülönböztetve
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a worker fájl létezése nem bizonyítja, hogy tényleg chunkol/indexel — csak a tényleges,
  idézett end-to-end teszt-futtatás
- mock-olt `chunk_fts`/`chunk_embeddings` sorok ≠ működő indexer bizonyítéka
- embedding generálás külső LLM/HTTP API-val (OpenAI, Anthropic, stb.) — TILOS, csak lokális
  modell (pl. `sentence-transformers`, már a `requirements.in`-ben)
- AI/LLM-döntés a chunk-határokról — TILOS, csak determinisztikus szabály
- "1536 a placeholder, nem kell vele foglalkozni" ≠ elfogadható — a séma kommentje explicit
  ezt a jobot nevezi meg a dimenzió-döntés felelőjének, ezt a döntést meg kell hozni és
  dokumentálni, akár 1536 marad (indokolva), akár változik

## Git instrukciók

Push a `feature/session-chunk-indexer-001` branch-re, a `cic-mcp-session` célrepóban.
Main-re az agent NEM pushol. A teszteléshez használt Docker konténert a munka végén állítsd
le és töröld.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/teszt-nevek angolul.
