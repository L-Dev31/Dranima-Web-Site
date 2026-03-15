import json
from pathlib import Path

path = Path(__file__).resolve().parent / 'datas' / 'wiki.json'

with path.open('r', encoding='utf-8') as f:
    data = json.load(f)

seen = set()
new_entries = []
removed = 0
for e in data.get('entries', []):
    eid = e.get('id')
    if eid in seen:
        removed += 1
        continue
    seen.add(eid)
    new_entries.append(e)

if removed:
    data['entries'] = new_entries
    with path.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

print(f"removed {removed} duplicate entries")
