const http = require('http');

function mcpCall(method, params = {}, id = 1) {
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

        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                console.log(`\n=== ${method} (id=${id}) ===`);
                console.log(`Status: ${res.statusCode}`);
                console.log(`Content-Type: ${res.headers['content-type']}`);
                console.log(data);
                resolve(data);
            });
        });

        req.on('error', reject);
        req.write(body);
        req.end();
    });
}

async function main() {
    try {
        // Initialize
        await mcpCall('initialize', {
            protocolVersion: '2025-06-18',
            capabilities: {},
            clientInfo: { name: 'test', version: '1.0.0' }
        }, 1);

        // Send initialized notification
        await mcpCall('notifications/initialized', {}, 0);

        // List tools
        await mcpCall('tools/list', {}, 2);

        // Check login status
        await mcpCall('tools/call', { name: 'check_login_status', arguments: {} }, 3);

        // Search
        await mcpCall('tools/call', { name: 'search_feeds', arguments: { keyword: '上海房产', limit: 5 } }, 4);

    } catch (err) {
        console.error('Error:', err.message);
    }
}

main();
