---
name: ctf-plat-skills
description: "Automates CTF platform interaction — detects platform type (GZCTF, Zerosecone, A1CTF, Adworld, CTFd), authenticates, and runs challenge actions (list, fetch, download, start, stop, submit flag) via scripts/. Use when: the user provides a CTF competition URL and needs to list challenges, download attachments, manage instances, or submit flags."
user-invocable: true
triggers:
  - "CTF"
  - "capture the flag"
  - "GZCTF"
  - "Zerosecone"
  - "A1CTF"
  - "Adworld"
  - "CTFd"
  - "list challenges"
  - "submit flag"
  - "start instance"
  - "download attachment"
  - "CTF platform"
---

# CTF Platform Workflow Skill

Detects CTF platform type from a URL, collects credentials, and routes actions (list, fetch, download, start, stop, renew, submit) to the correct platform script under `scripts/`.

## Inputs

- **Required:** target URL or domain, platform credentials (token) from the user
- **Optional:** action (`metadata`, `list`, `fetch`, `download`, `start`, `stop`, `renew`, `submit`), action arguments (`challenge_id`, `instance_id`, `flag`)

## Script Routing Map

| Detection result | Script | Env vars |
|---|---|---|
| `gzctf` | `python scripts/gzctf.py` | `GZCTF_URL`, `GZCTF_TOKEN` |
| `zerosecone` | `python scripts/zerosecone.py` | `ZEROSECONE_URL`, `ZEROSECONE_TOKEN` |
| `a1ctf` | `python scripts/a1ctf.py` | `A1CTF_URL`, `A1CTF_TOKEN` |
| `adworld` | `python scripts/adworld.py` | `ADWORLD_URL`, `ADWORLD_TOKEN` |

Detection also recognizes `ret2shell`, `ctfd`, `ichunqiu`, and `ctfplus` — but no scripts exist for them yet. Report unsupported platform if matched.

## Workflow

1. **Detect platform** — use the detection script only; do not infer from manual HTML inspection or branding heuristics.
   ```bash
   python scripts/detect_platorm.py --url <target_url>
   ```
   **Validate:** output must contain `Detected: <platform>`. If it prints an error or no match, stop and report.

2. **Collect credentials** — ask the user for the platform token. Save as environment variables or pass via `--url` / `--token` flags.

3. **Route and execute** — call the matched platform script with the requested action:
   ```bash
   python scripts/<platform>.py --url "$<PLATFORM>_URL" --token "$<PLATFORM>_TOKEN" <action> [args]
   ```
   Actions: `metadata`, `list`, `fetch <challenge_id>`, `download <challenge_id>`, `start <challenge_id>`, `stop <instance_id>`, `renew <instance_id>`, `submit <challenge_id> <flag>`

   **Validate:** command exits 0 and returns parseable JSON. On failure, show error details and offer retry/change action/stop.

## WebSocket Environments (GZCTF)

When a GZCTF instance returns a websocket proxy UUID instead of `host:port`:

1. Check `websocat` is installed: `command -v websocat`
2. If missing, install (`brew install websocat` on macOS, or download binary from the websocat GitHub releases page). If installation fails, ask user to install manually.
3. Probe directly first (no Cookie header):
   ```bash
   printf 'help\n' | websocat -v -k -t -E 'wss://<domain>/api/proxy/<instance_uuid>'
   ```
4. Bind to local port for TCP/HTTP tools:
   ```bash
   websocat tcp-l:127.0.0.1:<local_port> wss://<domain>/api/proxy/<instance_uuid>
   ```
5. Continue exploitation through the bound local port.

## Decision Points

- **No platform match:** stop and report detection failure
- **No mapped script:** report unsupported platform (e.g. ret2shell, ctfd)
- **Missing credentials:** prompt user before running platform script
- **Action failure:** return API error JSON, offer retry/change/stop
