"""Check that every teaching-text string in content.json appears word for word
in the source documents (tools/source_text.json).

Hand-written navigation labels live only in the keys listed in LABEL_KEYS and
are reported separately so they can be reviewed.

usage: python3 -I verify_verbatim.py <site dir>
"""
import json
import os
import re
import sys

SITE = sys.argv[1]
src = json.load(open(os.path.join(SITE, 'tools', 'source_text.json'), encoding='utf-8'))
content = json.load(open(os.path.join(SITE, 'content.json'), encoding='utf-8'))

LABEL_KEYS = {'title', 'nav', 'label', 'head', 'note', 'source', 'src', 'link', 'target',
              'id', 'mode', 't', 'style', 'missing', 'attrib', 'web', 'sim', 'heading', 'kind', 'cap', 'ref', 'lesson', 'time', 'links', 'imgs', 'docfiles', 'code', 'name', 'file', 'worksheet', 'sources', 'subtitle'}


def norm(s):
    return re.sub(r'\s+', '', s)


corpus_parts = []


def walk_src(x):
    if isinstance(x, str):
        corpus_parts.append(x)
    elif isinstance(x, list):
        for y in x:
            walk_src(y)
    elif isinstance(x, dict):
        for y in x.values():
            walk_src(y)


walk_src(src)
CORPUS = norm('\u0000'.join(corpus_parts))
LINES = {norm(p) for p in corpus_parts}

bad, labels, checked = [], set(), 0


def check(s, where):
    global checked
    if not s.strip():
        return
    checked += 1
    for line in s.split('\n'):
        n = norm(line)
        if n and n not in CORPUS:
            bad.append((where, line))


def walk(x, where, key=None):
    if isinstance(x, str):
        if key in LABEL_KEYS:
            labels.add(x)
        else:
            check(x, where)
    elif isinstance(x, list):
        for y in x:
            walk(y, where, key)
    elif isinstance(x, dict):
        for k, v in x.items():
            walk(v, where, k)


for p in content['pages']:
    walk(p, p['id'])

print(f'checked {checked} text fields')
if bad:
    print(f'NOT FOUND IN SOURCES: {len(bad)}')
    for w, s in bad:
        print(' ', w, '|', s[:80])
    sys.exit(1)
print('OK: every text field is verbatim from the 10 source documents')
print(f'{len(labels)} hand-written labels (navigation / headings):')
for l in sorted(labels):
    print('  ', l)
