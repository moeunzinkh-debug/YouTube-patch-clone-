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
data['version'] = '0.1.3'
data['download_url'] = 'https://github.com/ryuya0124/gemini-microg-patches/releases/download/v0.1.3/gemini-microg-patches-0.1.3.mpp'
p.write_text(json.dumps(data, indent=2) + '\n')
# Local artifact: no release or upstream download descriptor is published.
p = root / 'scripts/package-mpp.py'
s = p.read_text().replace("'Name': 'Gemini microG patches'", "'Name': 'Gemini microG patches (local Google 17.6.59 + Gemini 345 port)'")
s = s.replace("'Author': 'ryuya0124'", "'Author': 'ryuya0124; local Gemini profile by YouTube-patch-clone contributors'")
p.write_text(s)
p = root / 'scripts/kotlin/VerifyMpp.kt'
s = p.read_text().replace('== "Gemini microG patches"', '== "Gemini microG patches (local Google 17.6.59 + Gemini 345 port)"')
p.write_text(s)

# Register only the exact, inspected Google target. Keep upstream snapshot unmodified.
shutil.copyfile(Path(__file__).parent / 'overlay/Google_17_6_59.kt', common / 'versions/Google_17_6_59.kt')
p = common / 'VersionHookRegistry.kt'
s = p.read_text().replace('import app.morphe.patches.google.common.versions.google175418',
    'import app.morphe.patches.google.common.versions.google175418\nimport app.morphe.patches.google.common.versions.google17659')
s = s.replace('gemini10995038376)', 'gemini10995038376, google17659)')
p.write_text(s)
# MicroG 7.3 declares the fully qualified permission. Select by exact input version
# so the legacy upstream profiles retain their original behavior.
for filename in ('GmsCoreSupportPatch.kt', 'MicrogRuntimePermissionsPatch.kt'):
    p = common.parent / 'microg' / filename
    s = p.read_text()
    s = s.replace('"app.revanced.gms.EXTENDED_ACCESS",',
        '(if (packageMetadata.versionName == "17.6.59.ve.arm64") "app.revanced.android.gms.EXTENDED_ACCESS" else "app.revanced.gms.EXTENDED_ACCESS"),')
    if filename == 'MicrogRuntimePermissionsPatch.kt':
        s = s.replace('        val arrayRegister =', '        val extendedAccess = if (packageMetadata.versionName == "17.6.59.ve.arm64") "app.revanced.android.gms.EXTENDED_ACCESS" else "app.revanced.gms.EXTENDED_ACCESS"\n        val arrayRegister =')
        s = s.replace('const-string v$arrayRegister, "app.revanced.gms.EXTENDED_ACCESS"', 'const-string v$arrayRegister, "$extendedAccess"').replace('const-string v$stringRegister, "app.revanced.gms.EXTENDED_ACCESS"', 'const-string v$stringRegister, "$extendedAccess"')
    p.write_text(s)
