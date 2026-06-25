# Job: gateway-query-context-api-001

## Kontextus

A `gateway_core/compile_context.py` `compile_context()` függvénye jelenleg
KIZÁRÓLAG `session_id`/`repo_root`/`max_chunks` paramétereket fogad (354-359.
sor) — egy konzumer csak egy MÁR ISMERT `session_id`-hez tud kontextust
összeállítani, szabad szöveges kérdést (query) NEM tud feltenni. Ez azt
jelenti, hogy a gateway jelenleg nem tud válaszolni egy "mi a kapcsolat X és
Y között" jellegű kérdésre — csak "add ide ennek a session-nek a contextjét"
jellegű hívásra.

Ez a job a `compile_context()`-et bővíti `query`/`intent`/`repo`/
`token_budget` paraméterekkel, intent-felismeréssel, forrás-kiválasztással,
dedup/konfliktus-jelöléssel, és token-budget szerinti envelope-
összeállítással — DE a MEGLÉVŐ, már tesztelt `session_id`-only hívási útnak
TOVÁBBRA IS működnie kell, regresszió nélkül.

## Target

- target repo: `cic-mcp-gateway`
- target path: `gateway_core/compile_context.py` bővítése + a hozzá tartozó
  teszt + `output/gateway-query-context-api.md`
- change_type: `enhancement`
- status_after_merge: `candidate`
- status indoklás: valós teszt bizonyítja MIND a régi hívási út
  regresszió-mentességét, MIND az új query-alapú út működését

## Sources

- **KÖTELEZŐ elsődleges forrás:**
  - `gateway_core/compile_context.py` — a JELENLEGI `compile_context()`
    TELJES implementációja (354. sortól), olvasd el MIELŐTT bővítenéd
  - `jobs/session-context-pack-v1-001/output/session-context-pack-v1.md` és
    `jobs/gateway-compile-context-test-hardening-001/output/*.md` — a már
    meglévő, tesztelt viselkedés, amit NEM szabad megtörni

## Boot sequence

1. `kb_status` — ellenőrizd a cic-graph KB állapotát
2. Olvasd el TELJESEN a fenti forrásokat, MIELŐTT bármit írnál

## Feladat

### 1. Pre-change szignatúra idézése

```
grep -rn "def compile_context" --include="*.py" gateway_core/ | grep -v test_
```

Idézd a kimenetet, és a `compile_context()` PONTOS, jelenlegi szignatúráját
és a docstring-jét (file:line). Ez a "mit bővítünk, mit nem törhetünk" alap.

### 2. Bővített szignatúra

```python
def compile_context(
    session_id: str | None = None,
    repo_root: Path | str | None = None,
    max_chunks: int = 50,
    python_executable: Path | str | None = None,
    query: str | None = None,
    intent: str | None = None,
    repo: str | None = None,
    token_budget: int | None = None,
) -> dict[str, Any]:
```

(a konkrét mezőneveket/típusokat igazítsd a meglévő kódstílushoz, ha eltér —
indokold a "Decisions Proposed" szekcióban). Az implementáció:
- ha `query` is None és `session_id` meg van adva → a JELENLEGI viselkedés,
  VÁLTOZATLANUL
- ha `query` meg van adva → intent-felismerés (legalább egy egyszerű,
  kulcsszó- vagy szabály-alapú osztályozás elfogadható, nem kell ML), forrás-
  kiválasztás, és a session-context-ből egy releváns részlet összeállítása
  a query alapján (NEM az egész session összes chunkja)
- `token_budget` ha meg van adva → tényleges korlátozás a visszaadott
  envelope méretén (becsült karakter/token-szám alapján)

### 3. Regresszió-mentesség — valós teszt

Futtasd a MEGLÉVŐ teszteket (`gateway-compile-context-test-hardening-001`
tesztjei) a bővítés UTÁN — idézd a TÉNYLEGES kimenetet, mind zöldnek kell
lennie.

### 4. Új query-alapú út — valós teszt

Írj egy ÚJ tesztet, ami egy konkrét, szabad szöveges `query`-t ad a
`compile_context()`-nek (session_id NÉLKÜL vagy session_id-vel együtt — a
te választásod, indokolva), és bizonyítja hogy a visszaadott envelope a
query-hez RELEVÁNS session-kontextust tartalmaz, NEM csak az első N chunkot
sorban.

### 5. `token_budget` enforcement — valós teszt

Bizonyítsd egy KIS `token_budget` értékkel, hogy a visszaadott envelope
TÉNYLEGESEN kisebb/csonkolt, mint egy nagy `token_budget`-tel hívva ugyanarra
a query-re. Idézd mindkét hívás kimenetének méretét/tartalmát.

## Nem cél

- knowledge/shared források bekötése (`gateway-knowledge-shared-adapters-001`,
  KÜLÖN job — ez a job KIZÁRÓLAG a session-forrás query-alapú lekérdezését
  bővíti)
- a `cic-mcp-session` MCP szerver oldali módosítása (a gateway a MEGLÉVŐ
  session MCP tool-okat hívja, nem bővíti azokat)
- valódi ML-alapú intent-klasszifikáció — egyszerű, szabály-alapú
  megközelítés is elfogadható, ha valós teszttel bizonyított

## Required Output Files

- `output/gateway-query-context-api.md`
- a módosított `gateway_core/compile_context.py`
- a hozzá tartozó teszt-fájl(ok)

## Required Report Sections

```markdown
# gateway-query-context-api-001 Output

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

- [ ] pre-change szignatúra idézve, file:line hivatkozással
- [ ] a meglévő `session_id`-only hívási út tesztjei TOVÁBBRA IS zöldek,
      TÉNYLEGES pytest kimenettel bizonyítva
- [ ] új, query-alapú hívási út valós teszttel bizonyítva
- [ ] `token_budget` tényleges korlátozó hatása valós teszttel bizonyítva
      (kis vs nagy budget összehasonlítás)
- [ ] claim-evidence tábla kitöltve, nem üres

## Forbidden Shortcuts

- a bővített szignatúra léte ≠ implemented — a futtatott teszt kimenete
  bizonyít, a kód megírása nem
- a meglévő `session_id`/`repo_root`/`max_chunks` hívási út viselkedésének
  törése vagy néma megváltoztatása
- `token_budget` paraméter, amit elfogad, de sosem érvényesít
- knowledge/shared források bekötése ebben a jobban (KÜLÖN job)

## Git instrukciók

Push a `feature/gateway-query-context-api-001` branch-re, KIZÁRÓLAG a
`cic-mcp-gateway` célrepóban (a `cic-mcp-factory` saját klónjában NEM kell
pusholni, elég a lokális commit). Main-re az agent NEM pushol. **NE
módosítsd a `meta.yaml` `status` mezőjét** sehol.

## Nyelvi szabály

A report magyarul készüljön, a kódrészletek/parancsok/mezőnevek/kód angolul.
