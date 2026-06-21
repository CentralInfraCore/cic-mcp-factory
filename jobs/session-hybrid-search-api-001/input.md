# Job: session-hybrid-search-api-001

## Kontextus

Két retrieval-függvény már létezik és mergelve:
- `session_api.search_context()` — FTS, `'simple'`-konfiguráció, `ts_rank` — csak EGZAKT
  szótöveket talál meg (a `session-retrieval-quality-001` job javította a korábbi
  `'english'`-stemming hibát, de a `'simple'` konfiguráció ÁRA, hogy szemantikailag
  releváns, de eltérő szóalakot/szinonimát használó szöveget NEM talál meg)
- `session_api.search_context_vector()` — cosine-similarity a `chunk_embeddings`-en —
  szemantikailag releváns szöveget megtalál EGZAKT szóegyezés nélkül is, de nincs
  kulcsszó-pontossága (egy ritka, specifikus terminus/azonosító egzakt egyezését a vektor
  oldal nem garantálja kiemelni)

A két módszernek EGYMÁST KIEGÉSZÍTŐ vakfoltja van. Ez a job megírja az ELSŐ
`session_api` függvényt, ami a kettőt KOMBINÁLJA egy rangsorba.

**A kombinálás technikai nehézsége, amit a jobnak fel kell oldania**: a `ts_rank()`
(FTS) és a cosine similarity (vektor) NEM egy skálán mozognak — egy naív súlyozott összeg
(`0.5 * ts_rank + 0.5 * similarity`) félrevezető lenne, mert a két érték eloszlása
összemérhetetlen. Egy elfogadott megoldás a **Reciprocal Rank Fusion (RRF)**: mindkét
módszer SAJÁT rangsorát (1., 2., 3., ...) veszi, és `1/(k + rank)` alapján összegez —
ez nem igényli a pontszámok skála-egyeztetését, csak a sorrendet használja. Döntsd el
(RRF vagy egy másik, általad indokolt megoldás), és EXPLICIT indokold a skála-eltérés
problémájának kezelését — ezt NEM hagyhatod figyelmen kívül.

## Target

- target repo: `cic-mcp-session`
- target path: a migráció egy ÚJ SQL fájlban (pl.
  `output/session-hybrid-search-api-migration.sql`), additív, NEM a meglévő fájlok
  felülírása; ha Python helper is szükséges (pl. a két al-lekérdezés eredményének
  Python-oldali fúziójához, ha a választott módszer nem tisztán SQL-ben oldható meg),
  az agent válassza meg a helyét, konzisztensen `session_store/vector_search.py`
  elhelyezésével
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: az első fúziós retrieval-kód, egy KONSTRUÁLT (nem valós-méretű)
  fixture-rel bizonyítva — `candidate`-hez kellene egy valós-méretű kiértékelés és a
  fúziós súlyok/paraméterek hangolása

## Sources

- `${WORKDIR}/.cic-context/factory-docs/job-slices.yaml` — `session-hybrid-search-api-001`
  bejegyzés — NORMATÍV
- **KÖTELEZŐ elsődleges forrás (mind már a `cic-mcp-session` `main`-en van):**
  - `cic-mcp-session/output/session-retrieval-quality-migration.sql` — a `search_context()`
    JAVÍTOTT (`'simple'`-konfigurációs) definíciója — EZT a query-kifejezést használd a
    hibrid függvény FTS-oldalán, NE írd újra
  - `cic-mcp-session/output/session-vector-search-api-migration.sql` — a
    `search_context_vector()` definíciója — EZT a query-kifejezést használd a hibrid
    függvény vektor-oldalán, NE írd újra
  - `cic-mcp-session/session_store/vector_search.py` — `embed_query()`,
    `to_pgvector_literal()` — ÚJRAHASZNÁLD a query-embedding generáláshoz
  - `cic-mcp-session/tests/test_session_store/test_vector_search.py` és
    `test_session_api.py` — a meglévő valódi-láncon-átmenő fixture minták, amit kövess

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti KÖTELEZŐ forrásokat, MIELŐTT bármilyen kódot írnál

## Feladat

### 1. Valódi Postgres teszt-instance + teljes lánc alkalmazása

Indíts egy valódi Postgres instance-t (`pgvector/pgvector:pg16`, lokálisan cache-elve), és
alkalmazd EGYMÁS UTÁN: `session-postgres-schema.sql`, `session-chunk-indexer-migration.sql`,
`session-retrieval-quality-migration.sql`, `session-vector-search-api-migration.sql`, majd
az ÚJ migrációdat. **Egyfordulós végrehajtási fegyelem**: fejezd be a teljes munkát
egyetlen menetben.

### 2. Fúziós stratégia (döntsd el és indokold)

Válassz egy fúziós módszert (RRF ajánlott, de más is elfogadható, ha indokolod), ami
KEZELI a `ts_rank`/cosine-similarity skála-eltérés problémáját. Dokumentáld a "Decisions
Proposed"-ben, MIÉRT ez védhető (és mit vetettél el — pl. naív súlyozott összeg, miért nem
volt jó).

### 3. Additív SQL függvény (vagy SQL+Python, ha a fúzió ezt igényli)

Írj egy `session_api` függvényt (pl. `search_context_hybrid`), ami:
- paraméterei: `p_session_id UUID`, `p_query TEXT`, `p_query_embedding VECTOR(384)`,
  `p_limit INTEGER DEFAULT 20`
- belül FUT mindkét meglévő keresési kifejezést (a `search_context()` FTS-kifejezését ÉS
  a `search_context_vector()` vektor-kifejezését, NEM újraírva azokat), majd a választott
  fúziós módszerrel egyetlen rangsorba kombinálja
- visszaadja: `chunk_id`, `turn_id`, `text`, `fused_score` (vagy hasonló elnevezés)

### 4. Háromchunkos teszt-fixture a VALÓDI láncon keresztül

Hozz létre egy fixture-t (insert_envelope → turn_projector → chunk_indexer), amiben:
- **Chunk A (csak lexikailag releváns)**: tartalmazza a teszt-query egzakt szavát/kifejezését,
  de a query témájához szemantikailag NEM kapcsolódó kontextusban (pl. ha a query
  "adatbázis index", legyen egy chunk, ami az "index" szót egy könyv tárgymutatójának
  kontextusában használja, nem adatbázis-kontextusban)
- **Chunk B (csak szemantikailag releváns)**: a query témájáról szól, de NEM tartalmazza a
  query egzakt szavait (pl. a "lekérdezések gyorsítását" írja le, "index" szó nélkül)
- **Chunk C (irreleváns kontroll)**: semelyik szempontból nem kapcsolódik a query-hez

### 5. Bizonyítás: a három függvény ELTÉRŐ eredményt ad, a hibrid mindkettőt felszínre hozza

- `search_context()` (csak FTS) a query-re → bizonyítsd, hogy Chunk A-t megtalálja, de
  Chunk B-t NEM (vagy Chunk B alacsonyabban rangsorolva, mint A)
- `search_context_vector()` (csak vektor) a query-re → bizonyítsd, hogy Chunk B-t magasan
  rangsorolja, Chunk A-t NEM feltétlenül (vagy alacsonyabban)
- `search_context_hybrid()` a query-re → bizonyítsd, hogy MIND Chunk A, MIND Chunk B
  magasabban rangsorolt, mint Chunk C — a fúzió tényleg mindkét szignált hasznosítja
- mindhárom függvény TÉNYLEGES kimenetét idézd a reportban, EGYMÁS MELLETT, hogy a
  rangsor-eltérés látható legyen

### 6. Reachability ellenőrzés (kötelező)

Ha Python helper is készült: `grep -rn "<helper_function_name>" --include="*.py" . | grep
-v "test_" | grep -v "/tests/"`, `file:line` hivatkozással. A SQL függvény oldalát a
`session_api.*` minta szerint `file:line`-nal dokumentáld.

## Nem cél

- a fúziós paraméterek (pl. RRF `k` konstans) valós session-adaton végzett hangolása
- `session_idx.ranking_features` feltöltése/használata
- az MCP szerver átírása, hogy ezt a függvényt hívja
- permanens futtatási infrastruktúra
- `session_core.source_refs` feltöltése

## Required Output Files

- `output/session-hybrid-search-api-report.md`
- `output/session-hybrid-search-api-migration.sql`

## Required Report Sections

```markdown
# session-hybrid-search-api-001 Output

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
`proven` KIZÁRÓLAG akkor használható, ha a tényleges SQL-függvény-hívás kimenete idézve
van — valódi Postgres ellen. A függvény léte a migrációs fájlban ≠ működik — csak a
tényleges futtatás bizonyít.

## Definition Of Done

- [ ] fúziós stratégia kiválasztva és indokolva, a skála-eltérés problémája EXPLICIT kezelve
- [ ] additív migráció alkalmazva, kimenet idézve
- [ ] háromchunkos (lexikai/szemantikai/irreleváns) fixture létrehozva a VALÓDI láncon
- [ ] `search_context()` kimenet idézve a teszt-query-re (Chunk A megtalálva, Chunk B nem
      vagy alacsonyabban)
- [ ] `search_context_vector()` kimenet idézve ugyanarra a query-re (Chunk B magasan, Chunk
      A nem feltétlenül)
- [ ] `search_context_hybrid()` kimenet idézve ugyanarra a query-re, bizonyítva hogy MIND
      A, MIND B magasabban van, mint C
- [ ] reachability dokumentálva (ha van Python helper), `file:line` hivatkozással
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- naív súlyozott összeg a skála-eltérés kezelése NÉLKÜL — a "Decisions Proposed"-ben
  EXPLICIT foglalkozni kell ezzel
- olyan fixture, ahol a hibrid eredmény ugyanaz lenne, mint bármelyik egyedi módszeré — a
  fixture-nek úgy kell megépülnie, hogy a két módszer TÉNYLEG eltérjen egymástól
- a `search_context()`/`search_context_vector()` lekérdezési logikájának újraírása a
  hibrid függvényben — ÚJRAHASZNÁLD a meglévő kifejezéseket
- csak azt bizonyítani, hogy a hibrid függvény hibátlanul fut — a RANGSOR-KÜLÖNBSÉGET kell
  bizonyítani a három függvény között

## Git instrukciók

Push a `feature/session-hybrid-search-api-001` branch-re, a `cic-mcp-session`
célrepóban. Main-re az agent NEM pushol. A teszteléshez használt Docker konténert a munka
végén állítsd le és töröld. **NE módosítsd a `meta.yaml` `status` mezőjét** sehol — ez
orchestrátor-feladat.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/teszt-nevek angolul.
