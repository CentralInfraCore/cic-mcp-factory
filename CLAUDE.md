# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Mi ez a könyvtár

A `cic-mcp-factory` az MCP-ökoszisztéma **capability gyártó- és karbantartó factory-ja** — nem egy
tudás-szerver (mint `cic-mcp-knowledge`), hanem a `cic-mcp-*` család (`knowledge`, `workdir`, `session`,
`shared`, `gateway`) önfejlesztési mechanizmusa.

Réteg-térkép (forrás: a thead-ek — lásd lent):

```
CIC                  = főtermék
cic-factory          = CIC építéséhez és karbantartásához használt AI-agent gyártósor
cic-mcp-*            = CIC/factory agentjeinek információs idegrendszere
cic-mcp-factory       = ennek az idegrendszernek a karbantartó gyára (EZ A REPO)
```

**Fontos elhatárolás:** `cic-mcp-factory` ≠ `cic-mcp-gateway`.
- `gateway` = runtime frontend (kérdést route-ol, contextet fordít, válaszol)
- `factory` = build/maintenance backend (capability-t tervez, PR-t készít, contractot validál, registry-t frissít)

A szerkezete és a job-lifecycle mechanikája a `cic-factory` saját mintáját követi — ugyanaz az
orchestrátor/agent szétválasztás, csak a job-ok tartalma capability-specifikus, nem repo-általános.

---

## Nyelvi szabály

- Dokumentáció, Claude-utasítások, agent promptok: **magyarul**
- Forráskód, YAML, JSON, shell script, változónevek, kódon belüli komment: **angolul**

---

## Működési modell

### Szerepek

| Szereplő | Hol él | Mit csinál |
|---|---|---|
| Orchestrátor (te + Claude) | live `workdir/` (ez a repo) | capability-job spec létrehozás, review, merge döntés |
| Agent | `jobs/<job-id>/workspace/cic-mcp-factory/` (klón) | klónban dolgozik, feature branch-re commitol és pushol |

### Capability lifecycle

```
capability request                          (felismert hiány egy cic-mcp-* repóban)
  → input.md + meta.yaml                     (orchestrátor írja, capability: blokk kitöltve)
  → commit main → push
run-job.sh: pending → running commit → workspace klón → feature branch
agent:      olvas jobs/<job-id>/ → tervez + implementál + tesztel → ír output/
              → AI review summary (mit változtat, miért, mit bizonyít, kockázat, merge-ready-e)
              → commitol + pushol feature/<job-id>
orchestrátor: review GitHubon → merge main (kizárólag emberi/orchestrátor jog)
              → registry/target repo frissítése a kész capability-vel
```

A legfontosabb szabály (thead02): **az AI gyártja és validálja a capability-t, de a legitimáció
(merge) mindig embernél/orchestrátornál marad.** A factory nem mergel önmagába.

### Git a bizalom forrása

A Vault-aláírt commit maga az igazolás (`commit-msg` hook, `cic-my-sign-key`).
Az agent a klónból commitol és pushol a feature branch-re — review artifact, nem véglegesítés.
Push `main`-re kizárólag az orchestrátor joga.

---

## Job struktúra

```
jobs/
  index.yaml                  ← auto-generált állapottérkép (tools/update-index.sh)
  .schema/meta.yaml            ← kötelező mezők sémája (capability: blokkal kibővítve)
  <job-id>/
    input.md                   ← agent prompt (magyarul, git-tracked)
    meta.yaml                  ← lifecycle: pending | running | done | error (git-tracked)
    ref/                       ← referencia anyagok (opcionális, git-tracked)
    workspace/                 ← gitignored; agent klónjai élnek itt
      cic-mcp-factory/         ← git clone + feature/<job-id> branch
      <target cic-mcp-* repo>/ ← ha a job egy másik cic-mcp-* repóba is ír
```

### meta.yaml kötelező mezők

```yaml
schema_version: "1.0"
job_id: ""
parent_job_id: ""             # "" ha gyökér
level: ""                     # orchestrator | capability
capability:
  id: ""                      # pl. "cic_mcp.workdir.get_diff"
  target_repo: ""             # melyik cic-mcp-* repóba kerül, pl. "cic-mcp-workdir"
  change_type: ""             # new_capability | fix | enhancement
  status_after_merge: ""      # experimental | candidate | canonical
kb_focus: []                  # cic-graph focus_pack node-id-k
promptmap_ref: ""
agent:
  config_dir: ""              # ~/.claude-personal/agents/<id>
  model: ""
workplace:
  repos: []                   # pl. ["cic-mcp-workdir"] — workspace/<repo>/ alá klónozva
  branch: ""                  # feature/<job-id>
status: "pending"              # pending | running | done | error
error_message: ""
timestamps:
  created: ""
  started: ""
  completed: ""
```

### Kötelező PR-tartalom (thead02 — capability promotion proposal)

Minden capability-job output-jában (`jobs/<job-id>/output/`) szerepeljen:
1. miért kellett az új capability (melyik cic-mcp-* job/repo akadt el nélküle)
2. milyen tool/MCP contract jön létre
3. milyen output schema van
4. milyen teszt bizonyítja
5. milyen státuszban indul (`experimental` / `candidate`)
6. milyen registry/target-repo diff készül
7. ismert limitációk
8. rollback/deprecate út

---

## Eszközök

| Parancs | Mit csinál |
|---|---|
| `./tools/run-job.sh <job-id> [agent-id]` | Teljes lifecycle: klón, running→done, commit, push |
| `./tools/update-index.sh` | `jobs/index.yaml` újragenerálása |

---

## Agent auth

```
~/.claude-personal/agents/<id>/
  .credentials.json       ← symlink → ~/.claude-personal/.credentials.json
  settings.json           ← izolált config, auto mode
```

Indítás: `CLAUDE_CONFIG_DIR=~/.claude-personal/agents/<id> claude --print "..." --mcp-config <mcp-config>`

---

## Kapcsolódó repók

| Repo | Szerep |
|---|---|
| `cic-factory` | CIC építő gyártósor — ennek a mintáját követi ez a repo |
| `cic-mcp-knowledge` | Versioned canonical tudásréteg — a leggyakoribb capability-cél |
| `cic-mcp-workdir`, `cic-mcp-session`, `cic-mcp-shared`, `cic-mcp-gateway` | A többi trust-domain réteg (tervezés alatt) |

A teljes ökoszisztéma-térkép a `cic-factory/docs/ecosystem-map.md`-ben él — onnan derive-old, ha
egy job más CIC repóra is hivatkozik.

---

## Felülvizsgált AI párbeszédek

| Forrás | Döntés |
|---|---|
| thead01 | OCI provider WASM modul: provider-aware, de nem secret-aware; relay: secret-aware, nem provider-aware |
| thead02 | cic-mcp-* família elnevezés + trust-domain rétegezés; AI gyártja/validálja, ember legitimálja a capability-t |
| thead03 | knowledge.sources.yaml → generált .gitmodules → knowledge.lock.yaml → kb_data pipeline (cic-mcp-knowledge-ben implementálva) |

Ezek döntési alapok — a `rejected` részeket ne tervezd újra.
