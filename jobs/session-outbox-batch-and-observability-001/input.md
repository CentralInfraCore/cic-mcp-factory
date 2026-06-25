# Job: session-outbox-batch-and-observability-001

## Kontextus

A `turn_projector.py` és `chunk_indexer.py` `FOR UPDATE SKIP LOCKED`
selectjei (lásd `turn_projector.py:116-125`) JELENLEG NINCS `LIMIT`-elve —
egy worker EGY tranzakcióban zárolja az ÖSSZES `pending`/`failed` sort az
adott `job_type`-ra, ami nagy backlog esetén hosszú tranzakciót és egyetlen
worker számára teljes queue-monopóliumot jelent. A `session_jobs.outbox`
táblának MÁR VANNAK `locked_by`/`locked_at` oszlopai (lásd `output/session-
postgres-schema.sql:287-288`), de ezeket a `turn_projector.py:113`
EXPLICIT, dokumentált módon NEM tölti ki ("input.md scopes out").

**FONTOS, mit ez a job NEM csinál**: az `attempts`/`max_attempts`/
`dead_letter` retry-mechanizmus MÁR implementálva és tesztelve van
(`turn_projector.py:235-246`, `_mark_failed_or_dead_letter()`) — ez a job
EZT NEM nyúlja, NEM épít új claim/locking alrendszert. A hatókör SZŰK:
(1) `LIMIT` hozzáadása a select-ekhez, (2) egy `statement_timeout`
biztonsági háló, (3) a MÁR LÉTEZŐ `locked_by`/`locked_at` oszlopok
TÉNYLEGES kitöltése megfigyelhetőségi célból, (4) egy metrika-lekérdezés
(pending-darabszám, legöregebb pending kor, dead_letter-darabszám,
attempts-hisztogram).

## Target

- target repo: `cic-mcp-session`
- target path: `session_store/turn_projector.py` és `session_store/
  chunk_indexer.py` módosítása + egy metrika-view/lekérdező modul + a
  hozzá tartozó teszt + `output/session-outbox-batch-and-observability.md`
- change_type: `fix`
- status_after_merge: `candidate`
- status indoklás: valós Postgres teszt bizonyítja MIND a batch-limitet,
  MIND a `locked_by`/`locked_at` kitöltését, MIND a metrika-lekérdezést

## Sources

- **KÖTELEZŐ elsődleges forrás:**
  - `session_store/turn_projector.py` — TELJES fájl, KÜLÖNÖSEN a
    `_claim_pending_jobs()` (vagy ekvivalens, 106-126. sor körül) és a
    `_mark_failed_or_dead_letter()` (235-246. sor) — az UTÓBBIT NEM kell
    módosítani, csak megérteni hogy mi MÁR működik
  - `session_store/chunk_indexer.py` — az analóg `FOR UPDATE SKIP LOCKED`
    select (373-375. sor körül)
  - `output/session-postgres-schema.sql` — `session_jobs.outbox` TELJES
    schema (270-292. sor körül), KÜLÖNÖSEN a `locked_by`/`locked_at`
    oszlopok

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. Pre-change állapot megerősítése

```
grep -rn "LIMIT\|locked_by\|locked_at" --include="*.py" session_store/ | grep -v test_
```

Idézd a kimenetet — bizonyítsd, hogy JELENLEG nincs `LIMIT` a select-eken
ÉS hogy `locked_by`/`locked_at` SEHOL nincs írva (csak a schema-ban
léteznek, kódban nem).

### 2. Batch `LIMIT`

Adj hozzá egy konfigurálható `LIMIT`-et (pl. `batch_size: int = 100`
paraméter) MINDKÉT select-hez. Valós Postgres teszttel bizonyítsd, hogy
egy 250 soros pending-backlog esetén egy hívás CSAK `batch_size` sort zár
és dolgoz fel.

### 3. `statement_timeout` biztonsági háló

Állíts be egy `statement_timeout`-ot a claim-tranzakcióra (a session/
connection szintjén), hogy egy elakadt feldolgozás ne tarthassa a sorokat
zárolva a végtelenségig. Indokold a választott időkorlátot.

### 4. `locked_by`/`locked_at` kitöltése

Töltsd ki ezeket a MEGLÉVŐ oszlopokat a claim pillanatában (worker-azonosító
+ timestamp), és töröld/null-ozd a feldolgozás befejezésekor (done/failed/
dead_letter állapotba kerüléskor). Valós teszttel bizonyítsd.

### 5. Metrika-lekérdezés

Implementálj egy lekérdező függvényt/view-t, ami egy hívásra visszaadja:
`pending_count`, `oldest_pending_age_seconds`, `dead_letter_count`,
`attempts_histogram` (pl. `{0: N, 1: M, ...}`). Valós Postgres teszttel,
egy ISMERT állapotú fixture-ön (előre beállított pending/failed/
dead_letter sorokkal) bizonyítsd a pontos visszaadott értékeket.

## Nem cél

- az `attempts`/`max_attempts`/`dead_letter` retry-logika módosítása (MÁR
  helyes és tesztelt, nem ennek a jobnak a hatóköre)
- egy külön, hosszú életű monitoring-daemon/process építése — a
  metrika-lekérdezésnek igény szerint, egyszeri hívásra kell működnie
- a `session-schema-migration-tooling-001` hatóköre (ez a job KÖZVETLENÜL
  módosíthatja a kódot, a migrációs-keretrendszer KÜLÖN job)

## Required Output Files

- `output/session-outbox-batch-and-observability.md`
- a módosított `turn_projector.py` és `chunk_indexer.py`
- a metrika-lekérdező modul
- a hozzá tartozó teszt-fájl

## Required Report Sections

```markdown
# session-outbox-batch-and-observability-001 Output

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

Elfogadott `Status` értékek: `proven`, `partial`, `scaffold`, `concept`,
`missing`, `rejected`, `unknown`.

## Definition Of Done

- [ ] pre-change `LIMIT`-hiány és `locked_by`/`locked_at`-hiány grep-pel
      bizonyítva
- [ ] batch `LIMIT` valós teszttel bizonyítva (250 sor → csak batch_size
      zárolva/feldolgozva)
- [ ] `statement_timeout` beállítva, indokolva
- [ ] `locked_by`/`locked_at` ténylegesen kitöltve claim-nél, törölve
      befejezésnél, valós teszttel bizonyítva
- [ ] metrika-lekérdezés pontos értékeket ad ismert fixture-ön, valós
      teszttel bizonyítva
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a `LIMIT`/`locked_by` kód léte ≠ implemented — a futtatott Postgres
  teszt kimenete bizonyít, a kód megírása nem; a claim-evidence táblában
  minden állítást a tényleges select/update file:line hivatkozásával kell
  alátámasztani
- az `attempts`/`max_attempts`/`dead_letter` retry-logika módosítása vagy
  újraírása
- egy külön, hosszú életű daemon-process bevezetése a metrikákhoz
- "kitöltve" állítás `locked_by`/`locked_at`-re valós teszt nélkül

## Git instrukciók

Push a `feature/session-outbox-batch-and-observability-001` branch-re,
KIZÁRÓLAG a `cic-mcp-session` célrepóban (a `cic-mcp-factory` saját
klónjában NEM kell pusholni, elég a lokális commit). Main-re az agent NEM
pushol. **NE módosítsd a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek/kód angolul.
