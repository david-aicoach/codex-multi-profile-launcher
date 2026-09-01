# Changelog

## Unreleased

- added explicit GitHub PR review routing for `@codex-business review` and `@codex-david review`
- added a reusable self-hosted GitHub Actions workflow that runs only trusted default-branch router code
- added strict requester permission checks, command parsing, structured result validation, and sanitized failure handling
- added a dedicated review-runner verifier and cross-repository caller template
- kept native `@codex` behavior unchanged and explicitly prohibited quota-based profile rotation or automatic fallback

## 1.1.0 - 2026-07-11

- simplified the package into a Codex multi-profile launcher
- made your task workspace the explicit source of truth for tasks and orchestration
- changed worker codes to `C1` for Codex Business and `C2` for Codex David
- added Dock-friendly launchers for `C1` and `C2`
- removed the separate control-plane architecture language
- removed legacy ChatGPT-Web source reference files
- updated the wrapper to accept task filenames such as `065-example-2026-07-11.md`

## 1.0.0 - 2026-07-11

- initial dual-Codex package draft
