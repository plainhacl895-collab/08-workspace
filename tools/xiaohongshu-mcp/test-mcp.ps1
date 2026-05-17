$headers = @{
    'Accept' = 'application/json, text/event-stream'
    'Content-Type' = 'application/json'
}

$body = '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}'

$response = Invoke-RestMethod -Uri 'http://localhost:18060/mcp' -Method Post -Headers $headers -Body $body
$response | ConvertTo-Json -Depth 10
