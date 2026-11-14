$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot
Write-Host "Starting IntelSphere. Open http://127.0.0.1:8766 in your browser."
Write-Host "Keep this window open. Press Ctrl+C to stop the server."
python server.py

