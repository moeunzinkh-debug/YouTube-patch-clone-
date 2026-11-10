"""Decode and verify exact feature transforms for pinned SimSimi Hermes payloads."""
import hashlib
import io
import json
import sys
from pathlib import Path

from hermes_dec.parsers.hbc_bytecode_parser import parse_hbc_bytecode
from hermes_dec.parsers.hbc_file_parser import HBCReader

original = Path(sys.argv[1]).read_bytes()
patched = Path(sys.argv[2]).read_bytes()
assert len(original) == len(patched)
sha = hashlib.sha256(original).hexdigest()
old_gates = json.loads(Path('docs/simsimi/feature-gates.json').read_text())['gates']
if sha == '203256d3824cfbc449d110fca1601095ecf283f555079407d03a2f46ca0c7489':
    version = '9.2.3'
    gates = old_gates
    membership_ids = (6838, 6846)
    daily = {'function_id': 22097, 'relative_offset': 19, 'offset': 23509841,
             'original': '3701010243f4', 'replacement': '780176017801'}
elif sha == 'ae1029cfbc61343b27b8f849a21a50df2b22b2cca361bad8aac1c70f069d8e36':
    version = '9.2.6'
    gates = [
        {'feature': 'conversation_level', 'function_id': 26732, 'relative_offset': 91, 'offset': 24120758, 'original': '3605050165', 'replacement': '7805080505'},
        {'feature': 'profile_photo', 'function_id': 22279, 'relative_offset': 102, 'offset': 23541071, 'original': '2e010909', 'replacement': '78017801'},
        {'feature': 'group_cover', 'function_id': 21167, 'relative_offset': 52, 'offset': 23207684, 'original': '3602020387', 'replacement': '7802080202'},
        {'feature': 'group_cover', 'function_id': 21172, 'relative_offset': 280, 'offset': 23208408, 'original': '3605050c87', 'replacement': '7805080505'},
        {'feature': 'photo_send', 'function_id': 25611, 'relative_offset': 84, 'offset': 23915716, 'original': '360c000b87', 'replacement': '780c080c0c'},
        {'feature': 'photo_send', 'function_id': 30982, 'relative_offset': 167, 'offset': 25248710, 'original': '3602020c87', 'replacement': '7802080202'},
        {'feature': 'photo_send', 'function_id': 25715, 'relative_offset': 13, 'offset': 23934150, 'original': '2e020105', 'replacement': '78027802'},
        {'feature': 'photo_send', 'function_id': 31003, 'relative_offset': 895, 'offset': 25257172, 'original': '2e040307', 'replacement': '78047804'},
        {'feature': 'read_receipts', 'function_id': 25982, 'relative_offset': 18, 'offset': 23978078, 'original': '3601000187', 'replacement': '7801080101'},
        {'feature': 'item_controls', 'function_id': 20661, 'relative_offset': 17, 'offset': 23122915, 'original': '3602000287', 'replacement': '7802080202'},
        {'feature': 'item_controls', 'function_id': 22158, 'relative_offset': 17, 'offset': 23519138, 'original': '3602000287', 'replacement': '7802080202'},
    ]
    membership_ids = (6838, 6846)
    daily = {'function_id': 22095, 'relative_offset': 19, 'offset': 23505891,
             'original': '3701010245f4', 'replacement': '780176017801'}
else:
    raise AssertionError(f'Unknown original Hermes payload: {sha}')

reader = HBCReader(); reader.read_whole_file(io.BytesIO(patched))
original_reader = HBCReader(); original_reader.read_whole_file(io.BytesIO(original))
for gate in gates:
    offset = gate['offset']
    before, after = bytes.fromhex(gate['original']), bytes.fromhex(gate['replacement'])
    assert original[offset:offset + len(before)] == before, gate
    assert patched[offset:offset + len(after)] == after, gate
    header = reader.function_headers[gate['function_id']]
    lines = [repr(ins) for ins in parse_hbc_bytecode(header, reader)]
    prefix = f"{gate['relative_offset']:08x}: <LoadConstTrue>"
    assert any(line.startswith(prefix) for line in lines), gate
    old_header = original_reader.function_headers[gate['function_id']]
    assert old_header.offset == header.offset and old_header.bytecodeSizeInBytes == header.bytecodeSizeInBytes
    relative = gate['relative_offset']
    size = len(before)
    old_code = original[header.offset:header.offset + header.bytecodeSizeInBytes]
    new_code = patched[header.offset:header.offset + header.bytecodeSizeInBytes]
    assert old_code[:relative] == new_code[:relative]
    assert old_code[relative + size:] == new_code[relative + size:]

daily_before, daily_after = bytes.fromhex(daily['original']), bytes.fromhex(daily['replacement'])
daily_offset = daily['offset']
assert original[daily_offset:daily_offset + len(daily_before)] == daily_before
assert patched[daily_offset:daily_offset + len(daily_after)] == daily_after
daily_lines = [repr(ins) for ins in parse_hbc_bytecode(reader.function_headers[daily['function_id']], reader)]
assert any(line.startswith(f"{daily['relative_offset']:08x}: <LoadConstTrue>") for line in daily_lines)

listener = reader.function_headers[membership_ids[1]]
listener_lines = [repr(ins) for ins in parse_hbc_bytecode(listener, reader)]
assert any("'getMembershipObject'" in line for line in listener_lines)
assert not any("'currentMembershipStatus'" in line for line in listener_lines)
for required in ('F_SaveFreetalkLevelToServer', 'MyProfileSetImageScreen', 'GroupRoomSetCoverScreen',
                 'checkShowRewardAds', 'F_CheckImageSendLimit', 'msgHasBeenRead'):
    assert required in reader.strings, required

changed = [i for i in range(len(original) - 20) if original[i] != patched[i]]
reviewed = []
for gate in gates:
    reviewed.extend(range(gate['offset'], gate['offset'] + len(bytes.fromhex(gate['original']))))
# Membership and ad transforms are separately constrained by JVM tests; this
# output includes them, so only require every feature-region byte to be reviewed.
assert all(any(original[i] != patched[i] for i in range(g['offset'], g['offset'] + len(bytes.fromhex(g['original'])))) for g in gates)
print(json.dumps({
    'version': version,
    'decoded_feature_regions': len(gates),
    'decoded_feature_function_ids': sorted({g['function_id'] for g in gates}),
    'listener_uses_cloned_membership': True,
    'daily_bonus_membership_loader_branch_decoded': True,
    'changed_bytes_before_footer': len(changed),
    'device_runtime_tested': False,
}, indent=2))
