import os
from html.parser import HTMLParser

root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

class ImgParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.imgs = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'img':
            self.imgs.append(dict(attrs))

missing_alt = []
for dirpath, _, filenames in os.walk(root):
    for fn in filenames:
        if not fn.lower().endswith('.html'):
            continue
        path = os.path.join(dirpath, fn)
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            data = f.read()
        parser = ImgParser()
        parser.feed(data)
        for attrs in parser.imgs:
            if not attrs.get('alt') or not attrs.get('alt').strip():
                missing_alt.append((path, attrs.get('src', '')))

if missing_alt:
    print('Images missing alt text (in HTML files):')
    for path, src in missing_alt:
        print(f'- {path}: src="{src}"')
else:
    print('All images in HTML files have alt text.')
