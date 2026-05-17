const http = require('http');

/**
 * 小红书房产研究工具
 * 用法: node xhs-research.js <keyword> [limit]
 * 示例: node xhs-research.js 上海房产 10
 */

const keyword = process.argv[2] || '上海房产';
const limit = parseInt(process.argv[3]) || 10;

function mcpCall(method, params = {}, id = 1, sessionId = null) {
    return new Promise((resolve, reject) => {
        const body = JSON.stringify({ jsonrpc: '2.0', method, params, id });
        const options = {
            hostname: 'localhost', port: 18060, path: '/mcp', method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/event-stream',
                'Content-Length': Buffer.byteLength(body),
                ...(sessionId ? { 'Mcp-Session-Id': sessionId } : {})
            }
        };
        const req = http.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve({ sessionId: res.headers['mcp-session-id'], body: data, status: res.statusCode }));
        });
        req.on('error', reject);
        req.write(body);
        req.end();
    });
}

async function main() {
    // Initialize session
    const init = await mcpCall('initialize', {
        protocolVersion: '2025-06-18',
        capabilities: {},
        clientInfo: { name: 'xhs-research', version: '1.0.0' }
    }, 1);

    const sessionId = init.sessionId;

    // Send initialized notification
    const notifBody = JSON.stringify({ jsonrpc: '2.0', method: 'notifications/initialized', params: {} });
    await new Promise((resolve, reject) => {
        const req = http.request({
            hostname: 'localhost', port: 18060, path: '/mcp', method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/event-stream',
                'Content-Length': Buffer.byteLength(notifBody),
                'Mcp-Session-Id': sessionId
            }
        }, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', resolve);
        });
        req.on('error', reject);
        req.write(notifBody);
        req.end();
    });

    // Search
    const searchResult = await mcpCall('tools/call', {
        name: 'search_feeds',
        arguments: { keyword }
    }, 2, sessionId);

    const parsed = JSON.parse(searchResult.body);
    if (parsed.error) {
        console.error('搜索失败:', parsed.error.message);
        process.exit(1);
    }

    const feeds = JSON.parse(parsed.result.content[0].text).feeds;
    const notes = feeds.filter(f => f.modelType === 'note').slice(0, limit);

    console.log(`\n📊 小红书「${keyword}」搜索结果 (前${notes.length}条)\n`);
    console.log('='.repeat(60));

    notes.forEach((note, i) => {
        const card = note.noteCard;
        const user = card.user;
        const info = card.interactInfo;
        
        console.log(`\n${i + 1}. ${card.displayTitle}`);
        console.log(`   博主: ${user.nickname}`);
        console.log(`   类型: ${card.type === 'video' ? '视频' : '图文'}`);
        console.log(`   点赞: ${info.likedCount} | 收藏: ${info.collectedCount} | 评论: ${info.commentCount} | 分享: ${info.sharedCount}`);
        console.log(`   链接: https://www.xiaohongshu.com/explore/${note.id}`);
    });

    console.log('\n' + '='.repeat(60));
    console.log(`\n💡 提示: 搜索到 ${notes.length} 条笔记，总结果 ${feeds.length} 条`);
}

main().catch(err => {
    console.error('错误:', err.message);
    process.exit(1);
});
