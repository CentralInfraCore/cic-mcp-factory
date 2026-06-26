# session-audit-migration-wiring-001 — a `session_audit` séma bekötése a számozott migration-runnerbe

## Kontextus / miért kell

A `cic-mcp-session` provisioning-bizalma a `session_store/migrate.py` számozott
runneren áll: a `migrations/000N_*.sql` fájlok a **kizárólagos, checksum-kényszerített,
append-only** forrás (lásd `session-schema-migration-tooling-001`,
`output/session-schema-migration-tooling.md`). Egy friss adatbázist a `run_migrations()`
provisionál, sorrendben, és a `schema_migrations.applied` táblába jegyzi.

Két, audittal igazolt rés van ezen a láncon (mindkettő `concept→code→runtime` híd-szakadás):

1. **A `session-data-protection-001` migrationje sosem került be a számozott runnerbe.**
   A `session_audit.raw_reads` tábla DDL-je **csak** `output/session-data-protection-migration.sql`
   alatt él, a `migrations/` egyetlen számozott fájlja sem hozza létre. Következmény: egy
   tisztán `migrate.py`-vel provisionált DB-ben **nincs `session_audit.raw_reads`**, és
   `session_store/raw_read_audit.py:log_and_read_raw_envelopes()` futtatva
   `relation "session_audit.raw_reads" does not exist` hibára futna. A
   `tests/test_session_store/test_data_protection.py` ezt **elfedi**, mert a sémát kézzel,
   runneren kívül applikálja (docstring: *"output/session-data-protection-migration.sql
   already applied"*).

2. **A `session-raw-retention-purge-001` (0007) stale-re tette a `test_migrate.py`-t.**
   A `migrations/0007_raw_retention_purge.sql` bevezette a `session_audit` sémát +
   `session_audit.raw_purges` táblát, de a `tests/test_session_store/test_migrate.py`
   from-zero invariánsai **hard-kódolva `["0001".."0006"]`-ig mennek** (lásd a fájl
   ~100., ~108., ~130., ~137., ~192. sorát). A `run_migrations()` ma `["0001".."0007"]`-et
   ad vissza, így ezek az assertek **buknának** — csak azért nem piros a CI, mert a DB-tesztek
   ott nem futnak (nincs élő Postgres a CI venv-ben).

Ez a job mindkét rést bezárja: a `session_audit` réteget a számozott runner **valódi része**
teszi, és helyreállítja a from-zero migrate-teszt invariánsait.

## Forrás (ezekből dolgozz, ne máshonnan)

- `session_store/migrate.py` — `discover_migrations()` (`migrations/*.sql`, sequence-prefix
  sorrend), `run_migrations()` (checksum-verifikáció előbb, majd append-only apply),
  `MIGRATIONS_DIR`.
- `migrations/0007_raw_retention_purge.sql` — a `session_audit` sémát már létrehozza
  (`CREATE SCHEMA IF NOT EXISTS session_audit`) + `raw_purges`.
- `output/session-data-protection-migration.sql` — a bekötendő DDL (séma + `raw_reads` +
  COMMENT-ek + index). Ez a forrás-tartalom, amit számozott migrationné kell tenni.
- `session_store/raw_read_audit.py` — a `session_audit.raw_reads` tényleges fogyasztója.
- `tests/test_session_store/test_migrate.py` — a from-zero invariáns-teszt, amit javítani kell
  (`_ALL_SCHEMAS`, az `applied == [...]` és a `rows == [...]` assertek).

## Feladat (mit kell pontosan leszállítani)

1. **`migrations/0008_data_protection_raw_reads.sql`** — ÚJ számozott migration, a
   `output/session-data-protection-migration.sql` tartalmával (séma + `raw_reads` + COMMENT-ek +
   index), `CREATE SCHEMA / TABLE / INDEX IF NOT EXISTS` formában (idempotens). A számozás
   **0008 (append-only)**, NEM a 0007 elé szúrva: a 0007 már mergelt és checksum-kényszerített,
   az átszámozása megtörné a `schema_migrations.applied`-ben rögzített verziókulcsot a már
   migrált DB-ken. A `raw_reads` és a `raw_purges` egymástól független (mindkettő csak a
   `session_audit` sémát igényli `IF NOT EXISTS`-szel), ezért a sorrend funkcionálisan közömbös
   — ezt a döntést a migration fejlécében dokumentáld.

2. **`tests/test_session_store/test_migrate.py` javítása** úgy, hogy a from-zero invariáns
   tükrözze a `0007` + `0008` migrationt is:
   - a hard-kódolt `["0001".."0006"]` / `rows == [...]` listák kiegészítése `0007`-tel és
     `0008`-cal (`0007_raw_retention_purge.sql`, `0008_data_protection_raw_reads.sql`);
   - `_ALL_SCHEMAS` teardown-halmazba a `session_audit` felvétele (különben residue marad);
   - ÚJ assert: friss `run_migrations()` után a `session_audit` séma létezik, ÉS a
     `session_audit.raw_reads` ÉS `session_audit.raw_purges` tábla is létezik (a from-zero út
     bizonyítottan előállítja mindkét audit-táblát).

3. **Regressziós bizonyíték a #1 résre**: egy teszt, amely friss eldobható Postgres-en
   **`run_migrations()`-szel** (NEM kézi SQL-apply-jal) provisionál, majd igazolja, hogy
   `session_store/raw_read_audit.py:log_and_read_raw_envelopes()` ténylegesen működik (audit-sor
   keletkezik) — azaz a runner-only út már nem törött. Ez lehet a `test_migrate.py`-ban vagy egy
   külön teszt-modulban.

## Tilos / nem cél

- **TILOS** a 0007 (vagy bármely már mergelt migration) átszámozása vagy tartalmi módosítása —
  append-only, immutable. Ne rövidítsd „elég csak a 0007-et átírni"-ra.
- **TILOS** a `output/session-data-protection-migration.sql` törlése — a doc-tükör marad (a
  migration-tooling konvenció szerint az `output/` eredetik megmaradnak).
- Nem cél a `session_store/raw_read_audit.py` viselkedésének megváltoztatása — az változatlan,
  csak a provisioning-út lesz mögötte ép.
- Nem cél új audit-tábla bevezetése — kizárólag a meglévő `session_audit.raw_reads` bekötése.
- Push KIZÁRÓLAG a `cic-mcp-session` `feature/session-audit-migration-wiring-001` branch-re. A
  factory-klónban csak lokális commit. NE módosítsd a `meta.yaml` `status` mezőjét.

**Bizonyíték-küszöb (ne rövidítsd):** a `migrations/0008_*.sql` **fájl puszta létezése ≠
bekötve** — a runner-only provisioning csak akkor igazolt, ha a from-zero `run_migrations()`
teszt zölden előállítja a `session_audit.raw_reads`-et valódi Postgres-en. A pytest **exit code
0 ≠ sikeres capability**, ha a PASSED sorok nem fedik a claim→evidence tábla minden állítását.

## Reachability / korrektség-ellenőrzés (grep)

A bekötés tényét grep-pel igazold a kész állapotban:

```
grep -rn "session_audit.raw_reads" migrations/   # 0008-nak meg KELL jelennie a call-chainben
grep -rn "session_audit"           migrations/   # 0007 ÉS 0008 is
grep -rn "0008"                     tests/test_session_store/test_migrate.py  # a teszt tud a 0008-ról
grep -rn "raw_reads"               session_store/raw_read_audit.py  # a fogyasztó a bekötött táblát éri
```

A `discover_migrations()` `sorted(glob("*.sql"))` alapján rendez — igazold, hogy a `0008` a
`0007` után, sorrendben kerül alkalmazásra (a from-zero teszt `applied == [...,"0007","0008"]`
assertje ezt bizonyítja).

**Reachability artifact (kötelező az outputban):** a `session_audit.raw_reads` **production
hívási helyét** `file:line` formában nevezd meg — `session_store/raw_read_audit.py`-ben a
`log_and_read_raw_envelopes()` `INSERT INTO session_audit.raw_reads` sora (add meg a pontos
sorszámot grep-pel). A `symbol/tábla létezik` ≠ `production hívja`: a `raw_reads` akkor releváns,
ha a runner-only provisioning után ez a hívási hely ténylegesen működik (a regressziós teszt ezt
a call site-ot futtatja, nem csak a tábla létezését nézi).

## Teszt-futtatás (valódi Postgres, nincs mock)

`pgvector/pgvector:pg16` eldobható konténer, a `test_migrate.py` from-zero útját ELLENE futtatva:

```
docker run -d --name session-audit-wiring-test -e POSTGRES_PASSWORD=test \
  -e POSTGRES_DB=testdb -p 55443:5432 pgvector/pgvector:pg16
SESSION_STORE_PG_HOST=localhost SESSION_STORE_PG_PORT=55443 SESSION_STORE_PG_DB=testdb \
  SESSION_STORE_PG_USER=postgres SESSION_STORE_PG_PASSWORD=test \
  pytest tests/test_session_store/test_migrate.py -v
docker rm -f session-audit-wiring-test
```

A riportba a tényleges pytest-kimenet kerüljön (PASSED sorok), nem összefoglaló.

## Claim → evidence (a riportban kötelező tábla)

| Állítás | Státusz | Bizonyíték | Verifikációs módszer | Kockázat |
|---|---|---|---|---|
| Friss DB `run_migrations()`-szel létrehozza a `session_audit.raw_reads`-et | implemented | from-zero `test_migrate.py` assert (tábla létezik) | pytest valódi PG ellen | ha csak kézi apply, a runner-út továbbra is törött |
| `raw_read_audit.py` runner-only provisioninggal működik (nincs `relation does not exist`) | implemented | regressziós teszt: audit-sor keletkezik `run_migrations()` után | pytest: INSERT+SELECT a valós táblába | a teszt out-of-band sémát applikál → elfedi a rést |
| A 0007 + 0008 a runner része, sorrendben | implemented | `applied == [..., "0007", "0008"]` assert + grep | pytest + `grep -rn` | rossz sequence-prefix → rossz sorrend |
| A 0007 változatlan (append-only) | implemented | `git diff` nem érinti a `migrations/0007_*.sql`-t | `git diff --name-only` | átszámozás megtörné a checksum-kulcsot |
| `raw_purges` is előáll a from-zero úton | implemented | from-zero assert (tábla létezik) | pytest valódi PG ellen | a teszt invariáns stale marad a session_audit-ra |

## Output

`output/session-audit-migration-wiring.md` — magyarul, a CLAUDE.md „Kötelező PR-tartalom"
8 pontja szerint (miért kellett, milyen contract/diff, milyen teszt bizonyítja, milyen
státuszban indul = `experimental`, ismert limitációk, rollback/deprecate út), a fenti
claim→evidence táblával és a tényleges pytest-kimenettel. Kód/mezőnevek angolul, próza magyarul.
