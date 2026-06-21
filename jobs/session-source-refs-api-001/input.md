# Job: session-source-refs-api-001

## Kontextus

A `session-source-refs-extractor-001` job feltöltötte a `session_core.source_refs`
táblát (provenance-referenciák: `tool_call`, `file`, `url`), de eddig SEMMI nem
olvassa — nincs `session_api` függvény, ami lekérdezné. Az architektúra szabálya
(`architecture.md`: "Az MCP szerver ne táblákat turkáljon. Stabil API függvényeket
hívjon") megköveteli, hogy ez is egy `session_api.*` STABLE SQL függvényen keresztül
legyen elérhető, NEM direkt tábla-hozzáféréssel.

Ez a job megírja az ELSŐ `session_api` függvényt, ami a `source_refs` táblát olvassa.

## Target

- target repo: `cic-mcp-session`
- target path: a migráció egy ÚJ SQL fájlban (pl.
  `output/session-source-refs-api-migration.sql`), additív, NEM a meglévő fájlok
  felülírása
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: az első olvasó-függvény egy konstruált fixture-rel bizonyítva —
  `candidate`-hez kellene valós, nagyobb session-adaton végzett kiértékelés

## Sources

- `${WORKDIR}/.cic-context/factory-docs/job-slices.yaml` — `session-source-refs-api-001`
  bejegyzés — NORMATÍV
- **KÖTELEZŐ elsődleges forrás (mind már a `cic-mcp-session` `main`-en van):**
  - `cic-mcp-session/output/session-postgres-schema.sql` — `session_core.source_refs`
    DDL, és a MEGLÉVŐ `session_api.*` 4 függvény (`search_context`, `get_timeline`,
    `get_context_pack`, `session_status`) STÍLUSMINTÁJA — KÖVESD ugyanazt a mintát
    (paraméterezés, `STABLE SQL`, visszatérési tábla-alak)
  - `cic-mcp-session/session_store/chunk_indexer.py` — `extract_source_refs()` (a
    `ref_kind` lehetséges értékei: `tool_call`, `file`, `url`)
  - `cic-mcp-session/tests/test_session_store/test_chunk_indexer.py` — a meglévő
    4-eseti `source_refs` teszt-fixture minta (Eset A/B/C/D), amit kövess

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti KÖTELEZŐ forrásokat, MIELŐTT bármilyen kódot írnál

## Feladat

### 1. Valódi Postgres teszt-instance + teljes lánc alkalmazása

Indíts egy valódi Postgres instance-t (`pgvector/pgvector:pg16`, lokálisan cache-elve), és
alkalmazd EGYMÁS UTÁN az összes meglévő SQL fájlt (mind az 5: schema + 4 migráció), majd
az ÚJ migrációdat. **Egyfordulós végrehajtási fegyelem**: fejezd be a teljes munkát
egyetlen menetben.

### 2. Additív SQL függvény

Írj egy `session_api` függvényt (pl. `get_source_refs`), ami:
- paraméterei: `p_session_id UUID`, `p_ref_kind TEXT DEFAULT NULL` (NULL = minden kind),
  `p_limit INTEGER DEFAULT 100`
- a `session_core.source_refs`-t a `session_core.chunks`-on keresztül `p_session_id`-ra
  szűri (a `source_refs` táblának nincs direkt `session_id` oszlopa, a `chunk_id` FK-n
  keresztül kell eljutni a session-höz)
- ha `p_ref_kind` NEM NULL, csak az adott `ref_kind`-ú sorokat adja vissza
- visszaadja: `source_ref_id`, `chunk_id`, `turn_id`, `ref_kind`, `ref_value`,
  `content_hash`

### 3. Két-session-es teszt-fixture a VALÓDI láncon keresztül

Hozz létre KÉT különböző session-t a VALÓDI `insert_envelope()` lánccal:
- **Session 1**: mind a 3 ref_kind-ot tartalmazza (tool_call, file, url) — kövesd a
  `session-source-refs-extractor-001` 4-eseti fixture mintáját (Eset A/B/C), Eset D
  (kontroll, semmi kinyerhető) NEM kell hozzá kötelezően
- **Session 2**: legalább 1, Session 1-től ELTÉRŐ `ref_value`-jú referenciát tartalmaz
  (pl. egy másik fájlútvonal) — ez bizonyítja a session-scoping helyességét

### 4. Bizonyítás: NULL-filter, kind-filter, session-scoping

- `get_source_refs(session1_id, NULL)` → bizonyítsd, hogy MIND a 3 ref_kind sora
  visszajön Session 1-re, és Session 2 sora NEM jön vissza
- `get_source_refs(session1_id, 'file')` → bizonyítsd, hogy CSAK a `file` kind sora jön
  vissza
- `get_source_refs(session2_id, NULL)` → bizonyítsd, hogy CSAK Session 2 sora jön
  vissza, Session 1 sorai NEM

### 5. Regresszió-ellenőrzés

Futtasd le a TELJES meglévő `tests/test_session_store/` suite-ot, bizonyítva hogy a
`chunk_indexer`/`turn_projector`/`worker_loop`/`session_api`/`vector_search`/
`hybrid_search` tesztek NEM regresszáltak.

## Nem cél

- az MCP szerver átírása, hogy ezt a függvényt hívja
- recall-/pontosság-mérés valós session-adaton
- `session_idx.ranking_features` feltöltése
- a `search_context()`/`search_context_hybrid()` bővítése, hogy `source_refs`-et is
  visszaadjon (külön, jövőbeli döntés, ha egyáltalán szükséges)

## Required Output Files

- `output/session-source-refs-api-report.md`
- `output/session-source-refs-api-migration.sql`

## Required Report Sections

```markdown
# session-source-refs-api-001 Output

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

- [ ] additív migráció alkalmazva, kimenet idézve
- [ ] `get_source_refs()` létezik, a meglévő `session_api.*` stílusmintát követi,
      fájl:sor hivatkozással
- [ ] két-session-es fixture létrehozva a VALÓDI láncon
- [ ] NULL-filter eset bizonyítva (mind a 3 kind, Session 2 kizárva), kimenet idézve
- [ ] specifikus kind-filter eset bizonyítva, kimenet idézve
- [ ] session-scoping eset bizonyítva (Session 2 lekérdezése nem látja Session 1 sorait),
      kimenet idézve
- [ ] teljes meglévő teszt-suite lefuttatva, regresszió-mentesség bizonyítva
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- session_id-szűrés NÉLKÜLI függvény — ez cross-session provenance-adat szivárgást
  okozna, TILOS
- csak azt bizonyítani, hogy a függvény hibátlanul fut — a kind-filter ÉS a
  session-scoping mindkettőt KONKRÉT, idézett SQL-eredménnyel kell bizonyítani
- az MCP szerver vagy bármilyen más kód direkt `session_core.source_refs`
  tábla-hozzáférése a függvény megkerülésével

## Git instrukciók

Push a `feature/session-source-refs-api-001` branch-re, KIZÁRÓLAG a `cic-mcp-session`
célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni, elég a lokális
commit). Main-re az agent NEM pushol. A teszteléshez használt Docker konténert a munka
végén állítsd le és töröld. **NE módosítsd a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/teszt-nevek angolul.
