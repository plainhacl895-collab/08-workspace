$headers = @{
    'Accept' = 'text/event-stream'
    'Content-Type' = 'application/json'
}

# First, establish SSE connection
Write-Host "Step 1: Establishing SSE connection..."
$sseResponse = Invoke-WebRequest -Uri 'http://localhost:18060/mcp' -Headers $headers -Method Get -TimeoutSec 30
Write-Host "SSE Status: $($sseResponse.StatusCode)"
Write-Host "SSE Content-Type: $($sseResponse.Headers.'Content-Type')"

# Extract session endpoint from SSE response
$sseContent = $sseResponse.Content
Write-Host "SSE Content (first 500 chars):"
Write-Host $sseContent.Substring(0, [Math]::Min(500, $sseContent.Length))

# Look for endpoint URL in SSE events
if ($sseContent -match 'endpoint[=:](\S+)') {
    Write-Host "Found endpoint: $($Matches[1])"
}
