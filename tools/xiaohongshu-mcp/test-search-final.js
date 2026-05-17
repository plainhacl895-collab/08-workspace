const http = require('http');

function mcpCall(method, params = {}, id = 1, sessionId = null) {
    return new Promise((resolve, reject) => {
        const body = JSON.stringify({
            jsonrpc: '2.0',
            method: method,
            params: params,
            id: id
        });

        const options = {
            hostname: 'localhost',
            port: 18060,
            path: '/mcp',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/event-stream',
                'Content-Length': Buffer.byteLength(body)
            }
        };

        if (sessionId) {
            options.headers['Mcp-Session-Id'] = sessionId;
        }

        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                const newSessionId = res.headers['mcp-session-id'];
                resolve({ sessionId: newSessionId, body: data, status: res.statusCode });
            });
        });

        req.on('error', reject);
        req.write(body);
        req.end();
    });
}

async function main() {
    // Initialize
    const init = await mcpCall('initialize', {
        protocolVersion: '2025-06-18',
        capabilities: {},
        clientInfo: { name: 'test', version: '1.0.0' }
    }, 1);

    const sessionId = init.sessionId;

    // Send initialized notification (no id)
    const notifBody = JSON.stringify({
        jsonrpc: '2.0',
        method: 'notifications/initialized',
        params: {}
    });

    const notifOptions = {
        hostname: 'localhost',
        port: 18060,
        path: '/mcp',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream',
            'Content-Length': Buffer.byteLength(notifBody),
            'Mcp-Session-Id': sessionId
        }
    };

    await new Promise((resolve, reject) => {
        const req = http.request(notifOptions, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', resolve);
        });
        req.on('error', reject);
        req.write(notifBody);
        req.end();
    });

    // Search for 上海房产
    const searchResult = await mcpCall('tools/call', {
        name: 'search_feeds',
        arguments: { keyword: '上海房产' }
    }, 2, sessionId);

    console.log('\n=== Search Results ===');
    const parsed = JSON.parse(searchResult.body);
    if (parsed.error) {
        console.log('Error:', parsed.error.message);
    } else {
        const content = parsed.result.content[0].text;
        console.log(content);
    }
}

main().catch(console.error);
