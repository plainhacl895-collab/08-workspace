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
                console.log(`\n=== ${method} (id=${id}) ===`);
                console.log(`Status: ${res.statusCode}`);
                const newSessionId = res.headers['mcp-session-id'];
                if (newSessionId) {
                    console.log(`Session ID: ${newSessionId}`);
                }
                console.log(`Body:`, data);
                resolve({ sessionId: newSessionId, body: data });
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
    console.log('\nUsing session:', sessionId);

    // Send initialized notification
    await mcpCall('notifications/initialized', {}, 0, sessionId);

    // List tools
    await mcpCall('tools/list', {}, 2, sessionId);

    // Check login
    await mcpCall('tools/call', { name: 'check_login_status', arguments: {} }, 3, sessionId);

    // Search
    await mcpCall('tools/call', { name: 'search_feeds', arguments: { keyword: '上海房产', limit: 3 } }, 4, sessionId);
}

main().catch(console.error);
