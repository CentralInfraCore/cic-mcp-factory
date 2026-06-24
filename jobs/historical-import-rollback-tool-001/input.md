# Job: historical-import-rollback-tool-001

## Kontextus

A `historical-import-runner-001` (mergelve) megépítette a tényleges batch-importer-t,
amely egy szintetikus multi-shard bundle-t valós Postgres ellen importál, és
bizonyítottan biztonságosan resume-olható kill-mid-run után. Mielőtt EGY VALÓS,
SZEMÉLYES export-bundle elleni futtatás egyáltalán megfontolásra kerülne (külön,
dedikált biztonsági megbeszélés tárgya, NEM ez a job), szükség van egy célzott
ESZKÖZRE, amely egy ADOTT, már beimportált beszélgetést (és KIZÁRÓLAG azt) vissza
tud vonni — anélkül, hogy a teljes táblát ki kellene üríteni.

**A mechanizmus MÁR LÉTEZIK schema-szinten, kódváltoztatás nélkül**: minden ChatGPT
beszélgetés egy `session_core.sessions` sorra képződik le (`provider =
'chatgpt-export'`, `provider_session_id = conversation_id`,
`sessions_provider_session_unique UNIQUE (provider, provider_session_id)`,
`output/session-postgres-schema.sql`). A `session_core.turns`/`chunks`/
`source_refs`/`manifests` és a `session_idx.chunk_fts`/`chunk_embeddings`/
`ranking_features` mind `ON DELETE CASCADE`-del hivatkoznak `session_id`-re — egy
session törlése MINDEZT eltávolítja. EGYETLEN kivétel: a `session_raw.envelopes`
tábla NINCS FOREIGN KEY-jel a sessions táblához (a raw event store független a
projection-tól) — ezt KÜLÖN, `(provider, provider_session_id)` alapján kell törölni.

**KRITIKUS HATÁR**: ez a job KIZÁRÓLAG egy SCOPED, egy-beszélgetésre korlátozott
törlő-eszközt épít. NEM cél egy teljes-tábla `TRUNCATE` wrapper, és NEM cél a valós
export-bundle elleni futtatás (az egy KÜLÖN, ez a job után következő döntés).

## Target

- target repo: `cic-mcp-session`
- target path: `output/historical-import-rollback-tool.md` + egy ÚJ
  `session_store/rollback.py` modul + a hozzá tartozó teszt
- change_type: `new_capability`
- status_after_merge: `candidate`
- status indoklás: TÉNYLEGES, futtatható kód + valós Postgres-teszt, amely
  bizonyítja a SCOPED törlést (egy beszélgetés eltávolítva, egy MÁSIK érintetlen)

## Sources

- **KÖTELEZŐ elsődleges forrás (a `cic-mcp-factory` repo `main`-jén, MÁR ott van):**
  - `${WORKDIR}/jobs/index.yaml` — prerequisite-ellenőrzéshez `- id: "<job-id>"`
    kulccsal (NEM `job_id:`)
- **MÁSODIK forrás (a `cic-mcp-session` repo, a target, KLÓNOZVA):**
  - `output/session-postgres-schema.sql` — `session_core.sessions`
    (`sessions_provider_session_unique UNIQUE (provider, provider_session_id)`,
    kb. 137-151. sor), `session_core.turns`/`chunks`/`source_refs`/`manifests` ÉS
    `session_idx.chunk_fts`/`chunk_embeddings`/`ranking_features` `ON DELETE
    CASCADE` hivatkozásai `session_id`-re (kb. 155-230. sor) — EZ a teljes
    cascade-lánc, amit a törlésnek ki kell használnia, NEM kézzel
    újra-implementálnia minden egyes leszármazott táblára
  - `session_raw.envelopes` (kb. 48-77. sor) — NINCS FK a sessions táblához,
    `provider`/`provider_session_id` oszlopok KÜLÖN törlési feltételt igényelnek
  - `session_store/envelope_writer.py` — `SessionStoreConfig`/`SessionStoreConfig.
    from_env()` (kb. 74-89. sor) — EZT a konfigurációs mintát kell újrahasználni
    (NEM új connection-config osztály bevezetése)
  - `session_store/historical_import_runner.py` — a MEGLÉVŐ szintetikus bundle
    fixture-minta (`_write_synthetic_bundle` a teszt-fájlban) — EZT használd a
    teszteléshez, NEM egy új fixture-mintát feltalálni
  - `tests/test_session_store/test_envelope_writer.py` — `pg_config`/
    `_clean_envelopes_table`/`_count_rows` helper-ek — EZEKET a mintákat kell
    követni (real-Postgres teszt-stílus), NEM mockolt DB-kapcsolat

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. Prerequisite-ellenőrzés

```
grep -n '\- id: "historical-import-runner-001"' -A 3 jobs/index.yaml
```

Idézd a kimenetet, erősítsd meg `status: "done"`. Ha NEM, NO-GO és állj meg.

### 2. Cascade-lánc audit — grep + saját ellenőrzés

```
grep -rn "ON DELETE CASCADE" --include="*.sql" . | grep -v test_
```

Idézd a kimenetet. Erősítsd meg, melyik tábla hivatkozik `session_id`-re CASCADE-del,
és melyik (`session_raw.envelopes`) NEM — ez indokolja a két-lépéses törlést.

### 3. `rollback_conversation()` implementáció

Hozz létre `session_store/rollback.py`-t, egy függvénnyel, pl.
`rollback_conversation(provider: str, provider_session_id: str, *, config:
SessionStoreConfig | None = None) -> RollbackResult`, amely:
- EGY tranzakcióban (vagy két egymást követő, explicit lépésben — indokold a
  választást) törli:
  1. `DELETE FROM session_core.sessions WHERE provider = %s AND
     provider_session_id = %s` (a cascade gondoskodik turns/chunks/source_refs/
     manifests/chunk_fts/chunk_embeddings/ranking_features-ről)
  2. `DELETE FROM session_raw.envelopes WHERE provider = %s AND
     provider_session_id = %s` (külön, mert nincs FK)
- visszaadja, hány sor törlődött mindkét táblából (egy `RollbackResult`
  dataclass-ban, pl. `sessions_deleted: int`, `envelopes_deleted: int`)
- HA `provider`/`provider_session_id` nem létezik, nem hiba — `0`/`0` eredmény
  (idempotens, biztonságosan újra-hívható)

NE implementálj egy általános "törölj akármilyen feltétellel" API-t — a
függvény aláírása KIZÁRÓLAG `(provider, provider_session_id)` páros alapján
működjön, hogy strukturálisan kizárja a véletlen, scope nélküli törlést.

### 4. Valós, futtatott bizonyíték — scoped törlés

Importálj be LEGALÁBB 2 KÜLÖNBÖZŐ szintetikus beszélgetést (a MEGLÉVŐ
`historical_import_runner.run()`-t használva, a MEGLÉVŐ szintetikus
bundle-fixture mintán), valós Postgres ellen. Hívd meg `rollback_conversation()`-t
CSAK az egyikre, és bizonyítsd VALÓS psql-lekérdezéssel:
1. az érintett conversation MINDEN sora (sessions, turns, chunks, source_refs,
   manifests, chunk_fts, chunk_embeddings, ranking_features, envelopes) eltűnt
2. a MÁSIK, nem-célzott conversation MINDEN sora ÉRINTETLEN maradt

Idézd a TÉNYLEGES psql/pytest kimenetet mindkét bizonyításra.

## Nem cél

- a valós, személyes export-bundle elleni futtatás (külön, ezt a jobot KÖVETŐ
  biztonsági megbeszélés tárgya)
- egy teljes-tábla `TRUNCATE` wrapper vagy bármilyen scope nélküli törlő-eszköz
- a `historical_import_runner.py`/`chatgpt_import.py`/`envelope_writer.py` MEGLÉVŐ
  logikájának módosítása (ÉPÍTS rájuk, NE írd újra)
- CLI/operator-felület a rollback-hez (ha hasznosnak találod, javasolhatod a "Next
  Jobs"-ban, de NEM kötelező ebben a jobban)

## Required Output Files

- `output/historical-import-rollback-tool.md`
- `session_store/rollback.py`
- a hozzá tartozó teszt-fájl

## Required Report Sections

```markdown
# historical-import-rollback-tool-001 Output

## Scope
## Inputs Read
## Prerequisite Check
## Cascade Chain Audit
## rollback_conversation() Implementation
## Real Postgres Proof — Scoped Deletion (One Conversation, One Untouched)
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
`proven` egy "a rollback scoped, nem érinti a többi beszélgetést" állításra
KIZÁRÓLAG akkor használható, ha a TÉNYLEGES, futtatott teszt mindkét conversation
végállapotát (törölt ÉS érintetlen) külön-külön bizonyítja — a függvény leírása a
kódban nem bizonyítja, hogy helyesen fut.

## Definition Of Done

- [ ] a prerequisite `id:` kulccsal megerősítve, GO/NO-GO döntés indokolva
- [ ] a cascade-lánc file:line hivatkozással idézve, ÉS a `session_raw.envelopes`
      FK-nélküli kivétel explicit megnevezve
- [ ] `rollback_conversation()` KIZÁRÓLAG `(provider, provider_session_id)` alapján
      működik, file:line hivatkozással
- [ ] valós Postgres teszt: 2 conversation importálva, 1 rollback-elve, a TÖRÖLT
      conversation MINDEN táblájára ÉS az ÉRINTETLEN conversation MINDEN
      táblájára külön bizonyítva
- [ ] claim-evidence tábla kitöltve, nem üres
- [ ] a riport NEM állítja, hogy ez a job valós export-bundle-t importál vagy töröl

## Forbidden Shortcuts

- egy scope nélküli/feltétel nélküli törlő-funkció bevezetése
- csak a törölt VAGY csak az érintetlen conversation bizonyítása — MINDKETTŐ
  kötelező, ugyanabban a tesztben
- a meglévő cascade-lánc kézi, táblánkénti DELETE-ekkel való újra-implementálása
  (a `session_core.sessions` egy törlése elég a cascade-olt táblákhoz)
- a fájl/kód léte ≠ implemented (ez egyetlen soron) — a futtatott teszt kimenete
  bizonyít, a kód megírása nem

## Git instrukciók

Push a `feature/historical-import-rollback-tool-001` branch-re, KIZÁRÓLAG a
`cic-mcp-session` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell
pusholni, elég a lokális commit). Main-re az agent NEM pushol. **NE módosítsd a
`meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek/kód angolul.
