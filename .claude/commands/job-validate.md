# job-validate — Job spec validátor

Minden agent indítás előtt kötelező futtatni. Nem az input.md szándékát értékeli — konkrét kritériumok meglétre kérdez rá.

## Futtatás

```
/job-validate <job-id>
```

## Mit csinálj

### 1. lépés — Gépi ellenőrzés (shell script)

```bash
tools/validate-spec.sh <job-id>
```

Ha exit 1 → **azonnali NO-GO**, ne folytasd. Javítsd az input.md-t.

### 2. lépés — Evidence-alapú ellenőrzés (csak ha a script GO-t adott)

1. Olvasd el: `jobs/<job-id>/input.md`
2. Minden kritériumra: PASS / FAIL / N/A
3. **Minden PASS mellé kötelező idézet** a specből — az a sor vagy bekezdés ami alapján PASS lett
4. Ha bármelyik kritikus kritérium FAIL → **NO-GO**

---

## Kritériumok

### K1 — Forrás meghatározva (kritikus)
**Kérdés:** Explicit megnevezi-e a spec azt hogy honnan dolgozzon az agent?
- Forráskód audit (target repo) → konkrét path megadva
- KB audit → konkrét chunk-ok megadva
- Mindkettő → mindkettő megadva

FAIL ha: csak "nézd meg a kódot" / "KB alapján" — path vagy node-id nélkül

---

### K2 — Capability státusz definíció ellenőrzési módszerrel (kritikus)
**Kérdés:** Az `experimental` / `candidate` / `canonical` (capability.status_after_merge) választás
tartalmaz-e explicit indoklást/ellenőrzési módszert?

PASS csak ha:
- a spec leírja milyen bizonyíték kell `candidate`/`canonical` státuszhoz (pl. teszt lefedettség, contract validáció)
- Nem elég: "legyen experimental" — kell: "experimental, mert nincs még contract test"

FAIL ha: a státusz csak ki van jelölve, indoklás nélkül

---

### K3 — Explicit tiltott rövidítések (kritikus)
**Kérdés:** Van-e legalább egy explicit "NEM fogadható el" szabály?

Példa: "fájl létezése ≠ implemented", "teszt lefedettség ≠ implemented", "tool definíció ≠ működő capability"

FAIL ha: csak pozitív szabályok vannak

---

### K4 — Output formátum meghatározva
**Kérdés:** Az output fájlok neve és formátuma specifikálva van-e?

FAIL ha: csak "írj összefoglalót" — fájlnév és struktúra nélkül

---

### K5 — Tesztelhető sikeresség (közepes prioritás)
**Kérdés:** Van-e legalább egy olyan elvárás amit az orchestrátor közvetlenül ellenőrizhet?

Példa: "minden új tool-hoz add meg a teszt fájl path-ját", "contract validáció eredményét idézd"

FAIL ha: az output ellenőrizhetetlen az agent saját állításain kívül

---

### K6 — Negatív példák (közepes prioritás)
**Kérdés:** Van-e legalább egy példa arra hogy MIT NE csináljon az agent?

FAIL ha: csak pozitív utasítások vannak

---

### K7 — Forráskód audit specifikus (csak forráskód joboknál kritikus)
**Kérdés:** Explicit megköveteli-e a call-chain grep ellenőrzést, és kizárja-e a teszt fájlokat?

Elvárt minta (vagy ekvivalens):
```
grep -rn "<ToolNév>" --include="*.py"  | grep -v "test_"
grep -rn "<FuncName>" --include="*.go" | grep -v "_test.go"
0 találat → scaffold
```

FAIL ha: "olvasd el a fájlokat" — grep előírás nélkül.

FAIL ha: grep van, de nincs teszt-fájl kizárás — exportált szimbólumoknál a teszt referenciák
elfedik hogy a tool tényleg regisztrálva van-e a runtime-ban (`@mcp.tool()` decorator + tényleges hívás).

---

### K9 — Reachability artifact kötelező (kritikus, forráskód audit joboknál)
**Kérdés:** Megköveteli-e a spec hogy az agent production call site-ot (file:line) vagy
`deadcode`/import-graph outputot adjon az output artifact-ban?

A hiba struktúrális: ha a DoD "tool definiálva + test zöld", az agent mindig pass-olhat egy
sosem regisztrált/sosem hívott tool-on. A spec-nek reachability **bizonyítékot** kell követelnie.

Elvárt minta az output szekcióban:
```
Minden új tool-nál: a @mcp.tool() regisztráció file:sor + egy tényleges hívási példa (kliens oldalról)
VAGY: a registry/target-repo diff, ami mutatja hogy a gateway/factory ténylegesen útválasztja
```

FAIL ha: az output csak státuszlistát kér — reachability artifact nélkül.

---

### K8 — Claim-evidence tábla az outputban (kritikus)
**Kérdés:** Előírja-e a spec hogy az agent output tartalmazzon claim-evidence táblázatot?

Elvárt minta az output szekcióban:
```
| Állítás | Státusz | Bizonyíték | Verifikációs módszer | Kockázat |
```

FAIL ha: az output csak narratív összefoglalót vagy státuszlistát kér — claim-evidence tábla nélkül.

---

## Output formátum

```
## Validáció: jobs/<job-id>/input.md

### Gépi ellenőrzés (tools/validate-spec.sh)
[script output ide]

### Evidence-alapú ellenőrzés

| Kritérium | Státusz | Idézet a specből |
|---|---|---|
| K1 — Forrás | PASS/FAIL | "...pontos idézet..." (N. sor) |
| K2 — Capability státusz + indoklás | PASS/FAIL | "...pontos idézet..." (N. sor) |
| K3 — Tiltott rövidítések | PASS/FAIL | "...pontos idézet..." (N. sor) |
| K4 — Output formátum | PASS/FAIL | "...pontos idézet..." (N. sor) |
| K5 — Ellenőrizhetőség | PASS/FAIL | "...pontos idézet..." (N. sor) |
| K6 — Negatív példák | PASS/FAIL | "...pontos idézet..." (N. sor) |
| K7 — Call-chain grep + teszt-fájl kizárás | PASS/N/A/FAIL | "...pontos idézet..." (N. sor) |
| K8 — Claim-evidence tábla | PASS/FAIL | "...pontos idézet..." (N. sor) |
| K9 — Reachability artifact | PASS/N/A/FAIL | "...pontos idézet..." (N. sor) |

## Összesítés: GO / NO-GO

[Ha NO-GO: pontosan mi hiányzik, mit kell javítani az input.md-ben]
```

**Szabály:** Ha egy PASS mellé nem tudsz idézetet írni, az FAIL.

---

## Ami után GO esetén következik

`/job-run <job-id>`

## Ami után NO-GO esetén következik

Javítsd az input.md-t a jelzett pontokon, futtasd újra a validátort.
Ne indítsd el az agentet amíg NO-GO áll fenn.
