"""Decode the actual output fixture with pinned Hermes 96 definitions."""
import io
import json
import sys
from pathlib import Path
from hermes_dec.parsers.hbc_file_parser import HBCReader
from hermes_dec.parsers.hbc_bytecode_parser import parse_hbc_bytecode

original = Path(sys.argv[1]).read_bytes()
patched = Path(sys.argv[2]).read_bytes()
reader = HBCReader()
reader.read_whole_file(io.BytesIO(patched))
original_reader = HBCReader()
original_reader.read_whole_file(io.BytesIO(original))
gates = json.loads(Path('docs/simsimi/feature-gates.json').read_text())['gates']
ids = sorted({6838, 6846, 6882, 22097} | {gate['function_id'] for gate in gates})
decoded = {}
for fid in ids:
    header = reader.function_headers[fid]
    decoded[fid] = [repr(ins) for ins in parse_hbc_bytecode(header, reader)]
    assert decoded[fid], f'No instructions: {fid}'
assert any(line.startswith('00000015: <Call1>') for line in decoded[6846]), 'Wrong getter call opcode'
assert any("'getMembershipObject'" in line for line in decoded[6846]), 'Listener did not use cloned status'
assert not any("'currentMembershipStatus'" in line for line in decoded[6846]), 'Raw status still sent to UI'
for gate in gates:
    offset = gate['offset']
    before = bytes.fromhex(gate['original'])
    after = bytes.fromhex(gate['replacement'])
    assert original[offset:offset+len(before)] == before, gate
    assert patched[offset:offset+len(after)] == after, gate
    prefix = f"{gate['relative_offset']:08x}: <LoadConstTrue>"
    assert any(line.startswith(prefix) for line in decoded[gate['function_id']]), gate

# Decode both versions and ensure every instruction outside the selected region
# is unchanged, including all branch targets and calls in each feature handler.
for fid in {gate['function_id'] for gate in gates}:
    regions = [range(g['relative_offset'], g['relative_offset']+len(bytes.fromhex(g['original'])))
               for g in gates if g['function_id'] == fid]
    def outside_regions(line):
        address = int(line[:8], 16)
        return not any(address in region for region in regions)
    before = list(filter(outside_regions, (repr(ins) for ins in parse_hbc_bytecode(original_reader.function_headers[fid], original_reader))))
    after = list(filter(outside_regions, decoded[fid]))
    assert before == after, f'Unexpected instruction/control-flow change in feature handler {fid}'

# The forced true must lead to the existing eligible branches, and read truth is
# still a separate input to the original indicator (not a fabricated receipt).
for fid, address, instruction, destination in (
    (26734, 0x60, 'JStrictEqual', 0xa3),  # level setter + server save
    (22281, 0x6a, 'JStrictEqualLong', 0xfd),  # photo picker
    (21153, 0x39, 'JStrictEqualLong', 0xca),  # custom cover picker
    (25717, 0x13, 'JStrictEqualLong', 0xb7),  # direct-photo member send
    (31005, 0x383, 'JmpTrue', 0x3da),  # group-photo member send
    (25984, 0x17, 'JmpTrueLong', 0xb1),  # receipt renderer
    (25984, 0xb7, 'JmpTrue', 0xff),  # real message-read flag
):
    prefix = f'{address:08x}: <{instruction}>'
    assert any(line.startswith(prefix) and f'# Address: {destination:08x}' in line
               for line in decoded[fid]), f'Unexpected branch in {fid} at {address:#x}'
assert any("'F_SaveFreetalkLevelToServer'" in line for line in decoded[26734])
assert any("'MyProfileSetImageScreen'" in line for line in decoded[22281])
assert any("'GroupRoomSetCoverScreen'" in line for line in decoded[21153])
assert any("'checkShowRewardAds'" in line for line in decoded[25717])
assert any("'F_CheckImageSendLimit'" in line for line in decoded[31005])
assert any("'msgHasBeenRead'" in line for line in decoded[25984])
# Actual read state and server item use/photo counting must not be fabricated.
for fid in (20620, 16263):
    header = reader.function_headers[fid]
    start, end = header.offset, header.offset + header.bytecodeSizeInBytes
    assert original[start:end] == patched[start:end], f'Unexpected server/quota mutation: {fid}'
header = reader.function_headers[25984]
assert original[header.offset+0xb1:header.offset+header.bytecodeSizeInBytes] == patched[header.offset+0xb1:header.offset+header.bytecodeSizeInBytes], 'Actual receipt truth modified'
print(json.dumps({'decoded_function_ids': ids, 'listener_uses_clone': True,
                  'six_client_gates_decoded': True, 'read_truth_server_item_use_photo_count_code_unchanged': True,
                  'device_runtime_tested': False}, indent=2))
