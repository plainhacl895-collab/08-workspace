#!/usr/bin/env python3
import glob, os, json

base = os.path.expanduser('~/.hermes/sessions/')
files = sorted(glob.glob(base + 'session_2026051*.json'), key=os.path.getmtime, reverse=True)
print('All sessions today:')
for f in files[:10]:
    mtime = os.path.getmtime(f)
    import datetime
    dt = datetime.datetime.fromtimestamp(mtime).strftime('%H:%M:%S')
    print(dt, os.path.basename(f))
