# ScamShield Phase 1

Starter scaffold for A05 AgentReel. Contains an LLM-powered Planner agent ONLY;
not a complete autonomous reel pipeline. No API requests have been executed as
part of packaging this starter.

## Setup (macOS / Linux)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your own Groq key. Never commit `.env`.
Then run:

```bash
python -m agents.planner
```

Expected outcome: `outputs/plan.json`. `GROQ_MODEL` must be a model supporting
Groq JSON mode; change it if your account's model access differs. The Planner
has minimal validation; full QA, logs, source citations and feedback loops are
future phases. All scenarios described in the brief are conceptual, not actual
reports of incidents.
