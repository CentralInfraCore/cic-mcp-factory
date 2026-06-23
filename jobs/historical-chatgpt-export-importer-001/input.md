# Job: historical-chatgpt-export-importer-001

## Kontextus

Phase 5 ELSŐ jobja — a `SessionIngressEnvelope` schema (`session-ingress-envelope-
contract-001`) és a Postgres tárolási réteg (`session-postgres-storage-design-001`)
MÁR stabil. Ez a job KONTRAKTUS-szintű riport (NEM implementáció): definiálja, hogyan
fordítaná egy importer egy VALÓDI ChatGPT export-bundle tartalmát
`SessionIngressEnvelope` rekordokká.

**KRITIKUS BIZTONSÁGI HATÁR — OLVASD EL MIELŐTT BÁRMIT TENNÉL:**

A forrás egy VALÓDI, SZEMÉLYES ChatGPT export-bundle (`${CHATGPT_EXPORT_DIR}` — a
tényleges abszolút útvonalat az orchestrátor adja meg a futtatási promptban, NEM
ebben a fájlban van rögzítve). Ez a könyvtár NEM git-repo, NEM kerül klónozásra, és
SOHA nem szabad belőle SEMMIT bemásolni egyetlen git-tracked helyre (`cic-mcp-session`
klón, `cic-mcp-factory` klón, vagy a riport maga) — sem nyers JSON-fájlt, sem
fájlrészletet. A riport (amely GitHub-ra kerül, PR-ben review-zhető, PUBLIKUS-an
látható) KIZÁRÓLAG a következőket idézheti:

- mező-NEVEKET és struktúrát (pl. `"mapping"` egy dict, kulcsai node-id-k, minden node
  `{id, message, parent, children}` alakú) — ez STRUKTURÁLIS metaadat, nem személyes
  tartalom
- enum-szerű ÉRTÉKEKET, amelyek NEM egyedi/azonosító jellegűek (pl. `role` ∈
  {`system`,`user`,`assistant`,`tool`}, `content_type` ∈ {`text`,`code`,...}) — ezek
  GYAKORI, nem-egyedi kategória-értékek, NEM személyes tartalom
- AGGREGÁLT STATISZTIKÁKAT (pl. "X darab `conversations-NNN.json` fájl van", "egy
  minta-fájlban Y conversation-objektum található", "egy adott conversation
  `mapping`-jében átlagosan Z node van")

**SZIGORÚAN TILOS** a riportban idézni: tényleges `message.content.parts` szöveget
(felhasználói/assistant üzenet-tartalmat), `title` mező értékét, `conversation_id`/
`id` konkrét UUID-jét, fájlnevet egy konkrét melléklet-fájlból (a `file_*`/`file-*`
prefixű melléklet-fájlok NEVE is tartalmazhat személyes információt egy eredeti
fájlnévből), `user.json`/`user_settings.json` TARTALMÁT. Ha egy állítást csak konkrét
tartalom idézésével lehetne bizonyítani, írd le STRUKTURÁLISAN ("egy `message.content`
objektum `parts` mezője string-lista, az első elem hossza tipikusan N karakter") a
tényleges szöveg helyett.

## Target

- target repo: `cic-mcp-session`
- target path: `output/historical-chatgpt-importer-design.md`
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: kontraktus-riport, nincs futtatható importer-kód — `candidate`-hez
  egy tényleges implementáció és legalább egy valós, futtatott bizonyíték kellene (a
  `gateway-session-adapter-contract-001` → `session-context-pack-v1-001` mintát
  követve), DE a valós futtatás akkor is KIZÁRÓLAG STRUKTURÁLIS/aggregált kimenetet
  idézhetne, sosem tartalmat

## Sources

- `${WORKDIR}/.cic-context/corpus/normalized/thead-review-2026-06-20.yaml` —
  "rag_implications" + "recommended_next_actions" szekció (NORMATÍV — ez a job innen
  ered)
- `${WORKDIR}/.cic-context/factory-docs/execution-phases.md` — "Phase 5" szekció
- **KÖTELEZŐ elsődleges forrás (a `cic-mcp-factory` repo `main`-jén, MÁR ott van):**
  - `${WORKDIR}/jobs/index.yaml` — prerequisite-ellenőrzéshez `- id: "<job-id>"`
    kulccsal (NEM `job_id:` — lásd korábbi job-spec hibafelfedezés)
  - `${WORKDIR}/jobs/session-ingress-envelope-contract-001/output/session-ingress-
    envelope.schema.yaml` — a TELJES `SessionIngressEnvelope` schema, KÜLÖNÖSEN
    `idempotency_key` (214-246. sor körül: `sha256(provider + "\x1f" +
    provider_session_id + "\x1f" + (provider_event_name or "") + "\x1f" +
    raw_payload_hash)`), `raw_payload_hash`, `provider_session_id`,
    `provider_event_name`
  - `${WORKDIR}/jobs/session-postgres-storage-design-001/output/` — a meglévő
    perzisztencia-réteg (ha a riport-fájl megtalálható, idézd; ha nem, jelezd a
    "Findings"-ban és a `session-postgres-schema.sql`-ből idézz helyette)
- **KÖTELEZŐ MÁSODIK forrás — a VALÓDI export-bundle, KIZÁRÓLAG STRUKTURÁLIS
  vizsgálatra (lásd "KRITIKUS BIZTONSÁGI HATÁR" fent):**
  - `${CHATGPT_EXPORT_DIR}` — a tényleges útvonalat az orchestrátor adja meg

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál
3. Erősítsd meg ÚJRA a "KRITIKUS BIZTONSÁGI HATÁR" szabályait, MIELŐTT az export-
   bundle-t megnyitnád

## Feladat

### 1. Prerequisite-ellenőrzés

```
grep -n '\- id: "session-ingress-envelope-contract-001"' -A 3 jobs/index.yaml
grep -n '\- id: "session-postgres-storage-design-001"' -A 3 jobs/index.yaml
```

Idézd a kimenetet, erősítsd meg mindkettő `status: "done"`. Ha NEM, NO-GO és állj meg.

### 2. Export-bundle TÉNYLEGES struktúrájának feltérképezése (kizárólag struktúra)

Vizsgáld meg `${CHATGPT_EXPORT_DIR}` TOP-LEVEL tartalmát (`ls`, fájlnév-MINTÁK, NEM
fájl-TARTALOM, kivéve a séma-feltáráshoz feltétlenül szükséges JSON-kulcs-listázást).
Konkrétan dokumentáld:

- a tényleges fájlszerkezet (pl. egyetlen `conversations.json` VAGY sharded
  `conversations-NNN.json` fájlok — melyik van TÉNYLEGESEN ebben a bundle-ben, ne
  feltételezd az egyik vagy másik formátumot)
- egy `conversations-*.json` fájl top-level Python/JSON kulcsai EGY conversation-
  objektumon (`python3 -c "import json; d=json.load(open(...)); print(sorted(d[0].keys()))"`
  típusú, KIZÁRÓLAG kulcs-listázó parancs, SOHA nem `print(d[0])` vagy ehhez hasonló
  teljes-objektum kiírás)
- a `mapping` mező belső node-struktúrája (`{id, message, parent, children}`)
- a `message`/`message.author`/`message.content` mező-nevei (NEM értékei, kivéve a
  `role`/`content_type` enum-kategóriákat, amelyek nem egyediek)
- milyen egyéb top-level fájlok vannak (`user.json`, `user_settings.json`,
  `message_feedback.json`, `shared_conversations.json`, `export_manifest.json` — CSAK
  a LÉTÜKET és a NEVÜKET dokumentáld, a tartalmukat NE nyisd meg/idézd, mert ezek
  egyediebb/személyesebb adatot tartalmazhatnak, mint a conversation-objektumok maguk)
- VAN-e markdown-export is a bundle-ben (a job-slices.yaml "Report treats markdown
  export as backup, not source-of-truth when structured export exists" elvárása
  szerint) — ha nincs, jelezd ezt is

### 3. `conversations-*.json` → `SessionIngressEnvelope` mezőleképezés

Tábla formátumban: export-mező → `SessionIngressEnvelope` mező → megjegyzés.
KÖTELEZŐ minimum:
- `conversation_id`/`id` → `provider_session_id` (egy `chatgpt-export` `provider`
  alá) — DE NE idézd a tényleges UUID-értéket, csak a MEZŐ-megfelelést
- `mapping[node].message.create_time` → `occurred_at`
- `mapping[node].message.author.role` → szerepe a `payload`/projection logikában
  (NEM `SessionIngressEnvelope` mező, csak megjegyzés, hogy ez `turn_projector`
  oldali bemenet lesz egy jövőbeli implementációban)
- a TELJES `mapping[node].message` objektum (vagy a releváns alrésze) →
  `payload` (a `SessionIngressEnvelope.payload` "stored AS-IS" garanciája szerint —
  idézd ezt a garanciát a schema-fájlból)
- `provider` = konstans `"chatgpt-export"` (vagy hasonló, NEM `"claude-code"`)
- `provider_event_name` — definiáld, mi felelne meg neki egy historikus üzenetnél
  (pl. az `author.role` maga, vagy egy `"historical_message"` konstans — indokold a
  választást)

### 4. Dedupe/idempotency

A `SessionIngressEnvelope.idempotency_key` MÁR definiált hash-formula
(`sha256(provider + provider_session_id + provider_event_name + raw_payload_hash)`,
idézve a schema-fájlból). Definiáld: egy historikus importernél ez a formula
ELÉGSÉGES-e a dedupe-hoz, VAGY szükséges-e kiegészítés (pl. egy `conversations-*.json`
export ÚJRA-FUTTATÁSAKOR — ha a felhasználó egy frissebb exportot tölt fel, amely
RÉSZBEN átfedi a korábbit — a `idempotency_key` MÁR garantálja, hogy ugyanaz a
`(provider, provider_session_id, provider_event_name, raw_payload_hash)` kombináció
nem duplikálódik). Indokold, hogy ez MIÉRT elég (vagy miért nem).

### 5. Markdown export mint backup, NEM source-of-truth

Mondd ki EXPLICIT: ha a bundle-ben VAN strukturált `conversations-*.json` (vagy
`conversations.json`), az importer EZT használja elsődleges forrásként — egy
esetleges markdown-export (ha létezik) csak BACKUP/bootstrap-corpus, NEM az
elsődleges import-útvonal. Idézd a `thead-review-2026-06-20.yaml` "rag_implications"
megfelelő sorát.

## Nem cél

- tényleges importer-kód implementálása
- a `SessionIngressEnvelope` schema módosítása
- a `cic-mcp-session`/`cic-mcp-factory` repók módosítása az export-bundle-ből
  KIVONT tartalommal (csak STRUKTURÁLIS leírás kerülhet a riportba)
- bármilyen fájl/adat bemásolása az export-bundle-ből egy git-tracked helyre
- `historical-dedupe-idempotency-001` (a Phase 5 másik jobja — a tényleges
  dedupe-implementáció RÁ van bízva)

## Required Output Files

- `output/historical-chatgpt-importer-design.md`

## Required Report Sections

```markdown
# historical-chatgpt-export-importer-001 Output

## Scope
## Inputs Read
## Prerequisite Check
## Export Bundle Structure (Structural Only — No Content Quoted)
## conversations-*.json To SessionIngressEnvelope Mapping
## Dedupe/Idempotency Strategy
## Markdown Export As Backup, Not Source-of-Truth
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
`proven` egy "az export ezt a mezőt tartalmazza" állításra KIZÁRÓLAG akkor használható,
ha a TÉNYLEGES kulcs-listázó parancs kimenete idézve van — a mező megemlítése nem
bizonyítja a tényleges struktúrát, csak a kulcs-listázás bizonyít. UGYANAKKOR: a
kulcs-listázás SOHA nem terjedhet ki érték-kiíratásra (lásd "KRITIKUS BIZTONSÁGI
HATÁR").

## Definition Of Done

- [ ] mindkét prerequisite `id:` kulccsal megerősítve, GO/NO-GO döntés indokolva
- [ ] az export-bundle TÉNYLEGES struktúrája (sharded vs. egységes
      `conversations.json`) dokumentálva, kulcs-listázó parancs kimenetével — TARTALOM
      idézése nélkül
- [ ] mezőleképezési tábla kész, az `idempotency_key`/`payload` garanciákra
      hivatkozva
- [ ] dedupe-stratégia indokolva
- [ ] markdown-export-mint-backup állítás explicit kimondva
- [ ] claim-evidence tábla kitöltve, nem üres
- [ ] SEMMILYEN tényleges beszélgetés-tartalom, cím, UUID, vagy melléklet-fájlnév NEM
      jelenik meg a riportban

## Forbidden Shortcuts

- markdown export forrásként kezelése, amikor strukturált export elérhető (a
  job-slices.yaml explicit tiltott rövidítése)
- BÁRMILYEN tényleges üzenet-tartalom, cím, UUID, fájlnév idézése a riportban
- BÁRMILYEN fájl/adat bemásolása az export-bundle-ből egy git-tracked helyre
- a fájl/mező léte ≠ implemented (ez egyetlen soron) — a kulcs-listázás bizonyít, a
  mező megemlítése nem

## Git instrukciók

Push a `feature/historical-chatgpt-export-importer-001` branch-re, KIZÁRÓLAG a
`cic-mcp-session` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni,
elég a lokális commit). Main-re az agent NEM pushol. **NE módosítsd a `meta.yaml`
`status` mezőjét** sehol. **NE commitolj SEMMIT az export-bundle könyvtárból.**

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek angolul.
