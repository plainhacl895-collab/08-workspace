#!/usr/bin/env python3
import subprocess
import socket

# Read token
try:
    env = open('/home/huawei/.hermes/.env').read()
    for line in env.splitlines():
        if line.startswith('TELEGRAM_BOT_TOKEN'):
            token = line.split('=', 1)[1].split(':')[1]  # skip "875193:"
            break
except:
    token = None

# Test hosts file approach
with open('/etc/hosts') as f:
    content = f.read()
print('=== /etc/hosts has api.telegram.org?', 'api.telegram.org' in content)
print()

# Check default gateway
try:
    result = subprocess.run(['ip', 'route', 'show', 'default'], capture_output=True, text=True, timeout=5)
    print('=== Default route:', result.stdout.strip())
except:
    print('ip route failed')

# Check if there's a PROXY env
import os
for k in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
    v = os.environ.get(k, '')
    if v:
        print(f'{k}={v}')

# Try direct Telegram IP
targets = [
    ('95.161.76.101', 443),
]
for host, port in targets:
    try:
        s = socket.create_connection((host, port), timeout=5)
        s.close()
        print(f'✓ {host}:{port} reachable')
    except Exception as e:
        print(f'✗ {host}:{port} FAIL ({e})')
