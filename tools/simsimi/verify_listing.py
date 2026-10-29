#!/usr/bin/env python3
"""Ensure Morphe lists the existing SimSimi features and the opt-in Quick Return patch."""
import re
import sys
from pathlib import Path

EXPECTED = {
    'Disable ad eligibility (experimental)': True,
    'Unlock membership UI (client only, experimental)': True,
    'Pull down to restart chat (experimental)': True,
    'MicroG RE service routing (experimental)': False,
    'Daily bonus without video (client path, experimental)': False,
    'Conversation level controls (client only, experimental)': False,
    'Profile photo controls (client only, experimental)': False,
    'Custom group cover controls (client only, experimental)': False,
    'Photo sending controls (client only, experimental)': False,
    'Read receipt display (client only, experimental)': False,
    'Membership item controls (client only, experimental)': False,
    'Quick return: double-tap Chat (experimental)': False,
}
listing = Path(sys.argv[1]).read_text()
names = re.findall(r'^Name: (.+)$', listing, flags=re.MULTILINE)
enabled = re.findall(r'^Enabled: (true|false)$', listing, flags=re.MULTILINE | re.IGNORECASE)
if len(names) != len(EXPECTED) or len(enabled) != len(EXPECTED) or len(set(names)) != len(names):
    raise SystemExit('Morphe listing does not contain exactly the 12 expected selectors')
actual = {name: enabled.lower() == 'true' for name, enabled in zip(names, enabled)}
if actual != EXPECTED:
    raise SystemExit('SimSimi selector names or defaults changed unexpectedly')
package_count = listing.count('Package name: com.ismaker.android.simsimi')
version_count = listing.count('9.2.3')
if package_count != len(EXPECTED) or version_count < len(EXPECTED):
    details = ' | '.join(line.strip() for line in listing.splitlines()
                         if 'package' in line.lower() or 'version' in line.lower() or '9.2.3' in line)
    raise SystemExit(f'Unexpected SimSimi compatibility: package entries={package_count}, version mentions={version_count}; {details[:2000]}')
print('Morphe lists 11 preserved selectors and opt-in Quick Return for SimSimi 9.2.3')
