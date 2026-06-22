# factory-session-bridge-001 Output

## Scope

Ez a riport KIZÁRÓLAG kontraktus-szintű: definiálja, hogyan fordítható le a `cic-mcp-factory`
job-lifecycle saját metaadata-készlete (`meta.yaml`, `jobs/index.yaml`, `run-job.sh`
session-kezelés) egy `SessionIngressEnvelope`-ba, amit a `cic-mcp-session` be tud tölteni.
NEM tartalmaz collector/bridge FUTTATHATÓ kódot, NEM módosítja a `jobs/.schema/meta.yaml`
séma-fájlt. Önreferens job: a target repo maga a `cic-mcp-factory`.

## Inputs Read

- `.cic-context/corpus/normalized/factory-systems-review-2026-06-20.yaml` — TELJES egészében
  (key_findings fac-0001–fac-0006, risks risk-fac-0001–0004, recommended_next_jobs)
- `.cic-context/factory-docs/architecture.md` — "Factory legitimacio" (sor 208–230) és
  "Trust modell" (sor 187–206) szekciók
- `jobs/.schema/meta.yaml` — teljes mező-séma (51 sor)
- `jobs/index.yaml` — generált index, jelenlegi 27 job bejegyzéssel
- `tools/run-job.sh` — session_id kitöltési logika (sor 228–237, 293–307), meta.yaml
  lifecycle-frissítés regex-alapú mintája
- `tools/update-index.sh` — index-generálás Python/`yaml.safe_load` logikája (sor 7–66)
- `.cic-context/factory-docs/job-slices.yaml` — `factory-session-bridge-001` saját
  bejegyzése (sor 638–660): acceptance_gates, required_evidence, forbidden_shortcuts
- `jobs/session-ingress-envelope-contract-001/output/session-ingress-envelope.schema.yaml` —
  a MÁR LÉTEZŐ, normatív `SessionIngressEnvelope` JSON-Schema-szerű kontraktus (299 sor,
  `cic-mcp-session` repóba szánt korábbi capability-job kimenete, ebben a klónban
  job-tracking output-ként elérhető) — ez a tényleges leképezési cél, nem a spec
  illusztratív mezőnevei
- `jobs/session-hook-collector-001/output/session-hook-collector-report.md` — a
  `log-event.py` gap karakterizációja (idézet-szinten, lásd lent) és annak ténye, hogy a
  `cic-mcp-session` oldali collector-t egy KÉSŐBBI job már implementálta egy ÚJ,
  `cic-mcp-session`-ben élő `hooks/log-event.py` fájlban — ez NEM ugyanaz a fájl, mint a
  jelen jobban hivatkozott, NEM klónozott `workdir/tools/hooks/log-event.py`
- (Másodlagos, NEM megnyitva, csak idézetből jellemezve, az input.md előírása szerint:
  `workdir/tools/hooks/log-event.py`)

Boot sequence: `kb_status` lefuttatva — `kb_data/pkl` fájlok (`chunks`, `graph_nodes`,
`graph_edges`, `inverted_index`, `faiss.index`, `bm25`) léteznek, cache hit/miss 6/1,
currsize 1 — a KB élő és elérhető.

## Existing meta.yaml Fields Mapped

GREP kimenet, a spec által előírt pontos paranccsal:

```
$ grep -rn "^[a-z_]*:" jobs/.schema/meta.yaml | grep -v test_
jobs/.schema/meta.yaml:1:schema_version: "1.0"
jobs/.schema/meta.yaml:4:job_id: ""                  # unique, e.g. "workdir-get-diff-001"
jobs/.schema/meta.yaml:5:parent_job_id: ""           # parent job id if this is a child job; "" for root
jobs/.schema/meta.yaml:8:level: ""                   # orchestrator | capability
jobs/.schema/meta.yaml:11:capability:
jobs/.schema/meta.yaml:18:kb_focus: []                # focus_pack node-ids or tags, e.g. ["mcp", "trust-domain"]
jobs/.schema/meta.yaml:19:promptmap_ref: ""           # key in ai/PROMPTMAP.yaml; "" if not applicable
jobs/.schema/meta.yaml:22:agent:
jobs/.schema/meta.yaml:32:workplace:
jobs/.schema/meta.yaml:37:status: "pending"           # pending | running | agent_done | done | error
jobs/.schema/meta.yaml:44:error_message: ""           # only when status: error
jobs/.schema/meta.yaml:47:timestamps:
```

Megjegyzés: a `grep -rn "^[a-z_]*:"` minta csak a 0 space indentációjú (top-level) mezőket
találja meg — a `capability:`, `agent:`, `workplace:`, `timestamps:` ALATTI, 2 space
indentációjú nested mezők (pl. `capability.id`, `agent.session_id`, `timestamps.started`)
NEM jelennek meg ebben a kimenetben, mert azok a sorok `  id: ""` formátumúak, nem
`^[a-z_]`-mintával kezdődnek. Ez a grep-minta önmagában NEM elég a teljes mezőlista
felderítéséhez — a nested mezőket a fájl direkt elolvasásával (`jobs/.schema/meta.yaml`
1–51. sor) azonosítottam:

| meta.yaml mező | file:line | Session-releváns? | Megjegyzés |
|---|---|---|---|
| `schema_version` | `jobs/.schema/meta.yaml:1` | nem | csak séma-verzió, nem session-adat |
| `job_id` | `jobs/.schema/meta.yaml:4` | IGEN | egyedi azonosító, provider_session_id-szerű szerepkör a factory oldalán |
| `parent_job_id` | `jobs/.schema/meta.yaml:5` | IGEN | session-derivációs lánc (job hierarchia), nincs közvetlen `SessionIngressEnvelope` mező rá |
| `level` | `jobs/.schema/meta.yaml:8` | nem | orchestrator/capability — job-osztályozás, nem session-identitás |
| `capability.id` | `jobs/.schema/meta.yaml:12` | gyenge | workstream-szerű kontextus, nem session-identitás |
| `capability.target_repo` | `jobs/.schema/meta.yaml:13` | gyenge | workstream-kontextus |
| `capability.change_type` | `jobs/.schema/meta.yaml:14` | nem | — |
| `capability.status_after_merge` | `jobs/.schema/meta.yaml:15` | nem | — |
| `kb_focus` | `jobs/.schema/meta.yaml:18` | nem | — |
| `promptmap_ref` | `jobs/.schema/meta.yaml:19` | nem | — |
| `agent.config_dir` | `jobs/.schema/meta.yaml:23` | gyenge | a Claude Code config_dir azonosítja MELYIK agent-identitás futott, de nem maga a session |
| `agent.model` | `jobs/.schema/meta.yaml:24` | gyenge | model-context, nem session-identitás |
| `agent.session_id` | `jobs/.schema/meta.yaml:25` | IGEN | a tényleges Claude Code session UUID — ez a `provider_session_id` legközvetlenebb megfelelője |
| `workplace.repos` | `jobs/.schema/meta.yaml:33` | nem | klónozási unió, nem session-adat |
| `workplace.branch` | `jobs/.schema/meta.yaml:34` | gyenge | feature branch név, workstream-kontextus |
| `status` | `jobs/.schema/meta.yaml:37` | nem | job-lifecycle státusz, nem session-identitás (de lásd Findings — nincs session-szintű ekvivalens) |
| `error_message` | `jobs/.schema/meta.yaml:44` | nem | — |
| `timestamps.created` | `jobs/.schema/meta.yaml:48` | gyenge | job spec létrehozás ideje, nem session occurred_at |
| `timestamps.started` | `jobs/.schema/meta.yaml:49` | IGEN | a `occurred_at`/session-kezdet legközvetlenebb megfelelője |
| `timestamps.completed` | `jobs/.schema/meta.yaml:50` | IGEN | a session-vég jelzése; nincs explicit `SessionIngressEnvelope` mező rá (az envelope egy ESEMÉNYT ír, nem egy session-tartamot — lásd Findings) |

**Hiányzó mező, amit fel kellene venni a session-katalógushoz:** nincs a `meta.yaml`-ban
semmilyen `provider` mező (pl. `"claude-code"` konstans) és nincs `source.collector`-szerű
mező (melyik script/eszköz hozta létre a bejegyzést — `run-job.sh` vs. Agent tool/Mode A).
Jelenleg ez implicit (a `run-job.sh` script tölti ki `session_id`-t, Mode A esetén soha —
lásd Findings), nincs explicit mező rá a séma-fájlban.

## Why events.jsonl Is Not Enough

A `factory-systems-review-2026-06-20.yaml` két kapcsolódó megállapítása (fac-0005,
risk-fac-0004) együtt egy strukturális, nem csak "részletesség"-hiányt ír le:

fac-0005 szerint a jelenlegi hook-logging "intentionally lightweight and non-blocking;
it writes summary JSONL to `jobs/<job-id>/output/events.jsonl`" — tehát a könnyűsúlyúság
SZÁNDÉKOS design-döntés (a hook nem szabad hogy blokkolja az agent futást), NEM hiányosság
ami egyszerűen "be lehetne lőni". risk-fac-0004 ugyanezt élesebben fogalmazza meg:
"workdir hook log-event.py summarizes tool events and discards most raw payload detail" —
az `events.jsonl` ELVESZTI a nyers payloadot, és explicit ajánlása "Do not use current
events.jsonl as the final session source-of-truth; create a richer envelope collector."

A szintézis: a két megállapítás együtt egy ÉRTÉKVÁLASZTÁST ír le, nem hibát. A jelenlegi
`log-event.py` (workdir oldali, NEM klónozva ide) egy ÖSSZEFOGLALÓ-réteg, ami a fejlesztői
megfigyelhetőséghez (debug, gyors átnézés) elég, de STRUKTURÁLISAN nem tudja kiszolgálni a
`SessionIngressEnvelope` kontraktus két KÖTELEZŐ tulajdonságát:

1. **Raw payload preservation** — a `session-ingress-envelope.schema.yaml` `payload` mezője
   (sor 143–154) explicit megköveteli: "structurally preserved, not semantically summarized
   or reduced" — ez PONTOSAN az ellentéte annak, amit egy összefoglaló JSONL csinál
   (csonkolás, mezőszűrés).
2. **Idempotency garancia** — a `raw_payload_hash` és `idempotency_key` mezők (sor 165–247)
   determinisztikus SHA-256 hash-eket várnak a NYERS payload felett; egy már összefoglalt,
   csonkolt rekordból ez a hash nem reprodukálható ugyanúgy, mint az eredeti eseményből —
   tehát az `events.jsonl` ÖNMAGÁBAN nem alkalmas a dedup-garancia alapjának.

Más szóval: a két finding NEM azt mondja, hogy "az `events.jsonl` rossz log", hanem azt,
hogy egy MÁSIK RÉTEG (a tényleges `SessionIngressEnvelope` ingestion) számára szükséges
információ STRUKTURÁLISAN nincs benne a jelenlegi formátumban — ezért a bridge-nek a
`meta.yaml`/`run-job.sh` session-azonosító mezőkre kell támaszkodnia (ahol VAN explicit
`session_id`), nem az `events.jsonl` tartalmára.

## Bridge Proposal — Field Mapping Table

| Factory `meta.yaml` mező | `SessionIngressEnvelope` mező | Megjegyzés |
|---|---|---|
| (konstans, nincs meta.yaml mező) | `apiVersion` = `"cic.session/v1"` | konstans, a factory oldalon nem kell tárolni — a bridge-collector írja be |
| (konstans, nincs meta.yaml mező) | `kind` = `"SessionIngressEnvelope"` | konstans, ld. fent |
| (generálandó, nincs meglévő mező) | `event_id` | ÚJ, wrap-time generált UUID — NEM a `job_id`, mert az `event_id` az EGYES eseményhez (egy session-futáshoz), nem a job-hoz tartozik. Nem javaslom `meta.yaml` mezőként felvenni — ez a bridge-collector felelőssége, nem a job-spec-é. |
| (konstans) | `provider` = `"claude-code"` | konstans, a factory minden agent-futása Claude Code — nincs szükség `meta.yaml` mezőre |
| `agent.session_id` (`jobs/.schema/meta.yaml:25`) | `provider_session_id` | KÖZVETLEN, 1:1 megfelelés — ez a tényleges Claude Code session UUID, pontosan a kontraktus elvárt szemantikája. **MEGLÉVŐ mező, elég, nincs szükség új mezőre.** |
| (nincs meglévő mező, implicit `run-job.sh`-ban) | `source.kind` = `"hook"` vagy egyéb | a `session-ingress-envelope.schema.yaml` enum-ja (`hook`/`importer`/`manual`/`api`) NEM tartalmaz "agent-futás"-szerű forrást — a factory job-futás leginkább `"api"`-nak felelne meg (programozott indítás), de ez ÚJ döntést igényelne a `cic-mcp-session` oldalon, NEM ennek a jobnak a hatóköre |
| `agent.config_dir` (`jobs/.schema/meta.yaml:23`) | `source.collector` | KÖZVETETT — a config_dir azonosítja MELYIK agent-identitás (`agent-01` stb.) futtatta a job-ot, ez közelebb áll a "collector instance" szemantikájához, mint a `job_id`. **MEGLÉVŐ mező, részben elég, de a `source.collector` kontraktus inkább script/eszköz-nevet vár (pl. `"log-event.py"`), nem agent-config útvonalat — pontos illesztéshez egy ÚJ, explicit `agent.source_kind`/`agent.collector_id` mezőt kellene felvenni, ha ez a bridge tényleges implementációba megy.** |
| `timestamps.started` (`jobs/.schema/meta.yaml:49`) | `occurred_at` | KÖZVETLEN, de PONTATLAN — a `started` a JOB indulását jelzi, nem egy konkrét provider-eseményt. Több session-esemény (PreToolUse, PostToolUse, Stop stb.) történik egy job futása ALATT, a `meta.yaml`-nak csak a job-szintű kezdete/vége van, nem eseményszintű timestamp-je. **MEGLÉVŐ mező, de csak JOB-GRANULARITÁSÚ helyettesítő, nem esemény-granularitású `occurred_at`.** |
| (generálandó) | `ingested_at` | ÚJ, wrap-time generált — a bridge-collector futási ideje, nincs `meta.yaml` megfelelője, és NEM is kellene, mert ez a collector saját órájának időbélyege |
| `job_id` (`jobs/.schema/meta.yaml:4`) | `workstream` | KÖZVETLEN, az optional contextual mező pontosan ezt a szerepet várja ("Optional free-text linkage to a CIC job_id / workstream"). **MEGLÉVŐ mező, ELÉG, a `session-hook-collector-001` riport (sor 82) szerint a `cic-mcp-session` oldali collector MÁR a `CIC_JOB_ID` env var-t használja erre — ez konzisztens azzal, hogy a `run-job.sh` (sor 209) export-olja `CIC_JOB_ID`-t.** |
| (nincs meta.yaml mező, payload-tartalom) | `payload` | NEM mappelhető a `meta.yaml`-ból — a `payload` a tényleges hook/event nyers JSON-ja, nem job-metaadat. A `meta.yaml` sosem fogja tartalmazni a payload-ot, ez NEM hiányosság, mert a `meta.yaml` szerepe más (job-lifecycle, nem event-stream) |
| (nincs meta.yaml mező) | `raw_payload_hash`, `idempotency_key` | NEM mappelhető — ezek a `payload`-ból számolt hash-ek, a `meta.yaml`-nak nincs és nem is kellene saját hash-mezője |
| (nincs meta.yaml mező, de van architektúra-szintű elv) | `trust` | A `meta.yaml`-ban nincs explicit trust-mező, de az `architecture.md` "Trust modell" szekciója (sor 187–197) szerint minden session-szintű adat `trust: session_local` vagy `session_derived` — egy factory-job-eredetű envelope feltehetően `session_local` lenne. **NEM javaslom új `meta.yaml` mezőt erre — ez konstans/derivált érték a bridge-collector szintjén, nem job-spec-szintű döntés.** |
| `status` (`jobs/.schema/meta.yaml:37`) | (nincs közvetlen megfelelő) | a `pending/running/agent_done/done/error` job-lifecycle állapotnak NINCS `SessionIngressEnvelope` mezője — az envelope egy DISKRÉT eseményt ír (occurred_at pillanatában), nem egy állapot-átmenetet. Ha a bridge ezt is be akarná tölteni, minden státuszváltás KÜLÖN envelope-ot igényelne (`provider_event_name` mezővel jelölve, pl. `"job_status_running"`, `"job_status_agent_done"`) — ez ÚJ döntés, ezt a jobot meghaladja |

**Explicit jelölés ÚJ mezőről**: ha ez a bridge tényleges implementációba menne, egy
`agent.collector_id` vagy `agent.source_kind` mezőt kellene felvenni a `meta.yaml`
séma `agent:` blokkjába — ez egy JAVASLAT, NEM lett a séma-fájlba beírva (ld. "Nem cél" /
Forbidden Shortcuts). Minden más felsorolt mező a `SessionIngressEnvelope` releváns
részére MEGLÉVŐ `meta.yaml` mezőből vezethető le, vagy ELVI okból (payload, hash-ek,
event_id, ingested_at) NEM is kellene `meta.yaml`-ba kerülnie.

## Migration/Compatibility Plan

A `jobs/` alatt jelenleg **27 job-könyvtár** van (a `.schema/` kizárva), ebből **25 `status:
"done"`** és **2 `status: "running"`** (a jelen job, `factory-session-bridge-001`, és
`session-context-pack-v1-001`). Ellenőrzött tény: **MINDEN job `meta.yaml`-jában az
`agent.session_id` mező üres string (`""`)** — ezt a `grep -h "session_id:" jobs/*/meta.yaml`
27 sornyi kimenete mutatja, nincs egyetlen kitöltött érték sem.

Ennek oka a `run-job.sh` sor 228–237 logikájában keresendő: a `session_id` KIZÁRÓLAG akkor
töltődik ki, ha a job Mode B-vel (`run-job.sh`) futott ÉS a session jsonl fájl megtalálható
volt a marker-fájl utáni mtime-mal. Mivel a CLAUDE.md "Két indítási mód" szerint a
gyakoribb/preferált indítás Mode A (Agent tool, élő MCP), és Mode A-nál a `run-job.sh`
session-mentési blokkja SOHA nem fut le, ez megmagyarázza, hogy a 27 meglévő jobból
miért nincs egyetlen kitöltött `session_id` sem.

**Döntés: a bridge CSAK ÚJ jobokra vonatkozzon, retroaktív backfill NEM indokolt.**

Indoklás:

1. **Nincs adat retroaktív kitöltéshez.** A `session_id` mind a 27 meglévő jobban üres —
   nincs olyan forrás-adat (a `meta.yaml`-ban vagy az `index.yaml`-ban), amiből egy
   retroaktív bridge-collector egy valódi `provider_session_id`-t tudna előállítani. A
   Claude Code session jsonl fájlok (`~/.claude-personal/agents/<id>/projects/<slug>/`)
   ELVILEG még léteznek a korábbi futásokból, de a `meta.yaml`-ban nincs hozzájuk mutató
   azonosító — egy retroaktív backfill csak HEURISZTIKUS (mtime-alapú) párosítással
   menne, ami pont az a fajta nem-determinisztikus, audit-gyenge megoldás, amit a
   `SessionIngressEnvelope` `idempotency_key` mechanizmusa (determinisztikus hash,
   ld. schema sor 214–247) explicit el akar kerülni.
2. **A `SessionIngressEnvelope` esemény-szemantikája nem illik rá lezárt jobokra.**
   Az envelope egy DISKRÉT, `occurred_at` pillanatában történt eseményt ír le. A 25 `done`
   állapotú job esetén a releváns "esemény" (a job futása) már lezajlott, és a `meta.yaml`
   `timestamps.started/completed` mezői csak JOB-GRANULARITÁSÚ határokat adnak, nem a
   tényleges esemény-sorozatot (PreToolUse/PostToolUse/Stop stb.), amit az envelope
   `payload` mezője várna. Egy retroaktív envelope tehát szükségképpen INFORMÁCIÓ-
   SZEGÉNYEBB lenne, mint egy valós időben generált — ami megkérdőjelezi az értékét.
3. **A bridge jelenleg KONTRAKTUS, nincs collector-implementáció.** Mivel ez a job
   explicit NEM hoz létre futtatható collector-kódot (ld. "Nem cél"), a "migráció"
   kérdése jelen pillanatban ELMÉLETI — nincs mit retroaktívan futtatni. A döntés
   tényleges hatása csak akkor válik konkréttá, amikor egy KÉSŐBBI job (pl. egy
   `factory-session-bridge-002` vagy hasonló) tényleges collector-kódot ír.
4. **A `status_after_merge: experimental` jelzés is ezt támogatja** — a job-slices.yaml
   bejegyzés (sor 642) és az input.md "Target" szekció (sor 26–28) explicit kimondja:
   `candidate`-hez egy tényleges implementáció és legalább egy valós job-on átfutó próba
   szükséges. Egy `experimental`-státuszú kontraktusra retroaktív migrációt építeni
   idő előtti munka lenne.

**Mit JAVASOLOK a "csak új jobokra" döntés mellett, ha egy KÉSŐBBI job collectort ír:**
a collector legyen képes "best-effort" envelope-ot generálni egy meglévő, `session_id`
nélküli jobhoz is — `provider_session_id` helyett a `job_id`-t használva placeholder-ként,
és a `schema_notes` mezőben (schema sor 259–264, pontosan erre a célra való: "partial or
truncated capture") explicit jelezve, hogy ez egy retroaktívan rekonstruált, nem valós-idejű
envelope. Ez NEM ennek a jobnak a hatásköre, csak jelzés a Next Jobs felé.

## Findings

1. A `grep -rn "^[a-z_]*:" jobs/.schema/meta.yaml | grep -v test_` minta CSAK a top-level
   (0 space indentációjú) mezőket találja meg — a `capability.*`, `agent.*`, `workplace.*`,
   `timestamps.*` nested mezők kimaradnak a kimenetből, bár a fájlban léteznek. Ez magában
   a job input.md-jében megadott parancsban van, nem hiba a végrehajtásban — de fontos
   tudni, hogy ez a grep-minta ÖNMAGÁBAN nem teljes mező-audit.
2. `tools/update-index.sh` (sor 28–38) NEM aggregálja `agent.session_id`-t a generált
   `jobs/index.yaml`-ba — az index csak `id`, `level`, `status`, `parent`, `capability_id`,
   `target_repo`, `created`, `started`, `completed` mezőket vesz át. Egy session-katalógus
   szempontjából ez hiányosság: az `index.yaml` jelenleg NEM alkalmas arra, hogy belőle
   session_id-alapú lekérdezést végezzünk anélkül, hogy mind a 27 `meta.yaml`-t egyenként
   megnyitnánk.
3. A `session-ingress-envelope-contract-001` job (status: `done`, `cic-mcp-session`
   target_repo) MÁR létrehozta a normatív `SessionIngressEnvelope` schema-t
   (`jobs/session-ingress-envelope-contract-001/output/session-ingress-envelope.schema.yaml`)
   — ez sokkal pontosabb leképezési cél, mint az input.md illusztratív mezőnevei
   (`provider_session_id`-szerű azonosító), ezért a Bridge Proposal táblát ehhez a
   TÉNYLEGES schema-hoz igazítottam, nem a spec illusztratív kifejezéseihez.
4. A `session-hook-collector-001` job (status: `done`, `cic-mcp-session` target_repo) MÁR
   implementált egy ÚJ `hooks/log-event.py`-t a `cic-mcp-session` repóban, ami a régi
   (factory-side, `workdir/tools/hooks/log-event.py`) összefoglaló-mintát egy gazdagabb,
   `SessionIngressEnvelope`-kompatibilis íróra cserélte — ez egy MÁSIK irányú bridge (a
   Claude Code hook-ok felől), nem azonos ezzel a jobbal (ami a factory job-lifecycle
   metaadat felől közelít). A két bridge KOMPLEMENTER, nem ütköző.

## Claim-Evidence Matrix

| Claim | Status | Evidence | Verification Method | Risk |
|---|---|---|---|---|
| `agent.session_id` a `meta.yaml`-ban a Claude Code session UUID-ot tárolja | proven | `jobs/.schema/meta.yaml:25` (`session_id: ""` komment: "Claude Code session UUID, set by run-job.sh") | file:line idézet | low |
| `job_id` a `meta.yaml`-ban egyedi azonosító | proven | `jobs/.schema/meta.yaml:4` | file:line idézet | low |
| `timestamps.started`/`timestamps.completed` léteznek a `meta.yaml`-ban | proven | `jobs/.schema/meta.yaml:49`, `jobs/.schema/meta.yaml:50` | file:line idézet | low |
| A top-level grep-minta NEM találja meg a nested mezőket | proven | a grep kimenet (11 sor) nem tartalmaz `id:`/`session_id:`/`started:` sort, miközben a fájl direkt olvasása (1–51. sor) ezeket tartalmazza | grep parancs futtatva + fájl direkt olvasása összevetve | low |
| Minden meglévő job `meta.yaml`-jában `agent.session_id` üres | proven | `grep -h "session_id:" jobs/*/meta.yaml` 27 sora, mind `session_id: ""` | mechanikus grep-kimenet, manuálisan átnézve | low |
| 25 job `done`, 2 job `running` jelenleg | proven | `grep -h "^status:" jobs/*/meta.yaml \| sort \| uniq -c` → `25 status: "done"`, `2 status: "running"` | mechanikus parancs kimenete | low |
| `update-index.sh` nem veszi át `session_id`-t az index.yaml-ba | proven | `tools/update-index.sh:28-38` (a `jobs.append({...})` dict csak `id/level/status/parent/capability_id/target_repo/created/started/completed` kulcsokat tartalmaz) | file:line idézet, kódolvasás | low |
| `events.jsonl` jelenleg könnyűsúlyú, raw payload nélküli | proven | corpus fac-0005 + risk-fac-0004 idézve | corpus-fájl idézet (1:1 sources) | low |
| A `SessionIngressEnvelope` `payload` mezője a teljes raw payloadot várja, nem összefoglalót | proven | `jobs/session-ingress-envelope-contract-001/output/session-ingress-envelope.schema.yaml:143-154` | file:line idézet | low |
| `idempotency_key` determinisztikus hash-számítást igényel a raw payload felett | proven | `session-ingress-envelope.schema.yaml:214-247` | file:line idézet | low |
| Egy retroaktív backfill heurisztikus (nem determinisztikus) párosítást igényelne | partial | a session jsonl fájlok elvi léte (`~/.claude-personal/agents/<id>/projects/...`), de ezek tényleges tartalma NEM lett ellenőrizve ebben a jobban (nem volt a Sources között) | nincs közvetlen fájl-ellenőrzés, csak `run-job.sh` logika alapján vont következtetés | medium |
| `agent.config_dir`/`agent.model` nem session-identitás, csak agent-azonosítás | proven | `jobs/.schema/meta.yaml:23-24` | file:line idézet | low |
| `session-hook-collector-001` és `session-ingress-envelope-contract-001` `done` állapotú, `cic-mcp-session` target_repo jobok | proven | `jobs/index.yaml` megfelelő bejegyzései (sor 89-97, 116-124) | file:line idézet az index.yaml-ból | low |

## Decisions Proposed

1. A bridge-leképezés a MEGLÉVŐ `agent.session_id`, `job_id`, `timestamps.started`
   mezőkre épüljön, ÚJ `meta.yaml` mezőt NEM kell hozzáadni a `SessionIngressEnvelope`
   alapfunkciók (provider_session_id, workstream, occurred_at-közelítés) lefedéséhez.
2. Ha egy KÉSŐBBI job tényleges collectort ír, fontolja meg egy `agent.collector_id`/
   `agent.source_kind` mező felvételét a séma `agent:` blokkjába a `source.collector`
   pontosabb leképezéséhez — ez itt csak JAVASLAT, nem implementáció.
3. A migráció CSAK új jobokra vonatkozzon — nincs retroaktív backfill a 27 meglévő
   jobra (indoklás: "Migration/Compatibility Plan" szekció).
4. `update-index.sh`-t egy KÉSŐBBI job bővíthetné `session_id` aggregálással, ha az
   `index.yaml`-ból session-szintű lekérdezés válik szükségessé — ez NEM ennek a
   jobnak a hatásköre, csak megjegyzés a Findings-ben.

## Rejected / Out Of Scope

- collector/bridge futtatható kód írása — explicit "Nem cél" és "Forbidden Shortcuts"
- `jobs/.schema/meta.yaml` séma tényleges módosítása — csak JAVASLAT szintjén jelölve
- `cic-mcp-session`/`cic-mcp-gateway` repók módosítása — nincs ilyen klón, nem is
  szükséges ehhez a jobhoz
- a `workdir/tools/hooks/log-event.py` közvetlen megnyitása — csak a corpus-fájl
  idézeteiből jellemezve, ahogy az input.md előírja
- `events.jsonl` végső session source-of-truth-ként kezelése — explicit elutasítva a
  "Why events.jsonl Is Not Enough" szekcióban

## Risks

- **Heurisztikus session-jsonl párosítás kockázata** (ha egy jövőbeli job mégis
  retroaktív backfillt próbálna): a `run-job.sh` mtime-alapú session-fájl keresése
  (sor 229–230) elvileg téves párosítást adhatna, ha két job ugyanabban a másodpercben
  fut — ez a jelenlegi (élő, nem csak migrációs) mechanizmus egy meglévő, nem ehhez a
  jobhoz tartozó gyengesége, csak megjegyzésként rögzítve.
- **`source.collector` mező-illesztés bizonytalansága**: az `agent.config_dir` mező
  KÖZVETETT megfelelő a `source.collector`-nak, nem pontos 1:1 — egy tényleges
  implementáció során ez pontosítást igényelhet (ld. Decisions Proposed #2).
- **A két különböző `log-event.py` névazonosság-kockázata**: a régi (factory-side,
  `workdir/tools/hooks/log-event.py`) és az új (`cic-mcp-session`-beli,
  `session-hook-collector-001` job által írt) script UGYANAZT A NEVET viseli két
  különböző repóban, két különböző célra — ez jövőbeli zavart kelthet, ha valaki a
  két fájlt összekeveri. Ez egy MEGLÉVŐ, máshol (a `session-hook-collector-001`
  output sor 274–289) már dokumentált döntés, itt csak megjegyzésként újra rögzítve.

## Definition Of Done Check

- [x] a `meta.yaml` session-releváns mezői file:line-nal felsorolva — "Existing meta.yaml
  Fields Mapped" tábla, mind top-level grep, mind nested mezők file:line hivatkozással
- [x] az `events.jsonl` elégtelenségének indoklása szintetizálva (nem csak idézve) — "Why
  events.jsonl Is Not Enough" szekció, fac-0005 + risk-fac-0004 szintetizálva a
  `SessionIngressEnvelope` payload/idempotency követelményeivel összevetve
- [x] mezőleképezési tábla (factory mező → SessionIngressEnvelope mező) kész — "Bridge
  Proposal" szekció, a tényleges normatív schema-hoz illesztve
- [x] migrációs/kompatibilitási döntés indoklással — "Migration/Compatibility Plan",
  4 pontos indoklás + ellenjavaslat jövőbeli collectorhoz
- [x] claim-evidence tábla kitöltve, nem üres — 13 sornyi Claim-Evidence Matrix, minden
  sor `proven` vagy `partial` státusszal és konkrét evidence-szel

## Next Jobs

1. **`factory-session-bridge-collector-001`** (jövőbeli, NEM ez a job) — tényleges
   collector-kód, ami a `run-job.sh` futás után (vagy egy dedikált hook-on keresztül)
   egy valós `SessionIngressEnvelope`-ot generál a `meta.yaml` mezőkből, a fent
   javasolt leképezést implementálva. Ez lenne az a job, ami ezt a kontraktust
   `experimental`-ból `candidate`-be emelné (legalább egy valós job-futáson átfutó
   próbával, ld. input.md "Target" szekció status-indoklása).
2. **`update-index.sh` `session_id`-aggregáció** — ha session-szintű index-lekérdezés
   válik szükségessé, bővítendő a `tools/update-index.sh` `jobs.append({...})` dict
   `session_id` kulccsal (`tools/update-index.sh:28-38`).
3. **`meta.yaml` séma `agent.collector_id`/`agent.source_kind` mező felvétele** — ha a
   #1 collector-job megerősíti, hogy a `source.collector` pontosítása szükséges,
   ez egy ÖNÁLLÓ, séma-módosító job legyen (ez a jelen job explicit nem nyúlhatott
   a séma-fájlhoz).
