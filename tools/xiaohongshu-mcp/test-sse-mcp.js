const http = require('http');

// MCP uses SSE transport - need to establish session first
// According to MCP spec, POST to /mcp initiates session, then use SSE for events

function sseRequest(method, params = {}, id = 1) {
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
                'Accept': 'text/event-stream',
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
        // Step 1: Initialize with SSE accept
        await sseRequest('initialize', {
            protocolVersion: '2025-06-18',
            capabilities: {},
            clientInfo: { name: 'test', version: '1.0.0' }
        }, 1);

        // Step 2: Send initialized notification (no id for notifications)
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
                'Accept': 'text/event-stream',
                'Content-Length': Buffer.byteLength(notifBody)
            }
        };

        await new Promise((resolve, reject) => {
            const req = http.request(notifOptions, (res) => {
                let data = '';
                res.on('data', chunk => data += chunk);
                res.on('end', () => {
                    console.log(`\n=== notification ===`);
                    console.log(`Status: ${res.statusCode}`);
                    console.log(data);
                    resolve();
                });
            });
            req.on('error', reject);
            req.write(notifBody);
            req.end();
        });

        // Step 3: List tools
        await sseRequest('tools/list', {}, 2);

        // Step 4: Check login
        await sseRequest('tools/call', { name: 'check_login_status', arguments: {} }, 3);

        // Step 5: Search
        await sseRequest('tools/call', { name: 'search_feeds', arguments: { keyword: '上海房产', limit: 3 } }, 4);

    } catch (err) {
        console.error('Error:', err.message);
    }
}

main();
