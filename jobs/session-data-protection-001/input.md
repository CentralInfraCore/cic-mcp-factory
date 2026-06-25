# Job: session-data-protection-001

## Kontextus

A `session_raw.envelopes` táblába a teljes, nyers Claude Code hook payload
(és a leendő `session-transcript-reader-001`/`session-ingest-hook-
sandboxed-001` kimenete) kerül be — ez tartalmazhat credentialokat,
API-kulcsokat, tool-eredményeket, vagy más érzékeny adatot, JELENLEG SEMMI
redaction NÉLKÜL. Emellett nincs dokumentált retention policy, és nincs
audit-napló a raw envelope OLVASÁSOKHOZ.

A `historical-import-rollback-tool-001` job (mergelve) MÁR megépítette a
`rollback_conversation(provider, provider_session_id)` függvényt
(`session_store/rollback.py:72`), ami egy adott beszélgetést TELJESEN
töröl (mind a projected, mind a raw réteget) — ez a job ezt a függvényt
HASZNÁLJA a törlési primitívként, NEM épít másikat.

Ez a job EZT zárja: (1) secret-redaction lépés a raw envelope insert előtt,
(2) retention policy dokumentum, (3) `rollback_conversation()`
megerősítése törlési primitívként, (4) audit-log a raw envelope
OLVASÁSOKHOZ.

## Target

- target repo: `cic-mcp-session`
- target path: a raw envelope insert-pathba épített redaction-lépés +
  egy `session_audit.raw_reads` audit-tábla + retention policy dokumentum +
  a hozzá tartozó teszt + `output/session-data-protection.md`
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: a redaction és audit-log valós teszttel bizonyított, DE
  a retention policy TÉNYLEGES, automatikus kikényszerítése (pl. egy
  ütemezett purge-job) EZEN a jobon TÚLI, KÜLÖN követő munka — innen
  `experimental`, nem `candidate`

## Sources

- **KÖTELEZŐ elsődleges forrás:**
  - `session_store/rollback.py` — `rollback_conversation()` (72. sortól),
    TELJES implementáció, ezt a jobot REUSE-olja, NEM írja újra
  - a raw envelope insert-path (`session_raw.envelopes`-ba író kód —
    grep-pel azonosítsd a pontos file:line-t)

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. Pre-change állapot megerősítése

```
grep -rn "INSERT INTO session_raw.envelopes" --include="*.py" . | grep -v test_
```

Idézd a kimenetet — ez a redaction-lépés beillesztési pontja.

### 2. Secret-redaction

Implementálj egy redaction-függvényt, ami a raw payload-ot INSERT ELŐTT
átfuttatja, és legalább a leggyakoribb secret-mintákat (API-key-szerű
stringek, pl. `sk-...`, `ghp_...`, vagy egy konfigurálható regex-lista)
helyettesíti egy placeholder-rel (pl. `[REDACTED]`). Dokumentáld, hogyan
bővíthető a minta-lista (extensibility path) — NEM kell teljes secret-
scanning megoldást építeni, de a tervnek bővíthetőnek kell lennie.

### 3. Valós, futtatott bizonyíték — redaction

Írj egy tesztet, ami egy SZINTETIKUS payloadot ad be, ami egy
nyilvánvalóan secret-alakú stringet tartalmaz (pl. egy fixture API-key),
és bizonyítja, hogy a PERSISTÁLT sorban (`session_raw.envelopes`) ez a
string `[REDACTED]`-ként jelenik meg, NEM az eredeti értékként. Idézd a
tényleges, perzisztált sor tartalmát.

### 4. Retention policy dokumentum

Írj egy dokumentumot, ami megad egy KONKRÉT alapértelmezett retention
időtartamot (pl. "X nap a raw rétegben"), és leírja, HOGYAN lenne
kikényszerítve (akár ha a tényleges kikényszerítés egy KÖVETŐ jobban
készül el — ezt a "Next Jobs" szekcióban explicit jelöld).

### 5. `rollback_conversation()` megerősítése + audit-log olvasásra

Idézd file:line-nal, hogy `rollback_conversation()` VÁLTOZATLANUL a
törlési primitív (nem írod újra). Adj hozzá egy `session_audit.raw_reads`
táblát, és írj egy sort bele MINDEN alkalommal, amikor a raw envelope-okat
valaki (pl. egy admin lekérdezés vagy a historical importer) OLVASSA.
Valós teszttel bizonyítsd, hogy egy olvasás után TÉNYLEGESEN megjelenik az
audit-sor.

## Nem cél

- `rollback_conversation()` újraírása vagy módosítása (REUSE, nem
  reimplement)
- a retention policy TÉNYLEGES, automatikus kikényszerítése (purge-job) —
  ez egy KÖVETŐ job, explicit jelölve a "Next Jobs"-ban
- teljes, ipari secret-scanning megoldás (pl. külső szolgáltatás
  integrálása) — egy konfigurálható, bővíthető minta-lista elegendő

## Required Output Files

- `output/session-data-protection.md`
- a módosított insert-path (redaction-lépéssel)
- a `session_audit.raw_reads` migráció
- a retention policy dokumentum
- a hozzá tartozó teszt-fájl

## Required Report Sections

```markdown
# session-data-protection-001 Output

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

- [ ] pre-change insert-path grep-pel azonosítva, file:line idézve
- [ ] secret-redaction valós teszttel bizonyítva (perzisztált sor tartalma
      idézve)
- [ ] retention policy dokumentum konkrét időtartammal és kikényszerítési
      tervvel
- [ ] `rollback_conversation()` file:line-nal megerősítve mint
      VÁLTOZATLAN törlési primitív
- [ ] `session_audit.raw_reads` audit-log valós teszttel bizonyítva
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a redaction/audit kód léte ≠ implemented — a futtatott teszt kimenete
  bizonyít, a kód megírása nem
- `rollback_conversation()` újraírása vagy duplikálása
- a retention policy "kikényszerítve" állítása tényleges purge-mechanizmus
  nélkül (ha még nincs kikényszerítve, ezt EXPLICIT így kell jelölni,
  KÖVETŐ jobként)
- redaction-állítás a perzisztált sor TÉNYLEGES tartalmának idézése nélkül

## Git instrukciók

Push a `feature/session-data-protection-001` branch-re, KIZÁRÓLAG a
`cic-mcp-session` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell
pusholni, elég a lokális commit). Main-re az agent NEM pushol. **NE
módosítsd a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek/kód angolul.
