# security.py - Security hardening for YatraSetu Agents
import os
import re
import uuid
import time
import logging
import json
from datetime import datetime
from typing import Any, Optional, AsyncGenerator

import planner_utils

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# ---------------------------------------------------------------------------
# AUDIT LOGGING
# ---------------------------------------------------------------------------
def log_audit(user_id: str, agent: str, destination: str, response_length: int, status: str, report: Optional[dict] = None):
    """Logs requests and security incidents to logs/audit.log."""
    timestamp = datetime.now().isoformat()
    user_id = user_id or "default_user"
    agent = agent or "unknown_agent"
    destination = destination or "N/A"
    
    log_line = f"{timestamp} | {user_id} | {agent} | {destination} | {response_length} | {status}"
    if report:
        log_line += f" | {json.dumps(report, ensure_ascii=False)}"
    log_line += "\n"
    
    with open("logs/audit.log", "a", encoding="utf-8") as f:
        f.write(log_line)

# ---------------------------------------------------------------------------
# SESSION TRACKING
# ---------------------------------------------------------------------------
# In-memory store: session_id -> { "created_at": float, "last_accessed": float, "request_count": int }
sessions = {}

def track_session(session_id: str) -> dict:
    """Tracks session lifecycles, enforcing a 1-hour session timeout."""
    now = time.time()
    session_id = session_id or str(uuid.uuid4())
    
    if session_id not in sessions:
        sessions[session_id] = {
            "created_at": now,
            "last_accessed": now,
            "request_count": 0
        }
        
    session_data = sessions[session_id]
    
    # 1-hour timeout check (3600 seconds)
    if now - session_data["last_accessed"] > 3600:
        session_data["created_at"] = now
        session_data["request_count"] = 0
        
    session_data["last_accessed"] = now
    session_data["request_count"] += 1
    return session_data

# ---------------------------------------------------------------------------
# INPUT VALIDATION
# ---------------------------------------------------------------------------
def validate_input(destination: Optional[str], query: str):
    """Validates user query string to prevent injection attacks and enforce bounds."""
    if not query or not query.strip():
        raise ValueError("Input query cannot be empty.")
        
    if len(query) > 500:
        raise ValueError("Input query exceeds maximum length of 500 characters.")
        
    if destination and len(destination) > 100:
        raise ValueError("Destination exceeds maximum length of 100 characters.")
        
    # SQL Injection / Malicious script patterns
    sql_patterns = [
        r'\bdrop\b', r'\bdelete\b', r'\bselect\b', r'\binsert\b', r'\bupdate\b',
        r'\bunion\b', r'<\s*script', r'alert\('
    ]
    for pattern in sql_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            raise ValueError("Potential SQL injection or malicious script pattern detected.")
            
    # Prompt Injection patterns
    injection_patterns = [
        r'ignore\s+(?:your\s+)?instructions',
        r'reveal\s+(?:your\s+)?system\s+prompt',
        r'ignore\s+previous',
        r'system\s+instructions',
        r'system\s+prompt',
        r'developer\s+mode',
        r'system\s+override',
        r'jailbreak'
    ]
    for pattern in injection_patterns:
        if re.search(pattern, query, re.IGNORECASE):
            raise ValueError("Potential prompt injection attempt detected.")
            
    # Validate budget (0 to ₹1 crore = 10,000,000 INR)
    budget_matches = re.findall(r'(?:budget|cost|price|rupees|rs\.?|inr|₹)\s*of?\s*(?:rs\.?|inr|₹)?\s*([\d,]+)', query, re.IGNORECASE)
    for b_str in budget_matches:
        try:
            val = int(b_str.replace(',', ''))
            if not (0 <= val <= 10000000):
                raise ValueError("Budget must be between ₹0 and ₹1 crore.")
        except ValueError:
            pass
            
    # Validate days (1 to 365)
    days_matches = re.findall(r'\b(\d+)\s*days?\b|\b(\d+)-day\b', query, re.IGNORECASE)
    for d_tuple in days_matches:
        d_str = d_tuple[0] or d_tuple[1]
        try:
            val = int(d_str)
            if not (1 <= val <= 365):
                raise ValueError("Trip duration must be between 1 and 365 days.")
        except ValueError:
            pass

# ---------------------------------------------------------------------------
# OUTPUT SANITIZATION
# ---------------------------------------------------------------------------
def sanitize_output(text: str) -> str:
    """Removes sensitive details or scripting elements from text."""
    if not isinstance(text, str):
        return text
        
    # Strip script, iframe, and object tags
    text = re.sub(r'<\s*script[^>]*>.*?<\s*/\s*script\s*>', '', text, flags=re.IGNORECASE|re.DOTALL)
    text = re.sub(r'<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>', '', text, flags=re.IGNORECASE|re.DOTALL)
    text = re.sub(r'<\s*object[^>]*>.*?<\s*/\s*object\s*>', '', text, flags=re.IGNORECASE|re.DOTALL)
    text = re.sub(r'<\s*/?\s*(script|iframe|object)[^>]*>', '', text, flags=re.IGNORECASE)
    
    # Redact actual Google/Gemini API key
    text = re.sub(r'AIzaSy[A-Za-z0-9_-]{35}', '[REDACTED]', text)
    
    # Redact Bearer tokens
    text = re.sub(r'Bearer\s+[A-Za-z0-9\-._~+/]+=*', 'Bearer [REDACTED]', text)
    
    # Redact assignment-style credentials
    text = re.sub(r'\b(password|passwd|secret|key|token)\s*=\s*[\'"][^\'"]+[\'"]', r'\1=[REDACTED]', text, flags=re.IGNORECASE)
    
    # Redact database connection URLs
    text = re.sub(r'\b(mongodb\+srv|mongodb|postgresql|mysql|sqlite):\/\/[^\s\n]+', r'\1://[REDACTED]', text, flags=re.IGNORECASE)
    
    # Strip env/config references
    text = re.sub(r'\b\w+\.env\b|\b\.env\b|\bconfig\.(yaml|yml|json|ini)\b', '[REDACTED_CONFIG]', text, flags=re.IGNORECASE)
    
    return text

# ---------------------------------------------------------------------------
# RESPONSE GUARDRAILS (BLOCKING)
# ---------------------------------------------------------------------------
def guard_agent_response(text: str):
    """Throws ValueError if response violates sensitive information guardrails."""
    if not isinstance(text, str):
        return
        
    # Block literal credentials/keys
    if "GOOGLE_API_KEY" in text:
        raise ValueError("Response contains blocked keywords (GOOGLE_API_KEY).")
        
    # Block internal system paths
    if re.search(r'\b[A-Za-z]:\\(?:[A-Za-z0-9_.-]+\\)+[A-Za-z0-9_.-]+', text) or \
       re.search(r'\b/(?:home|usr|var|etc|opt|tmp|bin|Users)(?:/[A-Za-z0-9_.-]+)+', text):
        raise ValueError("Response contains internal system paths.")
        
    # Block database connection URLs
    if re.search(r'\b(mongodb\+srv|mongodb|postgresql|mysql|sqlite):\/\/', text, re.IGNORECASE):
        raise ValueError("Response contains database connection strings.")
        
    # Block agent implementation details
    implementation_keywords = [
        r'\broot_agent\b', r'\bAgentTool\b', r'\bheritage_agent\b', r'\bbooking_agent\b',
        r'\bsafety_agent\b', r'\bitinerary_agent\b', r'\bbudget_and_stay_agent\b',
        r'\bgoogle-adk\b', r'\badk run\b', r'system prompt', r'system instruction',
        r'\b\.env\b'
    ]
    for pattern in implementation_keywords:
        if re.search(pattern, text, re.IGNORECASE):
            raise ValueError("Response reveals internal agent implementation details or configuration.")

# ---------------------------------------------------------------------------
# MONKEY PATCH RUNNER
# ---------------------------------------------------------------------------
from google.adk.runners import Runner
from google.adk.events.event import Event

# Save original run_async
original_run_async = Runner.run_async

async def patched_run_async(
    self,
    *,
    user_id: str,
    session_id: str,
    invocation_id: Optional[str] = None,
    new_message: Optional[Any] = None,
    state_delta: Optional[dict[str, Any]] = None,
    run_config: Optional[Any] = None,
    yield_user_message: bool = False,
) -> AsyncGenerator[Event, None]:
    """Patched run_async that performs input validation, output sanitization, and guardrails."""
    # 1. Extract and Validate Input Query
    query_text = ""
    if new_message and hasattr(new_message, "parts"):
        parts = []
        for p in new_message.parts:
            if hasattr(p, "text") and p.text:
                parts.append(p.text)
        query_text = " ".join(parts)
        
    # Track session count & access
    track_session(session_id)
    
    # Try to resolve destination for audit logging
    destination = "N/A"
    dest_match = re.search(r'\b(jaipur|goa|delhi|varanasi|rajasthan)\b', query_text, re.IGNORECASE)
    if dest_match:
        destination = dest_match.group(1).capitalize()
    else:
        dest_match_generic = re.search(r'\b(?:to|visit|trip to|go to)\s+([A-Za-z\s]{1,100}?)(?:\s+in|\s+for|\s+with|\s+during|\.|$)', query_text, re.IGNORECASE)
        if dest_match_generic:
            destination = dest_match_generic.group(1).strip()
            
    # Initialize cache and session tracking in planner_utils
    planner_utils.set_current_session(session_id)
    planner_utils.clear_run_cache()

    # Validate input
    try:
        validate_input(destination if destination != "N/A" else None, query_text)
    except ValueError as e:
        # Rejected query: log as injection_attempts and yield security error event
        log_audit(user_id, self.agent.name, destination, 0, "injection_attempts")
        yield Event(output=f"Security Error: {str(e)}")
        return
        
    # 2. Run original and stream events
    status = "success"
    full_output_length = 0
    
    try:
        async for event in original_run_async(
            self,
            user_id=user_id,
            session_id=session_id,
            invocation_id=invocation_id,
            new_message=new_message,
            state_delta=state_delta,
            run_config=run_config,
            yield_user_message=yield_user_message,
        ):
            if event and hasattr(event, "output") and event.output:
                if isinstance(event.output, str):
                    text = event.output
                    
                    # Apply Response Guardrails (raises ValueError if blocked)
                    try:
                        guard_agent_response(text)
                        
                        # Apply Sanitization
                        sanitized_text = sanitize_output(text)
                        if sanitized_text != text:
                            status = "sanitized_content"
                            
                        event.output = sanitized_text
                        full_output_length += len(sanitized_text)
                        yield event
                    except ValueError as block_err:
                        status = "blocked_responses"
                        # Replace content with blocked warning
                        event.output = f"Security Error: Response blocked due to guardrail violation. ({str(block_err)})"
                        yield event
                        break
                else:
                    yield event
            else:
                yield event
    except Exception as run_err:
        status = f"error: {type(run_err).__name__}"
        raise run_err
    finally:
        # Fetch audit report from planner_utils and write detailed log entry
        report = planner_utils.get_audit_report(user_id, destination)
        log_audit(user_id, self.agent.name, destination, full_output_length, status, report)

# Apply monkey patch
Runner.run_async = patched_run_async
print("Applied Security Hardening monkey-patch to google.adk.runners.Runner.run_async")
