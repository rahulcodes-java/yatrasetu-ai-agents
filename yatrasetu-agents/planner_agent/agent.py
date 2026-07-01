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

# Ensure the parent directory is in sys.path so security can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import security

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool

# Import all five specialist agents
from heritage_agent.agent import root_agent as heritage_agent_root
from safety_agent.agent import root_agent as safety_agent_root
from booking_agent.agent import root_agent as booking_agent_root
from itinerary_agent.agent import root_agent as itinerary_agent_root
from budget_and_stay_agent.agent import root_agent as budget_agent_root

# Wrap them as AgentTools
heritage_tool = AgentTool(agent=heritage_agent_root)
safety_tool = AgentTool(agent=safety_agent_root)
booking_tool = AgentTool(agent=booking_agent_root)
itinerary_tool = AgentTool(agent=itinerary_agent_root)
budget_tool = AgentTool(agent=budget_agent_root)

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

root_agent = Agent(
    name="planner_agent",
    model="gemini-2.5-flash",
    description="A planner orchestrator that synthesizes inputs from five specialist agents and external services to create a cohesive travel plan.",
    instruction="""
You are the travel orchestrator for YatraSetu. Your job is to accept a single travel query containing destination, duration, budget, party size, and preferences.

Call all five specialist agents with the user's trip details to gather core recommendations:
1. heritage_guide_tool
2. safety_readiness_tool
3. booking_ticketing_tool
4. itinerary_tool
5. budget_stay_tool

In addition, call the following external services:
- Call get_weather_data with the destination and month (if specified in the query).
- Call get_destination_summary with the destination or key monuments.

Synthesize all independent responses and external service outputs into ONE unified, actionable travel plan.
Format as a readable, well-organized trip plan with clear sections:
- **Heritage & Culture** (from Heritage Guide, enriched with Wikipedia summary and URL link)
- **Weather & Seasonal Advice** (from get_weather_data tool - detailing temperature, weather conditions, packing recommendations, and weather-driven scheduling advice)
- **Safety & Readiness** (from Safety Agent - adjust packing lists and highlight hazards based on the weather)
- **Official Bookings** (from Booking Agent)
- **Day-by-Day Itinerary** (from Itinerary Agent - adjust activities dynamically to match the weather. For example, in hot summers recommend indoor attractions in the afternoon and outdoor sightseeing in the early morning/late evening. In heavy monsoons, suggest indoor/under-cover alternatives and caution about outdoor sites)
- **Budget Breakdown & Accommodations** (from Budget Agent)

Graceful Weather/Wiki Failures:
If the weather or Wikipedia services return error status or are unavailable, do not fail. Continue planning using your general knowledge and clearly state: "Note: Live weather/Wikipedia service was offline, utilizing fallback historical advice."

Do not skip any section. Synthesize everything into one unified, actionable travel plan.
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
