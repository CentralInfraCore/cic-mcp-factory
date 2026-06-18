# cic-mcp-factory

MCP capability gyártó- és karbantartó factory a `cic-mcp-*` családhoz (`knowledge`, `workdir`,
`session`, `shared`, `gateway`) — git-követett capability-job-ok, izolált agent workspace-ek.

---

## Gyors megértés AI-val

1. `CLAUDE.md` — működési modell, capability lifecycle, job struktúra
2. `.claude/commands/job-*.md` — boot/create/run/validate/review/close skill-ek
3. `jobs/` — jelenleg üres (még nincs lefuttatott capability-job); a struktúrát a
   `.schema/meta.yaml` és a `.claude/commands/job-create.md` írja le

---

*Ez a repó a `cic-factory` job-lifecycle mintáját követi, MCP capability-kre specializálva.*
