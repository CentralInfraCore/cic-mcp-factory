# Job futtatása — Mode A (interaktív, élő MCP)

Két hivatalos indítási mód létezik, NEM egymást helyettesítő alternatívák:

| | Mode A — ez a skill | Mode B — `tools/run-job.sh` |
|---|---|---|
| Indítás | Agent tool (orchestrátor session-ből) | `./tools/run-job.sh <job-id> [agent-id]` |
| MCP hozzáférés | ÉLŐ — örökli a session `cic-graph` MCP-jét | NINCS — `claude --print` headless módban a `--mcp-config` flag nem épít fel működő MCP kapcsolatot |
| Mikor használd | A job KB lekérdezést igényel valós időben (kb_status, search_nodes, stb.) | Batch/automatizált futtatás, amikor a job nem igényel élő KB-lekérdezést, vagy minden szükséges kontextus már a target repo klónban van |
| Workspace előkészítés | Manuális (lásd 2. lépés) | Automatikus (`workplace.repos` ∪ `capability.target_repo` klónozva) |
| Run evidence | Manuálisan kell generálni `/job-close`-nál (lásd ott) | `run-job.sh` automatikusan generálja (`run-evidence.md`) |
| Záró státusz sikeres futás után | `agent_done` (NEM `done`) | `agent_done` (NEM `done`) |

Mindkét mód ugyanarra a `pending → running → agent_done → done` lifecycle-re fut ki —
`done`-ra csak `/job-close` zár, review után.

## Kötelező lépések sorrendben

### 0. Spec validáció — KÖTELEZŐ, agent indítás előtt

**0a. Gépi ellenőrzés — ez az első, ez a kényszer:**
```bash
tools/validate-spec.sh <job-id>
```
Ha exit 1 → stop. Nem folytatható.

**0b. Evidence-alapú ellenőrzés:**
Futtasd le: `/job-validate <job-id>`

- **GO** (mindkét lépés) → folytasd
- **NO-GO** bármelyiknél → javítsd az input.md-t, futtasd újra

Az agent indítása NO-GO esetén tilos.

### 1. pending → running (live meta.yaml)

```python
# meta.yaml frissítés
status: "running"
timestamps.started: "<ISO 8601 now>"
```

```bash
bash tools/update-index.sh
git add jobs/$JOB_ID/meta.yaml jobs/index.yaml
git commit -m "job: $JOB_ID — running"
git push
```

**Ez a commit jön ELŐBB — az agent indítása UTÁN.**

### 2. Workspace klón

```bash
WORKSPACE="jobs/$JOB_ID/workspace"
rm -rf "$WORKSPACE"
mkdir -p "$WORKSPACE"
git clone git@github.com:CentralInfraCore/cic-mcp-factory.git "$WORKSPACE/cic-mcp-factory"
git -C "$WORKSPACE/cic-mcp-factory" checkout -b feature/$JOB_ID
```

Klónozd a `workplace.repos` listában szereplő összes repót is, ÉS a `capability.target_repo`-t
(ha az nincs benne a listában), mindegyiket ugyanarra a `feature/$JOB_ID` branch-re:

```bash
for repo in <workplace.repos elemei> <capability.target_repo, ha hiányzik a listából>; do
  git clone "git@github.com:CentralInfraCore/$repo.git" "$WORKSPACE/$repo"
  git -C "$WORKSPACE/$repo" checkout -b feature/$JOB_ID
done
```

A `workspace/` gitignored — nem kerül a repóba.

### 3. Agent indítása — Agent tool-lal (NEM run-job.sh)

Az Agent tool örökli a session MCP konfigurációját (`cic-graph` elérhető) — ez a Mode A
egyetlen ok-a a Mode B helyett. Ha nincs szükség élő MCP-re, használd `tools/run-job.sh`-t
helyette (Mode B) — az automatizálja a klónozást és az evidence-gyűjtést is.

Az agent promptban kötelező megadni minden klónozott repó path-ját:
```
cic-mcp-factory klón: `jobs/$JOB_ID/workspace/cic-mcp-factory`
Feature branch: `feature/$JOB_ID`
<workplace repo>: `jobs/$JOB_ID/workspace/<repo>`
```

Az agent a `jobs/$JOB_ID/input.md`-t olvassa a klónból.

### 4. Várakozás

Az agent háttérben fut. Értesítés érkezik befejezéskor — ne pollozd.

### 5. running → agent_done (live meta.yaml) — NEM done

Amikor az agent visszajelez, csak `agent_done`-ra zárd, NEM `done`-ra — a sikeres lefutás
nem bizonyítja hogy a push/output evidence teljes:

```python
status: "agent_done"
timestamps.completed: "<ISO 8601 now>"
```

```bash
bash tools/update-index.sh
git add jobs/$JOB_ID/meta.yaml jobs/index.yaml
git commit -m "job: $JOB_ID — agent_done"
git push
```

Mivel ebben a módban nincs automatikus `run-evidence.md`, a `/job-close`-nál neked (vagy az
agentnek a promptban) manuálisan kell generálnod az evidence-t minden klónozott repóra
(`git status --porcelain`, `git log -1 --oneline`, `git branch --show-current`,
`git rev-parse HEAD` vs `git rev-parse @{u}`) — lásd `/job-close` "Run evidence ellenőrzés".

## Hibák amiket el kell kerülni

- ❌ running commit UTÁN indítani az agentet (fordított sorrend)
- ❌ run-job.sh használata amikor élő MCP kell (nincs MCP hozzáférése), VAGY Agent tool
  használata amikor run-job.sh elég lenne (kihagyod az automatikus klónozást/evidence-t)
- ❌ `~/.claude-personal/agents/.../workspace/` path — a workspace `jobs/$JOB_ID/workspace/`
- ❌ Az agent promptban nem adod meg minden klón path-ját
- ❌ agent visszajelzés után rögtön `done`-t írni `agent_done` helyett
