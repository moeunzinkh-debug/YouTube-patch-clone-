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
blocks = {match.group(1): match.group(0) for match in re.finditer(
    r'^Name: (.+)$.*?(?=^Name: |\Z)', listing, flags=re.MULTILINE | re.DOTALL
)}
daily = blocks['Daily bonus without video (client path, experimental)']
compatible_tail = daily.split('Compatible versions:', 1)[1]
if not re.search(r'^\s*9\.2\.3\s*$', compatible_tail, flags=re.MULTILINE) or re.search(
        r'^\s*9\.2\.6\s*$', compatible_tail, flags=re.MULTILINE):
    raise SystemExit('Daily bonus must remain 9.2.3-only because the 9.2.6 flow changed')
package_count = listing.count('Package name: com.ismaker.android.simsimi')
version_counts = {version: listing.count(version) for version in ('9.2.3', '9.2.6')}
expected_version_counts = {'9.2.3': len(EXPECTED), '9.2.6': len(EXPECTED) - 1}
if package_count != len(EXPECTED) or any(
        version_counts[version] < count for version, count in expected_version_counts.items()):
    details = ' | '.join(line.strip() for line in listing.splitlines()
                         if 'package' in line.lower() or 'version' in line.lower()
                         or any(version in line for version in version_counts))
    raise SystemExit(
        f'Unexpected SimSimi compatibility: package entries={package_count}, '
        f'version mentions={version_counts}; {details[:2000]}'
    )
print('Morphe lists 12 selectors for 9.2.3 and 11 remapped selectors for 9.2.6; changed daily-bonus flow stays 9.2.3-only')
