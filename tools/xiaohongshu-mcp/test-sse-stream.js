const http = require('http');

// MCP SSE Transport - maintain single connection
async function main() {
    return new Promise((resolve, reject) => {
        let messageCount = 0;
        const maxMessages = 20;

        // Connect to SSE endpoint
        const options = {
            hostname: 'localhost',
            port: 18060,
            path: '/mcp',
            method: 'GET',
            headers: {
                'Accept': 'text/event-stream'
            }
        };

        const req = http.request(options, (res) => {
            console.log(`SSE Status: ${res.statusCode}`);
            console.log(`SSE Content-Type: ${res.headers['content-type']}`);

            let buffer = '';
            
            res.on('data', (chunk) => {
                buffer += chunk.toString();
                
                // Parse SSE events
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.substring(6);
                        try {
                            const msg = JSON.parse(data);
                            messageCount++;
                            console.log(`\n=== SSE Message ${messageCount} ===`);
                            console.log(JSON.stringify(msg, null, 2));
                            
                            if (messageCount >= maxMessages) {
                                res.destroy();
                                resolve();
                            }
                        } catch (e) {
                            console.log(`Raw: ${data.substring(0, 200)}`);
                        }
                    }
                }
            });

            res.on('end', () => {
                console.log('SSE connection ended');
                resolve();
            });

            res.on('error', reject);
        });

        req.on('error', (err) => {
            console.error('Request error:', err.message);
            reject(err);
        });

        req.end();

        // After 5 seconds, try to send a POST request
        setTimeout(async () => {
            console.log('\n--- Sending POST request ---');
            
            const body = JSON.stringify({
                jsonrpc: '2.0',
                method: 'tools/list',
                params: {},
                id: 1
            });

            const postOptions = {
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

            const postReq = http.request(postOptions, (postRes) => {
                let postData = '';
                postRes.on('data', chunk => postData += chunk);
                postRes.on('end', () => {
                    console.log(`POST Status: ${postRes.statusCode}`);
                    console.log(postData);
                });
            });

            postReq.on('error', console.error);
            postReq.write(body);
            postReq.end();
        }, 5000);

        // Timeout after 15 seconds
        setTimeout(() => {
            req.destroy();
            resolve();
        }, 15000);
    });
}

main().catch(console.error);
