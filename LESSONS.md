# Lessons

Operational incidents and their permanent fixes. Append newest at the top.

---

## 2026-09-05 — Do not touch `~/projects/codex`; it is a load-bearing path

### The two checkouts are NOT interchangeable
| Path | Role | Never |
|---|---|---|
| `~/projects/codex` | **Canonical local checkout.** Hardcoded by GL-023, the Codex delegation wrapper, the Dock `.app` launchers, and other automations. | move, rename, or delete it |
| `~/projects/codex-multi-profile-launcher` | Public-facing checkout of the same GitHub repo, used for the public install flow. | point local automations at it |

Both clone the same remote (`tbhrc/codex-multi-profile-launcher`), so they
look redundant. They are not: automations depend on the literal string
`/Users/david/projects/codex/...`, not on git identity.

### What broke
`~/projects/codex` was moved to the Trash during a cleanup that assumed it was
a stale duplicate. That silently broke:
- `Codex C1 Business.app` / `Codex C2 David.app` — their
  `Contents/MacOS/launcher` stub `exec`s
  `/Users/david/projects/codex/scripts/launch-codex-*-desktop.sh`; the app
  opened to nothing (exit 0, no window, no process).
- `bash /Users/david/projects/codex/wrappers/delegate_to_codex.sh` — the
  Codex worker dispatch path in GL-023. Codex delegation stopped working.
- Anything else keyed to that path.

### Fix
Restore the directory to its exact original location:
```bash
mv "$HOME/.Trash/codex-OLD-…" "$HOME/projects/codex"
```
and re-point the launcher stubs back:
```bash
for pair in "Codex C1 Business:launch-codex-business-desktop.sh" \
            "Codex C2 David:launch-codex-david-desktop.sh"; do
  app="${pair%%:*}"; script="${pair##*:}"
  printf '#!/usr/bin/env bash\nexec "%s/projects/codex/scripts/%s" "$@"\n' \
    "$HOME" "$script" > "$HOME/Applications/$app.app/Contents/MacOS/launcher"
  chmod +x "$HOME/Applications/$app.app/Contents/MacOS/launcher"
done
```

### Prevention
- Treat `~/projects/codex` as infrastructure, not a working copy. Do not
  "tidy" it even if it looks like a duplicate of
  `codex-multi-profile-launcher`.
- Before removing any `~/projects/*` directory, grep for its path first:
  `grep -rn "projects/<name>/" ~/FolderDesk-OS/700-knowledge ~/Library/LaunchAgents ~/.hermes ~/.config`
- Health check — every stub must resolve to a real executable:
  ```bash
  for a in "Codex C1 Business" "Codex C2 David"; do
    t=$(sed -n 's/^exec "\(.*\)" .*/\1/p' "$HOME/Applications/$a.app/Contents/MacOS/launcher")
    printf '%s -> %s' "$a" "$t"; [ -x "$t" ] && echo "  OK" || echo "  MISSING"
  done
  ```
- Also verify the dispatch wrapper:
  `bash ~/projects/codex/wrappers/delegate_to_codex.sh` should print usage, not
  "No such file or directory".
