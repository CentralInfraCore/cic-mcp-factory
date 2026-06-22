# Job: shared-cross-session-search-001

## Kontextus

Phase 4 MÁSODIK jobja. A `shared-session-catalog-consumer-001` (mergelve) definiálta az
alap adapter-kontraktust: a `cic-mcp-shared` az MCP tool-határon keresztül fogyasztja a
`cic-mcp-session` katalógust, csak DERIVÁLT adatot (klaszterek, súlyozott jelöltek,
provenance-pointerek) perzisztál, a raw session-tartalmat sosem duplikálja. Az a riport
explicit DEFERRÁLTA a `search_session_context_fts`/`search_session_context_vector`
finomhangolását és a cross-session rangsorolás kérdését EZ a jobra (lásd
`output/shared-session-catalog-consumer.md` "Session MCP API Surface" záró bekezdése).

Ez a job KONTRAKTUS-szintű (NEM implementáció): definiálja, HOGYAN ismerne fel a
`cic-mcp-shared` egy VISSZATÉRŐ FOGALMAT több, különböző session-ben — anélkül, hogy
mély szemantikai claim-extraction-t végezne a session-rétegben (ez a `cic-mcp-session`
"Fő határok" "Nem" listájának sérülése volna: "végleges döntésbányászat" NEM session-
réteg feladat, és ez a job sem viheti át azt máshova rejtve). A keresztezett (konfliktus/
superseded) jelölt-kezelés adatmodelljét is itt definiáljuk.

**Kritikus határ** (job-slices.yaml `forbidden_shortcuts`): a cross-session keresés NEM
válhat canonical tudásgráffá, és a session-rétegben TILOS mély szemantikai
claim-extraction-t végezni — a "visszatérő fogalom" detektálás KIZÁRÓLAG lexikai/vektor-
hasonlóság (a már létező `search_session_context` hibrid RRF-fúzió) alapján történhet,
NEM egy új NLP/LLM-alapú entitás-kinyerő réteggel.

## Target

- target repo: `cic-mcp-shared`
- target path: `output/shared-cross-session-search.md`
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: kontraktus-riport, nincs futtatható kereszt-session kereső/aggregátor
  kód — `candidate`-hez egy tényleges implementáció és legalább egy valós, futtatott
  bizonyíték kellene (a `gateway-session-adapter-contract-001` →
  `session-context-pack-v1-001` mintát követve)

## Sources

- `${WORKDIR}/.cic-context/factory-docs/architecture.md` — "cic-mcp-shared" + "Fő
  határok" szekció
- `${WORKDIR}/.cic-context/factory-docs/execution-phases.md` — "Phase 4" szekció
- **KÖTELEZŐ elsődleges forrás (a `cic-mcp-factory` repo `main`-jén, MÁR ott van):**
  - `${WORKDIR}/jobs/index.yaml` — a prerequisite-ellenőrzéshez a `- id: "<job-id>"`
    kulccsal (FIGYELEM: NEM `job_id:` — ezt a kulcs-eltérést a
    `shared-session-catalog-consumer-001` riport "Findings" #1 pontja már felfedte és
    dokumentálta, ne ismételd meg a hibát)
  - `${WORKDIR}/jobs/shared-session-catalog-consumer-001/output/shared-session-catalog-
    consumer.md` — TELJES egészében, NORMATÍV (az "Adapter Contract Table" és a
    "Persisted vs. Live-Queried Split" a közvetlen alapja ennek a jobnak)
- **KÖTELEZŐ MÁSODIK forrás (a `cic-mcp-session` repo, KLÓNOZVA ehhez a jobhoz,
  KIZÁRÓLAG OLVASÁSRA — NE módosítsd):**
  - `cic-mcp-session/mcp-server/session_server.py` — `search_session_context`,
    `search_session_context_fts`, `search_session_context_vector` TÉNYLEGES
    szignatúrája (94-95, 150-151, 199-200. sor)
  - `cic-mcp-session/output/session-retrieval-quality-report.md` — az RRF-fúzió
    pontos mechanizmusa (ha létezik ilyen riport — ha nem található, jelezd a
    "Findings"-ban és a `session_store/` forrásból idézz helyette)
- **HARMADIK forrás (a `cic-mcp-shared` repo, a target):**
  - `cic-mcp-shared/CLAUDE.md` — "Fő határok", "Trust modell" szekció

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. Prerequisite-ellenőrzés

```
grep -n '\- id: "shared-session-catalog-consumer-001"' -A 3 jobs/index.yaml
```

Idézd a kimenetet, erősítsd meg `status: "done"`. Ha NEM, NO-GO és állj meg.

### 2. Visszatérő-fogalom detektálás — lexikai/vektor-hasonlóság, NEM szemantikai claim-extraction

Először GREP-pel erősítsd meg a 3 keresési tool tényleges szignatúráját:

```
grep -rn "@mcp.tool()" -A 1 mcp-server/session_server.py | grep -v test_
```

Definiáld a konkrét folyamatot: adott egy shared-oldali klaszter-leírás (rövid
szöveges kulcsszó/lekérdezés, NEM egy LLM által kivont "claim"), a shared aggregátor
HOGYAN használja a `search_session_context(session_id, query, limit)` hibrid tool-t N
KÜLÖNBÖZŐ session_id-re, hogy bizonyítékot gyűjtsön egy visszatérő fogalomhoz. Definiáld
explicit: a `query` paraméter MINDIG egy egyszerű kulcsszó/rövid mondat, amit a shared
réteg ÁLLÍT ELŐ (pl. egy korábbi klaszter-cím alapján) — NEM egy session-tartalomból
kivont, LLM-generált szemantikai "claim". Indokold, miért ez tartja be a
`forbidden_shortcuts` "deep semantic claim extraction performed inside the session
layer" tilalmát.

### 3. Cross-session query shape és rangsorolás

Definiáld a konkrét lépéssort: hány session-t kérdez le egy ciklus (pl. "az utolsó N
aktív session", `get_session_status`-szal szűrve), milyen sorrendben, és HOGYAN
kombinálja a több session `search_session_context` válaszának `fused_score`/`rank`
értékeit egy egységes cross-session rangsorba (pl. egyszerű összegzés/átlag, vagy
session-enkénti normalizálás szükséges-e a session-méret-különbségek miatt — indokold a
választást).

### 4. Konfliktus/superseded jelölt-kezelés adatmodellje

Definiáld: amikor KÉT, különböző session-ből származó bizonyíték EGYMÁSNAK
ELLENTMOND (pl. egy korábbi klaszter állítása és egy újabb session evidence-e
eltér), a shared hogyan jelöli ezt — egy `conflicting_with`/`superseded_by` mező a
saját `shared_core.*` jelölt-rekordon (analóg a `GatewayContextEnvelope.conflicts[]`
mintájával, de a shared SAJÁT adatmodelljén, NEM a gateway schema-ján). Definiáld: a
"superseded" döntés (egy régebbi jelölt egy újabb által felülírva) IS embert igényel-e,
vagy lehet-e automatikus heurisztika (pl. időbélyeg-alapú) — indokold a választást a
`cic-mcp-shared` trust modellje szerint (a `reviewed_shared`-hez vezető review-lépés
nélkül egy automatikus "superseded" jelölés se válhatna `canonical`-lá).

## Nem cél

- tényleges kereső/aggregátor kód implementálása
- LLM-alapú szemantikai claim-extraction vagy entitás-kinyerés bármilyen formában
  (ez explicit forbidden_shortcut)
- a `SessionIngressEnvelope`/`GatewayContextEnvelope` schema módosítása
- `cic-mcp-session` repo módosítása (KIZÁRÓLAG olvasásra klónozva)
- `shared-weighting-model-001` (a Phase 4 harmadik jobja — a tényleges súlyozási
  formula/score-számítás RÁ van bízva, ez a job csak a query-alak és a
  konfliktus-adatmodell)

## Required Output Files

- `output/shared-cross-session-search.md`

## Required Report Sections

```markdown
# shared-cross-session-search-001 Output

## Scope
## Inputs Read
## Prerequisite Check
## Session MCP API Surface

(a 3 keresési tool file:line szignatúrával idézve)

## Recurring-Concept Detection Without Semantic Claim Extraction
## Cross-Session Query Shape And Ranking
## Conflict/Superseded Candidate Data Model
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
`proven` egy "ez a tool ezt a szignatúrát adja" állításra KIZÁRÓLAG akkor használható,
ha a `mcp-server/session_server.py` tényleges sora idézve van — a fájl léte ≠
implemented, a tool neve megemlítve a riportban nem bizonyítja a tényleges szignatúrát.

## Definition Of Done

- [ ] prerequisite (`shared-session-catalog-consumer-001`) `id:` kulccsal megerősítve
      (NEM `job_id:`), GO/NO-GO döntés indokolva
- [ ] a 3 keresési tool file:line-nal idézve
- [ ] a visszatérő-fogalom detektálás explicit lexikai/vektor-alapú, NEM
      szemantikai-claim-extraction-alapú, indoklással
- [ ] cross-session query shape és rangsorolási döntés indokolva
- [ ] konfliktus/superseded adatmodell definiálva, a review-igény tisztázva
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- mély szemantikai claim-extraction/entitás-kinyerés a session-rétegben vagy a shared
  konzument-adapterben (a `query` paraméter MINDIG előre megadott kulcsszó, sosem
  LLM-generált "claim")
- a cross-session keresés canonical tudásgráfként kezelése
- automatikus `canonical` promotion egy "superseded" döntés alapján emberi review
  nélkül

## Git instrukciók

Push a `feature/shared-cross-session-search-001` branch-re, KIZÁRÓLAG a `cic-mcp-shared`
célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni, elég a lokális
commit; a `cic-mcp-session` klónba SEMMIT nem szabad commitolni/pusholni). Main-re az
agent NEM pushol. **NE módosítsd a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek angolul.
