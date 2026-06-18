# Boot sequence — orchestrátor kötelező lépései

**Minden session elején és minden capability-job létrehozása előtt.**
Ezt NEM delegálod agentnek — te futtatod le.

## Kötelező lépések

### 1. KB státusz
`kb_status` — elérhető és friss?

### 2. cic-mcp-* családtérkép

```
cic-mcp-knowledge  — versioned canonical tudásréteg (knowledge.sources.yaml → .gitmodules → kb_data)
cic-mcp-workdir    — aktuális repo/branch/commit/diff (tervezés alatt)
cic-mcp-session    — aktuális beszélgetés kontextusa (tervezés alatt)
cic-mcp-shared     — session-ek zanzája, accepted/candidate memória (tervezés alatt)
cic-mcp-gateway    — trust-domain-aware context compiler, runtime frontend (tervezés alatt)
cic-mcp-factory    — capability gyártó/karbantartó (EZ A REPO)
```

Trust-sorrend (thead02): `knowledge > workdir > shared > session`.

### 3. Amit ebből tudni kell mielőtt jobot írsz

```
capability request → terv → MCP server/tool contract → schema → implementation
  → tests → AI review summary → PR → human merge → registry/target-repo update
  → gateway route-olhatja

A factory:
  - tervez és implementál, de NEM mergel önmagába
  - minden új capability `experimental` státusszal indul, `candidate`/`canonical`-ra
    csak bizonyított (teszt, contract validáció) után léphet
  - gateway ≠ factory: a gateway a runtime route, a factory a build/maintenance backend
```

### 4. Kapcsolódó thead-ek (CLAUDE.md "Felülvizsgált AI párbeszédek")

Mielőtt egy capability-jobot írnál, nézd át, hogy a tervezett capability nem ütközik-e egy már
elvetett iránnyal (thead01–03).

## Miért kötelező

Ha nem futtatod le: olyan capability-t tervezhetsz, ami már elvetett irányt ismétel meg
(pl. gateway-be tett build-logikát, vagy redundáns repót egy már létező mellett — lásd
`cic-mcp-public` vs `cic-mcp-knowledge` esetét, ahol a névhasonlóság majdnem duplikációhoz vezetett).

## Jel hogy kihagytad

- Capability-jobot írsz anélkül hogy tudnád melyik trust-domain réteghez tartozik
- "A factory mergeli a saját PR-ját" — ez tilos, a legitimáció emberi/orchestrátor jog
- Új cic-mcp-* repót hozol létre anélkül hogy ellenőrizted nincs-e már hasonló célú
