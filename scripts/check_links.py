import os
from html.parser import HTMLParser

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for (k, v) in attrs:
            if k in ('href', 'src') and v:
                self.links.append((tag, k, v))

missing = []

for dirpath, _, filenames in os.walk(root):
    for fn in filenames:
        if not fn.lower().endswith('.html'):
            continue
        path = os.path.join(dirpath, fn)
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            data = f.read()
        parser = LinkParser()
        parser.feed(data)
        for tag, attr, val in parser.links:
            if val.startswith(('http://', 'https://', 'mailto:', 'tel:', '//', '#', 'javascript:')):
                continue
            val = val.split('#')[0]
            if val == '':
                continue
            if val.startswith('/'):
                target = os.path.join(root, val.lstrip('/'))
            else:
                target = os.path.join(dirpath, val)
            target = os.path.normpath(target)
            if not os.path.exists(target):
                missing.append((path, tag, attr, val, target))

if missing:
    print('Missing referenced files:')
    for p, tag, attr, val, tgt in missing:
        print(f'- {p}: <{tag} {attr}="{val}"> -> {tgt}')
else:
    print('No missing referenced files found.')
