# Job: session-schema-migration-tooling-001

## Kontextus

A `cic-mcp-session` Postgres schema-ja JELENLEG 6 különálló, KÉZZEL,
SORRENDBEN alkalmazott SQL fájlból áll (megerősítve `find output -iname
"*.sql"`-lel):

```
output/session-postgres-schema.sql            (alap schema)
output/session-chunk-indexer-migration.sql
output/session-hybrid-search-api-migration.sql
output/session-retrieval-quality-migration.sql
output/session-source-refs-api-migration.sql
output/session-vector-search-api-migration.sql
```

Nincs schema-version tábla, nincs gépi sorrend-kikényszerítés, nincs
idempotens újra-futtatás, nincs dokumentált rollback policy. Egy friss
Postgres-instance felállításakor valakinek KÉZZEL kell tudnia, milyen
sorrendben futtassa ezt a 6 fájlt — ez hibalehetőség és nem skálázódik.

Ez a job EZT formalizálja: egy migrációs futtató (lehet egyszerű Python
script, NEM kell külső keretrendszer mint Alembic, ha a job indokolja a
döntést), `schema_version` tábla, kikényszerített sorrend, idempotens
re-apply, dokumentált rollback policy, és egy startup compatibility check.

## Target

- target repo: `cic-mcp-session`
- target path: a 6 meglévő SQL fájl ÁTHELYEZÉSE/átnevezése egy
  `migrations/` könyvtárba (sorszámozva, pl. `0001_postgres_schema.sql`),
  + egy migrációs futtató modul + `output/session-schema-migration-
  tooling.md`
- change_type: `new_capability`
- status_after_merge: `candidate`
- status indoklás: valós Postgres teszt bizonyítja az idempotens
  re-apply-t és a `schema_version` tábla pontosságát

## Sources

- **KÖTELEZŐ elsődleges forrás:**
  - `find output -iname "*.sql"` kimenete — a 6 fájl és azok TÉNYLEGES,
    eddig betartott alkalmazási sorrendje (ezt a git history/output-
    dokumentáció alapján erősítsd meg, ne találd ki)
  - minden egyes SQL fájl TARTALMA — a migrációs eszköz ezeket
    KIZÁRÓLAG mozgatja/sorszámozza, a TARTALMUKAT NEM írja át

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 0. Pre-change állapot megerősítése

```
grep -rn "schema_migrations\|schema_version" --include="*.py" --include="*.sql" . | grep -v test_
```

Idézd a kimenetet (várhatóan 0 találat) — ez bizonyítja, hogy JELENLEG
nincs migrációs-keretrendszer.

### 1. Sorrend megerősítése

A 6 fájl FÜGGŐSÉGI sorrendjét (melyik melyik UTÁN futhat — pl. egy
`migration` fájl `ALTER TABLE`-je csak az alap `CREATE TABLE` UTÁN futhat)
idézd, jobonkénti hivatkozással (melyik job-output melyik fájlt hozta
létre, milyen sorrendben — nézd meg a `jobs/index.yaml`-t a job-ok
`completed` timestamp-jei alapján, vagy a fájlok közötti `ALTER`/`CREATE`
függőséget olvasva).

### 2. `migrations/` könyvtár + `schema_version` tábla

Hozz létre egy `migrations/` könyvtárat, mozgasd/másold át a 6 fájlt
sorszámozott névvel (TARTALMUKAT NE módosítsd, csak a fájlnevet/helyet),
és definiálj egy `schema_migrations.applied` táblát: `version`,
`filename`, `applied_at`, `checksum` (a fájl tartalmának hash-e, hogy
észlelhető legyen, ha valaki utólag módosítana egy már alkalmazott
migrációt).

### 3. Migrációs futtató

Implementálj egy futtatót (pl. `tools/migrate.py` vagy `session_store/
migrate.py`), ami:
- megnézi a `schema_migrations.applied` táblát, és csak a MÉG NEM
  alkalmazott migrációkat futtatja, sorrendben
- minden sikeres migráció után beír egy sort a `schema_migrations.applied`
  táblába
- ha egy migráció checksum-ja eltér az eredetileg alkalmazottól, HIBÁVAL
  áll meg (nem csendben folytatja)

### 4. Idempotencia — valós, futtatott bizonyíték

Valós Postgres teszttel bizonyítsd:
1. egy ÜRES DB-n a futtató lefuttatja mind a 6 migrációt, sorrendben
2. UGYANAZT a futtatót MÉGEGYSZER lefuttatva a MÁR migrált DB-n: NULL
   hatású (no-op), a `schema_migrations.applied` tábla TARTALMA
   változatlan
3. idézd mindkét futás TÉNYLEGES kimenetét

### 5. Rollback policy

Dokumentáld LEGALÁBB 1 migrációra a tényleges reverse SQL-t, VAGY ha a
döntés "forward-only, nincs rollback" — mondd ki EXPLICIT-en, indokolva
(pl. ha egy migráció adatvesztő DROP COLUMN-t tartalmaz, a rollback nem
triviális, és ezt dokumentálni kell, nem hallgatni el).

## Nem cél

- a meglévő 6 SQL fájl TARTALMÁNAK átírása vagy a köztük lévő, már
  alkalmazott sorrend megváltoztatása
- külső migrációs keretrendszer (Alembic, Flyway) bevezetése, HACSAK a
  report explicit nem indokolja, miért szükséges egy egyszerű,
  saját-írt futtató helyett
- a `session-outbox-batch-and-observability-001` hatóköre (az a job a
  futó kódot módosítja, ez a job a schema-deploy folyamatot formalizálja)

## Required Output Files

- `output/session-schema-migration-tooling.md`
- a `migrations/` könyvtár (a 6 átnevezett fájllal)
- a migrációs futtató modul
- a hozzá tartozó teszt-fájl

## Required Report Sections

```markdown
# session-schema-migration-tooling-001 Output

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

- [ ] a 6 fájl TÉNYLEGES, eddig betartott sorrendje idézve és indokolva
- [ ] `migrations/` könyvtár + `schema_migrations.applied` tábla
      definiálva
- [ ] migrációs futtató implementálva, checksum-ellenőrzéssel
- [ ] üres DB-n teljes apply valós teszttel bizonyítva
- [ ] második futás no-op, valós teszttel bizonyítva (TÉNYLEGES kimenet
      mindkét futásra)
- [ ] rollback policy dokumentálva legalább 1 migrációra (vagy explicit
      "forward-only" indoklással)
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a migrációs futtató léte ≠ implemented — a futtatott Postgres teszt
  kimenete bizonyít, a kód megírása nem; minden állítást a tényleges
  apply-hívás file:line hivatkozásával kell alátámasztani
- a meglévő SQL fájlok TARTALMÁNAK módosítása ürügyként a
  "formalizáláshoz"
- "idempotens" állítás a második-futás TÉNYLEGES kimenete nélkül
- checksum-ellenőrzés kihagyása vagy csendes felülírás eltérő checksum
  esetén

## Git instrukciók

Push a `feature/session-schema-migration-tooling-001` branch-re,
KIZÁRÓLAG a `cic-mcp-session` célrepóban (a `cic-mcp-factory` saját
klónjában NEM kell pusholni, elég a lokális commit). Main-re az agent NEM
pushol. **NE módosítsd a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek/kód angolul.
