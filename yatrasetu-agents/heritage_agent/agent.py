"""
Heritage Guide & Cultural Context Agent
----------------------------------------
Part of the YatraSetu AI Travel Companion system (Agents for Good track).

Responsibilities:
1. PRE-TRIP PRIMER  - explain the history/significance of a place BEFORE the
   traveler visits, grounded in real search results (not guessed facts).
2. ETIQUETTE CHECK   - quick, practical do's and don'ts for that specific
   site, pulled from a small curated lookup (a stand-in for a future
   database of verified local customs).

This is intentionally the SIMPLEST agent in the system: one LLM + two tools.
Once you understand this file, the same shape applies to every other
specialist agent (Safety, Booking, Budget, Itinerary) - only the instruction
and the tools change.
"""

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool

# ---------------------------------------------------------------------------
# CUSTOM TOOL
# ---------------------------------------------------------------------------
# ADK turns any plain Python function into a tool the model can call.
# The model decides WHEN to call it based on three things it can "read":
#   1. the function name
#   2. the type hints
#   3. the docstring  <-- this is not just documentation, the LLM reads this
#                          to understand what the tool does and what to pass.
#
# This dict is a placeholder. In the real system it becomes a small database
# table (or a call to a verified-customs API) - the function signature below
# stays exactly the same either way, which is the whole point of wrapping
# logic in a tool: you can swap the implementation without touching the agent.

ETIQUETTE_NOTES = {
    "hampi": "Remove footwear before entering temple complexes. Photography is restricted inside some shrines - look for signage.",
    "varanasi": "Avoid pointing your feet toward the river or the cremation ghats. Ask permission before photographing rituals.",
    "golden temple": "Cover your head before entering. Footwear must be removed, and washing your feet at the entrance is required.",
}


def get_etiquette_tip(place: str) -> dict:
    """Looks up local etiquette and customs to follow at a specific tourist site.

    Use this whenever a user asks about a destination, even if they didn't
    explicitly ask about etiquette - travelers should always be told this
    before they arrive.

    Args:
        place: Name of the tourist site or city, e.g. "Hampi" or "Varanasi".

    Returns:
        A dict with a 'status' key. If a tip exists, it's under 'tip'.
        If not, 'message' explains that no note is on file yet.
    """
    key = place.strip().lower()
    if key in ETIQUETTE_NOTES:
        return {"status": "success", "place": place, "tip": ETIQUETTE_NOTES[key]}
    return {
        "status": "not_found",
        "place": place,
        "message": "No specific etiquette note on file yet for this place - "
                   "this list will grow as more destinations are added.",
    }


# ---------------------------------------------------------------------------
# SUB-AGENT: search specialist
# ---------------------------------------------------------------------------
# Gemini's API does not allow a built-in tool (like google_search) and a
# custom function tool to be called in the SAME request. The fix is the
# "agent-as-a-tool" pattern: put google_search in its own small agent, then
# hand that whole agent to the main agent as if it were just another tool.

search_agent = Agent(
    name="search_heritage_info",
    model="gemini-2.5-flash-lite",
    description=(
        "Searches the web for accurate historical and cultural background "
        "on a tourist destination."
    ),
    instruction="""
Use the google_search tool to find accurate historical and cultural
background on the place the user asks about. Summarize it in 3-5 engaging
sentences written so a first-time visitor understands why the place matters
before they arrive - not a dry encyclopedia entry. Never invent facts; only
state what the search results actually returned, and say so honestly if
results are thin.
""",
    tools=[google_search],
)


# ---------------------------------------------------------------------------
# THE AGENT
# ---------------------------------------------------------------------------
# `root_agent` is the ONE required variable ADK looks for in this file.

root_agent = Agent(
    name="heritage_guide_agent",
    model="gemini-2.5-flash",
    description=(
        "Explains the history and cultural significance of a tourist "
        "destination, and gives practical etiquette tips for visiting it "
        "respectfully."
    ),
    instruction="""
You are the Heritage Guide & Cultural Context Agent for YatraSetu, a travel
companion app focused on helping Indian tourists travel safely, respectfully,
and without fear of being exploited or caught off guard.

When a user asks about a destination, do BOTH of the following every time:

1. PRE-TRIP PRIMER: Call the search_heritage_info tool to get accurate
   historical and cultural background, then present it to the user.

2. ETIQUETTE CHECK: Always also call get_etiquette_tip for the same place
   and include its result in your answer, even if no specific tip is on
   file - in that case, tell the user honestly that you don't have a
   verified note for this destination yet.

Never invent historical facts yourself. This app exists to protect
travelers, not mislead them.
""",
    tools=[AgentTool(agent=search_agent), get_etiquette_tip],
)