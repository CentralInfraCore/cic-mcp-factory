# Job: historical-import-runner-001

## Kontextus

Phase 6 ("Wiring") ötödik, ZÁRÓ kódjobja. A `historical-dedupe-idempotency-001` job
megírta a konvertert (`session_store/chatgpt_import.py`:
`chatgpt_message_to_envelope()`), és a `historical-chatgpt-export-importer-001`
strukturális riport dokumentálta a export-bundle felépítését (sharded
`conversations-NNN.json`, `mapping` fa-csomópontok `{id, message, parent, children}`
alakban) — DE **semmilyen kód nem olvas be jelenleg egy export-fájlt végponttól
végpontig**: a konverter csak EGY `message`-dict-et alakít át, a fa-bejárás és a
shard-okon-átívelő iterálás SOSEM lett implementálva. A strukturális riport explicit
NYITOTT KÉRDÉSKÉNT hagyta a `mapping` fa-bejárási sorrendjét (lásd
`historical-chatgpt-importer-design.md` 329. sor).

Ez a job EZT a hiányt zárja: megírja a tényleges batch-runner-t, amely végigjárja a
fa-t, minden node-ra meghívja a meglévő `chatgpt_message_to_envelope()`-ot és
`insert_envelope()`-ot, több shard-fájlon át, és bizonyítja, hogy egy
részben-megszakadt import biztonságosan újrafuttatható (az idempotency-key dedupe
miatt nincs duplikáció).

**KRITIKUS BIZTONSÁGI HATÁR (kötelező, lásd `historical-dedupe-idempotency-001`
előzménye)**: a teszt-fixture-ök KIZÁRÓLAG fabrikált, szintetikus tartalom lehetnek —
legalább 3 darab kitalált shard-fájl, a valós export `conversations-NNN.json`
struktúráját tükrözve. A valós, személyes export-bundle elleni futtatás ennek a
jobnak EXPLICIT NEM CÉLJA, és külön, dedikált biztonsági megbeszélést igényel,
MIELŐTT megfontolásra kerülne.

## Target

- target repo: `cic-mcp-session`
- target path: `output/historical-import-runner.md` + a runner-kód (a repo Python-
  struktúrájának megfelelő helyen, pl. `session_store/historical_import_runner.py`
  — NÉZD MEG a repót, NE találj ki új konvenciót) + a hozzá tartozó teszt
- change_type: `new_capability`
- status_after_merge: `candidate`
- status indoklás: TÉNYLEGES, futtatható kód + valós Postgres-teszt, beleértve egy
  kill-mid-run/resume forgatókönyvet — megfelel a `historical-dedupe-idempotency-001`
  mintájának

## Sources

- **KÖTELEZŐ elsődleges forrás (a `cic-mcp-factory` repo `main`-jén, MÁR ott van):**
  - `${WORKDIR}/jobs/index.yaml` — prerequisite-ellenőrzéshez `- id: "<job-id>"`
    kulccsal (NEM `job_id:`)
  - `${WORKDIR}/jobs/historical-chatgpt-export-importer-001/output/historical-
    chatgpt-importer-design.md` — "Export Bundle Structure" szekció (a `mapping`
    node `{id, message, parent, children}` alakja), ÉS a 329. sor: "A `mapping` fa-
    bejárási sorrendje NYITOTT KÉRDÉS marad" — EZT a kérdést EZ a job dönti el
- **MÁSODIK forrás (a `cic-mcp-session` repo, a target, KLÓNOZVA):**
  - `session_store/chatgpt_import.py` — `chatgpt_message_to_envelope()` (144. sor
    körül) TELJES szignatúra, NE módosítsd, ÉPÍTS rá
  - `session_store/envelope_writer.py` — `insert_envelope()` (165. sor körül)
    TELJES szignatúra, NE módosítsd, ÉPÍTS rá
  - `tests/test_session_store/test_chatgpt_import.py` — a TELJES szintetikus
    fixture-minta (a modul docstring-je + `_synthetic_conversation()` és a hozzá
    tartozó `pg_config`/`_clean_envelopes_table`/`_count_rows` fixture-ök
    `test_envelope_writer.py`-ból újrahasznosítva) — EZT A MINTÁT kell követni az
    ÚJ teszthez, NEM újra feltalálni

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. Prerequisite-ellenőrzés

```
grep -n '\- id: "historical-dedupe-idempotency-001"' -A 3 jobs/index.yaml
grep -n '\- id: "historical-chatgpt-export-importer-001"' -A 3 jobs/index.yaml
```

Idézd a kimenetet, erősítsd meg mindkettő `status: "done"`. Ha NEM, NO-GO és állj meg.

### 2. Fa-bejárási sorrend eldöntése — a nyitott kérdés lezárása

Először GREP-pel erősítsd meg a konverter és az insert függvény tényleges
szignatúráját (teszt-fájlok kizárva):

```
grep -rn "^def chatgpt_message_to_envelope\|^def insert_envelope" --include="*.py" . | grep -v test_
```

Idézd a kimenetet. Válassz és INDOKOLJ egy konkrét bejárási sorrendet a "Decisions
Proposed" szekcióban (pl. DFS preorder a gyökér node-tól, ahol `parent is None`,
`children` tömb sorrendjét követve) — ez egy KONKRÉT, determinisztikus, megírt
algoritmus kell legyen, NEM csak megemlített elv.

### 3. Runner-implementáció

Írj egy függvényt/modult, amely:
- bemenetként kap egy mappára mutató path-ot, amely 1..N darab `conversations-
  NNN.json` shard-fájlt tartalmaz (a valós export sharding-mintáját követve)
- minden shard-fájlt beolvas, minden conversation-objektum `mapping`-fáját a (2)
  pontban eldöntött sorrendben bejárja
- minden node-ra meghívja a MEGLÉVŐ `chatgpt_message_to_envelope()`-ot és
  `insert_envelope()`-ot (NEM reimplementálja a konverziós/idempotency logikát)
- nyomon követi, mely shard-fájlok lettek TELJESEN feldolgozva (pl. egy
  progress-jelölő mechanizmus — a konkrét formát indokold a riportban), hogy egy
  megszakított futás után a már teljesen feldolgozott shard-okat ne kelljen
  újraolvasni — DE az idempotency-key dedupe-nak KELL biztosítania, hogy egy
  TÉNYLEGESEN megszakadt, félig-feldolgozott shard biztonságosan újrafuttatható
  legyen duplikáció nélkül, akkor is, ha a progress-jelölés maga nem lenne pontos

### 4. Valós, futtatott bizonyíték — kill-mid-run/resume forgatókönyv

Hozz létre LEGALÁBB 3 SZINTETIKUS shard-fájlt (KIZÁRÓLAG fabrikált tartalom, a
`test_chatgpt_import.py` fixture-stílusát követve), valós Postgres ellen:
1. futtasd a runner-t a TELJES bundle-ön végig, számold le a beírt sorokat
2. ürítsd ki a táblát, futtasd a runner-t úgy, hogy SZÁNDÉKOSAN megszakítod
   (pl. kivételt dobsz/`sys.exit`-elsz) a 2. shard közepén
3. futtasd a runner-t ÚJRA a teljes bundle-ön (resume/re-run)
4. bizonyítsd VALÓS psql-lekérdezéssel: a sorok száma PONTOSAN egyezik az 1. lépés
   eredményével, NINCS duplikáció, MINDEN node beírva

Idézd a TÉNYLEGES pytest/psql kimenetet.

## Nem cél

- a `chatgpt_message_to_envelope()`/`insert_envelope()` módosítása (ÉPÍTS rájuk)
- valós, személyes export-bundle elleni futtatás (külön biztonsági megbeszélés kell)
- a `historical-chatgpt-export-importer-001` strukturális riportjának felülírása —
  KIZÁRÓLAG a fa-bejárási sorrend nyitott kérdését zárja le
- shared/gateway bekötés (másik Phase 6 job tárgya, már lezárva)

## Required Output Files

- `output/historical-import-runner.md`
- a runner-kód fájlja
- a hozzá tartozó teszt-fájl

## Required Report Sections

```markdown
# historical-import-runner-001 Output

## Scope
## Inputs Read
## Prerequisite Check
## Mapping Traversal Order Decision
## Runner Implementation
## Synthetic Multi-Shard Test Fixture
## Real Postgres Kill-Mid-Run/Resume Proof
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
`proven` egy "a resume nem duplikál" állításra KIZÁRÓLAG akkor használható, ha a
TÉNYLEGES, futtatott kill-mid-run/resume teszt kimenete (a tényleges sorszámokkal)
idézve van — a dedupe-formula leírása a kódban nem bizonyítja, hogy a resume
helyesen fut.

## Definition Of Done

- [ ] mindkét prerequisite `id:` kulccsal megerősítve, GO/NO-GO döntés indokolva
- [ ] a `mapping` fa-bejárási sorrend KONKRÉTAN eldöntve és megírva, file:line
      hivatkozással, a nyitott kérdés explicit lezárva
- [ ] a runner a MEGLÉVŐ `chatgpt_message_to_envelope()`/`insert_envelope()`-ot
      hívja, NEM reimplementálja a logikájukat, file:line hivatkozással
- [ ] legalább 3 szintetikus, fabrikált shard-fájl, valós tartalom nélkül
- [ ] valós Postgres teszt: teljes futás + kill-mid-run + resume, a sorszámok
      PONTOSAN egyeznek, nincs duplikáció — a TÉNYLEGES számértékek idézve
- [ ] a riport explicit kimondja, hogy valós, személyes export-bundle elleni
      futtatás külön biztonsági review-t igényel, és ez itt NEM történt meg
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- valós, személyes export-bundle bármilyen, akár részleges használata
  teszt-fixture-ként
- valós export-bundle elleni futtatás külön biztonsági review nélkül
- a fa-bejárási sorrend eldöntés nélkül/csak megemlítve hagyása
- a `chatgpt_message_to_envelope()`/`insert_envelope()` logikájának
  reimplementálása/duplikálása a runner-ben
- a fájl/kód léte ≠ implemented (ez egyetlen soron) — a futtatott
  kill-mid-run/resume teszt kimenete bizonyít, a kód megírása nem

## Git instrukciók

Push a `feature/historical-import-runner-001` branch-re, KIZÁRÓLAG a
`cic-mcp-session` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni,
elég a lokális commit). Main-re az agent NEM pushol. **NE módosítsd a `meta.yaml`
`status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek/kód angolul.
