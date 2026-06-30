"""
Planner Orchestrator Agent
---------------------------
Part of the YatraSetu AI Travel Companion system (Agents for Good track).

Responsibilities:
1. Accept a single travel query (destination, duration, budget, party size, preferences).
2. Call all five specialist agents (heritage, safety, booking, itinerary, budget_and_stay) in parallel/sequence.
3. Synthesize their independent outputs into one unified, actionable travel plan covering the five dimensions.
"""

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

root_agent = Agent(
    name="planner_agent",
    model="gemini-2.5-flash",
    description="A planner orchestrator that synthesizes inputs from five specialist agents to create a cohesive travel plan.",
    instruction="""
You are the travel orchestrator for YatraSetu. Your job is to accept a single travel query containing destination, duration, budget, party size, and preferences.

Call all five specialist agents with the user's trip details. You should call them in sequence or parallel to gather all necessary information:
1. heritage_guide_tool
2. safety_readiness_tool
3. booking_ticketing_tool
4. itinerary_tool
5. budget_stay_tool

Synthesize their independent responses into ONE unified, actionable travel plan.
Format as a readable, well-organized trip plan with clear sections:
- **Heritage & Culture** (from Heritage Guide)
- **Safety & Readiness** (from Safety Agent)
- **Official Bookings** (from Booking Agent)
- **Day-by-Day Itinerary** (from Itinerary Agent)
- **Budget Breakdown & Accommodations** (from Budget Agent)

Do not skip any section. Synthesize their independent responses into one unified, actionable travel plan.
""",
    tools=[
        AgentTool(agent=search_agent),
        heritage_tool,
        safety_tool,
        booking_tool,
        itinerary_tool,
        budget_tool
    ]
)
