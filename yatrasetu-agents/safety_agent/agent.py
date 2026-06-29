
"""
Safety & Travel Readiness Agent
--------------------------------
Part of the YatraSetu AI Travel Companion system (Agents for Good track).

Responsibilities:
1. SCAMS & EMERGENCIES - Warn about destination-specific scams and provide local emergency contacts.
2. HEALTH ADVISORY - Provide health recommendations, food/water safety advice, and clinic/pharmacy info.
3. WEATHER & PACKING - Offer packing advice (what to wear/carry) adjusted for weather/season.
4. ACCESSIBILITY - Detail accessibility guidelines for elderly, children, and mobility needs.

Like heritage_agent, this agent implements the "agent-as-a-tool" pattern because Gemini's API
does not allow combining a built-in tool (like google_search) with custom function tools directly
in the same agent definition.
"""

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool

# ---------------------------------------------------------------------------
# CUSTOM TOOL: VERIFIED SCAMS & PACKING DICTIONARY
# ---------------------------------------------------------------------------
# ADK turns python functions into model-callable tools based on the function name,
# argument type hints, and the docstring description.
# Curated data prevents model hallucinations for sensitive safety-critical info.

SCAMS_AND_PACKING = {
    "varanasi": {
        "scams": (
            "1. Boat Ride Overcharging: Always agree on the price (e.g., INR 200-300 per person or INR 1500 for a private boat) BEFORE boarding.\n"
            "2. Cremation Ghat Photography & 'Wood Donation' Scam: At Manikarnika Ghat, aggressive touts may demand money for 'funeral wood charity' or threaten you for taking photos. Avoid talking to them; no donation is official.\n"
            "3. Fake Sadhus: People dressed as holy men may offer blessings or put tikka on your forehead and demand large sums. Politely decline."
        ),
        "emergency_contacts": "Varanasi Tourist Police: +91-542-2508178, Police Helpline: 112, Ambulance: 102",
        "packing_advice": (
            "1. Modest Clothing: Shoulders and knees must be covered. Pack loose-fitting cotton shirts and long pants/skirts.\n"
            "2. Slip-on Shoes: You will constantly be removing shoes at temples; slip-ons are highly recommended.\n"
            "3. Mosquito Repellent: Crucial for ghat areas, especially at dawn and dusk.\n"
            "4. Hand Sanitizer: Essential before eating local street food."
        )
    },
    "hampi": {
        "scams": (
            "1. Coracle Ride Pricing: Coracle rides across the river should have fixed pricing. Verify with locals or official signage before paying.\n"
            "2. Fake Tour Guides: Ensure any guide you hire shows an official Ministry of Tourism ID card.\n"
            "3. Overpriced Tuk-Tuks: Always negotiate the fare before starting, or ask your hotel for standard rates."
        ),
        "emergency_contacts": "Hampi Police Station: +91-8394-241233, Police Helpline: 112, Ambulance: 102",
        "packing_advice": (
            "1. Sun Protection: Hampi is very hot and dry with little shade. Pack a wide-brimmed hat, sunglasses, and high-SPF sunscreen.\n"
            "2. Sturdy Walking Shoes: The terrain is rocky and involves significant walking/climbing over ruins.\n"
            "3. Hydration: Carry a reusable water bottle; dehydration is a common issue here.\n"
            "4. Light Colors: Wear light-colored, breathable clothing to reflect heat."
        )
    },
    "golden temple": {
        "scams": (
            "1. Unofficial Tour Guides: Avoid people offering private fast-track entry or tours for money. Entry is free and queues are managed systematically.\n"
            "2. Overpriced Souvenirs: Bargain politely at the markets surrounding the temple complex."
        ),
        "emergency_contacts": "Amritsar Police: +91-183-2225054, Police Helpline: 112, Ambulance: 102",
        "packing_advice": (
            "1. Head Covering: Both men and women must cover their heads. Pack a clean scarf/bandana (or purchase one cheaply outside).\n"
            "2. Clean Socks: Shoes must be deposited at the free counter. Walking barefoot on hot marble can be tough in summer, so carry clean socks.\n"
            "3. Modest Dress: Dress conservatively, covering shoulders and knees."
        )
    }
}


def get_safety_and_packing_info(place: str) -> dict:
    """Looks up scam patterns, emergency contact information, and packing advice for a specific tourist destination.

    Use this whenever a user asks about safety, scams, emergency numbers, packing recommendations,
    or general travel preparation for a destination. This ensures consistent, verified advice is
    delivered rather than AI-generated placeholder information.

    Args:
        place: Name of the tourist site or city, e.g. "Varanasi", "Hampi", or "Golden Temple".

    Returns:
        A dict with a 'status' key. If safety/packing info exists, it's under the keys:
        'scams', 'emergency_contacts', and 'packing_advice'.
        If not found, 'message' explains that no verified note is on file yet.
    """
    key = place.strip().lower()
    
    # Check if there is an exact key match or if the key is inside any of our database entries
    matched_key = None
    for k in SCAMS_AND_PACKING.keys():
        if k in key or key in k:
            matched_key = k
            break
            
    if matched_key:
        return {
            "status": "success",
            "place": place,
            "scams": SCAMS_AND_PACKING[matched_key]["scams"],
            "emergency_contacts": SCAMS_AND_PACKING[matched_key]["emergency_contacts"],
            "packing_advice": SCAMS_AND_PACKING[matched_key]["packing_advice"]
        }
        
    return {
        "status": "not_found",
        "place": place,
        "message": "No verified scam patterns or destination-specific packing list on file yet for this place - "
                   "this database will grow as more destinations are added."
    }


# ---------------------------------------------------------------------------
# SUB-AGENT: SEARCH SPECIALIST
# ---------------------------------------------------------------------------
# Gemini's API does not allow combining built-in tools (google_search) with custom
# function tools in the same agent. We bypass this by wrapping the google_search in a
# separate search sub-agent and exposing it as an AgentTool.

search_agent = Agent(
    name="search_safety_info",
    model="gemini-2.5-flash-lite",
    description=(
        "Searches the web for up-to-date safety alerts, current weather, seasonal conditions, "
        "health risks (like water safety or common illnesses), and accessibility details for a destination."
    ),
    instruction="""
Use the google_search tool to find up-to-date information on:
1. Current weather and seasonal conditions at the destination (so the traveler knows how to dress/prepare).
2. Recent safety alerts, health risks (e.g. food/water safety, local outbreaks), and reliable local healthcare options.
3. Accessibility features or challenges for elderly travelers, children, or individuals with mobility issues at the main sights.

Summarize these findings clearly and concisely in a few short paragraphs. Always cite your search results and never invent any facts or alerts.
""",
    tools=[google_search],
)


# ---------------------------------------------------------------------------
# THE AGENT
# ---------------------------------------------------------------------------
# `root_agent` is the main agent definition required by the ADK.

root_agent = Agent(
    name="safety_and_readiness_agent",
    model="gemini-2.5-flash",
    description=(
        "Provides destination-specific safety advice, scam warnings, emergency contacts, "
        "health advisories, packing recommendations (adjusted for weather), and accessibility notes."
    ),
    instruction="""
You are the Safety & Travel Readiness Agent for YatraSetu, an Indian travel companion system.
Your goal is to keep travelers safe, healthy, prepared, and informed about local conditions.

When a user asks about a destination (e.g., "I'm visiting Varanasi in July, what should I know?"), you must address the following four pillars:

1. SCAMS & EMERGENCIES: Call the get_safety_and_packing_info tool to retrieve verified scam patterns and emergency contacts. Always present these clearly. If the destination is not in the local database, advise the user to remain vigilant, use official services, and check local helpline numbers.
2. HEALTH RISKS: Call the search_safety_info tool to check for region-specific health risks (e.g., food/water safety advice, seasonal illnesses) and nearest medical guidance.
3. WEATHER & PACKING: Call the search_safety_info tool to check the weather/season for the travel month (if provided) or current conditions, and combine this with the curated packing advice from get_safety_and_packing_info. Guide the user on what to wear and carry.
4. ACCESSIBILITY: Call the search_safety_info tool or analyze search results to provide notes on accessibility for elderly travelers, kids, or mobility-impaired individuals at the destination.

Structure your final response clearly, with separate sections for each of the four pillars (Scams & Emergency Contacts, Health & Medical Advisory, Weather & Packing Guide, Accessibility Notes). Make the tone warm, helpful, and reassuring, but direct and clear about safety. Never fabricate facts, safety alerts, or emergency contacts.
""",
    tools=[AgentTool(agent=search_agent), get_safety_and_packing_info],
)
