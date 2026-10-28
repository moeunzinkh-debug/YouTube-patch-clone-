"""Map real membership feature gates; never infer a grant from UI state."""
import io
import json
import re
import sys
import zipfile
from pathlib import Path
from hermes_dec.parsers.hbc_file_parser import HBCReader
from hermes_dec.parsers.hbc_bytecode_parser import parse_hbc_bytecode

with zipfile.ZipFile(sys.argv[1]) as apk:
    payload = apk.read('assets/index.android.bundle')
reader = HBCReader()
reader.read_whole_file(io.BytesIO(payload))
pattern = re.compile(r'conversation.*level|level.*conversation|profile|cover|photo|read.*message|message.*read|receipt|membership|item|slider|topic', re.I)
result = {'status': 'Analysis only; individual feature functionality is not established.',
          'named_functions': [], 'membership_references': [], 'api_paths': []}
for text in reader.strings:
    if text.startswith('/') and pattern.search(text):
        result['api_paths'].append(text)
ids = [reader.strings.index(text) for text in ('hasMembership', 'getMembershipObject')]
needles = [index.to_bytes(length, 'little') for index in ids for length in (2, 4)]
for fid, header in enumerate(reader.function_headers):
    name = reader.strings[header.functionName]
    entry = {'function_id': fid, 'name': name, 'offset': header.offset,
             'size': header.bytecodeSizeInBytes, 'frame_size': header.frameSize,
             'has_exception_handler': bool(header.hasExceptionHandler)}
    if pattern.search(name):
        result['named_functions'].append(entry)
    code = payload[header.offset:header.offset+header.bytecodeSizeInBytes]
    if not any(needle in code for needle in needles):
        continue
    disassembly = [repr(ins) for ins in parse_hbc_bytecode(header, reader)]
    refs = [index for index, line in enumerate(disassembly)
            if "# String: 'hasMembership'" in line or "# String: 'getMembershipObject'" in line]
    if not refs:
        continue
    selected = set()
    for index in refs:
        selected.update(range(max(0, index-15), min(len(disassembly), index+45)))
    entry = dict(entry, instruction_count=len(disassembly), bytecode_hex=code.hex(),
                 disassembly=[disassembly[index] for index in sorted(selected)])
    result['membership_references'].append(entry)
Path(sys.argv[2]).write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
print('Membership references:', len(result['membership_references']))
