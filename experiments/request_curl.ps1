# request_curl.ps1
# Sends a chat request to the local llama-server (OpenAI-compatible endpoint).
# Uses curl.exe explicitly to bypass PowerShell's `curl` alias (Invoke-WebRequest),
# which does not understand the `-d @file` syntax.
#
# Reads the request body from payload.json next to this script (edit the prompt there).
# Run from anywhere:  powershell -ExecutionPolicy Bypass -File experiments\request_curl.ps1

$Endpoint    = "http://localhost:8080/v1/chat/completions"
$PayloadPath = Join-Path $PSScriptRoot "payload.json"

curl.exe $Endpoint -H "Content-Type: application/json" -d "@$PayloadPath"
