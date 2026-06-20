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

### 3. Output áthozása — KÜLÖN BRANCH-RE, NEM main-re

**A `done`-ra zárás MINDIG PR-en megy, sosem direkt commit `main`-re.** Ugyanaz a
legitimációs elv vonatkozik a job-lezárásra, mint a capability-target-repo implementációra:
"AI gyártja és validálja, de nem legitimál" — a `main`-re kerülés (= `done` állapot
életbe lépése) emberi PR-merge-höz van kötve, nem az orchestrátor saját `git push`-ához.

```bash
JOB_ID="<job-id>"
CLONE="jobs/$JOB_ID/workspace/cic-mcp-factory"

git checkout main && git pull --ff-only
git checkout -b "close/$JOB_ID"

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
a target repo saját feature branch-én van — review és merge ott, KÜLÖN PR-ben (lásd
"Kötelező PR-tartalom"). Ez a `close/$JOB_ID` branch csak a cic-mcp-factory saját
job-tracking-ját zárja, nem helyettesíti a target-repo PR-t.

### 4. agent_done → done — a `close/$JOB_ID` branch-en, NEM a live main-en

```python
# jobs/$JOB_ID/meta.yaml, a close/$JOB_ID branch-en
status: "done"
timestamps.completed: "<ISO 8601 now>"
```

Ha az 1. vagy 2. lépésben hiányt találtál: **NE írj `done`-t.** Hagyd `agent_done`-on
(vagy `error`-ra, ha a hiány blokkoló), törölt a `close/$JOB_ID` branch-et, és indítsd
újra a jobot a hiány pótlására.

### 5. Commit, push, PR — ez zárja a jobot

```bash
bash tools/update-index.sh
git add jobs/$JOB_ID/ jobs/<sub-job-id>/ jobs/index.yaml
git commit -m "job: $JOB_ID — done + output"
git push -u origin "close/$JOB_ID"
gh pr create --title "job: $JOB_ID — close (done)" --body "..."
```

A PR body-ban röviden idézd a run-evidence eredményt és a fő findings-eket — ez a
review-artifact, amit a merge előtt át lehet nézni. **A job csak akkor `done` a valóságban,
amikor ezt a PR-t valaki (ember/orchestrátor) mergeli `main`-re.** A meta.yaml-ban a
`status: "done"` addig csak a branch-en él, a live `main`-en a job `agent_done` marad,
amíg a PR nincs mergelve.

### 6. Workspace takarítás (opcionális, a PR push UTÁN)

```bash
rm -rf jobs/$JOB_ID/workspace
```

A workspace gitignored, de helyet foglal. Törölhető ha az output már a `close/$JOB_ID`
branch-en pusholva van.

## Hibák amiket el kell kerülni

- ❌ `agent_done`-t automatikusan `done`-ra írni anélkül hogy a `run-evidence.md`-t elolvastad — exit code 0 ≠ kész capability-job
- ❌ A workspace klón `output/`-ját nézni a live workdir `output/` helyett ("jó az anyag" ellenőrzés nélkül)
- ❌ Sub-job speceket nem másolni át — akkor nem futtathatók `run-job.sh`-val
- ❌ done commit előtt nem futtatni `update-index.sh`-t
- ❌ A `capability.status_after_merge` mezőt (experimental/candidate/canonical) figyelmen kívül hagyni a target-repo PR-jénél
- ❌ `done`-t írni úgy, hogy a `run-evidence.md` szerint a target repo `NOT PUSHED`
- ❌ **A `done`-lezárást direkt `main`-re pusholni PR nélkül** — ez minden job-lezárásra
  vonatkozik, nem csak a target-repo-t módosító capability-jobokra. Nincs kivétel
  "ez csak audit/csak bookkeeping" alapon.
