# CodeGuard

A governance-focused Coding Agent Harness built from scratch — no LangChain, no AutoGen, just Python.

## What is CodeGuard?

CodeGuard is a Coding Agent Harness that implements the full agent loop (context → LLM → action → guardrail → tool → feedback → stop) with a deep focus on **governance**: guardrails, HITL state machine, scope fence, and audit logging.

Every core mechanism is deterministic code testable with mock LLM — no prompts pretending to be safety mechanisms.

## Quick Start

### Docker (Recommended)

```bash
# Pull and run
docker pull ghcr.io/jiahuizhong205/codeguard:latest

# First run: configure credentials
docker run -it -p 8000:8000 -v codeguard-data:/data codeguard:latest init

# Start server
docker run -p 8000:8000 -v codeguard-data:/data -v /path/to/workspace:/workspace codeguard:latest serve
```

Open http://localhost:8000 in your browser.

### From Source

```bash
git clone https://github.com/jiahuizhong205/codeguard.git
cd codeguard
pip install -e ".[dev]"
codeguard init
codeguard serve
```

## Credential Security

- API keys are encrypted with Fernet (master password)
- Keys never hardcoded, never in git, never in logs
- First run guides you through secure setup
- Check status: `codeguard credentials status` (no plaintext shown)

## Mechanism Demo

```bash
codeguard demo
```

Demonstrates 3 governance behaviors under mock LLM:
1. Guardrail blocks `rm -rf`
2. Feedback loop drives self-correction
3. Scope fence blocks path escape

## Testing

```bash
make test
```

All core mechanisms have deterministic unit tests with mock LLM.

## Architecture

```
Agent Main Loop
├── LLM Client (mockable)
├── Tool Dispatcher
│   ├── Built-in Tools (file, shell, test, lint)
│   └── MCP Tool Adapter (external tools)
├── Guardrail Engine (11 rules, configurable)
├── HITL Manager (state machine)
├── Scope Fence (workspace boundary)
├── Audit Log (JSONL, sanitized)
├── Feedback Validators (test, lint)
├── Memory Store (cross-session JSON)
└── Skill Loader (markdown skills)
```

## Tech Stack

- Python 3.12, FastAPI, pytest
- React + Vite (frontend)
- Docker (distribution)
- cryptography/Fernet (credential encryption)

## Known Limitations

- Requires Docker (or Python 3.12+ from source)
- Workspace must be mounted into container
- MCP servers must be accessible from container
- No system keyring in Docker (uses encrypted file)

## License

MIT
