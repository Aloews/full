# OpenGSD Migration & Legacy GSD Cleanup Report

Audit of a machine for legacy **GSD / GSD2 / Pi** traces, safe removal of any
found, and installation of the **OpenGSD** continuation line.

> **Scope note:** This was performed inside an ephemeral remote execution
> container (`HOME=/root`), which is **not** guaranteed to be the same host as
> the operator's personal machine. Re-run the same steps on the real target
> host if that is where the legacy install is suspected to live.

## Summary

- **No legacy GSD / GSD2 / Pi / OpenGSD install was found anywhere.** Nothing
  was deleted (there was nothing to delete).
- Installed the continuation line **`@opengsd/gsd-pi@1.11.0`** via its official
  command. `gsd` is now on `PATH` and reports `1.11.0`.
- No legacy-line packages (`gsd-pi`, `@gsd-build/*`, `@gsd-now/*`) were used,
  installed, or pulled in transitively.

## Environment

- `HOME=/root` → so "`~/.claude`" resolves to `/root/.claude`.
- Node `v22.22.2` / npm `10.9.7`; global root `/opt/node22/lib/node_modules`.

## 1. Inventory (read-only)

Every location where a GSD install typically leaves traces was checked. All clean:

| Location | Result |
| --- | --- |
| `~/.claude/commands`, `~/.claude/agents`, `~/.claude/plugins` | directories do not exist |
| `~/.claude/skills` | only standard skills (docx, pdf, pptx, xlsx, morning, …) — no GSD skill |
| `~/.claude.json` | 0 matches for `gsd` |
| Global npm packages | no `gsd`, `gsd-pi`, or `@opengsd/*` before install |
| bun / pnpm / yarn global | empty |
| `gsd` / `gsd-cli` / `gsd-pi` / `gsd-core` on `PATH` | none present |
| `~/.gsd`, `~/.config/gsd`, `~/.local/share/gsd` | did not exist |
| shell rc (`.bashrc`, `.zshrc`, `.profile`) | no `gsd` references |
| repo working tree | no GSD config committed |

## 2. Categorization of findings

- **Legacy GSD1 files** — none.
- **Legacy GSD2 / Pi package** — none on the machine. (For reference, the
  legacy line does exist in the npm registry and is deprecated: unscoped
  `gsd-pi@3.0.0` and the `@gsd-build/*` engine packages. Neither was installed
  here.)
- **Questionable / non-obvious artifacts** — every `gsd` hit from a broad
  filesystem search was a false positive and needs no manual review:
  - `pml.xsd` inside the docx/pptx/xlsx skills → the Office schema type
    `CT_TagsData` (substring `…Ta`**`gsD`**`ata`).
  - `pygments` lexers `thingsdb.py`, lasso, sas → substring inside unrelated words.
  - the session transcript `.jsonl` under `~/.claude/projects/…` → contains
    "GSD" only because this task's own prompt is logged there.
  - git refs `claude/`**`gsd`**`-legacy-cleanup-…` → this task's working branch.

## 3. Deletion

Nothing to delete. No legacy uninstall commands were run (a registry package
`old-gsd-cleanup` exists but was deliberately **not** executed — it would fetch
third-party code and there was nothing to clean). No unrelated user configs
were touched.

## 4. Post-removal verification

Because nothing legacy existed, there are no legacy entrypoints to dangle: no
`gsd*` binaries, no `~/.gsd` runtime home (pre-install), and no shell-rc hooks
referenced any legacy install.

## 5. Installation — OpenGSD continuation line

- **Package:** `@opengsd/gsd-pi@1.11.0` (scope `@opengsd/*`, repo
  `open-gsd/gsd-pi`) — the official successor to the deprecated `gsd-pi`/"Pi"
  line. The unscoped npm name `opengsd` was rejected: it is an unrelated 2017
  utility, not this project.
- **Command used:** `npm install -g @opengsd/gsd-pi@latest` (the documented
  direct global install; the interactive guided `npx` installer was avoided
  because this session is non-interactive).
- **Result:** binaries `gsd`, `gsd-cli`, `gsd-pi` installed to
  `/opt/node22/bin`; `gsd --version` → `1.11.0`.
- **Scaffolded:** managed home `~/.gsd/agent/` including the RTK shell-compression
  binary (`~/.gsd/agent/bin/rtk`); native engine `@opengsd/engine-linux-x64-gnu`.
- **Skipped:** the installer's own Chromium download (this container already
  provides Chromium; browser automation can use it).
- **Clean of legacy:** transitive deps are all `@opengsd/*` (contracts,
  engine-linux-x64-gnu, gsd-browser, mcp-server, rpc-client) + standard SDKs —
  no `gsd-pi`/`@gsd-build`/`@gsd-now`.

## Command reference (what to use going forward)

| Command | Purpose |
| --- | --- |
| `gsd` | Launch the interactive coding agent (TUI). First run walks provider setup. |
| `gsd config` | Re-run the setup wizard (model provider / API key / OAuth). |
| `gsd -p "…"` / `gsd "…"` | Single-shot / print mode. |
| `gsd --web` | Browser-based control plane. |
| `gsd list` / `gsd install <source>` / `gsd remove <source>` | Manage extensions / skills / commands. |
| `gsd update` (alias `gsd upgrade`) | Update GSD to the latest release. |
| `gsd auto` / `gsd headless` | Run auto-mode / `/gsd` commands without the TUI. |
| `gsd --version` / `gsd --help` | Version / help. |

## Manual follow-ups

1. Run **`gsd config`** to set a model provider and credentials before the
   first real session — the install does not configure any provider.
2. If the real target is a **different host** than this container, run the same
   inventory + `npm install -g @opengsd/gsd-pi@latest` there.
3. Future upgrades: `gsd update` or `npm install -g @opengsd/gsd-pi@latest`.
