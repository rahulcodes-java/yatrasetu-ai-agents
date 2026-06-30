# YatraSetu Agents

A multi-agent travel companion system, built with Google's Agent Development
Kit (ADK). This folder currently contains three working agents
(`heritage_agent`, `safety_agent`, `booking_agent`) that each follow the
same 2-file pattern — learn one and you know them all.

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
adk run heritage_agent   # history, cultural context, etiquette tips
adk run safety_agent     # scams, health risks, packing, accessibility
adk run booking_agent    # official ticket links, scam price radar, crowd forecast
```

Each drops you into an interactive terminal chat with that agent.
Try asking `booking_agent`: `I want to visit the Taj Mahal — where do I book tickets and what should I watch out for?`

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
    ├── heritage_agent/        <- DONE - history, cultural context, etiquette
    │   ├── __init__.py
    │   └── agent.py
    ├── safety_agent/          <- DONE - scams, health risks, packing, accessibility
    │   ├── __init__.py
    │   └── agent.py
    ├── booking_agent/         <- DONE - official ticket links, scam price radar, crowd forecast
    │   ├── __init__.py
    │   └── agent.py
    ├── itinerary_agent/       <- DONE - day-wise plan + routes
    │   ├── __init__.py
    │   └── agent.py
    ├── budget_and_stay_agent/ <- DONE - stay/cost breakdown
    │   ├── __init__.py
    │   └── agent.py
    └── planner_agent/         <- DONE - orchestrator that calls the other agents and merges output
        ├── __init__.py
        └── agent.py
```

Every agent follows the exact same 2-file shape (`__init__.py` + `agent.py`
with a `root_agent` variable). Environment variables are consolidated in a
single root-level `.env` file — ADK automatically finds it by walking up
parent folders. Once a Planner Agent exists alongside the specialist agents,
ADK's **multi-agent / Workflow** support handles orchestration without you
wiring it by hand.

## Rate-limit architecture note

Each agent uses the **"agent-as-a-tool"** pattern to work around Gemini's
restriction on mixing built-in tools (`google_search`) with custom function
tools in the same request:

- The `search_agent` sub-agent inside each specialist agent uses
  `gemini-2.5-flash-lite` — this runs on a **separate free-tier quota bucket**
  from the root agent, reducing rate-limit pressure.
- The `root_agent` in every specialist stays on `gemini-2.5-flash` for
  full response quality.

## Why this counts toward the hackathon rubric

- **Multi-agent system (ADK):** this file structure — once Planner +
  sub-agents both exist — is the literal pattern judges will look for in code.
- **MCP Server / tool use:** `google_search` here is a built-in tool;
  `get_etiquette_tip`, `get_safety_and_packing_info`, and
  `get_booking_scam_info` are custom ones. The Booking and Safety agents are
  good candidates to wrap as an MCP server later, since they're the most
  reusable across the rest of YatraSetu.
