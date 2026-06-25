# Job: session-raw-retention-purge-001

## Kontextus

A `session-data-protection-001` job (prerequisite) megírta a
`session_raw.envelopes` réteg **retention policy**-jét
(`output/session-data-protection-retention-policy.md`), de **szándékosan NEM
implementálta a kikényszerítést** — a policy doc explicit "Next Jobs"
szekciója kimondja:

> "Egy KÖVETŐ job, amely a fenti 1-3. pontot TÉNYLEGESEN implementálja
> (ütemezett purge-job + `session_audit.raw_purges` audit-tábla) — ez a
> hiányzó láncszem, amiért [a data-protection] job `status_after_merge:
> experimental`, NEM `candidate`."

**Ez az a követő job.** A policy a következőt rögzíti normatívan:

1. Egy időalapú purge, ami a `session_raw.envelopes` sorokat **`occurred_at`**
   (NEM `ingested_at`) alapján törli, alapértelmezés szerint **90 nap** felett:
   ```sql
   DELETE FROM session_raw.envelopes WHERE occurred_at < now() - INTERVAL '90 days';
   ```
2. A purge MAGA is audit-sort ír egy (eddig NEM létező)
   `session_audit.raw_purges` táblába — "ki/mikor/hány sort purge-olt" — a
   törléssel **AZONOS tranzakcióban** (a `session_audit.raw_reads` mintáját
   követve: egy purge sosem maradhat audit nélkül, ha a tranzakció elhasal).
3. A purge a `rollback_conversation()` (`session_store/rollback.py:72`) MÁR
   létező, MANUÁLIS, (provider, provider_session_id)-kulcsú törlési primitívum
   MELLETT él, nem helyette — ezt a job **újrahasználja referenciaként, NEM
   implementálja újra**.

## A határ, amit ez a job TISZTEL

A policy doc 3. pontja egy "archívum/hideg tárolóba export" lépést **KÜLÖN
döntésként, hatókörön kívül** jelöl — ez a job NEM épít archiválást.

Továbbá: **egy tényleges systemd timer / cron telepítése hosting/operátor
döntés**, nem agent-feladat (lásd `session-ingest-hook-sandboxed-001` és
`session-worker-scheduler-deployment` precedensét: a futtatható entrypoint +
a séma elkészül és VALÓS teszttel bizonyított, de az ÜTEMEZŐ ÉLES TELEPÍTÉSE
külön emberi lépés). Innen a `status_after_merge: experimental`, NEM
`candidate`.

## Target

- target repo: `cic-mcp-session`
- target path:
  - `session_store/retention_purge.py` — a purge entrypoint (callable,
    NEM daemon): `purge_expired_raw_envelopes(...)`
  - egy additív migration a `session_audit.raw_purges` táblára (a
    `session-data-protection-migration.sql` / `session-schema-migration-
    tooling-001` mintáját követve)
  - `tests/test_session_store/` alá a valós (eldobható Postgres elleni) teszt
  - `output/session-raw-retention-purge.md` (report)
- change_type: `new_capability`
- status_after_merge: `experimental`

## Sources

- **KÖTELEZŐ elsődleges forrás (a cic-mcp-session klónban):**
  - `output/session-data-protection-retention-policy.md` — a NORMATÍV policy,
    amit ez a job kikényszerít (90 nap, `occurred_at`, `session_audit.
    raw_purges`, azonos tranzakció, `rollback_conversation()` mellette)
  - `output/session-data-protection-migration.sql` — a `session_audit.
    raw_reads` tábla alakja + a same-transaction audit minta, amire a
    `session_audit.raw_purges` modellezendő
  - `session_store/rollback.py` `rollback_conversation()` (csak referencia,
    NEM módosítandó)
  - `session_store/raw_read_audit.py` — a same-transaction audit-write minta,
    amit a purge audit-ja követ
  - `session_raw.envelopes` séma (`output/session-postgres-schema.sql`) — az
    `occurred_at` oszlop, amin a retention mérődik

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Ellenőrizd, hogy `session-data-protection-001` `done` állapotban van-e
   (`jobs/session-data-protection-001/meta.yaml` a cic-mcp-factory klónban,
   ÉS a `session_audit` séma + `raw_reads` migration jelen van-e a
   `cic-mcp-session` klónban) — ha NEM, állítsd a jobot **NO-GO**-ra és állj
   meg (a `session_audit` séma és a policy doc nélkül ez a job nem építhető)
3. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. A purge entrypoint (`session_store/retention_purge.py`)

Egy tiszta, hívható függvény (NEM daemon, NEM önindító loop):

```
purge_expired_raw_envelopes(
    conn,                       # élő DB-kapcsolat (a hívó adja, mint a worker_loop mintában)
    retention_days: int = 90,   # alapértelmezés a policy szerint; env-felülírható (lásd lent)
    purger: str = "...",        # ki/mi indította (szabad szöveg, mint raw_reads.reader)
    dry_run: bool = False,      # True esetén CSAK számol, NEM töröl
) -> <eredmény: rows_deleted, cutoff, ...>
```

Követelmények:
- A törlés feltétele **`occurred_at < now() - INTERVAL '<retention_days> days'`**
  — KIZÁRÓLAG `occurred_at`, SOHA `ingested_at` (a policy ezt nyomatékosítja).
- KIZÁRÓLAG a `session_raw.envelopes` táblát érinti. A `session_core.*`
  (turns/chunks) projektált réteg **NEM** esik e job hatókörébe — ne töröld.
- Az audit-sor beszúrása ÉS a `DELETE` **AZONOS tranzakcióban** fut, és az
  audit `rows_deleted` mezője a TÉNYLEGESEN törölt sorszámot tükrözi (pl.
  `DELETE ... RETURNING` / cursor.rowcount), nem egy előzetes becslést.
- `dry_run=True` esetén SEMMIT nem töröl és audit-sort SEM ír (vagy ha ír,
  egyértelműen dry-run-ként jelölve) — a számolt értéket adja vissza.
- A `retention_days` env-felülírható (pl. `SESSION_RAW_RETENTION_DAYS`,
  illeszkedve a `session-runtime-env-unification-001` env-konvencióhoz, ha az
  releváns); a default mindig 90.

#### Reachability / korrektség-ellenőrzés (grep)

A reportban idézd az alábbi parancsok `file:line` találatait, bizonyítva, hogy
a purge kódútja a HELYES oszlopot használja és a tiltott oszlopot SOHA:

```
# A purge a session_raw.envelopes-on occurred_at-et használ (van találat):
grep -rn "occurred_at" --include="*.py" session_store/retention_purge.py | grep -v test_

# A purge kódja SOHA nem hivatkozik ingested_at-re (NINCS találat = helyes):
grep -rn "ingested_at" --include="*.py" session_store/retention_purge.py | grep -v test_

# A purge NEM implementálja újra a conversation-törlést (rollback_conversation
# csak referencia/komment, nem hívott törlési logika a purge-ban):
grep -rn "rollback_conversation\|DELETE FROM session_core" --include="*.py" session_store/retention_purge.py | grep -v test_
```

A teszt-fájlokat a `grep -v test_` KIZÁRJA — a call-chain a futtatott kódra
vonatkozik, nem a teszt-fixture-ökre.

### 2. A `session_audit.raw_purges` migration

Additív migration (a meglévő `session_audit` sémába), a `raw_reads` tábla
mintáját követve. Javasolt oszlopok (igazítsd a `raw_reads` stílusához):

```
purge_id        BIGSERIAL PRIMARY KEY
purger          TEXT NOT NULL          -- ki/mi indította (mint raw_reads.reader)
retention_days  INTEGER NOT NULL       -- a használt retention ablak
cutoff          TIMESTAMPTZ NOT NULL   -- a now() - interval határ, ami ALATT töröltünk
rows_deleted    INTEGER NOT NULL       -- TÉNYLEGESEN törölt sorok száma
dry_run         BOOLEAN NOT NULL DEFAULT false
purged_at       TIMESTAMPTZ NOT NULL DEFAULT now()
```
+ index `purged_at`-ra. A migration `CREATE TABLE IF NOT EXISTS` / additív, a
`session-schema-migration-tooling-001` által elvárt formátumban, megfelelő
`COMMENT ON`-okkal (mint a `raw_reads` migration).

### 3. `rollback_conversation()` — megerősítés, NEM újraimplementálás

A reportban `file:line` hivatkozással erősítsd meg, hogy a
`rollback_conversation()` (`session_store/rollback.py:72`) VÁLTOZATLAN marad,
és magyarázd el a két mechanizmus elhatárolását: a `rollback_conversation()`
CÉLZOTT, (provider, provider_session_id)-kulcsú, azonnali törlés (pl. GDPR
kérésre); a purge IDŐ-alapú (`occurred_at`), automatikus háztartás. Ne
implementáld újra a conversation-törlést.

### 4. Valós teszt — eldobható Postgres ellen

Írj `tests/test_session_store/` alá tesztet, ami egy ELDOBHATÓ Postgres
instance (a data-protection / meglévő session-tesztek mintáját követve)
ellen bizonyítja:

- **Időhatár**: seedelj envelope-okat — egy részük `occurred_at`-je 90 napnál
  régebbi, más részük frissebb. A purge után a régiek TÖRLŐDTEK, a frissek
  MEGMARADTAK.
- **`occurred_at`, nem `ingested_at`**: egy olyan sor, aminek az `occurred_at`-je
  régi, de az `ingested_at`-je friss, **TÖRLŐDIK** (és fordítva: friss
  `occurred_at` + régi `ingested_at` MEGMARAD).
- **Audit-sor**: a purge után pontosan egy `session_audit.raw_purges` sor
  létezik, helyes `rows_deleted`/`cutoff`/`retention_days` értékkel.
- **Atomicitás**: az audit-sor `rows_deleted`-je megegyezik a ténylegesen
  eltűnt sorok számával (azonos tranzakció bizonyítéka).
- **Dry-run**: `dry_run=True` mellett SEMMI nem törlődik, de a visszaadott
  szám helyes.
- **Scope**: a `session_core.*` (ha a fixture-ben van projektált sor) a purge
  után ÉRINTETLEN.

A reportban idézd a TÉNYLEGES teszt-kimenetet (pl. a sorok száma előtte/utána,
az audit-sor tartalma) — a kód léte nem bizonyíték, a futtatott teszt az.

## Nem cél

- **Archívum / hideg-tároló export** a purge előtt — a policy doc KÜLÖN
  döntésként, hatókörön kívül jelöli
- **Éles systemd timer / cron telepítése** vagy bármilyen tartós ütemező
  beüzemelése — hosting/operátor döntés, ezen a jobon TÚL (a job a hívható
  entrypoint-ot + a sémát szállítja, az ütemezőt nem)
- a `session_core.*` (turns/chunks) projektált réteg retention-je — KÜLÖN,
  KÉSŐBBI job tárgya, ez a job KIZÁRÓLAG `session_raw.envelopes`
- a `rollback_conversation()` újraimplementálása vagy módosítása
- `ingested_at`-alapú törlés — a retention KIZÁRÓLAG `occurred_at`-en mérődik

## Required Output Files

- `output/session-raw-retention-purge.md`
- `session_store/retention_purge.py`
- a `session_audit.raw_purges` additív migration (`.sql`)
- a hozzá tartozó teszt-fájl(ok) `tests/test_session_store/` alatt

## Required Report Sections

```markdown
# session-raw-retention-purge-001 Output

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

- [ ] `purge_expired_raw_envelopes(...)` létezik, `occurred_at`-alapú, 90-nap
      default, env-felülírható, `dry_run` támogatott
- [ ] `session_audit.raw_purges` additív migration kész, a `raw_reads`
      mintáját követve, `COMMENT ON`-okkal
- [ ] valós, eldobható Postgres elleni teszt bizonyítja: időhatár,
      `occurred_at`-vs-`ingested_at`, audit-sor, atomicitás, dry-run, scope
- [ ] a report `file:line`-nal megerősíti, hogy `rollback_conversation()`
      VÁLTOZATLAN és NEM újraimplementált
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a purge függvény léte ≠ implemented — a futtatott teszt kimenete bizonyít
- `ingested_at`-alapú törlés `occurred_at` helyett (a policy explicit tiltja)
- a `session_core.*` réteg törlése (hatókörön kívül)
- az audit-sor és a `DELETE` KÜLÖN tranzakcióban (egy purge sosem maradhat
  audit nélkül)
- `candidate`/`canonical` státusz állítása — a `status_after_merge` pontosan
  `experimental`, mert az éles ütemező-telepítés külön emberi döntés
- a `rollback_conversation()` újraimplementálása

## Git instrukciók

Push a `feature/session-raw-retention-purge-001` branch-re, KIZÁRÓLAG a
`cic-mcp-session` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell
pusholni, elég a lokális commit). Main-re az agent NEM pushol. **NE
módosítsd a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek/kód angolul.
