# YatraSetu Agents

A multi-agent travel companion system, built with Google's Agent Development
Kit (ADK). This folder currently contains ONE working agent
(`heritage_agent`) so you can learn the pattern before building the other 5.

## What an "agent" actually is here

In ADK, an agent is just three things wired together:

1. A **model** (which Gemini model answers)
2. An **instruction** (a system prompt - the agent's job description)
3. A list of **tools** (Python functions / built-ins the model can call when
   it decides it needs them)

That's it. `adk` handles the loop of "ask the model -> did it ask to call a
tool? -> run the tool -> give the result back to the model -> repeat until
it has a final answer."

## Setup

```bash
# 1. From this folder, create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. Install ADK
pip install -r requirements.txt

# 3. Add your API key
cp ../.env.example ../.env
# then open ../.env at the project root and paste your real key from
# https://aistudio.google.com/apikey
```

## Run it (terminal)

```bash
adk run heritage_agent
```

This drops you into an interactive terminal chat with just this one agent.
Try asking: `Tell me about Hampi` and watch it call both tools.

## Run it (browser, optional)

```bash
adk web
```

Opens a local web UI where you can watch each tool call happen step by step
- useful once you're debugging multiple agents later.

## Project structure (current + planned)

```
yatrasetu-ai-agents/ (Project Root)
├── .env.example
├── .gitignore
└── yatrasetu-agents/
    ├── requirements.txt
    ├── README.md
    ├── heritage_agent/        <- DONE - built in this session
    │   ├── __init__.py
    │   └── agent.py
    ├── safety_agent/          <- next: scams, health risk advisory, packing
    │   ├── __init__.py
    │   └── agent.py
    ├── itinerary_agent/       <- day-wise plan + routes
    ├── budget_agent/          <- stay/cost breakdown
    ├── booking_agent/         <- redirects to verified official ticket sources
    └── planner_agent/         <- orchestrator: calls the other 5 and merges output
```

Every future agent follows the exact same 2-file shape as `heritage_agent/`:
`__init__.py` and `agent.py` (with a `root_agent` variable). Environment variables
are consolidated in a single root-level `.env` file, as ADK automatically finds
it by walking up parent folders. Once 2+ agents exist side by side in this folder,
the Planner Agent will use ADK's **multi-agent / Workflow** support to call them
as sub-agents instead of you wiring that by hand.

## Why this counts toward the hackathon rubric

- **Multi-agent system (ADK):** this file structure - once Planner +
  sub-agents both exist - is the literal pattern judges will look for in code.
- **MCP Server / tool use:** `google_search` here is a built-in tool;
  `get_etiquette_tip` is a custom one. The Booking and Safety agents are
  good candidates to wrap as an MCP server later, since they're the most
  reusable across the rest of YatraSetu.
