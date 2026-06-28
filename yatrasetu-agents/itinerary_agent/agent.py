"""
Itinerary Planner Agent (Optimized)
-----------------------------------
Part of the YatraSetu AI Travel Companion system (Agents for Good track).

Responsibilities:
1. DAY-BY-DAY PLANNING & TRANSIT - scaffolds a complete, pre-calculated route
   and transit itinerary in one shot, avoiding multi-hop reasoning passes.
2. SELECTIVE SEARCH ENRICHMENT - searches the web only when specific factual details
   (e.g., ticket costs or opening times) are missing, using a strict fallback rule.
"""

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool

# ---------------------------------------------------------------------------
# DATA & CUSTOM TOOLS
# ---------------------------------------------------------------------------

TRAVEL_TIMES = {
    # Delhi <-> Agra
    ("delhi", "agra", "train"): "2 to 3 hours (via Gatimaan Express or Shatabdi Express).",
    ("delhi", "agra", "cab"): "3.5 to 4.5 hours depending on Yamuna Expressway traffic.",
    ("delhi", "agra", "bus"): "4.5 to 5.5 hours via Yamuna Expressway.",
    
    # Agra Fort <-> Taj Mahal
    ("agra fort", "taj mahal", "walk"): "30 to 40 minutes (approx. 2.5 km).",
    ("agra fort", "taj mahal", "cab"): "10 to 15 minutes.",
    ("agra fort", "taj mahal", "auto"): "10 to 15 minutes by auto-rickshaw.",
    
    # Taj Mahal <-> Mehtab Bagh
    ("taj mahal", "mehtab bagh", "cab"): "20 to 25 minutes (via Yamuna Bridge, approx. 8 km).",
    ("taj mahal", "mehtab bagh", "auto"): "25 to 30 minutes by auto-rickshaw.",
    ("taj mahal", "mehtab bagh", "walk"): "Not recommended (river crossing required; approx. 8 km walking detour).",
    
    # Agra Fort <-> Mehtab Bagh
    ("agra fort", "mehtab bagh", "cab"): "15 to 20 minutes.",
    ("agra fort", "mehtab bagh", "auto"): "20 to 25 minutes.",
    
    # Agra <-> Jaipur
    ("agra", "jaipur", "train"): "4 to 5 hours (via Marudhar Express or Shatabdi).",
    ("agra", "jaipur", "cab"): "4.5 to 5.5 hours via Bikaner-Agra Road.",
    ("agra", "jaipur", "bus"): "5 to 6 hours via RSRTC express bus.",

    # Delhi <-> Jaipur
    ("delhi", "jaipur", "train"): "4.5 to 5.5 hours (via Ajmer Shatabdi or Double Decker).",
    ("delhi", "jaipur", "cab"): "5 to 6 hours depending on NH48 traffic.",
    ("delhi", "jaipur", "bus"): "6 to 7 hours.",

    # Jaipur <-> Amber Fort
    ("jaipur", "amber fort", "cab"): "25 to 35 minutes depending on traffic.",
    ("jaipur", "amber fort", "auto"): "35 to 45 minutes by auto-rickshaw.",
    ("jaipur", "amber fort", "bus"): "45 to 55 minutes via local city bus.",
    
    # Varanasi Junction <-> Dashashwamedh Ghat
    ("varanasi junction", "dashashwamedh ghat", "auto"): "20 to 30 minutes by auto-rickshaw.",
    ("varanasi junction", "dashashwamedh ghat", "cab"): "25 to 35 minutes.",
    
    # Dashashwamedh Ghat <-> Kashi Vishwanath Temple
    ("dashashwamedh ghat", "kashi vishwanath temple", "walk"): "5 to 10 minutes (approx. 400m through narrow alleyways).",
    
    # Varanasi <-> Sarnath
    ("varanasi", "sarnath", "cab"): "30 to 45 minutes (approx. 10 km).",
    ("varanasi", "sarnath", "auto"): "40 to 50 minutes.",
    
    # Mumbai <-> Pune
    ("mumbai", "pune", "train"): "3 to 4 hours depending on the express train.",
    ("mumbai", "pune", "cab"): "3 to 3.5 hours via the Mumbai-Pune Expressway.",
    
    # Bangalore Airport <-> Indiranagar
    ("bangalore airport", "indiranagar", "cab"): "1 to 1.5 hours depending on peak hour traffic.",
    ("bangalore airport", "indiranagar", "bus"): "1.5 to 2 hours via Vayu Vajra KIA-7A/KIA-7 buses.",
    
    # Indiranagar <-> Bangalore Palace
    ("indiranagar", "bangalore palace", "cab"): "30 to 45 minutes depending on traffic.",
    ("indiranagar", "bangalore palace", "auto"): "35 to 50 minutes.",
}


def build_full_itinerary(destinations: list[str], days: int, pace: str, mode: str) -> str:
    """Use this to generate a complete day-by-day travel itinerary with estimated transit times between stops.

    Use this when the user has provided destinations, trip duration, pace, and preferred transit mode.

    Args:
        destinations: List of destinations or attractions to visit (e.g. ["Delhi", "Agra Fort", "Taj Mahal"]).
        days: Trip duration in number of days.
        pace: Trip pace, which must be 'relaxed', 'moderate', or 'packed'.
        mode: Preferred transport mode, which must be 'train', 'bus', 'cab', 'auto', or 'walk'.
    """
    if not destinations:
        return "No destinations provided. Cannot build an itinerary."

    if days <= 0:
        return "Invalid trip duration. Days must be at least 1."

    pace_clean = pace.strip().lower()
    if pace_clean not in ["relaxed", "moderate", "packed"]:
        pace_clean = "moderate"

    mode_clean = mode.strip().lower()
    if mode_clean not in ["train", "bus", "cab", "auto", "walk"]:
        mode_clean = "cab"

    # 1. Distribute stops across days based on pace
    if pace_clean == "relaxed":
        limit = 1
    elif pace_clean == "packed":
        limit = 4
    else:  # moderate
        limit = 2

    num_destinations = len(destinations)
    warning_msg = ""
    if num_destinations > days * limit:
        warning_msg = (
            f"*[Note: Visiting {num_destinations} locations in {days} day(s) might feel too rushed "
            f"for a '{pace_clean}' pace. Consider extending the trip or removing some stops.]*\n\n"
        )

    base_size = num_destinations // days
    remainder = num_destinations % days

    day_chunks = []
    idx = 0
    for d in range(1, days + 1):
        size = base_size + (1 if d <= remainder else 0)
        day_stops = destinations[idx : idx + size]
        idx += size
        day_chunks.append(day_stops)

    # Helper function to get travel time between two stops
    def lookup_time(origin: str, dest: str) -> str:
        orig_k = origin.strip().lower()
        dest_k = dest.strip().lower()
        
        # Check direct and reverse keys in dictionary
        key = (orig_k, dest_k, mode_clean)
        if key in TRAVEL_TIMES:
            return TRAVEL_TIMES[key]
            
        rev_key = (dest_k, orig_k, mode_clean)
        if rev_key in TRAVEL_TIMES:
            return TRAVEL_TIMES[rev_key]
            
        # Fallback to general lookup without mode if possible
        for (o, d, m), time_info in TRAVEL_TIMES.items():
            if (o == orig_k and d == dest_k) or (o == dest_k and d == orig_k):
                return f"{time_info} (Note: estimate is for mode '{m}')"
                
        return f"Please consult search_sub_agent to verify travel time by {mode_clean}."

    # 2. Build the formatted response
    lines = []
    lines.append(f"### Detailed Day-by-Day Itinerary ({pace_clean.capitalize()} Pace, {days} Days)")
    lines.append(f"**Preferred Transport Mode**: {mode_clean.capitalize()}\n")
    if warning_msg:
        lines.append(warning_msg)

    for d_idx, day_stops in enumerate(day_chunks):
        day_num = d_idx + 1
        lines.append(f"#### Day {day_num}")
        
        if not day_stops:
            lines.append("- Leisure time / local exploration\n")
            continue
            
        for s_idx, stop in enumerate(day_stops):
            lines.append(f"- **Stop {s_idx + 1}**: {stop}")
            
            # Transit to next stop on the same day
            if s_idx < len(day_stops) - 1:
                next_stop = day_stops[s_idx + 1]
                t_time = lookup_time(stop, next_stop)
                lines.append(f"  *Transit to next stop [{next_stop}]: {t_time}*")
                
        # Transit to first stop of the next day
        if day_num < days:
            next_day_stops = day_chunks[d_idx + 1]
            if day_stops and next_day_stops:
                last_stop_today = day_stops[-1]
                first_stop_tomorrow = next_day_stops[0]
                t_time = lookup_time(last_stop_today, first_stop_tomorrow)
                lines.append(f"\n*End of Day {day_num} / Start of Day {day_num+1} transit from [{last_stop_today}] to [{first_stop_tomorrow}]: {t_time}*\n")
            else:
                lines.append("")
        else:
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# SUB-AGENT: SEARCH SPECIALIST (SINGLE-QUERY ONLY)
# ---------------------------------------------------------------------------

search_sub_agent = Agent(
    name="search_sub_agent",
    model="gemini-2.5-flash",
    description=(
        "Searches the web for transit schedules, opening/closing hours, "
        "entry ticket prices, and route details in India."
    ),
    instruction="""
You will receive a single, specific question. Answer it in 2-3 sentences using google_search. Do not ask follow-up questions or do multi-step reasoning.
""",
    tools=[google_search],
)


# ---------------------------------------------------------------------------
# MAIN ITINERARY AGENT
# ---------------------------------------------------------------------------

root_agent = Agent(
    name="itinerary_agent",
    model="gemini-2.5-flash",
    description=(
        "Generates day-wise travel itineraries, calculates travel times between "
        "Indian cities or landmarks, and retrieves transport schedules and opening hours."
    ),
    instruction="""
You are the Itinerary Agent for YatraSetu, a travel companion app designed to help first-time and budget travelers explore India safely, comfortably, and economically.

Your primary role is to create practical, realistic day-wise travel plans based on the user's input.

Follow these execution guidelines:
1. Gather Inputs:
   Check if the user has provided:
   - Destination(s)
   - Number of days for the trip
   - Travel companions (e.g., solo, family, friends)
   - Pace preference (relaxed, moderate, packed)
   - Transport mode preference (train, bus, cab, auto, walk) (Default to cab if not specified)
   If any of these details are missing (except transport mode), ask the user politely to provide them before generating the final itinerary.

2. Generate Itinerary (Strict Tool Order):
   - Always call build_full_itinerary first. Only invoke the search sub-agent if a specific piece of information (opening hours, ticket prices, real-time transport changes) is NOT available from the tool. Never use search to confirm what a Python tool already returned.

3. Output Format:
   Your final response should combine the output of build_full_itinerary with any supplemental search results in this structure:
   - **Trip Overview**: Brief summary of destination, duration, pace, preferred transport, and travel companions.
   - **Day-by-Day Itinerary**: Insert the pre-calculated day-wise plan directly. Supplement each attraction with details like operating hours or entry fees (obtained via search_sub_agent ONLY if needed).
   - **Pro-Tips / Budget Advice**: Local tips (e.g. "Buy Taj Mahal tickets online to skip queues").

4. Tone:
   Maintain a friendly, practical, and helpful tone, like a local resident who is planning a trip for a dear friend. Keep travel times realistic and consider buffer times for India's traffic conditions.
""",
    tools=[
        AgentTool(agent=search_sub_agent),
        build_full_itinerary,
    ],
)
