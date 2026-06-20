# CIC MCP Factory Documentation Pack

Ez a csomag a `cic-mcp-*` komponensek factory-szellemu megvalositasahoz keszult.

Celja:

- a `cic-mcp-session` es `cic-mcp-gateway` parhuzamos inditasanak dokumentalasa
- Postgres-first, DB-heavy tarolasi es feldolgozasi modell rogzítese
- Claude/agent jobokra bonthato, kontextusmeret-tudatos feladatsor adasa
- a `cic-mcp-factory` job lifecycle-hez illesztheto bemeneti anyag biztositasa

## Olvasasi sorrend

1. `architecture.md`
2. `execution-phases.md`
3. `acceptance-contract.md`
4. `job-slices.yaml`
5. `claude-job-authoring-guide.md`
6. `initial-job-briefs.md`

## Fo dontesek

- A `cic-mcp-session` mar letezo scaffold, de nem uzemszeru komponens.
- A `cic-mcp-gateway` elejetol kulon komponens/repo legyen.
- A session es gateway parhuzamosan induljon, kozos envelope/trust/factory szerzodessel.
- A session tarolasa PostgreSQL-first, DB-heavy irany: schema szeparacio, trigger/outbox, FTS, vector index, metadata, stable SQL API.
- A ChatGPT historical export importer kesobbi fazis; elobb a live/factory session modell stabilizalasa kell.

## Repo allapot (2026-06-20 frissitve)

A tervezes idejen (2026-06-20 koran reggel) a `cic-mcp-session`, `cic-mcp-shared`, `cic-mcp-gateway`
repok meg NEM leteztek — a fenti "mar letezo scaffold" allitas akkor meg nem volt igaz. Ezt
2026-06-20 folyaman bootstrappeltuk:

- mindharom repo letrehozva a `CentralInfraCore` orgban (public), a `base-repo` `mcp/main`
  specializacios branch-ebol mergelve (`base-repo` remote tartosan bekotve a jovobeli
  `mcp/main` frissiteshez)
- README.md/CLAUDE.md komponens-specifikusra atirva (PR-en keresztul, mergelve)
- `cic-mcp-workdir` NEM keszult el — ezt a szerepet a mar letezo `cic-factory` (workdir/) tolti be,
  nem kap kulon `cic-mcp-*` repot

Tehat innentol a "mar letezo scaffold" allitas a `cic-mcp-session`-re es a `cic-mcp-gateway`-re is
**tenylegesen igaz** — de csak a `base-repo` MCP-template szintjen (FastMCP szerver scaffold,
ures `source/`), session/gateway-specifikus implementacio (SessionIngressEnvelope,
GatewayContextEnvelope, Postgres storage) meg semelyikben nincs. A `gateway-repo-baseline-or-bootstrap-001`
job "bootstrap" aga ezzel lezarva; a tovabbi jobok (`session-ingress-envelope-contract-001`,
`gateway-context-envelope-contract-001` stb.) most mar valodi celrepora futtathatok.

## Factory hasznalat

Ezt a csomagot ne egyben add oda egy agentnek. Egy job inputja legfeljebb:

- 1 relevans fazis az `execution-phases.md`-bol
- 1 job definicio a `job-slices.yaml`-bol
- a kozos context rules rovid resze a `claude-job-authoring-guide.md`-bol
- konkret target repo path + output kovetelmenyek

Az agent ne kapja meg minden thead teljes tartalmat. Ha forras kell, hasznalja a review artifactokat:

- `../corpus/normalized/thead-review-2026-06-20.yaml`
- `../corpus/normalized/factory-systems-review-2026-06-20.yaml`

## Szigor

Az `acceptance-contract.md` a csomag normativ resze. Ha egy job input vagy output ellentmond neki, akkor a job NO-GO.

Factory futtatas elott az orchestratornak a konkret jobhoz ki kell masolnia:

- a relevans job szeletet a `job-slices.yaml`-bol
- az `acceptance-contract.md` megfelelo reszeit
- a target repo konkret pathjat
- a kotelezo output fajlneveket

Nem eleg azt mondani, hogy "tervezd meg". A jobnak ellenorizheto artifactot kell termelnie.
