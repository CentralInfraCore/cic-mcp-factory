# Job: historical-dedupe-idempotency-001

## Kontextus

Phase 5 MÁSODIK jobja. A `historical-chatgpt-export-importer-001` (mergelve)
KONTRAKTUS-szinten definiálta a mezőleképezést (`conversation_id`/`id` →
`provider_session_id`, `message.create_time` → `occurred_at`, teljes `message`
objektum → `payload`, `provider` = `"chatgpt-export"`, `provider_event_name` =
`author.role`), és a dedupe-formula ELÉGSÉGESSÉGÉT LOGIKAILAG levezette — de a saját
Claim-Evidence Matrix-a ezt `partial`-ként jelölte: **"NINCS valós, futtatott teszt két
egymást átfedő export-futásra (csak logikai levezetés a schema garanciáiból)"**.

Ez a job ezt a hiányt zárja le: TÉNYLEGES converter-kódot ír (ChatGPT export
message-node → `SessionIngressEnvelope`), és VALÓS Postgres teszttel bizonyítja a
dedupe-ot. A `cic-mcp-session` repóban a generikus dedupe-mechanizmus (`ON CONFLICT
(idempotency_key) DO NOTHING`) MÁR létezik és MÁR tesztelt
(`tests/test_session_store/test_envelope_writer.py:148`
`test_duplicate_idempotency_key_is_noop_not_duplicate` — generikus envelope-on). EZ a
job NEM ezt a generikus mechanizmust teszteli újra — a converter-specifikus
helyességet teszteli: hogy a ChatGPT export-mezőkből SZÁMÍTOTT `idempotency_key`
(`occurred_at` normalizálással, `raw_payload_hash`-sel) ugyanazt a kulcsot adja-e egy
változatlan üzenet ÚJRA-importálásakor.

**KRITIKUS BIZTONSÁGI HATÁR — OLVASD EL MIELŐTT BÁRMIT TENNÉL:**

A teszt-fixture KIZÁRÓLAG SZINTETIKUS, KÉZZEL/KÓDDAL FABRIKÁLT adat lehet — SOHA nem
a `historical-chatgpt-export-importer-001`-ben vizsgált valódi, személyes export-bundle
tartalma (sem részlet, sem anonimizált forma belőle). A korábbi job kizárólag
STRUKTÚRÁT idézett a valódi bundle-ből (mező-nevek, enum-értékek, aggregát számok) —
ez a job AZ ALAPJÁN a struktúrán felépített, teljesen kitalált tartalommal (pl.
`"role": "user"`, `"content": {"content_type": "text", "parts": ["hello world test
message"]}`, fabrikált `conversation_id` mint `"test-conv-0001"`) dolgozik. Ha
bármilyen kétség merül fel afelől, hogy egy fixture-mező valós exportból származna,
NE használd — fabrikálj helyette egy nyilvánvalóan szintetikus értéket.

## Target

- target repo: `cic-mcp-session`
- target path: `output/historical-dedupe-idempotency.md` + a converter-implementáció +
  a hozzá tartozó pytest fájl
- change_type: `new_capability`
- status_after_merge: `candidate`
- status indoklás: ELLENTÉTBEN a `historical-chatgpt-export-importer-001`
  kontraktus-riporttal (ami `experimental` maradt, mert nem volt futtatható kód), EZ a
  job TÉNYLEGES, futtatható converter-kódot ír ÉS valós Postgres-teszttel bizonyítja —
  ez megfelel a `gateway-session-adapter-contract-001` → `session-context-pack-v1-001`
  mintának (kontraktus → implementáció + valós teszt = `candidate`)

## Sources

- **KÖTELEZŐ elsődleges forrás (a `cic-mcp-factory` repo `main`-jén, MÁR ott van):**
  - `${WORKDIR}/jobs/index.yaml` — prerequisite-ellenőrzéshez `- id: "<job-id>"`
    kulccsal
  - `${WORKDIR}/jobs/historical-chatgpt-export-importer-001/output/historical-chatgpt-
    importer-design.md` — TELJES egészében, NORMATÍV. A "conversations-*.json To
    SessionIngressEnvelope Mapping" tábla a converter PONTOS specifikációja — NE
    találd ki újra, kövesd 1:1.
  - `${WORKDIR}/jobs/session-ingress-envelope-contract-001/output/session-ingress-
    envelope.schema.yaml` — `idempotency_key` (214-247. sor, 5 komponensű formula,
    `occurred_at`-tal — lásd az importer-design report korrekcióját), `raw_payload_hash`
- **MÁSODIK forrás (a `cic-mcp-session` repo, KLÓNOZVA ehhez a jobhoz):**
  - `cic-mcp-session/session_store/envelope_writer.py` — `insert_envelope()`
    (165-232. sor), KÜLÖNÖSEN a `ON CONFLICT (idempotency_key) DO NOTHING` (199. sor)
    és `validate_envelope()` (105. sor körül) — EZT a függvényt HÍVD a converterből,
    NE írj új insert-logikát
  - `cic-mcp-session/tests/test_session_store/test_envelope_writer.py` — KÖVESD ezt a
    MEGLÉVŐ teszt-mintát (`pg_config` fixture, `_clean_envelopes_table`, `_count_rows`
    helper-ek, `test_duplicate_idempotency_key_is_noop_not_duplicate` mint közvetlen
    minta a 148. sor körül) — NE találj fel új Postgres-fixture-mechanizmust

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál
3. Erősítsd meg ÚJRA a "KRITIKUS BIZTONSÁGI HATÁR" szabályait

## Feladat

### 1. Prerequisite-ellenőrzés

```
grep -n '\- id: "historical-chatgpt-export-importer-001"' -A 3 jobs/index.yaml
grep -n '\- id: "session-raw-event-store-001"' -A 3 jobs/index.yaml
```

Idézd a kimenetet, erősítsd meg mindkettő `status: "done"`. Ha NEM, NO-GO és állj meg.

### 2. Converter implementáció

Először GREP-pel erősítsd meg az `insert_envelope`/`ON CONFLICT` tényleges call-chain-jét
(teszt-fájlok kizárva):

```
grep -rn "def insert_envelope\|ON CONFLICT" session_store/envelope_writer.py | grep -v test_
```

Idézd a kimenetet — ez a `file:line` hivatkozás, amely bizonyítja, hogy a dedupe-
mechanizmus a converter ALATT már létezik és nem kell újraírni.

Írj egy függvényt (pl. `session_store/chatgpt_import.py`, `chatgpt_message_to_envelope
(conversation: dict, node: dict, provider_session_id: str) -> dict` szignatúrával vagy
hasonlóval), amely EGY ChatGPT export `mapping`-node-ot (a
`historical-chatgpt-importer-design.md` mezőleképezése szerint) egy érvényes
`SessionIngressEnvelope` dict-té alakít:

- `provider` = `"chatgpt-export"`
- `provider_session_id` = a conversation `conversation_id`/`id`
- `provider_event_name` = `message.author.role`
- `occurred_at` = `message.create_time` RFC3339 UTC-re normalizálva (a schema 230.
  sora szerint, másodperc-pontossággal)
- `payload` = a teljes `message` objektum
- `raw_payload_hash` = a `payload` JSON-szerializációjának SHA-256 hash-e (vagy ezzel
  ekvivalens determinisztikus hash — a schema `raw_payload_hash` mező leírása szerint)
- `idempotency_key` = a schema 5-komponensű formulája szerint számolva (importáld vagy
  hívd a schema/séma szerinti logikát, NE duplikáld kézzel, HA van már segédfüggvény a
  repóban a hash-számításra — ha NINCS, írd meg ezt is, és idézd a `file:line`-t ahol
  definiálva van)
- a `SessionIngressEnvelope` egyéb kötelező mezői (lásd schema `required` listája) a
  historikus kontextushoz illő, indokolt konstans/levezetett értékkel

A converter NE hívjon DB-t direktben — adja vissza a dict-et, a hívó oldal hívja
`insert_envelope()`-ot.

### 3. Szintetikus teszt-fixture + valós Postgres teszt

Írj egy pytest fájlt (pl. `tests/test_session_store/test_chatgpt_import.py`), amely:

1. fabrikál egy SZINTETIKUS ChatGPT export `conversation`+`mapping`-node struktúrát
   (lásd "KRITIKUS BIZTONSÁGI HATÁR" — kitalált tartalom, NEM valós export-adat)
2. a converterrel `SessionIngressEnvelope`-dá alakítja
3. `insert_envelope()`-pal beszúrja (a MEGLÉVŐ `pg_config`/`_clean_envelopes_table`
   fixture-mintát követve)
4. UGYANAZT a szintetikus node-ot MÉG EGYSZER konvertálja és beszúrja (re-import
   szimulációja)
5. ASSERT: a sorok száma a táblában PONTOSAN 1 marad a második beszúrás után is (a
   `_count_rows` helper-rel, a meglévő teszt-minta szerint)
6. (opcionális, de ajánlott) egy MÁSIK szintetikus node-dal (más `occurred_at` VAGY
   más `role`) bizonyítsd, hogy AZ nem ütközik az elsővel — külön sort kap

Futtasd le a tesztet VALÓS Postgres ellen (a meglévő `pg_config` fixture
kapcsolódási módja szerint — docker-compose vagy a repo Makefile szerint, NE mockolt
DB-vel), és idézd a TÉNYLEGES teszt-futás kimenetét (`pytest -v` output, `N passed`)
a riportban.

## Nem cél

- a teljes export-bundle (`conversations-NNN.json` shard-ok) bejárásának/batch-
  feldolgozásának implementálása (ez egy KÉSŐBBI, performance-fókuszú job —
  `historical-chatgpt-importer-design.md` "Rejected / Out Of Scope" listájának
  megfelelően a `mapping` fa-bejárási sorrend is nyitott kérdés marad)
- a `mapping` fa-bejárási algoritmus (DFS/BFS sorrend) eldöntése — a converter EGY
  node-ot alakít át, a hívó oldal felelőssége a bejárás
- a `SessionIngressEnvelope` schema módosítása
- VALÓDI export-bundle bármilyen tartalmának felhasználása teszt-fixture-ként

## Required Output Files

- `output/historical-dedupe-idempotency.md`
- a converter-implementáció (pl. `session_store/chatgpt_import.py`)
- a teszt-fájl (pl. `tests/test_session_store/test_chatgpt_import.py`)

## Required Report Sections

```markdown
# historical-dedupe-idempotency-001 Output

## Scope
## Inputs Read
## Prerequisite Check
## Converter Implementation
## Synthetic Test Fixture (No Real Export Content)
## Real Postgres Test Run — Dedupe Proof
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
`proven` a "a teszt zöld" állításra KIZÁRÓLAG akkor használható, ha a TÉNYLEGES
`pytest` futás kimenete (parancs + output) idézve van — a teszt fájl léte ≠
implemented (ez egyetlen soron), a teszt megírása nem bizonyítja, hogy futott és
zöld.

## Definition Of Done

- [ ] mindkét prerequisite `id:` kulccsal megerősítve, GO/NO-GO döntés indokolva
- [ ] converter implementáció a `historical-chatgpt-importer-design.md`
      mezőleképezését 1:1 követi, `file:line` hivatkozással
- [ ] szintetikus teszt-fixture, SEMMILYEN valós export-tartalom nélkül
- [ ] valós Postgres teszt PARANCS + KIMENET idézve, mutatva hogy a második
      beszúrás után a sorok száma változatlan (dedupe bizonyítva)
- [ ] claim-evidence tábla kitöltve, nem üres
- [ ] SEMMILYEN tényleges beszélgetés-tartalom a VALÓDI export-bundle-ből nem
      jelenik meg sehol (kódban, tesztben, riportban)

## Forbidden Shortcuts

- bármilyen valós export-bundle tartalom (akár részlet, akár anonimizált) használata
  teszt-fixture-ként
- a dedupe-ot kizárólag logikai levezetéssel állítani bizonyítottnak, futtatott
  Postgres teszt nélkül
- a `historical-chatgpt-importer-design.md` mezőleképezésének újra-kitalálása/
  felülírása a converterben
- a fájl/teszt léte ≠ implemented (ez egyetlen soron) — a `pytest` kimenete bizonyít,
  a fájl megemlítése nem
- a generikus `test_duplicate_idempotency_key_is_noop_not_duplicate` teszt
  megismétlése/lemásolása ÚJ assertion nélkül — ennek a jobnak a converter-specifikus
  helyességet kell bizonyítania, nem a már bizonyított generikus mechanizmust

## Git instrukciók

Push a `feature/historical-dedupe-idempotency-001` branch-re, KIZÁRÓLAG a
`cic-mcp-session` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni,
elég a lokális commit). Main-re az agent NEM pushol. **NE módosítsd a `meta.yaml`
`status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek/kód angolul.
