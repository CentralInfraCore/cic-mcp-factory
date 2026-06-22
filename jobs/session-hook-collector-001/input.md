# Job: session-hook-collector-001

## Kontextus

A `session-raw-event-store-001` job megírta a write-path-ot (`insert_envelope()`), de
SOSEM volt valódi forrása — minden eddigi envelope ennek a repónak a TESZTJEIBEN, KÉZZEL
konstruált fixture-ként került be (`_valid_envelope()`/`_run_chain_for_envelope()` minták
a `tests/test_session_store/*.py` fájlokban). A `source.collector` mező minden ilyen
fixture-ben `"log-event.py"` — egy fájl, ami EDDIG SOSEM lett megírva.

Ez a job megírja az ELSŐ valódi producer-t: egy Claude Code HOOK szkriptet, ami egy
valódi Claude Code session eseményéből (stdin JSON) tölt fel egy
`SessionIngressEnvelope`-ot és hívja a MEGLÉVŐ `insert_envelope()`-et.

**A LEGFONTOSABB MEGSZORÍTÁS**: a Claude Code hook-ok BLOKKOLJÁK a tényleges
session-t/tool-hívást, amíg a hook script lefut. Ha ez a szkript egy DB-hibán
elszáll vagy blokkoló exit code-dal tér vissza, EGY ROSSZ POSTGRES-KAPCSOLAT KÉPES
TÖNKRETENNI A FELHASZNÁLÓ TÉNYLEGES CLAUDE CODE SESSION-JÉT. Ez NEM ALKU KÉPES —
ugyanolyan súlyú gate, mint a `session-mcp-config-wiring-001` "nincs secret a
tpl-ben" szabálya.

## Target

- target repo: `cic-mcp-session`
- target path: ÚJ fájl, pl. `hooks/log-event.py` (a meglévő fixture-ök
  `source.collector` mezője ezt a nevet várja — ha más nevet/helyet választasz,
  indokold és frissítsd a riportban, hogy ez eltér a konvenciótól)
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: a script logikája KONSTRUÁLT, a dokumentált hook-kontraktusnak
  megfelelő minta-payload-okkal bizonyítva, de SOSEM futott valódi, élő Claude Code
  session ellen — `candidate`-hez egy tényleges, élő session általi meghívás kellene

## Sources

- `${WORKDIR}/.cic-context/factory-docs/job-slices.yaml` —
  `session-hook-collector-001` bejegyzés — NORMATÍV
- **KÖTELEZŐ elsődleges forrás (mind már a `cic-mcp-session` `main`-en van):**
  - `cic-mcp-session/session_store/envelope_writer.py` — `insert_envelope()`,
    `validate_envelope()`, `REQUIRED_FIELDS`, `SessionStoreConfig.from_env()` — EZT
    hívd, NE írd újra a write-path logikát
  - `cic-mcp-session/tests/test_session_store/*.py` — `_valid_envelope()` minta
    (MINDEN tesztfájlban hasonló) — ez a SessionIngressEnvelope KONKRÉT alakja, amit
    a script-nek elő kell állítania
  - `cic-mcp-session/session_store/turn_projector.py` — `map_role()`,
    `PROVIDER_EVENT_NAME_TO_ROLE` — a `provider_event_name` ismert értékei
    (`UserPromptSubmit`, `PostToolUse`, `PreToolUse`, `Stop`, stb.) — ez mutatja, hogy
    a downstream feldolgozás MELYIK hook-eseményeket várja
  - `cic-mcp-session/session_store/chunk_indexer.py` — `extract_source_refs()` és a
    `TOOL_NAME_KEY`/`FILE_PATH_KEYS`/`NESTED_TOOL_INPUT_KEY` konstansok — ez mutatja,
    hogy a downstream provenance-kinyerés MILYEN payload-alakot vár
    (`tool_name`, `tool_input.file_path`/`path`/`notebook_path`)
- **Claude Code hook-kontraktus**: a hook stdin JSON pontos mezőit (`session_id`,
  `transcript_path`, `cwd`, `hook_event_name`, és esemény-specifikus mezők:
  `tool_name`/`tool_input`/`tool_response` PreToolUse/PostToolUse-nál, `prompt`
  UserPromptSubmit-nál) a SAJÁT TUDÁSODBÓL vagy elérhető dokumentációból deríts ki —
  EXPLICIT idézd/hivatkozd a forrást a "Decisions Proposed"-ben, ne találd ki
  találólag a mezőneveket

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti KÖTELEZŐ forrásokat, MIELŐTT bármilyen kódot írnál

## Feladat

### 1. Valódi Postgres teszt-instance + teljes lánc alkalmazása

Indíts egy valódi Postgres instance-t (`pgvector/pgvector:pg16`, lokálisan cache-elve), és
alkalmazd EGYMÁS UTÁN az összes meglévő SQL fájlt. **Egyfordulós végrehajtási
fegyelem**: fejezd be a teljes munkát egyetlen menetben.

### 2. A hook script

Írd meg a script-et úgy, hogy:
- stdin-ről olvassa a Claude Code hook JSON-t
- determinisztikusan map-eli egy `SessionIngressEnvelope` dict-té (lásd Sources —
  `_valid_envelope()` alak): `provider="claude-code"`, `provider_session_id` = a
  hook JSON session_id mezője, `provider_event_name` = a hook JSON
  `hook_event_name` mezője, `source={"kind": "hook", "collector": "<a script
  fájlneve>"}`, `payload` = a TELJES nyers hook JSON (vagy indokolt részhalmaza),
  `occurred_at`/`ingested_at` = jelenlegi UTC idő, `raw_payload_hash` = sha256 a
  nyers payload-ról, `trust="session_local"`, `canonical=False`,
  `interpreted=False`
- hívja a MEGLÉVŐ `insert_envelope()`-et
- **SOHA nem blokkolja/nem utasítja el a tényleges Claude Code hívást** — minden
  kivételt (DB-kapcsolati hiba, validációs hiba, bármi) elkapsz, stderr-re/lokális
  fájlba logolsz, és olyan exit code-dal térsz vissza, ami NEM blokkolja a Claude
  Code műveletet

### 3. Determinisztikus idempotency_key

Javasolj és indokolj egy determinisztikus (NEM véletlenszerű) `idempotency_key`
levezetési stratégiát — a Claude Code hook JSON nem feltétlenül ad egyetlen, egyedi
esemény-azonosítót. Dokumentáld a választott mezőket és a trade-off-ot
(álpozitív/álnegatív duplikáció-kockázat) a "Decisions Proposed"-ben.

### 4. Négy konstruált minta-payload teszt

Hozz létre legalább 4, a dokumentált hook-kontraktusnak megfelelő MINTA JSON
payload-ot (`PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `Stop`), és add őket a
script stdin-jére. Bizonyítsd SQL-lekérdezéssel, hogy mindegyikre helyes alakú
`session_raw.envelopes` sor keletkezik.

### 5. DB-elérhetetlenség szimulációja — KÖTELEZŐ

Állítsd le a teszt Postgres konténert, futtasd a script-et egy ÚJ minta-payload-dal,
és bizonyítsd, hogy a script EXIT CODE-ja/viselkedése UGYANAZ marad (nem blokkoló),
mint sikeres esetben — idézd az exit code-ot mindkét állapotban (konténer fut / nem
fut).

### 6. Példa `.claude/settings.json` hook-konfiguráció

Adj egy DOKUMENTÁLT (NEM aktivált, NEM telepített) `.claude/settings.json`
hook-bekötési mintát a riportba, ami megmutatja, hogyan kötné be egy valódi Claude
Code session a `PreToolUse`/`PostToolUse`/`UserPromptSubmit`/`Stop` eseményeket erre
a script-re.

### 7. Regresszió-ellenőrzés

Futtasd le a TELJES meglévő `tests/test_session_store/` suite-ot, bizonyítva hogy
semmi nem regresszált.

## Nem cél

- a script TÉNYLEGES aktiválása/telepítése bármilyen éles `.claude/settings.json`-ba
- `insert_envelope()`/`validate_envelope()` módosítása — KIZÁRÓLAG hívod, nem írod
  újra
- bármilyen állítás, hogy ez egy VALÓDI, élő Claude Code session ellen futott —
  CSAK konstruált minta-payload-okkal tesztelt
- teljesítmény-optimalizálás, retry-logika, batch-elés
- monitoring/alerting integráció

## Required Output Files

- `output/session-hook-collector-report.md`

## Required Report Sections

```markdown
# session-hook-collector-001 Output

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
`proven` KIZÁRÓLAG akkor használható, ha a tényleges script-futtatás kimenete (SQL
lekérdezés + exit code) idézve van — valódi Postgres ellen. A script léte a fájlban
≠ működik — csak a tényleges futtatás bizonyít.

## Definition Of Done

- [ ] a hook script létrejött, `insert_envelope()`-et hívja, fájl:sor hivatkozással
- [ ] a hook JSON → envelope mezőleképezés táblázatban dokumentálva, forrás-
      hivatkozással
- [ ] determinisztikus `idempotency_key` stratégia indokolva
- [ ] mind a 4 minta-payload (PreToolUse/PostToolUse/UserPromptSubmit/Stop) lefuttatva,
      tényleges SQL-eredmény idézve mindegyikre
- [ ] DB-elérhetetlenség szimuláció lefuttatva, az exit code/viselkedés azonossága
      bizonyítva mindkét állapotban
- [ ] példa `.claude/settings.json` hook-konfiguráció a riportban, EXPLICIT "nincs
      aktiválva" kijelentéssel
- [ ] teljes meglévő teszt-suite lefuttatva, regresszió-mentesség bizonyítva
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- BÁRMILYEN kódútvonal, ahol egy DB/network hiba blokkolhatja/elutasíthatja/
  hibásan jelezheti a TÉNYLEGES Claude Code tool-hívást/session-t — TILOS, nem
  alku képes
- véletlenszerű/nem-determinisztikus `idempotency_key` használata
- `insert_envelope()`/`validate_envelope()` újraírása/módosítása
- azt állítani, hogy ez valódi, élő Claude Code session ellen tesztelt, amikor csak
  konstruált minta-payload-okkal volt tesztelve
- a hook TÉNYLEGES telepítése/aktiválása bármilyen éles `.claude/settings.json`-ba

## Git instrukciók

Push a `feature/session-hook-collector-001` branch-re, KIZÁRÓLAG a `cic-mcp-session`
célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni, elég a lokális
commit). Main-re az agent NEM pushol. A teszteléshez használt Docker konténert a
munka végén állítsd le és töröld. **NE módosítsd a `meta.yaml` `status` mezőjét**
sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/teszt-nevek angolul.
