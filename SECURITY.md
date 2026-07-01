# Security Hardening Guidelines & Documentation

This document describes the security policies, validation rules, sanitization controls, and best practices implemented for the YatraSetu AI Travel Companion.

---

## 1. Input Validation Rules (Injection Prevention)

Every user query submitted to YatraSetu agents is scanned before execution:
- **Null/Empty Check**: Empty queries are immediately rejected.
- **Length Boundaries**:
  - Full Query: Maximum **500 characters**.
  - Destination Parameter: Maximum **100 characters**.
- **SQL Injection Prevention**:
  - Detects and rejects queries containing case-insensitive SQL commands such as `DROP`, `DELETE`, `SELECT`, `INSERT`, `UPDATE`, `UNION`, or scripting patterns like `<script` and `alert(`.
- **Prompt Injection Prevention**:
  - Rejects queries attempting to manipulate the LLM state, bypass instructions, or read system prompts. Blocked phrases include:
    * `"ignore instructions"`
    * `"reveal your system prompt"`
    * `"ignore previous"`
    * `"system instructions"`
    * `"developer mode"`
    * `"system override"`
    * `"jailbreak"`
- **Bounds Checking**:
  - **Budget**: Scans and parses numeric values after keywords like `budget`, `price`, or symbols like `₹`. Rejects values outside the range **₹0 to ₹1 crore (10,000,000 INR)**.
  - **Days**: Scans and parses duration phrases (e.g. `5-day`, `5 days`). Rejects values outside the range **1 to 365 days**.

---

## 2. Output Sanitization (Redaction)

Responses returned by agents undergo automatic cleansing:
- **HTML/Script Tag Stripping**: Removes `<script>`, `<iframe>`, and `<object>` tags to prevent Cross-Site Scripting (XSS).
- **Credential Redaction**:
  - Automatically replaces Google/Gemini API keys (`AIzaSy...`) with `[REDACTED]`.
  - Replaces Bearer tokens with `Bearer [REDACTED]`.
  - Replaces assignments to password variables (e.g., `password = "..."`) with `password=[REDACTED]`.
- **Configuration Redaction**:
  - Redacts occurrences of file names such as `.env` or configurations (`config.yaml`, etc.) to `[REDACTED_CONFIG]`.

---

## 3. Response Guardrails (Blocking)

If an agent's response contains sensitive information, the response is blocked completely and replaced with a security warning. Responses are blocked if they contain:
- The keyword `GOOGLE_API_KEY` or `Bearer` tokens.
- Internal system/file paths (e.g., `C:\Users\...` or `/home/...`).
- Database connection strings or credentials (e.g., `mongodb://...`, `postgresql://...`).
- Agent implementation details or system instructions (e.g., `root_agent`, `AgentTool`, `heritage_agent`).

---

## 4. Audit Logging

All transactions are recorded in `logs/audit.log` for security audits. To protect user privacy, **no full request or response text is logged**.
- **Log Format**:
  `timestamp | user_id | agent | destination | response_length | status`
- **Logged Statuses**:
  - `success`: Request executed successfully.
  - `injection_attempts`: Query rejected due to input validation failures.
  - `blocked_responses`: Response blocked due to leakage of internal paths/credentials.
  - `sanitized_content`: Response successfully scrubbed of API keys or script tags.
  - `error: [Name]`: Execution failed due to a system error.

---

## 5. Security Best Practices for Developers

1. **Credentials Management**:
   - **Never commit your `.env` file**. Keep all sensitive credentials in the local `.env` and commit only `.env.example`.
2. **Instruction Isolation**:
   - Instruct agents to never repeat, summarize, or expose their system instructions or prompts.
3. **Response Verification**:
   - Ensure all credentials, internal configurations, and code files are redacted before being rendered or displayed in user interfaces.
4. **Log Incident Reporting**:
   - Monitor `logs/audit.log` periodically for any `injection_attempts` or `blocked_responses`. Report incidents of recurrent violations.
