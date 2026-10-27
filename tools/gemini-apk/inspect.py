"""Inspect the uploaded Gemini APK without modifying or redistributing it."""
import hashlib
import json
from pathlib import Path
import sys
from loguru import logger
logger.remove()
from androguard.core.apk import APK
from androguard.core.dex import DEX

path = Path(sys.argv[1])
apk = APK(str(path))
assert apk.get_package() == 'com.google.android.apps.bard'
assert apk.get_androidversion_name() == '1.0.995038376'
report = dict(package=apk.get_package(), version=apk.get_androidversion_name(),
              version_code=apk.get_androidversion_code(), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
              min_sdk=apk.get_min_sdk_version(), matches=[])
for index, data in enumerate(apk.get_all_dex(), 1):
    dex = DEX(data)
    for cls in dex.get_classes():
        for method in cls.get_methods():
            code = method.get_code()
            if code is None:
                continue
            instructions = list(code.get_bc().get_instructions())
            hits = [ins for ins in instructions if ins.get_name() in ('const-string', 'const-string/jumbo')
                    and ins.get_string() == 'com.google.android.googlequicksearchbox']
            if hits:
                report['matches'].append(dict(dex=index, class_name=cls.get_name(), method=method.get_name(),
                    descriptor=method.get_descriptor(), count=len(hits),
                    instructions=[ins.get_name() + ' ' + ins.get_output() for ins in instructions]))
report['redirect_match_count'] = sum(m['count'] for m in report['matches'])
output = Path('docs/gemini-apk-inspection.json')
output.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k:v for k,v in report.items() if k != 'matches'}, indent=2))
