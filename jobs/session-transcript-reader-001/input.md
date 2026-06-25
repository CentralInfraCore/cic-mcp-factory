# Job: session-transcript-reader-001

## Kontextus

A `session-hook-collector-001` (mergelve, lásd `jobs/session-hook-collector-001/output/session-hook-collector-report.md`)
megerősítette, hogy minden Claude Code hook-esemény stdin JSON-ja tartalmaz egy
`transcript_path` mezőt — egy JSONL fájl elérési útját, amely a TELJES
beszélgetés transcript-jét tárolja. A hook-esemény payloadja ÖNMAGÁBAN NEM
tartalmazza az assistant válasz szövegét — csak metaadatot (session_id,
transcript_path, cwd, hook_event_name, stb.). Ha a session-ingest pipeline a
hook payloadot önmagában tárolná, kereshető eseménynaplót kapnánk, NEM
beszélgetés-memóriát.

Ez a job EZT a hiányt zárja: egy inkrementális `transcript_path` JSONL-olvasót
épít, amely stabil id-jú user/assistant/tool üzeneteket nyer ki, tool_use/
tool_result párokat összepárosítja, és a `SessionIngressEnvelope`-kompatibilis
turn-listát ad ki. Ez a `session-ingest-hook-sandboxed-001` job előfeltétele
(az a job ezt a readert hívja majd a hook scriptekből).

**Ez a job NEM a hook-okat építi** (az `session-ingest-hook-sandboxed-001`
KÜLÖN job), és NEM köt be semmit éles `settings.json`-ba — ez egy önálló,
fájl-bemenetű olvasó/parser modul, amit bármilyen hívó (teszt, leendő hook)
meghívhat egy transzkript-path-tal.

## Target

- target repo: `cic-mcp-session`
- target path: `session_store/transcript_reader.py` (vagy hasonló elnevezés,
  a repo meglévő `session_store/` modul-konvencióját követve) +
  `output/session-transcript-reader.md`
- change_type: `new_capability`
- status_after_merge: `candidate`
- status indoklás: valódi, futtatott teszt bizonyítja az idempotens
  inkrementális olvasást és a tool_use/tool_result párosítást egy valódi
  transcript JSONL minta ellen

## Sources

- **KÖTELEZŐ elsődleges forrás:**
  - `jobs/session-hook-collector-001/output/session-hook-collector-report.md`
    — a `transcript_path` mező létezésének és a hook payload pontos
    szerkezetének bizonyítéka (177., 229., 355-371. sor körül)
  - `jobs/session-ingress-envelope-contract-001/output/session-ingress-envelope-contract.md`
    — a `SessionIngressEnvelope` schema, amihez a kimenő turn-listának
    illeszkednie kell
  - `session_store/` (meglévő modulok, a kódstílus és import-konvenció
    követéséhez)

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál
3. Generálj (vagy keress) egy VALÓDI Claude Code transcript JSONL fájlt —
   ha a saját futó session-ed `transcript_path`-ja elérhető (nézd meg egy
   tetszőleges korábbi hook-eseményt, ha van log róla, vagy generálj egy
   minimális, de STRUKTURÁLISAN valódi JSONL fixture-t a Claude Code
   dokumentált transcript-formátuma alapján) — idézd a tényleges
   sor-szerkezetet, amire a parser épül

## Feladat

### 1. Transcript JSONL sor-szerkezet megerősítése

Először győződj meg róla, hogy ehhez a kapacitáshoz nincs MÁR meglévő
implementáció a repóban (ne duplikálj):

```
grep -rn "read_transcript\|class Turn\|TranscriptReader" --include="*.py" session_store/ | grep -v test_
```

Idézd a kimenetet (várhatóan 0 találat). Majd idézd egy valódi (vagy a dokumentált formátumot pontosan követő, de
egyértelműen FIXTURE-ként jelölt) transcript JSONL legalább 3 sorát: egy user
üzenetet, egy assistant üzenetet (szöveggel), és egy tool_use/tool_result
párt. Ez a parser tervének alapja.

### 2. `transcript_reader` modul

Implementálj egy függvényt (pl. `read_transcript_incremental(transcript_path:
str, since_offset: int = 0) -> tuple[list[Turn], int]`), amely:
- a megadott offset-től olvas (sor- vagy byte-alapú, indokolva, melyiket
  választod és miért)
- minden user/assistant/tool sorhoz egy `Turn` rekordot épít, STABIL id-vel,
  ami a transcript TARTALMÁBÓL (nem `uuid4()`-ből) származik — pl. a sor
  tartalmának hash-éből, vagy a transcript saját message-id mezőjéből, ha
  van ilyen
- tool_use és a hozzá tartozó tool_result sort egyetlen turn rekordba
  párosítja, a tool_use_id (vagy ekvivalens) alapján
- visszaadja az új offset-et, hogy a hívó (a leendő hook) tudja honnan
  folytassa legközelebb

### 3. Idempotencia — valós, futtatott bizonyíték

Írj egy tesztet, amely:
1. beolvas egy fixture transcript-et offset 0-tól → N turn, offset O1
2. HOZZÁFŰZ a fixture-höz 2 ÚJ sort
3. újra beolvas O1-től → PONTOSAN 2 ÚJ turn jön ki, NEM N+2
4. Idézd a TÉNYLEGES pytest kimenetet

### 4. `SessionIngressEnvelope` illesztés

Mutasd meg (kód + teszt), hogy a kimenő `Turn` lista mezői 1:1 megfelelnek a
`SessionIngressEnvelope` schema turn-mezőinek (vagy ha eltérés van, indokold
és dokumentáld a "Decisions Proposed" szekcióban).

## Nem cél

- a 6 hook script megépítése (`session-ingest-hook-sandboxed-001`, KÜLÖN job)
- éles `settings.json` bármilyen módosítása — ez a job KIZÁRÓLAG egy
  fájl-bemenetű olvasó modult épít, sosem nyúl hook-konfigurációhoz
- a worker loop / outbox bekötése (a kimenő Turn-lista beillesztése az
  outbox-ba egy KÉSŐBBI, ezt a modult HÍVÓ lépés, nem ennek a jobnak a
  hatóköre)

## Required Output Files

- `output/session-transcript-reader.md`
- a transcript reader modul (pl. `session_store/transcript_reader.py`)
- a hozzá tartozó teszt-fájl

## Required Report Sections

```markdown
# session-transcript-reader-001 Output

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
`missing`, `rejected`, `unknown`. `proven` az idempotencia-állításra
KIZÁRÓLAG akkor használható, ha a TÉNYLEGES, futtatott teszt kimenete idézve
van — a kód megírása nem bizonyítja, hogy helyesen fut.

## Definition Of Done

- [ ] valódi (vagy a dokumentált formátumot pontosan követő, fixture-ként
      jelölt) transcript JSONL sor-szerkezet idézve
- [ ] `read_transcript_incremental()` (vagy ekvivalens) implementálva,
      file:line hivatkozással
- [ ] stabil, tartalom-alapú turn id (NEM `uuid4()`)
- [ ] tool_use/tool_result párosítás valós teszttel bizonyítva
- [ ] idempotencia (második olvasás csak az ÚJ sorokat adja) valós,
      futtatott teszttel bizonyítva, TÉNYLEGES pytest kimenettel
- [ ] `SessionIngressEnvelope` illesztés bemutatva vagy az eltérés indokolva
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a modul léte a repóban ≠ implemented — a futtatott teszt kimenete
  bizonyít, a kód megírása nem
- a hook payload önmagában elegendő az assistant válasz tartalmához (NEM —
  ez pontosan az a hiba, amit ez a job zár)
- `uuid4()` vagy más, a tartalomtól független turn id (megtöri az
  idempotens re-ingestiont)
- bármilyen írás `~/.claude/settings.json`-ba vagy
  `~/.claude-personal/settings*.json`-ba — ez a job KIZÁRÓLAG egy
  transcript-olvasó modult épít, hook-bekötéshez nem nyúl
- az idempotencia-állítás bizonyítása EGYETLEN olvasással (mindkét olvasást
  — első és második — meg kell mutatni, a második kimenetével együtt)

## Git instrukciók

Push a `feature/session-transcript-reader-001` branch-re, KIZÁRÓLAG a
`cic-mcp-session` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell
pusholni, elég a lokális commit). Main-re az agent NEM pushol. **NE
módosítsd a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek/kód angolul.
