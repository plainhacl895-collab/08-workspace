$headers = @{
    'Accept' = 'application/json, text/event-stream'
    'Content-Type' = 'application/json'
}

# Step 1: Initialize
$initBody = '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}},"id":1}'
$initResponse = Invoke-RestMethod -Uri 'http://localhost:18060/mcp' -Method Post -Headers $headers -Body $initBody
Write-Host "=== Initialize ==="
$initResponse | ConvertTo-Json -Depth 5

# Step 2: Send initialized notification (no id)
$notifBody = '{"jsonrpc":"2.0","method":"notifications/initialized","params":{}}'
try {
    Invoke-RestMethod -Uri 'http://localhost:18060/mcp' -Method Post -Headers $headers -Body $notifBody
    Write-Host "=== Initialized Notification Sent ==="
} catch {
    Write-Host "Notification response: $_"
}

# Step 3: List tools
$listBody = '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":2}'
$listResponse = Invoke-RestMethod -Uri 'http://localhost:18060/mcp' -Method Post -Headers $headers -Body $listBody
Write-Host "`n=== Tools List ==="
$listResponse | ConvertTo-Json -Depth 10

# Step 4: Check login status
$loginBody = '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"check_login_status","arguments":{}},"id":3}'
$loginResponse = Invoke-RestMethod -Uri 'http://localhost:18060/mcp' -Method Post -Headers $headers -Body $loginBody
Write-Host "`n=== Login Status ==="
$loginResponse | ConvertTo-Json -Depth 10

# Step 5: Search for 上海房产
$searchBody = '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"search_feeds","arguments":{"keyword":"上海房产","limit":5}},"id":4}'
$searchResponse = Invoke-RestMethod -Uri 'http://localhost:18060/mcp' -Method Post -Headers $headers -Body $searchBody
Write-Host "`n=== Search Results ==="
$searchResponse | ConvertTo-Json -Depth 10
