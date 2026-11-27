"""List source-document text that does not appear anywhere in content.json.

usage: python3 -I coverage.py <site dir>
Template hints (提示：…) and form instructions are reported separately.
"""
import json
import os
import re
import sys

SITE = sys.argv[1]
src = json.load(open(os.path.join(SITE, 'tools', 'source_text.json'), encoding='utf-8'))
content = json.load(open(os.path.join(SITE, 'content.json'), encoding='utf-8'))


def norm(s):
    return re.sub(r'\s+', '', s)


parts = []


def walk(x):
    if isinstance(x, str):
        parts.append(x)
    elif isinstance(x, list):
        for y in x:
            walk(y)
    elif isinstance(x, dict):
        for y in x.values():
            walk(y)


walk(content)
SITE_TEXT = norm('\u0000'.join(parts))

missing = {}
for doc, blocks in src.items():
    seen = set()

    def chk(t, where):
        for line in t.split('\n'):
            n = norm(line)
            if not n or n.startswith('提示：') or n in seen:
                continue
            seen.add(n)
            if n not in SITE_TEXT:
                missing.setdefault(doc, []).append((where, line.strip()))

    for bi, b in enumerate(blocks):
        if isinstance(b, str):
            chk(b, f'P{bi}')
        else:
            for ri, row in enumerate(b):
                for ci, cell in enumerate(row):
                    for p in cell:
                        if isinstance(p, str):
                            chk(p, f'T{bi}.{ri}.{ci}')

total = 0
for doc, items in missing.items():
    print(f'== {doc}: {len(items)} lines not on the site')
    for w, l in items:
        print(f'  {w:10} {l[:90]}')
    total += len(items)
print('TOTAL', total)
