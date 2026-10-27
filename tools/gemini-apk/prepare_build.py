"""Apply a local, reviewed Gemini-only overlay to a fresh pinned upstream checkout."""
from pathlib import Path
import json
import shutil
import sys
root = Path(sys.argv[1])
common = root / 'src/main/kotlin/app/morphe/patches/google/common'
shutil.copyfile(Path(__file__).parent / 'overlay/Gemini_1_0_995038376.kt', common / 'versions/Gemini_1_0_995038376.kt')
p = common / 'VersionHookRegistry.kt'
s = p.read_text()
assert 'listOf(google175418, gemini10958859967)' in s
s = s.replace('import app.morphe.patches.google.common.versions.gemini10958859967',
              'import app.morphe.patches.google.common.versions.gemini10958859967\nimport app.morphe.patches.google.common.versions.gemini10995038376')
s = s.replace('listOf(google175418, gemini10958859967)', 'listOf(google175418, gemini10958859967, gemini10995038376)')
p.write_text(s)
p = root / 'patches-bundle.json'
data = json.loads(p.read_text())
data['version'] = '0.1.2'
data['download_url'] = 'https://github.com/ryuya0124/gemini-microg-patches/releases/download/v0.1.2/gemini-microg-patches-0.1.2.mpp'
p.write_text(json.dumps(data, indent=2) + '\n')
# Local artifact: no release or upstream download descriptor is published.
p = root / 'scripts/package-mpp.py'
s = p.read_text().replace("'Name': 'Gemini microG patches'", "'Name': 'Gemini microG patches (local Gemini 345 port)'")
s = s.replace("'Author': 'ryuya0124'", "'Author': 'ryuya0124; local Gemini profile by YouTube-patch-clone contributors'")
p.write_text(s)
