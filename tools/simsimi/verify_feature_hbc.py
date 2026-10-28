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
    prefix = f"{gate['relative_offset']:08x}: <LoadConstTrue>"
    assert any(line.startswith(prefix) for line in decoded[gate['function_id']]), gate
# Actual read state and server item use/photo counting must not be fabricated.
for fid in (20620, 16263):
    header = reader.function_headers[fid]
    start, end = header.offset, header.offset + header.bytecodeSizeInBytes
    assert original[start:end] == patched[start:end], f'Unexpected server/quota mutation: {fid}'
header = reader.function_headers[25984]
assert original[header.offset+0xb1:header.offset+header.bytecodeSizeInBytes] == patched[header.offset+0xb1:header.offset+header.bytecodeSizeInBytes], 'Actual receipt truth modified'
print(json.dumps({'decoded_function_ids': ids, 'listener_uses_clone': True,
                  'six_client_gates_decoded': True, 'read_truth_server_item_use_photo_count_preserved': True,
                  'device_runtime_tested': False}, indent=2))
