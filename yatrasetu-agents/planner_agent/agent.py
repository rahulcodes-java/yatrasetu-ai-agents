"""
Planner Orchestrator Agent
---------------------------
Part of the YatraSetu AI Travel Companion system (Agents for Good track).

Responsibilities:
1. Accept a single travel query (destination, duration, budget, party size, preferences).
2. Call all five specialist agents (heritage, safety, booking, itinerary, budget_and_stay) in parallel/sequence.
3. Synthesize their independent outputs into one unified, actionable travel plan covering the five dimensions.
"""
import sys
import os
import json
import urllib.parse
import urllib.request

# Ensure the parent directory is in sys.path so security and planner_utils can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import security
import planner_utils

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool

# Import all five specialist agents
from heritage_agent.agent import root_agent as heritage_agent_root
from safety_agent.agent import root_agent as safety_agent_root
from booking_agent.agent import root_agent as booking_agent_root
from itinerary_agent.agent import root_agent as itinerary_agent_root
from budget_and_stay_agent.agent import root_agent as budget_agent_root

# Wrap them as AgentTools with deduplication, timing, and fault-tolerance
heritage_tool = planner_utils.wrap_agent_tool(AgentTool(agent=heritage_agent_root))
safety_tool = planner_utils.wrap_agent_tool(AgentTool(agent=safety_agent_root))
booking_tool = planner_utils.wrap_agent_tool(AgentTool(agent=booking_agent_root))
itinerary_tool = planner_utils.wrap_agent_tool(AgentTool(agent=itinerary_agent_root))
budget_tool = planner_utils.wrap_agent_tool(AgentTool(agent=budget_agent_root))

# Search agent for research if needed
search_agent = Agent(
    name="search_agent",
    model="gemini-2.5-flash-lite",
    description="Searches the web for general travel information if needed.",
    instruction="""
Use google_search to find any supplementary travel information not covered by the specialist agents.
""",
    tools=[google_search]
)

# ---------------------------------------------------------------------------
# EXTERNAL MCP TOOLS
# ---------------------------------------------------------------------------

def get_weather_data(destination: str, month: str = None) -> dict:
    """Retrieves curated weather data for a specific destination and optional month.
    
    This includes temperature range, weather conditions, best visiting season,
    monsoon season, packing suggestions, and travel advice.
    
    Args:
        destination: The target destination (e.g. Jaipur, Goa, Delhi, Varanasi, Rajasthan).
        month: The optional month of travel (e.g. June, December).
    """
    url = "http://localhost:5001/weather"
    params = {"destination": destination}
    if month:
        params["month"] = month
        
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"
    
    try:
        req = urllib.request.Request(full_url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                return json.loads(response.read().decode('utf-8'))
            else:
                return {"status": "error", "message": f"Server returned status code {response.status}"}
    except Exception as e:
        return {
            "status": "error",
            "message": f"Could not connect to Weather Service on localhost:5001. Live weather data is unavailable. Proceeding with general travel advice. (Error: {str(e)})"
        }

def get_destination_summary(destination: str) -> dict:
    """Queries Wikipedia for a summary and article URL of the specified destination.
    
    Use this to enrich the historical and cultural context of the travel plan.
    
    Args:
        destination: The target destination or monument (e.g. "Taj Mahal", "Varanasi").
    """
    url = "http://localhost:5002/wiki"
    params = {"destination": destination}
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"
    
    try:
        req = urllib.request.Request(full_url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                return json.loads(response.read().decode('utf-8'))
            else:
                return {"status": "error", "message": f"Server returned status code {response.status}"}
    except Exception as e:
        return {
            "status": "error",
            "message": f"Could not connect to Wikipedia Service on localhost:5002. Wikipedia data is unavailable. Proceeding. (Error: {str(e)})"
        }

# Wrap functions with session caching, timing, and deduplication
get_weather_data = planner_utils.wrap_function_tool(get_weather_data)
get_destination_summary = planner_utils.wrap_function_tool(get_destination_summary)

root_agent = Agent(
    name="planner_agent",
    model="gemini-2.5-flash",
    description="A planner orchestrator that synthesizes inputs from specialist agents and external services to create a cohesive travel plan.",
    instruction="""
You are the travel orchestrator for YatraSetu. Your job is to coordinate specialist agents and external services to assemble a unified travel plan.

To minimize Gemini API calls and keep responses efficient, you MUST strictly follow these rules in order:

1. INTENT CLASSIFICATION:
   - First, analyze the user query to classify the user's intent. Determine which of the following intents are present:
     * Heritage: history, culture, monument background, or etiquette (uses heritage_guide_tool, get_destination_summary).
     * Weather: temperature, climate, monsoons, seasonal advice (uses get_weather_data).
     * Safety: safety precautions, emergency contacts, local scams (uses safety_readiness_tool).
     * Booking: flight/train bookings, ticket prices, booking scams, official booking portals (uses booking_ticketing_tool).
     * Itinerary: day-by-day travel plan or route (uses itinerary_tool).
     * Budget: costs, trip expense estimation, budget stay recommendations (uses budget_stay_tool).
     * Complete Planning: a full trip plan request (implies Itinerary, Budget, Booking, Safety, and Heritage).

2. CONTEXT-SPECIFIC INPUT VALIDATION:
   - Verify if the required inputs for the classified intent(s) are present in the user query:
     * Heritage queries -> Requires ONLY **destination** (trip duration/days is NOT required).
     * Weather queries -> Requires ONLY **destination** (month is optional; duration/days is NOT required).
     * Safety queries -> Requires ONLY **destination** (duration/days is NOT required).
     * Booking queries -> Requires ONLY **destination** (plus attraction/monument if applicable; duration/days is NOT required).
     * Itinerary queries -> Requires **destination** and **duration (days)**.
     * Budget queries -> Requires **destination**, **duration (days)**, **number of travelers**, and **budget tier** (e.g. budget/mid-range/premium).
     * Complete Planning queries -> Requires **destination** and **duration (days)**.
   - If any required inputs for the detected intent(s) are missing, DO NOT call any tools or specialist agents. Immediately return a single, polite clarification message asking for all missing fields relevant to that intent. Do not ask for fields that are not required for the intent (e.g. do not ask for trip duration if they only asked about weather or history).

3. SELECTIVE INVOCATION:
   - Call ONLY the specialist agents and tools that are directly relevant to the detected intent(s). Never call agents unconditionally if the query only concerns a subset.
   - If a specialist agent or tool returns a fully formatted, presentation-ready response, embed it directly into the final plan. Do NOT edit, rephrase, summarize, or alter its content in any way. Keep it as-is.

4. PURE ORCHESTRATOR ROLE:
   - Do not generate your own domain-specific advice. Rely entirely on the output of the specialist agents and tools.

Format the final response with sections matching the user's requested topics:
- **Heritage & Culture** (from Heritage Guide + Wikipedia link if queried)
- **Weather & Seasonal Advice** (from Weather tool if queried)
- **Safety & Readiness** (from Safety Agent if queried)
- **Official Bookings** (from Booking Agent if queried)
- **Day-by-Day Itinerary** (from Itinerary Agent if queried)
- **Budget Breakdown & Accommodations** (from Budget Agent if queried)

If any service fails or is offline, include the recovery error message directly in the plan and proceed with the remaining sections.
""",
    tools=[
        AgentTool(agent=search_agent),
        heritage_tool,
        safety_tool,
        booking_tool,
        itinerary_tool,
        budget_tool,
        get_weather_data,
        get_destination_summary
    ]
)
