# Job lezárása

Agent befejezése után (`status: agent_done`) a lifecycle zárása `done`-ra és az output
áthozása a live workdir-ba. **`agent_done → done` kizárólag itt, review után történik —
a Claude folyamat sikeres lefutása (exit 0) önmagában nem elég.**

## Kötelező lépések sorrendben

### 1. Run evidence ellenőrzés — ELŐSZÖR EZT OLVASD EL

```bash
CLONE="jobs/$JOB_ID/workspace/cic-mcp-factory"
cat "$CLONE/jobs/$JOB_ID/output/run-evidence.md"
```

Ezt Mode B (`run-job.sh`) automatikusan generálta mechanikusan (branch, HEAD, uncommitted
diff, push státusz minden klónozott repóra) — nem az agent állítása.

**Ha Mode A-val (Agent tool) futott a job és nincs `run-evidence.md`:** generáld le manuálisan,
ugyanazt nézve minden klónozott repóra (`jobs/$JOB_ID/workspace/<repo>`):
```bash
for dir in "$CLONE" jobs/$JOB_ID/workspace/<egyéb klónozott repo>...; do
  git -C "$dir" status --porcelain
  git -C "$dir" log -1 --oneline
  git -C "$dir" branch --show-current
  git -C "$dir" rev-parse HEAD
  git -C "$dir" rev-parse '@{u}'   # ha eltér a HEAD-től vagy hibázik → nincs (teljesen) pusholva
done
```

Ha bármelyik repónál `NOT PUSHED` / nincs upstream / HEAD ≠ `@{u}` derül ki, **NO-GO a
done-ra**: vissza `/job-run` 0. lépéséhez (`--resume` vagy input.md javítás), amíg a target
repo push nem igazolt.

### 2. Output ellenőrzés

```bash
ls "$CLONE/jobs/$JOB_ID/output/"
```

Olvasd el a fő output fájlokat. Lásd `/job-review` skill az értékelési szabályokhoz.
Ellenőrizd a "Kötelező PR-tartalom" listát a CLAUDE.md-ből (miért kellett, milyen contract,
milyen teszt, milyen státusz, milyen registry/target-repo diff).

### 3. Output áthozása live workdir-ba

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

### 4. agent_done → done (live meta.yaml) — csak 1–3 lépés után, ha minden PASS

```python
status: "done"
timestamps.completed: "<ISO 8601 now>"
```

Ha az 1. vagy 2. lépésben hiányt találtál: **NE írj `done`-t.** Hagyd `agent_done`-on
(vagy `error`-ra, ha a hiány blokkoló), és indítsd újra a jobot a hiány pótlására.

### 5. Commit és push

```bash
bash tools/update-index.sh
git add jobs/$JOB_ID/ jobs/<sub-job-id>/ jobs/index.yaml
git commit -m "job: $JOB_ID — done + output"
git push
```

### 6. Workspace takarítás (opcionális)

```bash
rm -rf jobs/$JOB_ID/workspace
```

A workspace gitignored, de helyet foglal. Törölhető ha az output már a live workdir-ban van.

## Hibák amiket el kell kerülni

- ❌ `agent_done`-t automatikusan `done`-ra írni anélkül hogy a `run-evidence.md`-t elolvastad — exit code 0 ≠ kész capability-job
- ❌ A workspace klón `output/`-ját nézni a live workdir `output/` helyett ("jó az anyag" ellenőrzés nélkül)
- ❌ Sub-job speceket nem másolni át — akkor nem futtathatók `run-job.sh`-val
- ❌ done commit előtt nem futtatni `update-index.sh`-t
- ❌ A `capability.status_after_merge` mezőt (experimental/candidate/canonical) figyelmen kívül hagyni a target-repo PR-jénél
- ❌ `done`-t írni úgy, hogy a `run-evidence.md` szerint a target repo `NOT PUSHED`
