$headers = @{
    'Accept' = 'application/json, text/event-stream'
    'Content-Type' = 'application/json'
}

# Test check_login_status
$body = '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"check_login_status","arguments":{}},"id":2}'

$response = Invoke-RestMethod -Uri 'http://localhost:18060/mcp' -Method Post -Headers $headers -Body $body
Write-Host "=== Login Status ==="
$response | ConvertTo-Json -Depth 10

# Test search_feeds
$body2 = '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"search_feeds","arguments":{"keyword":"上海房产","limit":5}},"id":3}'

$response2 = Invoke-RestMethod -Uri 'http://localhost:18060/mcp' -Method Post -Headers $headers -Body $body2
Write-Host "`n=== Search Results ==="
$response2 | ConvertTo-Json -Depth 10
