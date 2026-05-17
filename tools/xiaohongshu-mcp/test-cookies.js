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
                console.log(`Headers:`, res.headers);
                console.log(`Body:`, data);
                resolve({ headers: res.headers, body: data });
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

    // Check for session cookie or token
    const setCookie = init.headers['set-cookie'];
    console.log('\nSet-Cookie:', setCookie);

    // Send initialized notification
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
            'Content-Length': Buffer.byteLength(notifBody)
        }
    };

    // Add cookie if present
    if (setCookie) {
        notifOptions.headers['Cookie'] = setCookie;
    }

    await new Promise((resolve, reject) => {
        const req = http.request(notifOptions, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                console.log(`\n=== notification ===`);
                console.log(`Status: ${res.statusCode}`);
                console.log(`Headers:`, res.headers);
                resolve();
            });
        });
        req.on('error', reject);
        req.write(notifBody);
        req.end();
    });

    // List tools with cookie
    const toolsBody = JSON.stringify({
        jsonrpc: '2.0',
        method: 'tools/list',
        params: {},
        id: 2
    });

    const toolsOptions = {
        hostname: 'localhost',
        port: 18060,
        path: '/mcp',
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json, text/event-stream',
            'Content-Length': Buffer.byteLength(toolsBody)
        }
    };

    if (setCookie) {
        toolsOptions.headers['Cookie'] = setCookie;
    }

    await new Promise((resolve, reject) => {
        const req = http.request(toolsOptions, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                console.log(`\n=== tools/list ===`);
                console.log(`Status: ${res.statusCode}`);
                console.log(data);
                resolve();
            });
        });
        req.on('error', reject);
        req.write(toolsBody);
        req.end();
    });
}

main().catch(console.error);
