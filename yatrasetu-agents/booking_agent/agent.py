"""
Booking & Ticketing Safety Agent
----------------------------------
Part of the YatraSetu AI Travel Companion system (Agents for Good track).

Responsibilities:
1. OFFICIAL TICKET SOURCE  - Identify and link to the correct, verified
   official booking portal for a destination (ASI, IRCTC, state tourism, etc.).
   This agent NEVER processes payments or sells tickets itself; it only
   redirects to the legitimate source.

2. SCAM PRICE RADAR        - Flag destination-specific ticketing scams:
   "the official price is roughly ₹X; anything 3–4× that, or a UPI request
   to a personal number instead of an official gateway, is almost certainly
   a scam."  The scam data in BOOKING_SCAM_DATA is curated manually so the
   model never has to guess at prices.

3. CROWD / QUEUE FORECAST  - Predict the best day/time slot to visit to
   avoid crowds and long queues, based on known seasonal patterns. Always
   labelled clearly as an ESTIMATE, not live data.

File shape: follows the exact same 2-file pattern as heritage_agent and
safety_agent (__init__.py + agent.py, no .env - ADK finds the root-level
one automatically via walk-up lookup).

Architecture note — "agent-as-a-tool" pattern:
  Gemini's API forbids mixing a built-in tool (google_search) with custom
  function tools inside the SAME agent.  The fix: put google_search inside
  its own lightweight sub-agent (search_agent), then expose that sub-agent
  to the root_agent via AgentTool.  This is identical to the approach used
  by heritage_agent and safety_agent.
"""

from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool


# ---------------------------------------------------------------------------
# CUSTOM TOOL: BOOKING SCAM RADAR
# ---------------------------------------------------------------------------
# Why a curated dict instead of letting the model answer?
#   Pricing and scam patterns are safety-critical. If the model hallucinates
#   a wrong "official" price, it could actually harm the traveller (they pay
#   more thinking it's right, or dismiss a genuine overcharge as normal).
#   Curated data = deterministic, auditable, easy to extend.
#
# Structure per destination:
#   official_price   - approximate official ticket price in INR (adult, Indian)
#   foreign_price    - official price for foreign nationals (where different)
#   booking_url      - canonical official URL (may need search to confirm for
#                      lesser-known sites - that's what the search_agent is for)
#   scam_patterns    - human-readable list of known local scam tactics
#   crowd_forecast   - best/worst time advice based on known seasonal patterns

BOOKING_SCAM_DATA = {
    "taj mahal": {
        "official_price": "₹50 (Indian nationals) | ₹1,300 (foreign nationals) + ₹200 Taj Mahal entry fee",
        "booking_url": "https://asi.payumoney.com/  (ASI official portal) OR https://www.tajmahal.gov.in/",
        "scam_patterns": (
            "1. TOUT TICKETS: Touts near Agra Cantt station and Taj Ganj sell 'fast-track' or 'special view' tickets "
            "for ₹500–₹2,000. These do not exist. All tickets are priced the same at the ASI portal.\n"
            "2. FAKE GUIDES: Only licensed guides carry an official Ministry of Tourism photo ID card. "
            "Unlicensed guides near the East/West/South gates often demand ₹1,000–₹3,000 upfront.\n"
            "3. UPI TO PERSONAL NUMBERS: Legitimate ASI payments are via the official PayUMoney gateway only. "
            "Any UPI QR code to a personal phone number outside the official portal is a scam.\n"
            "4. SOUVENIR SHOPS LABELED 'GOVERNMENT EMPORIUM': Many shops near Taj Ganj falsely claim to be "
            "government-run to justify inflated marble inlay prices. Look for the genuine 'UP Handicrafts' logo."
        ),
        "crowd_forecast": (
            "BEST TIME: Tuesday–Thursday, first entry slot (6:00 AM) or the last hour before closing (around 6 PM). "
            "Fridays: Taj Mahal is CLOSED. "
            "WORST TIME: Saturday/Sunday mornings (10 AM–2 PM) and public holidays — peak domestic tourist rush. "
            "SEASON: October–March is peak tourist season overall; June–August (monsoon) is quieter but humid. "
            "NOTE: This is an estimate based on typical patterns, not live queue data."
        ),
    },
    "red fort": {
        "official_price": "₹35 (Indian nationals) | ₹500 (foreign nationals)",
        "booking_url": "https://asi.payumoney.com/  (ASI official portal)",
        "scam_patterns": (
            "1. UNOFFICIAL TICKET WINDOWS: Touts set up near Lahore Gate selling look-alike tickets. "
            "Only buy at the official ASI counters or the PayUMoney portal.\n"
            "2. LIGHT & SOUND SHOW SCAMS: Separate tickets for the evening show are sold at the fort; "
            "be aware touts sometimes sell photocopied tickets. Verify at the main booking counter.\n"
            "3. GUIDE OVERCHARGING: Licensed guide rates are regulated. The official rate is roughly "
            "₹450 for groups (up to 5 persons) per the Ministry of Tourism — negotiate against this benchmark."
        ),
        "crowd_forecast": (
            "BEST TIME: Weekday mornings (9–11 AM), especially Tuesday–Thursday. "
            "WORST TIME: Republic Day (26 Jan), Independence Day (15 Aug) — these are national events at Red Fort; "
            "expect very large crowds and security restrictions. "
            "NOTE: Estimate based on typical seasonal patterns, not live data."
        ),
    },
    "golden temple": {
        "official_price": "FREE — no entry ticket required. The langar (community kitchen) is also free.",
        "booking_url": (
            "No ticket booking needed. For accommodation in SGPC-run sarai (guesthouses), visit: "
            "https://www.goldentemple.gov.in/  or contact the SGPC office directly."
        ),
        "scam_patterns": (
            "1. ENTRY FEE SCAM: The Golden Temple has NO entry fee. Anyone asking for payment at the gate is a scam.\n"
            "2. ACCOMMODATION TOUTS: Touts outside the complex may offer 'SGPC-approved' rooms at inflated prices. "
            "Book only directly at the SGPC counter inside the complex.\n"
            "3. 'SPECIAL DARSHAN' OFFERS: There is no VIP or priority darshan purchase — all visitors queue equally."
        ),
        "crowd_forecast": (
            "BEST TIME: Early morning (4–6 AM for the opening ceremony, Palki Sahib procession) or late evening (9–10 PM). "
            "WORST TIME: Gurpurab festivals and Baisakhi (April 13–14) — expect hundreds of thousands of pilgrims. "
            "Weekend afternoons are consistently the busiest secular tourist windows. "
            "NOTE: Estimate based on typical patterns, not live data."
        ),
    },
    "hampi": {
        "official_price": "₹40 (Indian nationals) | ₹600 (foreign nationals) — covers the main monument complex",
        "booking_url": (
            "https://asi.payumoney.com/  (for ASI-managed monuments) | "
            "Karnataka tourism sites: https://www.karnatakatourism.org/"
        ),
        "scam_patterns": (
            "1. UNOFFICIAL ENTRY POINTS: Some guides offer 'secret' free entry routes to bypass ASI counters. "
            "These are illegal and can result in fines.\n"
            "2. CORACLE RIDE OVERPRICING: Standard coracle (round boat) crossing is around ₹30–₹60 per person. "
            "Demand for ₹300+ for a solo crossing is overcharging.\n"
            "3. GUIDE ID CHECKS: Always verify Ministry of Tourism photo ID before hiring a guide."
        ),
        "crowd_forecast": (
            "BEST TIME: November–February (cool season), weekdays, morning start at 8 AM. "
            "WORST TIME: Hampi Utsav festival (usually November) — beautiful but extremely crowded. "
            "April–June: very hot, fewer tourists but physically demanding. "
            "NOTE: Estimate based on typical patterns, not live data."
        ),
    },
    "varanasi ghats": {
        "official_price": (
            "Ghat walking is FREE. Boat rides have no fixed official rate — "
            "always negotiate BEFORE boarding. Typical fair range: ₹200–₹400/person for a shared sunrise ride."
        ),
        "booking_url": (
            "No centralized booking portal for ghat access. For UP Tourism certified boats and guides: "
            "https://www.uptourism.gov.in/"
        ),
        "scam_patterns": (
            "1. BOAT OVERCHARGING: Always agree on the exact price before stepping in. ₹1,000+ for a short ride "
            "is typical overcharging; ₹200–₹300/person for a sunrise shared ride is the normal range.\n"
            "2. 'SPECIAL GANGA AARTI' RESERVATIONS: The Ganga Aarti at Dashashwamedh Ghat is free to watch "
            "from the ghats. Anyone selling 'reserved seating' tickets is running a scam.\n"
            "3. PRASAD DONATION PRESSURE: Fake priests may thrust prasad into your hands then demand large cash "
            "'donations'. Politely decline; no donation at ghats is obligatory."
        ),
        "crowd_forecast": (
            "BEST TIME: Early morning (5–7 AM) for the sunrise boat ride — this is genuinely magical and less "
            "crowded than evenings. Mid-week (Tue–Thu) is quieter than weekends. "
            "WORST TIME: Diwali/Dev Deepawali (Kartik Purnima, usually November) — ghats are packed wall-to-wall. "
            "Maha Shivratri also draws very large crowds. "
            "NOTE: Estimate based on typical patterns, not live data."
        ),
    },
}


def get_booking_scam_info(place: str) -> dict:
    """Looks up official ticket price, booking URL, scam warnings, and crowd
    forecast for a specific tourist destination.

    Call this for EVERY destination the user mentions — even if they only asked
    about booking and not scams. Travelers should always know both the right
    place to buy and what to watch out for before they arrive.

    This tool returns CURATED, VERIFIED data for known destinations. For any
    destination not in the local database, the root agent should call the
    search_booking_info sub-agent tool to confirm the official booking URL via
    live web search, then advise the user to cross-check prices on the ASI or
    relevant state tourism website.

    Args:
        place: Name of the tourist site or city, e.g. "Taj Mahal", "Red Fort",
               "Golden Temple", "Hampi", or "Varanasi Ghats".

    Returns:
        A dict with a 'status' key.
        On success (status='success'):
            'official_price'  - approximate official entry fee in INR
            'booking_url'     - the canonical official booking portal URL
            'scam_patterns'   - numbered list of known local scam tactics
            'crowd_forecast'  - best/worst visit times (clearly marked as estimate)
        On miss (status='not_found'):
            'message' explains no curated data is on file yet.
    """
    key = place.strip().lower()

    # Fuzzy key match: accept "taj mahal agra" matching "taj mahal", etc.
    matched_key = None
    for k in BOOKING_SCAM_DATA:
        if k in key or key in k:
            matched_key = k
            break

    if matched_key:
        data = BOOKING_SCAM_DATA[matched_key]
        return {
            "status": "success",
            "place": place,
            "official_price": data["official_price"],
            "booking_url": data["booking_url"],
            "scam_patterns": data["scam_patterns"],
            "crowd_forecast": data["crowd_forecast"],
        }

    return {
        "status": "not_found",
        "place": place,
        "message": (
            "No curated booking/scam data on file yet for this destination. "
            "Use the search_booking_info tool to find the official booking source, "
            "and remind the user to cross-check any ticketing URL against the ASI "
            "portal (asi.payumoney.com) or the relevant state tourism website before paying."
        ),
    }


# ---------------------------------------------------------------------------
# SUB-AGENT: SEARCH SPECIALIST
# ---------------------------------------------------------------------------
# Gemini's API does not allow a built-in tool (google_search) and a custom
# function tool to coexist inside the SAME agent in a single request.
# Solution: isolate google_search in a dedicated lightweight sub-agent, then
# expose it to root_agent via AgentTool — exactly as heritage_agent and
# safety_agent do.
#
# Model choice: gemini-2.5-flash-lite (NOT gemini-2.5-flash)
#   This sub-agent only summarises search results — it doesn't need the full
#   reasoning power of Flash. Using Lite keeps the search calls on a separate
#   free-tier quota bucket, reducing rate-limit pressure on the root agent's
#   Flash quota. This matches the same pattern applied to heritage_agent and
#   safety_agent.

search_agent = Agent(
    name="search_booking_info",
    model="gemini-2.5-flash-lite",   # Lite: separate quota bucket, sufficient for search summarization
    description=(
        "Searches the web to find and verify the current official ticket booking "
        "portal URL for a specific Indian tourist destination. Also retrieves the "
        "current official ticket price when not already known."
    ),
    instruction="""
Use the google_search tool to find:
1. The official, government-authorised ticket booking URL for the destination
   the user mentioned (e.g. ASI portal, IRCTC Tourism, state tourism authority).
2. The current official entry ticket price (Indian nationals and foreign nationals
   separately, if available).

Return only verified, government-linked URLs. If the top search results are
travel blogs or third-party aggregators, keep searching until you find the
primary source. Clearly state the URL and the price you found, and name the
source (e.g. "per the ASI official website"). Never invent a URL or price.
""",
    tools=[google_search],
)


# ---------------------------------------------------------------------------
# THE AGENT
# ---------------------------------------------------------------------------
# `root_agent` is the ONE variable ADK looks for in this module.
# It is exposed as a tool to the future planner_agent (orchestrator) which
# will call it when a user's trip-planning request involves booking or
# ticketing questions.

root_agent = Agent(
    name="booking_agent",
    model="gemini-2.5-flash",   # Flash: full reasoning for the final response
    description=(
        "Helps travellers book tickets safely for Indian tourist destinations. "
        "Provides official booking portal links, flags destination-specific "
        "ticketing scams and realistic price benchmarks, and estimates the best "
        "time to visit to avoid crowds. Never processes payments itself."
    ),
    instruction="""
You are the Booking & Ticketing Safety Agent for YatraSetu, an AI travel
companion focused on protecting Indian travellers from exploitation and confusion.

YOUR THREE JOBS — address all three for every destination the user mentions:

────────────────────────────────────────────────────────────────────────────
1. OFFICIAL TICKET SOURCE
────────────────────────────────────────────────────────────────────────────
Always call get_booking_scam_info first. If it returns a booking_url, present
that to the user as the verified official source.

If get_booking_scam_info returns status='not_found', call the
search_booking_info tool to locate the current official portal via web search,
then present the URL you found and note that the user should cross-verify it
on the official ASI (asi.payumoney.com) or state tourism website.

CRITICAL: This agent NEVER sells tickets, processes payments, or generates
payment links. You only ever redirect the user to the verified official source.
Make this crystal clear in your response.

────────────────────────────────────────────────────────────────────────────
2. SCAM PRICE RADAR
────────────────────────────────────────────────────────────────────────────
Always present the official price range from get_booking_scam_info (or
search_booking_info if not in the local database) alongside the scam_patterns
returned by get_booking_scam_info. Frame it clearly:

  "The official price is [₹X]. If anyone quotes you 3–4× that amount,
   or asks for a UPI payment to a personal phone number instead of an
   official payment gateway, treat that as a scam."

If the destination has no curated scam data, give general-purpose advice:
  - Buy only at official counters or on the official portal
  - Never pay via UPI to a personal number for a heritage site
  - Always verify a guide's Ministry of Tourism photo ID

────────────────────────────────────────────────────────────────────────────
3. CROWD / QUEUE FORECAST
────────────────────────────────────────────────────────────────────────────
Present the crowd_forecast from get_booking_scam_info. Always label this
section with: "⏱ Crowd Estimate (based on typical patterns — not live data)".
If the destination is not in the local database, give a generic reasoned
estimate based on what you know about Indian public holiday and weekend
patterns, and label it as an estimate.

────────────────────────────────────────────────────────────────────────────
TONE AND FORMAT
────────────────────────────────────────────────────────────────────────────
- Structure your response with clear headings for each of the three sections.
- Be warm and protective in tone — you're helping someone who may be visiting
  for the first time and may not know what to watch out for.
- Never fabricate prices, URLs, or scam patterns. When in doubt, say so and
  direct the user to the official source for confirmation.
""",
    tools=[AgentTool(agent=search_agent), get_booking_scam_info],
)
