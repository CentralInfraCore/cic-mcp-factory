# Job létrehozása

Új capability-job spec létrehozása a live workdir-ban.

## Kötelező lépések sorrendben

### 1. Könyvtárstruktúra

```bash
JOB_ID="<job-id>"
mkdir -p jobs/$JOB_ID/output
mkdir -p jobs/$JOB_ID/ref   # ha kell referencia anyag
touch jobs/$JOB_ID/output/.gitkeep
```

### 2. meta.yaml

A `.schema/meta.yaml` alapján. Kötelező mezők:
- `job_id` — egyedi, kebab-case
- `parent_job_id` — "" ha gyökér
- `level` — orchestrator | capability
- `capability.id` — pl. "cic_mcp.workdir.get_diff"
- `capability.target_repo` — melyik cic-mcp-* repóba kerül
- `capability.change_type` — new_capability | fix | enhancement
- `capability.status_after_merge` — experimental | candidate | canonical
- `kb_focus` — releváns cic-graph node ID-k (ha ismert)
- `workplace.repos` — további klónozandó repók a `capability.target_repo`-n felül, ha kell
  (pl. ha a capability több cic-mcp-* repót is érint). NE vedd fel "cic-mcp-factory"-t —
  azt a runner mindig automatikusan klónozza. `capability.target_repo` automatikusan
  bekerül a klónozási unióba, nem kell külön megismételni itt, ha más repo nem szükséges.
- `workplace.branch` — "feature/<job-id>"
- `status` — "pending"
- `timestamps.created` — ISO 8601

### 3. input.md

**Nyelv: magyar.**

Az `input.md` felépítése:
1. Kontextus — milyen capability-hiányt old meg és miért (lásd CLAUDE.md "Capability lifecycle")
2. Boot sequence — mit kell a KB-ban / a target repóban feltérképezni
3. Feladat — milyen tool/MCP contract-ot kell tervezni/implementálni
4. Output — kötelező PR-tartalom (lásd CLAUDE.md), fájlok listája és helye
5. Git instrukciók — push csak feature branch-re
6. Nyelvi szabály

**Alapszabály az input.md írásához:**
> Ne te tervezd meg előre a contract részleteit. Írj olyan instrukciókat, amelyek alapján az
> agent maga tárja fel a target repo meglévő mintáit és azokhoz illesztve tervez.

### 4. Commit és push

```bash
bash tools/update-index.sh
git add jobs/$JOB_ID/ jobs/index.yaml
git commit -m "job: $JOB_ID — pending"
git push
```

## Ellenőrzőlista

- [ ] `meta.yaml` — minden kötelező mező kitöltve (`capability.*` is), status: pending
- [ ] `input.md` — magyarul, tartalmaz target-repo feltérképezési utasításokat
- [ ] `output/.gitkeep` — létezik
- [ ] `jobs/index.yaml` — frissítve
- [ ] Commitolva és pusholt main-re
