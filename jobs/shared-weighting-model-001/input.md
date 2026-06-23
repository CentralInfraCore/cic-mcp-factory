# Job: shared-weighting-model-001

## Kontextus

Phase 4 HARMADIK, UTOLSÓ jobja. A `shared-cross-session-search-001` (mergelve)
definiálta a cross-session query-alakot (session-enkénti min-max normalizálás +
összesítés a `fused_score`-okra) és a `conflicting_with`/`superseded_by` adatmodellt —
de explicit DEFERRÁLTA "a tényleges súlyozási FAKTOROK (recurrence count, factory/PR/
artifact linkage, recency-bónusz)" kérdését EZ a jobra (lásd `output/shared-cross-
session-search.md` "Cross-Session Query Shape And Ranking" 5. pont).

Ez a job definiálja a SÚLYOZÁSI MODELLT: milyen konkrét faktorok emelik egy
visszatérő-fogalom jelöltet a `mixed` trust-szintről `candidate`-ra (azaz formális
`promotion_candidate` állapotba), ÉS explicit kimondja — a thead02 döntési alap szerint
("AI gyártja és validálja a capability-t, de a legitimáció mindig embernél/
orchestrátornál marad") —, hogy a `cic-mcp-knowledge`-be való canonical promotion EGY
TELJESEN KÜLÖN, emberi review-flow, amit ez a job NEM helyettesít és NEM automatizál.

**Kritikus határ** (job-slices.yaml `forbidden_shortcuts`): a shared SOHA nem promote-
olhat egy jelöltet automatikusan canonical-ra emberi review nélkül — ez a `cic-mcp-
shared` trust modelljének (`canonical: false` by default) és a `Factory legitimacio`
elvnek ("Human merge = state transition authorization") direkt folytatása.

## Target

- target repo: `cic-mcp-shared`
- target path: `output/shared-weighting-model.md`
- change_type: `new_capability`
- status_after_merge: `experimental`
- status indoklás: kontraktus-riport, nincs futtatható súlyozó-algoritmus kód —
  `candidate`-hez egy tényleges implementáció és legalább egy valós, futtatott
  bizonyíték kellene (a `gateway-session-adapter-contract-001` →
  `session-context-pack-v1-001` mintát követve)

## Sources

- `${WORKDIR}/.cic-context/factory-docs/architecture.md` — "cic-mcp-shared" + "Factory
  legitimacio" szekció — NORMATÍV ("AI gyárt és validál, de nem legitimál. Human merge
  = state transition authorization.")
- **KÖTELEZŐ elsődleges forrás (a `cic-mcp-factory` repo `main`-jén, MÁR ott van):**
  - `${WORKDIR}/jobs/index.yaml` — prerequisite-ellenőrzéshez a `- id: "<job-id>"`
    kulccsal (NEM `job_id:` — lásd `shared-session-catalog-consumer-001` riport
    "Findings" #1, ne ismételd meg a hibát)
  - `${WORKDIR}/jobs/shared-cross-session-search-001/output/shared-cross-session-
    search.md` — TELJES egészében, NORMATÍV (a "Conflict/Superseded Candidate Data
    Model" mező-táblája a közvetlen kiindulópont — `candidate_id`, `trust`, `canonical`,
    `provenance_refs[]`, `conflicting_with`, `superseded_by` mezők MÁR definiáltak,
    EZEKHEZ adsz hozzá súlyozási mezőket, NEM találod ki újra a teljes rekordot)
  - `${WORKDIR}/jobs/shared-session-catalog-consumer-001/output/shared-session-catalog-
    consumer.md` — a "Trust Mapping" szekció (`mixed`/`candidate`/`reviewed_shared`)
- **HARMADIK forrás (a `cic-mcp-shared` repo, a target):**
  - `cic-mcp-shared/CLAUDE.md` — "Fő határok", "Trust modell" szekció

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. Prerequisite-ellenőrzés

```
grep -n '\- id: "shared-cross-session-search-001"' -A 3 jobs/index.yaml
```

Idézd a kimenetet, erősítsd meg `status: "done"`. Ha NEM, NO-GO és állj meg.

### 2. Súlyozási faktorok listája, indoklással

Definiálj LEGALÁBB 3 konkrét súlyozási faktort, amelyek egy `mixed` trust-szintű
jelöltet `candidate` (`promotion_candidate`) állapotba emelnek:

- **recurrence count**: hány KÜLÖNBÖZŐ `session_id`-ben jelent meg bizonyíték
  ugyanarra a `keyword_description`-re (a `shared-cross-session-search-001` cross-
  session normalizált-összesített pontszáma ehhez kapcsolódik — idézd a kapcsolódó
  szekciót)
- **factory job/PR/artifact linkage**: ha a jelölt EGY konkrét `cic-mcp-factory`
  job-id-hez/PR-hez/artifacthoz köthető (pl. egy `meta.yaml` `job_id` mező, vagy egy
  GitHub PR-szám a `provenance_refs[]`-en keresztül), ez NÖVELI a súlyt — indokold,
  miért: egy factory-job-hoz kötött jelölt nagyobb eséllyel egy VALÓS, dokumentált
  döntés, nem véletlen lexikai egyezés
  - itt KÖTELEZŐ konkrétan megnevezni, MELY `meta.yaml`/`jobs/index.yaml` mező adná
    ezt a linkage-t. Először GREP-pel erősítsd meg a tényleges mező-neveket
    (teszt-fájlok kizárva, bár ezen a séma-fájlon ez no-op):
    ```
    grep -rn "^[a-z_]*:" jobs/.schema/meta.yaml | grep -v test_
    ```
    Idézd a kimenetet, és ebből válassz konkrét mezőt (pl. `capability_id`,
    `target_repo`, `job_id`) — a választott mezőre add meg a `file:line` hivatkozást
    a `jobs/.schema/meta.yaml`-ban, és legalább egy MEGLÉVŐ, lezárt job `meta.yaml`-
    jából is idézd ugyanazt a mezőt (pl. `jobs/shared-cross-session-search-001/
    meta.yaml`-ból) — ez bizonyítja, hogy a mező NEM csak a sémában létezik, hanem
    tényleges, korábban kitöltött jobokban is megjelenik
- **recency-bónusz**: frissebb bizonyíték magasabb súlyt kap-e, és ha igen, milyen
  egyszerű (NEM ML-alapú) függvénnyel (pl. lineáris decay, vagy egyszerű "utolsó N nap"
  ablak) — indokold, miért elég egy egyszerű függvény (a tényleges implementáció egy
  jövőbeli jobra van bízva, itt csak a FAKTOR létezése és a döntés ELVE kell)

Minden faktorhoz add meg: hogyan kombinálódik a `shared-cross-session-search-001`
normalizált cross-session pontszámával (összeadás? szorzás? külön küszöbök?) —
indokold a választást.

### 3. `promotion_candidate` schema-mezők

Bővítsd a `shared-cross-session-search-001` riportban MÁR definiált jelölt-rekordot
(`candidate_id`, `trust`, `canonical`, `provenance_refs[]`, `conflicting_with`,
`superseded_by`) ÚJ, súlyozás-specifikus mezőkkel (pl. `weight_score`,
`recurrence_count`, `linked_factory_job_ids[]`, `last_evidence_at`). Tábla
formátumban: mező → típus → jelentés → melyik súlyozási faktorhoz tartozik.

### 4. Canonical promotion — EXPLICIT különálló, emberi review-flow

Mondd ki EXPLICIT (idézve a `architecture.md` "Factory legitimacio" szekciót és a
thead02 döntési alapot a CLAUDE.md-ből): a `promotion_candidate` állapot ELÉRÉSE
(akármilyen magas `weight_score`-ral) SOHA nem jelenti a `cic-mcp-knowledge`-be való
canonical promotiont — az egy TELJESEN KÜLÖN, emberi review-flow, amit ez a job NEM
specifikál részletesen (csak az ÁLLÍTÁS szükséges, hogy létezik és kötelező). Definiáld
a HATÁRT: mi az UTOLSÓ shared-oldali állapot, amit egy jelölt automatikusan elérhet
(`candidate`/`promotion_candidate`, súlyozási küszöb alapján), és mi az, ami MINDIG
emberi akciót igényel (`reviewed_shared`-re emelés, majd egy KÜLÖN, nem ehhez a jobhoz
tartozó folyamat a `canonical: true`-hoz).

## Nem cél

- tényleges súlyozó-algoritmus kód implementálása
- a `cic-mcp-knowledge`-be való canonical promotion folyamatának RÉSZLETES
  kidolgozása (csak az ÁLLÍTÁS, hogy embert igényel, kötelező — a folyamat maga egy
  másik, itt nem definiált job/repo tárgya)
- a `shared-cross-session-search-001`/`shared-session-catalog-consumer-001` által MÁR
  definiált mezők/döntések megkérdőjelezése vagy újradefiniálása (ÉPÍTS rájuk, ne
  helyettesítsd őket)
- `cic-mcp-session` repo módosítása vagy klónozása (ehhez a jobhoz NEM szükséges — a
  forrás kizárólag a `cic-mcp-factory` és `cic-mcp-shared` repókban él)

## Required Output Files

- `output/shared-weighting-model.md`

## Required Report Sections

```markdown
# shared-weighting-model-001 Output

## Scope
## Inputs Read
## Prerequisite Check
## Weighting Factors

(legalább 3 faktor, mindegyik indoklással + kombinálási móddal)

## promotion_candidate Schema Fields
## Canonical Promotion Boundary — Human Review Required
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
`proven` egy "a `jobs/index.yaml`-ban ez a mező létezik" állításra KIZÁRÓLAG akkor
használható, ha a tényleges sor idézve van — a fájl léte ≠ implemented (ez egyetlen
soron), a mező megemlítése a riportban nem bizonyítja a tényleges tartalmat.

## Definition Of Done

- [ ] prerequisite (`shared-cross-session-search-001`) `id:` kulccsal megerősítve,
      GO/NO-GO döntés indokolva
- [ ] legalább 3 súlyozási faktor definiálva, mindegyik indoklással és a cross-session
      pontszámmal való kombinálási móddal
- [ ] a factory job/PR/artifact linkage faktorhoz KONKRÉT `meta.yaml`/`index.yaml` mező
      megnevezve
- [ ] `promotion_candidate` schema-mezők táblája kész, ÉPÍT a
      `shared-cross-session-search-001` jelölt-rekordjára (nem helyettesíti)
- [ ] explicit kimondva: canonical promotion KÜLÖN, emberi review-flow, hivatkozva a
      `architecture.md` "Factory legitimacio" + thead02 forrásra
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a shared automatikusan canonical-ra promote-ol egy jelöltet emberi review nélkül
  (a job-slices.yaml explicit tiltott rövidítése)
- a `weight_score` küszöb elérése ÖNMAGÁBAN `canonical: true`-t eredményez
- a `shared-cross-session-search-001`/`shared-session-catalog-consumer-001` mezőinek
  csendes felülírása/újradefiniálása

## Git instrukciók

Push a `feature/shared-weighting-model-001` branch-re, KIZÁRÓLAG a `cic-mcp-shared`
célrepóban (a `cic-mcp-factory` saját klónjában NEM kell pusholni, elég a lokális
commit). Main-re az agent NEM pushol. **NE módosítsd a `meta.yaml` `status` mezőjét**
sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek angolul.
