"""Inventory an original SimSimi APK. Does not modify or claim to unlock it."""
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from loguru import logger
from androguard.core.apk import APK

logger.remove()
path = Path(sys.argv[1])
apk = APK(str(path))
report = {
    'source': {'release_tag': 'Simsimi', 'asset_id': 684067855, 'filename': path.name},
    'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'package': apk.get_package(),
    'version_name': apk.get_androidversion_name(),
    'version_code': apk.get_androidversion_code(),
    'min_sdk': apk.get_min_sdk_version(),
    'target_sdk': apk.get_target_sdk_version(),
    'main_activity': apk.get_main_activity(),
    'permissions': sorted(apk.get_permissions()),
    'services': sorted(apk.get_services()),
    'split': apk.get_attribute_value('manifest', 'split'),
    'findings_are': 'Static inventory only, not proof of patchability or server entitlement bypass.',
}
patterns = {
    'google_services': r'(?:com[./]google[./](?:android[./]gms|firebase)|com[./]android[./]billing)[A-Za-z0-9_./;$-]{0,160}',
    'membership': r'[A-Za-z0-9_./;$-]{0,60}(?:[Mm]embership|[Ss]ubscription|[Pp]remium|[Bb]illing|[Pp]urchase)[A-Za-z0-9_./;$-]{0,100}',
    'advertising': r'[A-Za-z0-9_./;$-]{0,60}(?:[Rr]ewarded|[Ii]nterstitial|[Aa]dmob|[Aa]ppLovin|[Ii]ronSource|[Uu]nityAds)[A-Za-z0-9_./;$-]{0,100}',
}
with zipfile.ZipFile(path) as z:
    report['dex_files'] = [n for n in z.namelist() if re.fullmatch(r'classes\d*\.dex', n)]
    report['native_libraries'] = [n for n in z.namelist() if n.startswith('lib/') and n.endswith('.so')]
    report['static_matches'] = {}
    for group, pattern in patterns.items():
        matches = set()
        for name in report['dex_files']:
            matches.update(re.findall(pattern, z.read(name).decode('latin1')))
        report['static_matches'][group] = {'total_unique': len(matches), 'sample': sorted(matches)[:100]}
    report['split_metadata_files'] = [n for n in z.namelist() if 'split' in n.lower() and n.endswith('.xml')]
output = Path(sys.argv[2])
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
print(json.dumps({k: report[k] for k in ('package','version_name','version_code','min_sdk','target_sdk','main_activity','sha256')}, indent=2))
