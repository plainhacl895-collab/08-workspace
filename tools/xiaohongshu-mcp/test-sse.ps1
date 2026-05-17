$headers = @{
    'Accept' = 'text/event-stream'
}

# Connect to SSE endpoint
$uri = 'http://localhost:18060/mcp'

Write-Host "Connecting to SSE endpoint..."

# Use Invoke-WebRequest with streaming
$webRequest = [System.Net.WebRequest]::Create($uri)
$webRequest.Method = 'GET'
$webRequest.Headers.Add('Accept', 'text/event-stream')

try {
    $response = $webRequest.GetResponse()
    $stream = $response.GetResponseStream()
    $reader = New-Object System.IO.StreamReader($stream)
    
    Write-Host "SSE Connected! Reading events..."
    
    # Read first few events
    for ($i = 0; $i -lt 5; $i++) {
        $line = $reader.ReadLine()
        if ($line) {
            Write-Host "Event $i : $line"
        } else {
            break
        }
    }
    
    $reader.Close()
    $response.Close()
} catch {
    Write-Host "Error: $_"
}
