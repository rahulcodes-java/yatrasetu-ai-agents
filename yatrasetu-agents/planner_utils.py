# planner_utils.py - Caching, deduplication, timing, and fault tolerance for YatraSetu Planner
import time
import json
import asyncio
import functools
from typing import Any, Optional, Callable, Dict, List

# ---------------------------------------------------------------------------
# SESSION-LEVEL CACHING (Conversation scoped)
# ---------------------------------------------------------------------------
# Format: session_id -> { destination_lower -> { month_lower -> response_dict } }
session_weather_cache: Dict[str, Dict[str, Dict[str, dict]]] = {}

# Format: session_id -> { destination_lower -> response_dict }
session_wiki_cache: Dict[str, Dict[str, dict]] = {}

def get_cached_weather(session_id: str, destination: str, month: Optional[str]) -> Optional[dict]:
    session_id = session_id or "default_session"
    dest = destination.strip().lower()
    m = (month or "").strip().lower()
    
    if session_id not in session_weather_cache:
        return None
    dest_cache = session_weather_cache[session_id].get(dest)
    if not dest_cache:
        return None
    return dest_cache.get(m)

def set_cached_weather(session_id: str, destination: str, month: Optional[str], data: dict):
    session_id = session_id or "default_session"
    dest = destination.strip().lower()
    m = (month or "").strip().lower()
    
    if session_id not in session_weather_cache:
        session_weather_cache[session_id] = {}
    if dest not in session_weather_cache[session_id]:
        session_weather_cache[session_id][dest] = {}
        
    session_weather_cache[session_id][dest][m] = data

def get_cached_wiki(session_id: str, destination: str) -> Optional[dict]:
    session_id = session_id or "default_session"
    dest = destination.strip().lower()
    
    if session_id not in session_wiki_cache:
        return None
    return session_wiki_cache[session_id].get(dest)

def set_cached_wiki(session_id: str, destination: str, data: dict):
    session_id = session_id or "default_session"
    dest = destination.strip().lower()
    
    if session_id not in session_wiki_cache:
        session_wiki_cache[session_id] = {}
    session_wiki_cache[session_id][dest] = data


# ---------------------------------------------------------------------------
# SINGLE-REQUEST STATE (Request scoped)
# ---------------------------------------------------------------------------
_current_session_id: Optional[str] = None
_current_run_tool_cache: Dict[Any, Any] = {}
_tool_executions: List[dict] = []
_cached_uses: List[str] = []

def set_current_session(session_id: str):
    global _current_session_id
    _current_session_id = session_id

def clear_run_cache():
    global _current_run_tool_cache, _tool_executions, _cached_uses
    _current_run_tool_cache = {}
    _tool_executions = []
    _cached_uses = []


# ---------------------------------------------------------------------------
# TOOL DECORATORS & WRAPPERS
# ---------------------------------------------------------------------------

def wrap_agent_tool(agent_tool: Any) -> Any:
    """Wraps an ADK AgentTool's run_async to provide single-request deduplication, timing, and fault tolerance."""
    orig_run_async = agent_tool.run_async
    
    async def wrapped_run_async(*args, **kwargs) -> Any:
        tool_name = agent_tool.name
        args_dict = kwargs.get("args", {})
        
        # Deduplication: check single-request tool cache
        key = (tool_name, json.dumps(args_dict, sort_keys=True))
        if key in _current_run_tool_cache:
            _cached_uses.append(tool_name)
            print(f"[DEDUPLICATE] Reusing request cached result for agent: {tool_name}")
            return _current_run_tool_cache[key]
            
        print(f"[INVOKE] Calling agent: {tool_name} with {args_dict}")
        start_time = time.time()
        try:
            result = await orig_run_async(*args, **kwargs)
            exec_time = time.time() - start_time
            _current_run_tool_cache[key] = result
            
            _tool_executions.append({
                "tool": tool_name,
                "args": args_dict,
                "execution_time": exec_time,
                "status": "success"
            })
            return result
        except Exception as e:
            exec_time = time.time() - start_time
            _tool_executions.append({
                "tool": tool_name,
                "args": args_dict,
                "execution_time": exec_time,
                "status": f"failed: {str(e)}"
            })
            # Fault Tolerance: Return friendly failure string instead of raising exception
            print(f"[RECOVERY] Agent {tool_name} failed. Isolating error and continuing...")
            return f"Error: [Service Failure] Could not retrieve data from {tool_name} (details: {str(e)}). Proceeding with remaining plan."
            
    agent_tool.run_async = wrapped_run_async
    return agent_tool


def wrap_function_tool(func: Callable) -> Callable:
    """Wraps a sync Python function tool (Weather/Wiki) to provide session caching, request deduplication, timing, and fault tolerance."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        tool_name = func.__name__
        
        # Extract arguments safely
        dest = kwargs.get("destination") or (args[0] if args else "")
        month = kwargs.get("month") or (args[1] if len(args) > 1 else None)
        
        clean_dest = dest.strip().lower() if isinstance(dest, str) else ""
        clean_month = month.strip().lower() if isinstance(month, str) else None
        
        session_id = _current_session_id or "default_session"
        
        # 1. Check Session-Level Caches
        if tool_name == "get_weather_data":
            cached = get_cached_weather(session_id, clean_dest, clean_month)
            if cached:
                _cached_uses.append("Weather Service")
                print(f"[SESSION CACHE HIT] Reusing weather data for {clean_dest} ({clean_month or 'general'})")
                return cached
        elif tool_name == "get_destination_summary":
            cached = get_cached_wiki(session_id, clean_dest)
            if cached:
                _cached_uses.append("Wikipedia Service")
                print(f"[SESSION CACHE HIT] Reusing wiki data for {clean_dest}")
                return cached
                
        # 2. Check Single-Request Cache (Deduplication)
        key = (tool_name, clean_dest, clean_month)
        if key in _current_run_tool_cache:
            print(f"[DEDUPLICATE] Reusing request cached result for function: {tool_name}")
            return _current_run_tool_cache[key]
            
        print(f"[INVOKE] Calling function: {tool_name} with {args} {kwargs}")
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            exec_time = time.time() - start_time
            
            # Store in request cache
            _current_run_tool_cache[key] = result
            
            # Store in session cache on success
            if isinstance(result, dict) and result.get("status") == "success":
                if tool_name == "get_weather_data":
                    set_cached_weather(session_id, clean_dest, clean_month, result)
                elif tool_name == "get_destination_summary":
                    set_cached_wiki(session_id, clean_dest, result)
                    
            _tool_executions.append({
                "tool": tool_name,
                "args": {"destination": dest, "month": month},
                "execution_time": exec_time,
                "status": "success"
            })
            return result
        except Exception as e:
            exec_time = time.time() - start_time
            _tool_executions.append({
                "tool": tool_name,
                "args": {"destination": dest, "month": month},
                "execution_time": exec_time,
                "status": f"failed: {str(e)}"
            })
            print(f"[RECOVERY] Function {tool_name} failed. Continuing...")
            return {
                "status": "error",
                "message": f"Error: [Service Failure] Could not retrieve data from {tool_name} (details: {str(e)})."
            }
            
    return wrapper


# ---------------------------------------------------------------------------
# REPORT GENERATION FOR AUDITING
# ---------------------------------------------------------------------------

def get_audit_report(user_id: str, destination: str) -> dict:
    """Classifies user intent and compiles list of invoked/skipped agents, cached usage, timings, and failures."""
    invoked_agents = []
    skipped_agents = []
    
    # Core registered specialist agents
    specialist_agents = {
        "heritage_guide_agent": "Heritage & Culture",
        "safety_and_readiness_agent": "Safety & Readiness",
        "booking_agent": "Official Bookings",
        "itinerary_agent": "Day-by-Day Itinerary",
        "budget_and_stay_agent": "Budget Breakdown & Accommodations"
    }
    
    invoked_names = set(item["tool"] for item in _tool_executions if item["tool"] in specialist_agents)
    
    for sa in specialist_agents:
        if sa in invoked_names:
            invoked_agents.append(sa)
        else:
            skipped_agents.append(sa)
            
    # Classify intent based on which agents were invoked
    if len(invoked_names) == len(specialist_agents):
        intent_class = "Comprehensive Trip Planning"
    elif len(invoked_names) == 0:
        # Check if external service tools were invoked
        called_tools = [item["tool"] for item in _tool_executions]
        if "get_weather_data" in called_tools:
            intent_class = "Weather Information Request"
        elif "get_destination_summary" in called_tools:
            intent_class = "Historical Context Inquiry"
        else:
            intent_class = "General Inquiry / Clarification"
    else:
        intent_class = f"Selective Planning ({', '.join(specialist_agents[sa] for sa in invoked_names)})"
        
    tool_times = {item["tool"]: f"{item['execution_time']:.3f}s" for item in _tool_executions}
    failures = [
        {"tool": item["tool"], "error": item["status"]}
        for item in _tool_executions if item["status"].startswith("failed")
    ]
    
    return {
        "user_intent_classification": intent_class,
        "invoked_specialist_agents": invoked_agents,
        "skipped_specialist_agents": skipped_agents,
        "cached_response_usage": list(set(_cached_uses)),
        "external_service_usage": [
            item["tool"] for item in _tool_executions 
            if item["tool"] in ["get_weather_data", "get_destination_summary"]
        ],
        "execution_time_per_tool": tool_times,
        "failures_and_recovery_actions": failures
    }
