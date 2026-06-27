# PowerShell script to launch ADK API server and static UI
# ------------------------------------------------------------
# The .venv lives inside yatrasetu-agents/ (NOT the project root).
$agentsDir = "$PSScriptRoot\yatrasetu-agents"
$webUiDir  = "$PSScriptRoot\web_ui"

# 1. Start ADK API server in a new visible cmd window.
#    --allow_origins http://localhost:8080   → CORS for the UI
#    --auto_create_session                   → no need to pre-create sessions
Write-Host "Starting ADK API server at http://127.0.0.1:8000 ..."
Start-Process "cmd.exe" -ArgumentList "/k `"call .venv\Scripts\activate && adk api_server --allow_origins http://localhost:8080 --auto_create_session .`"" `
    -WorkingDirectory $agentsDir

# Give uvicorn a moment to bind before opening the browser.
Start-Sleep -Seconds 3

# 2. Start a simple Python static file server for the web UI.
Write-Host "Starting Web UI server at http://localhost:8080 ..."
Start-Process "cmd.exe" -ArgumentList "/k `"python -m http.server 8080`"" `
    -WorkingDirectory $webUiDir

Write-Host ""
Write-Host "--- URLs ---"
Write-Host "API docs  : http://localhost:8000/docs"
Write-Host "Web UI    : http://localhost:8080/"
Write-Host ""
Write-Host "Leave both cmd windows open while using the app."
Write-Host "Close them (or press Ctrl+C inside each) to stop the servers."
