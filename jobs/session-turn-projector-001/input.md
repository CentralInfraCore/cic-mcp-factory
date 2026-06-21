# Job: session-turn-projector-001

## Kontextus

A `session-raw-event-store-001` job megírta a write-path-ot: `insert_envelope()` beír egy
`SessionIngressEnvelope`-ot a `session_raw.envelopes` táblába, és a tábla trigger-je
(`trg_session_raw_envelopes_enqueue`) automatikusan ír egy sort a `session_jobs.outbox`-ba
(`job_type='project_envelope'`). Eddig viszont SEMMI nem konzumálja ezt az outbox-ot — a
sorok örökre `pending` állapotban maradnak.

Ez a job megírja az ELSŐ outbox-worker-t: beolvassa a `pending`/`failed` `project_envelope`
job-okat, projektálja a hozzájuk tartozó `session_raw.envelopes` sort
`session_core.sessions`/`session_core.turns`-ba, és lezárja az outbox-sort
(`done`/`failed`/`dead_letter`).

**Fontos döntési pont, amit a jobnak fel kell oldania**: a `session_core.turns` táblának
van egy `role TEXT NOT NULL` mezője (pl. user/assistant/tool/system), de a
`SessionIngressEnvelope` schema NEM definiál `role` mezőt — csak `provider_event_name`-et
(pl. `PostToolUse`, `Stop`, opcionális). A workernek MECHANIKUS (nem AI/LLM-alapú) leképezést
kell készítenie `provider_event_name`/`source.kind` → `role` között, és ezt explicit
dokumentálnia kell a reportban — ez NEM szemantikus interpretáció (azt az ingress-szint
`interpreted: false` tiltja), hanem egy determinisztikus, kódban rögzített kategorizálás,
összhangban azzal hogy a `session_core` réteg "projektált, feldolgozott állapot" (lásd a
`session-postgres-storage-design-001` report "session_core projections are derived/
interpreted state, distinct from the ingress envelope's pinned interpreted=false").

## Target

- target repo: `cic-mcp-session`
- target path: az agent válassza meg a modul helyét (pl. `session_store/turn_projector.py`,
  konzisztensen az előző job `session_store/envelope_writer.py` elhelyezésével), és idézze a
  választott path-ot a reportban
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: ez az első worker, valódi end-to-end Postgres-teszttel, de egyetlen
  worker-instance feltételezéssel fut (nincs konkurens lock-olás/claim-mechanizmus) —
  `candidate`-hez kellene egy multi-worker konkurencia-teszt és/vagy egy permanens
  futtatási mechanizmus (cron/supervisor), amit ez a job explicit NEM ad

## Sources

- `${WORKDIR}/.cic-context/factory-docs/job-slices.yaml` — `session-turn-projector-001`
  bejegyzés (phase 3, acceptance_gates, required_evidence, forbidden_shortcuts) — NORMATÍV
- `${WORKDIR}/.cic-context/factory-docs/architecture.md` — "## Schema szeparacio" szekció
- **KÖTELEZŐ elsődleges forrás (mindkettő már a `cic-mcp-session` `main`-en van):**
  - `cic-mcp-session/output/session-postgres-schema.sql` — a `session_jobs.outbox`,
    `session_core.sessions`, `session_core.turns` táblák pontos DDL-je
  - `cic-mcp-session/session_store/envelope_writer.py` — a write-path, amit a teszt
    fixture-ödnek kell hívnia envelope-ok beszúrásához (NE írj új insert-kódot az
    envelope-okhoz, használd a meglévő `insert_envelope()`-ot)

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a `session-postgres-schema.sql` `session_jobs.outbox`,
   `session_core.sessions`, `session_core.turns` tábla-definícióit, és a
   `session_store/envelope_writer.py`-t, MIELŐTT bármilyen kódot írnál

## Feladat

### 1. Valódi Postgres teszt-instance

Indíts egy valódi Postgres instance-t (`pgvector/pgvector:pg16`, lokálisan cache-elve, lásd
az előző jobok mintáját) Docker-rel, és alkalmazd a `session-postgres-schema.sql`-t.
**Egyfordulós végrehajtási fegyelem**: ez egy gyors konténer-indítás, fejezd be a teljes
munkát ebben az egyetlen menetben, ne próbálj semmit "később visszanézni".

### 2. role-leképezés (döntsd el és dokumentáld)

Készíts egy determinisztikus, kódban rögzített leképezést `provider_event_name`/
`source.kind` → `role` között (pl. `PostToolUse`/`PostToolUseFailure` → `tool`, `Stop` →
`assistant`, `source.kind == "manual"` → `manual`, minden más → `event` vagy hasonló
fallback). Indokold a választást a "Decisions Proposed" szekcióban. Ez NEM lehet
LLM/AI-hívás — egy egyszerű, tesztelhető if/dict-lookup elegendő és KÖTELEZŐ.

### 3. Worker implementáció

Írj egy Python függvényt/modult, ami egy futtatásban:
- beolvassa a `session_jobs.outbox` `pending`/`failed` (`job_type='project_envelope'`)
  sorait
- minden sorhoz: beolvassa a hozzá tartozó `session_raw.envelopes` sort (`source_id`
  alapján)
- upsert-eli a `session_core.sessions` sort (`provider`+`provider_session_id` alapján,
  `ON CONFLICT ... DO UPDATE SET last_seen_at = ...`)
- beszúr egy `session_core.turns` sort (`turn_seq` = az adott session-höz tartozó
  legnagyobb `turn_seq` + 1, tranzakción belül kiszámolva, hogy elkerüld a race-t — egyetlen
  worker-instance feltételezéssel ez elég, dokumentáld a limitációt)
- siker esetén az outbox sort `done`-ra állítja
- hiba esetén `attempts`-et növeli, `last_error`-t kitölti, `failed`-re állítja, vagy
  `dead_letter`-re ha `attempts >= max_attempts`

### 4. Hibakezelés teszt

Hozz létre egy outbox sort, ami egy NEM LÉTEZŐ `source_id`-ra hivatkozik (pl. törölt vagy
soha nem létezett envelope) — a workernek ezt `failed`/`dead_letter`-re kell állítania, NEM
szabad kivételt dobnia kezeletlenül, és NEM szabad örökre `pending`-en hagynia.

### 5. Tesztek — end-to-end, VALÓDI Postgres ellen

Írj pytest teszteket, amik a VALÓDI Postgres konténer ellen futnak (nem mock-olt
kapcsolattal), és a TELJES láncot lefedik:
- `insert_envelope()` hívása (a meglévő write-path-ból) → trigger létrehoz egy outbox sort
  → worker futtatása → `session_core.sessions`/`session_core.turns` sorok ellenőrzése →
  outbox sor `done` állapotának ellenőrzése
- a hibakezelés teszt (4. pont)
- legalább egy teszt, ami 2 envelope-ot ír be UGYANAHHOZ a session-höz, és ellenőrzi hogy a
  `turn_seq` helyesen 1, 2 (nem ütközik, nem ugrik)

### 6. Reachability ellenőrzés (kötelező)

```bash
grep -rn "<worker_function_name>" --include="*.py" . | grep -v "test_" | grep -v "/tests/"
```

Ha 0 production hívás (csak a saját tesztjei hívják), jelöld `scaffold`-ként a "production
reachability" claim-re a reportban — ugyanúgy, mint az előző job tette az
`insert_envelope()`-pal. Ha van dokumentált, futtatható CLI belépési pont (pl. `python -m
session_store.turn_projector`), ezt különítsd el: a CLI létezése/dokumentáltsága lehet
`proven` ("hívható, dokumentált paranccsal"), de a "valaki/valami tényleg rendszeresen
futtatja production-ben" külön, `missing`/`scaffold` állítás legyen — ne keverd össze a
kettőt.

## Nem cél

- embedding-generálás vagy `session_idx.*` feltöltése (külön job:
  `session-chunk-indexer-001`)
- `session_core.chunks`/`source_refs`/`manifests` táblák feltöltése (ez a job csak
  `sessions`+`turns`-ig megy)
- konkurens, multi-worker-instance lock-olás/claim-mechanizmus
- permanens futtatási infrastruktúra (cron/supervisor/systemd timer)
- `mcp-server/server.py` átírása, hogy bármit innen olvasson

## Required Output Files

- `output/session-turn-projector-report.md`

## Required Report Sections

A report MUST kövesse az `.cic-context/factory-docs/acceptance-contract.md`
"Universal Output Contract" szakaszát:

```markdown
# session-turn-projector-001 Output

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
`unknown`. `proven` KIZÁRÓLAG akkor használható, ha a tényleges, end-to-end teszt-futtatás
kimenete idézve van — valódi Postgres ellen.

## Definition Of Done

- [ ] role-leképezés definiálva és indokolva (determinisztikus, NEM AI/LLM-alapú)
- [ ] worker függvény/modul létezik, fájl:sor hivatkozással
- [ ] end-to-end teszt (insert_envelope → outbox → worker → session_core sorok → outbox
      done) lefuttatva, kimenet idézve
- [ ] hibakezelés teszt (nem létező source_id) lefuttatva, kimenet idézve, bizonyítva hogy
      nincs kezeletlen kivétel és nincs örökre pending sor
- [ ] turn_seq helyes inkrementálás tesztelve 2+ envelope-ra ugyanazon session-höz
- [ ] reachability `grep -rn` eredmény idézve, production hívási lánc állapota explicit
      `proven`/`scaffold`-ként jelölve (a CLI-dokumentáltság és a "valaki tényleg futtatja"
      külön állításként, nem összemosva)
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a worker fájl létezése nem bizonyítja, hogy tényleg projektál — csak a tényleges,
  idézett end-to-end teszt-futtatás
- mock-olt outbox/session_raw sorok ≠ működő projekció bizonyítéka — VALÓDI Postgres ellen
  futtatott teszt kell
- a worker külső LLM/HTTP-t hív a role-leképezéshez vagy bármilyen feldolgozáshoz — TILOS,
  csak determinisztikus, kódban rögzített logika
- "a trigger/outbox mechanizmus már bizonyított az előző jobban, nem kell újra tesztelni" ≠
  elfogadható — ennek a jobnak A VÉGIG, a tényleges worker-fogyasztással kell bizonyítania a
  láncot, nem csak hivatkozni a korábbi jobra

## Git instrukciók

Push a `feature/session-turn-projector-001` branch-re, a `cic-mcp-session` célrepóban.
Main-re az agent NEM pushol. A teszteléshez használt Docker konténert a munka végén állítsd
le és töröld, hogy ne maradjon árva erőforrás.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/teszt-nevek angolul.
