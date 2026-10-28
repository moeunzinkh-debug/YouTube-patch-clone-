"""Read-only mapping for the exact Hermes 96 payload, using a pinned parser."""
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
pattern = re.compile(r'daily|bonus|membership|premium|rewarded|interstitial|onRefresh|reload|showAd|loadAd|removeAds|adFree|refreshHome', re.I)
result = {'parser_commit': '2e796663e1fedb93dca51060797ebf3327b3fedb', 'functions': [],
          'status': 'Read-only analysis. No premium entitlements or ad callbacks have been modified.'}
result['membership_recipe'] = {'Object_id': reader.strings.index('Object'), 'assign_id': reader.strings.index('assign')} 
for fid, header in enumerate(reader.function_headers):
    name = reader.strings[header.functionName]
    if not pattern.search(name):
        continue
    entry = {'function_id': fid, 'name': name, 'offset': header.offset, 'size': header.bytecodeSizeInBytes, 'frame_size': header.frameSize, 'has_exception_handler': bool(header.hasExceptionHandler)}
    if fid in (6838, 6882):
        entry['bytecode_hex'] = payload[header.offset:header.offset+header.bytecodeSizeInBytes].hex()
    if len(result['functions']) < 65 or re.search(r'daily|bonus', name, re.I) or fid in (26538, 29954, 29958):
        instructions = list(parse_hbc_bytecode(header, reader))
        entry['disassembly'] = [repr(ins) for ins in (instructions[:500] if re.search(r'daily|bonus', name, re.I) else instructions[:120])]
        entry['instruction_count'] = len(instructions)
    result['functions'].append(entry)
result['total_function_count'] = len(reader.function_headers)
Path(sys.argv[2]).write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
print('Matched', len(result['functions']), 'functions out of', result['total_function_count'])
