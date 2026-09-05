# Lessons

Operational incidents and their permanent fixes. Append newest at the top.

---

## 2026-09-05 — Dock launchers broke because the repo clone was deleted

### Symptom
`Codex C1 Business.app` (and `Codex C2 David.app`) did nothing when opened.
No window, no error dialog, `open -n` returned exit 0 but no `ChatGPT
--user-data-dir=.../Codex-C1-Business` process ever appeared.

### Root cause
The generated `.app` bundles are thin stubs. Each
`<App>.app/Contents/MacOS/launcher` is a one-line script that `exec`s an
**absolute path** into the repo clone it was installed from:

```
exec "/Users/david/projects/codex/scripts/launch-codex-business-desktop.sh" "$@"
```

That clone (`~/projects/codex`) was moved to the Trash during cleanup. The
launcher then exec'd a missing file and died silently. C2 kept working only
because it was already running from before the move; it would have failed on
its next cold start too.

### Fix applied
Repointed both bundles at the surviving clone
(`~/projects/codex-multi-profile-launcher/scripts/`). The launch scripts are
self-locating (`ROOT` is derived from `BASH_SOURCE`), so only the stub path
needed changing.

### Prevention
- **Do not delete or rename the clone the launchers were installed from.**
  Treat `~/projects/codex-multi-profile-launcher/` as the permanent install
  location. If it must move, re-run `scripts/install-macos-launchers.sh` from
  the new location afterwards.
- If you maintain more than one clone, only ever install launchers from the
  canonical one, and delete the extras *before* installing so a stale path is
  never baked in.
- Quick health check (should print a real, executable file for each app):
  ```bash
  for a in "Codex C1 Business" "Codex C2 David"; do
    t=$(sed -n 's/^exec "\(.*\)" .*/\1/p' "$HOME/Applications/$a.app/Contents/MacOS/launcher")
    printf '%s -> %s' "$a" "$t"; [ -x "$t" ] && echo "  OK" || echo "  MISSING"
  done
  ```
