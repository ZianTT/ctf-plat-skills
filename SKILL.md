---
name: ctf-plat-skills
description: "Use when: detecting target CTF platform type, collecting user credentials, and routing actions to the correct script under scripts/ by platform."
---

# CTF Platform Workflow Skill

## Outcome
Produce a reusable automation flow that can:
- Detect target CTF platform type from the target URL/domain using the repository detection script only
- Collect credentials from the user safely
- Route commands to the correct script in `scripts/` based on platform type

## Inputs
- Required:
  - target URL or domain
  - platform credential(s) from the user
- Optional:
  - desired action (`metadata`, `list`, `fetch`, `download`, `start`, `stop`, `renew`, `submit`)
  - action arguments (`challenge_id`, `instance_id`, `flag`)

## Script Routing Map
- `zerosecone` -> `python scripts/zerosecone.py ...`
- More platforms can be added later by creating new scripts in `scripts/` and extending the routing map.

## Core Workflow
Run from the workspace root.

1. Detect platform type using the repository detection script only. Fix to url format if needed.
```bash
python scripts/detect_platorm.py --url <target_url>
```
Do not infer platform type from manual HTML inspection, browser checks, ad-hoc HTTP probing, or branding heuristics when this script is available.
2. Ask user for required credentials after detection.

3. Save base_url and token (or other credentials) in environment variables or pass as arguments to platform scripts.

4. Route to the matched platform script.
- If detected platform is `zerosecone`, call:
```bash
python scripts/zerosecone.py list
```

5. Execute user-requested action with routed script.
```bash
python scripts/zerosecone.py fetch <challenge_id>
python scripts/zerosecone.py download <challenge_id>
python scripts/zerosecone.py start <challenge_id>
python scripts/zerosecone.py renew <instance_id>
python scripts/zerosecone.py submit <challenge_id> <flag>
```

## Environment Variable

- ZEROSECONE_URL: Base URL of the Zerosecone CTF platform (e.g., https://www.aliyunctf.com)
- ZEROSECONE_TOKEN: Authentication token for API access

## Decision Points
- If platform detection script returns no match:
  - stop and report detection failure
- If detected platform has no mapped script:
  - stop and report unsupported platform
- If credentials are missing:
  - prompt user for required fields before running platform script
- If action fails:
  - return API JSON/error details and ask whether to retry, switch action, or stop

## Completion Checks
- Platform type is identified by `scripts/detect_platorm.py`
- Required credentials are explicitly collected from the user
- Correct script path is selected based on platform type
- Routed command executes and returns parseable output
- On failures, the response includes next-step options (retry/change action/stop)

## Command Patterns
Detection:
```bash
python scripts/detect_platorm.py --url <target_url>
```

Zerosecone with env token:
```bash
python scripts/zerosecone.py list
```

Zerosecone with explicit credentials:
```bash
python scripts/zerosecone.py --url <target_url> --token "$ZEROSECONE_TOKEN" <action> [args]
```
