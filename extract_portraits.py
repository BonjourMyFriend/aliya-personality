import UnityPy
import os
import re

out_dir = 'C:/Users/Administrator/Desktop/Aliya personality/aliya_chat/assets/portraits/'
os.makedirs(out_dir, exist_ok=True)

asset_files = [
    'E:/Steam/steamapps/common/Aliya/Aliya_Data/resources.assets',
    'E:/Steam/steamapps/common/Aliya/Aliya_Data/sharedassets0.assets',
    'E:/Steam/steamapps/common/Aliya/Aliya_Data/globalgamemanagers.assets',
]

# Patterns to extract
extract_patterns = [
    r'^XDT-\d+$',        # XDT-000 through XDT-029 (character portraits)
    r'^XDT\d+$',          # XDT00 through XDT29
    r'^A_\d+$',           # A_00 through A_59 (character art variants)
    r'^A_light_\d+$',     # A_light_XX
    r'^DialogBox',        # DialogBox UI elements
    r'^PlayerChoice',     # PlayerChoice UI
    r'^MessageWindow',    # Message window
    r'^AliyaName',        # Aliya name display
    r'^OptionButton',     # Option buttons
    r'^Background$',      # Background art
]

extract_re = [re.compile(p) for p in extract_patterns]

extracted = {}
skipped = 0

for fpath in asset_files:
    if not os.path.exists(fpath):
        continue
    print(f'Processing: {os.path.basename(fpath)}')
    env = UnityPy.load(fpath)

    for obj in env.objects:
        if obj.type.name not in ['Texture2D', 'Sprite']:
            continue

        data = obj.read()
        name = data.m_Name if hasattr(data, 'm_Name') else ''

        # Check if name matches any pattern
        match = any(r.match(name) for r in extract_re)
        if not match:
            skipped += 1
            continue

        # Skip if already extracted (avoid duplicates)
        if name in extracted:
            continue

        try:
            if obj.type.name == 'Texture2D':
                img = data.image
                out_path = os.path.join(out_dir, f'{name}.png')
                img.save(out_path)
                extracted[name] = out_path
                print(f'  Extracted Texture2D: {name}')
            elif obj.type.name == 'Sprite':
                img = data.image
                out_path = os.path.join(out_dir, f'{name}_sprite.png')
                img.save(out_path)
                extracted[name] = out_path
                print(f'  Extracted Sprite: {name}')
        except Exception as e:
            print(f'  FAILED {name}: {e}')

print(f'\nTotal extracted: {len(extracted)}')
print(f'Skipped: {skipped}')

# List extracted files
print('\nExtracted files:')
for name, path in sorted(extracted.items()):
    size = os.path.getsize(path)
    print(f'  {name} -> {os.path.basename(path)} ({size} bytes)')
