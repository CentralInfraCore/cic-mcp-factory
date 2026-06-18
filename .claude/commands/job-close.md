# Job lezárása

Agent befejezése után a lifecycle zárása és az output áthozása a live workdir-ba.

## Kötelező lépések sorrendben

### 1. Output ellenőrzés — ELŐSZÖR OLVASD EL

```bash
CLONE="jobs/$JOB_ID/workspace/cic-mcp-factory"
ls "$CLONE/jobs/$JOB_ID/output/"
```

Olvasd el a fő output fájlokat. Lásd `/job-review` skill az értékelési szabályokhoz.
Ellenőrizd a "Kötelező PR-tartalom" listát a CLAUDE.md-ből (miért kellett, milyen contract,
milyen teszt, milyen státusz, milyen registry/target-repo diff).

### 2. Output áthozása live workdir-ba

```bash
CLONE="jobs/$JOB_ID/workspace/cic-mcp-factory"

# output fájlok
cp "$CLONE/jobs/$JOB_ID/output/"*.md "jobs/$JOB_ID/output/"

# sub-job specek (ha az agent hozott létre) — csak valódi job-könyvtárak,
# nem index.yaml / .schema / egyéb top-level fájl
for job_dir in $(find "$CLONE/jobs" -mindepth 1 -maxdepth 1 -type d \
                   ! -name "$JOB_ID" ! -name ".schema" -printf '%f\n'); do
  [[ -f "$CLONE/jobs/$job_dir/meta.yaml" ]] || continue   # nem job-könyvtár, skip
  mkdir -p "jobs/$job_dir"
  cp "$CLONE/jobs/$job_dir/input.md" "jobs/$job_dir/"
  cp "$CLONE/jobs/$job_dir/meta.yaml" "jobs/$job_dir/"
done
```

Ha a job egy target cic-mcp-* repóba is implementált (`capability.target_repo`), az a változás
a target repo saját feature branch-én van — review és merge ott, külön PR-ben (lásd
"Kötelező PR-tartalom").

### 3. running → done (live meta.yaml)

```python
status: "done"
timestamps.completed: "<ISO 8601 now>"
```

### 4. Commit és push

```bash
bash tools/update-index.sh
git add jobs/$JOB_ID/ jobs/<sub-job-id>/ jobs/index.yaml
git commit -m "job: $JOB_ID — done + output"
git push
```

### 5. Workspace takarítás (opcionális)

```bash
rm -rf jobs/$JOB_ID/workspace
```

A workspace gitignored, de helyet foglal. Törölhető ha az output már a live workdir-ban van.

## Hibák amiket el kell kerülni

- ❌ A workspace klón `output/`-ját nézni a live workdir `output/` helyett ("jó az anyag" ellenőrzés nélkül)
- ❌ Sub-job speceket nem másolni át — akkor nem futtathatók `run-job.sh`-val
- ❌ done commit előtt nem futtatni `update-index.sh`-t
- ❌ A `capability.status_after_merge` mezőt (experimental/candidate/canonical) figyelmen kívül hagyni a target-repo PR-jénél
