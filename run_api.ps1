# Start the orchestrator API with the project venv (Python 3.10–3.13; CrewAI does not run on 3.14+).
# First time:  py -3.13 -m venv .venv
#                .\.venv\Scripts\pip install -r requirements.txt
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root
$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Error "Missing .venv. Create it with: py -3.13 -m venv .venv`nThen: .\.venv\Scripts\pip install -r requirements.txt"
    exit 1
}
& $py -m uvicorn api_server:app --host 127.0.0.1 --port 8080
