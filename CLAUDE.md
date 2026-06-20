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
run-job.sh / Agent tool: pending → running commit → workspace klón (factory + workplace.repos
              ∪ capability.target_repo) → feature branch
agent:      olvas jobs/<job-id>/ → tervez + implementál + tesztel → ír output/
              → AI review summary (mit változtat, miért, mit bizonyít, kockázat, merge-ready-e)
              → commitol + pushol feature/<job-id> (factory ÉS minden módosított target repo)
            → status: agent_done (a Claude folyamat lefutott — exit code 0 ≠ kész capability-job)
orchestrátor: /job-close — run-evidence.md ellenőrzés (push tényleg megtörtént-e), output review
              → státusz agent_done → done CSAK review után
              → review GitHubon → merge main (kizárólag emberi/orchestrátor jog)
              → registry/target repo frissítése a kész capability-vel
```

A legfontosabb szabály (thead02): **az AI gyártja és validálja a capability-t, de a legitimáció
(merge) mindig embernél/orchestrátornál marad.** A factory nem mergel önmagába.

### Státusz lifecycle

```
pending → running → agent_done → done
                 ↘ error (--resume-mal folytatható)
```

`agent_done` és `done` szándékosan külön állapot: a Claude folyamat sikeres lefutása (exit 0,
vagy Agent tool sikeres visszatérése) nem bizonyítja hogy az output teljes, a target repo
push megtörtént, és a "Kötelező PR-tartalom" minden pontja megvan. `done`-ra csak
`/job-close` zár, evidence-ellenőrzés után — lásd `.claude/commands/job-close.md`.

### Két indítási mód

| | Mode A | Mode B |
|---|---|---|
| Hogyan | Agent tool, `.claude/commands/job-run.md` szerint | `tools/run-job.sh <job-id> [agent-id]` |
| MCP | élő (session MCP öröklődik) | nincs (headless `claude --print`) |
| Mikor | jobnak valós idejű KB-lekérdezés kell | batch/automatizált futtatás |
| Evidence | manuális (job-close-nál) | automatikus (`run-evidence.md`) |

Mindkét mód a `workplace.repos` ∪ `capability.target_repo` uniót klónozza (a `cic-mcp-factory`
mindig külön, automatikusan) — a `target_repo` csak azt jelöli ki HOVA kerül az implementáció,
nem azt hogy MIT kell klónozni.

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
      cic-mcp-factory/         ← git clone + feature/<job-id> branch (mindig)
        jobs/<job-id>/output/run-evidence.md  ← Mode B: mechanikus push/branch/HEAD bizonyíték
      <repo>/                  ← workplace.repos ∪ capability.target_repo minden tagja
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
                               # NE vedd fel "cic-mcp-factory"-t, az mindig automatikus
                               # capability.target_repo automatikusan bekerül a klónozási unióba
  branch: ""                  # feature/<job-id>
status: "pending"              # pending | running | agent_done | done | error
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
| `./tools/validate-spec.sh <job-id>` | Mechanikus spec-ellenőrzés (K1/K3/K4/K7/K8/K9) — exit 1 = NO-GO |
| `./tools/run-job.sh <job-id> [agent-id]` | Mode B teljes lifecycle: validate-spec → klón (factory + `workplace.repos` ∪ `capability.target_repo`) → running→**agent_done** → run-evidence.md → commit, push |
| `./tools/update-index.sh` | `jobs/index.yaml` újragenerálása (`yaml.safe_load`, nem regex; üres lista `jobs: []`) |

`run-job.sh` headless `claude --print`-et használ — ÉLŐ MCP hozzáférést igénylő joboknál (kb_status,
search_nodes valós időben) az Agent tool-lal indítás kell (Mode A), lásd `.claude/commands/job-run.md`.
`run-job.sh` automatikusan futtatja a `validate-spec.sh`-t friss indításnál (nem `--resume`-nál) —
NO-GO esetén nem indítja el az agentet. **Soha nem zár `done`-ra** — csak `agent_done`-ra; a
`done` átírás kizárólag `/job-close` review után, lásd "Státusz lifecycle".

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

## Ismert korlátok / roadmap

`validate-spec.sh` + `/job-validate` jelenleg **prompt-quality guardrail**, nem valódi capability
contract validator — mintaillesztéssel ellenőrzi hogy a spec tartalmazza a kötelező elemeket
(forrás, tiltott rövidítés, output formátum, claim-evidence tábla, reachability), de nem
ellenőrzi a tényleges output/contract tartalmát szemantikailag. Ez jó első kapu, de nem
helyettesíti a következő, még nem implementált rétegeket (nincs még konkrét capability-job,
ami ellen ezeket meg lehetne tervezni):

- `meta.yaml` schema validation (jelenleg csak konvenció, nincs gépi kikényszerítés)
- `input.md` kötelező szekciók validation (jelenleg `validate-spec.sh` regex-mintákkal közelíti)
- output artifact schema validation (a "Kötelező PR-tartalom" lista jelenleg csak emberi review-nál ellenőrzött)
- target repo diff validation (mit szabad/nem szabad módosítania egy capability-jobnak a target repóban)
- claim-evidence tábla parser (jelenleg csak vizuálisan ellenőrzött `/job-review`-nál)
- PR readiness checker (gépi GO/NO-GO a teljes "Kötelező PR-tartalom" listára, nem csak a spec-re)

---

## Felülvizsgált AI párbeszédek

| Forrás | Döntés |
|---|---|
| thead01 | OCI provider WASM modul: provider-aware, de nem secret-aware; relay: secret-aware, nem provider-aware |
| thead02 | cic-mcp-* família elnevezés + trust-domain rétegezés; AI gyártja/validálja, ember legitimálja a capability-t |
| thead03 | knowledge.sources.yaml → generált .gitmodules → knowledge.lock.yaml → kb_data pipeline (cic-mcp-knowledge-ben implementálva) |

Ezek döntési alapok — a `rejected` részeket ne tervezd újra.
