#!/usr/bin/env python3
"""Length-safe Android binary-XML string-pool rewriting for test fixtures only."""
import struct


def _len8(data: bytes, offset: int):
    first = data[offset]
    return (((first & 0x7f) << 8) | data[offset + 1], offset + 2) if first & 0x80 else (first, offset + 1)


def _len16(data: bytes, offset: int):
    first = struct.unpack_from('<H', data, offset)[0]
    return (((first & 0x7fff) << 16) | struct.unpack_from('<H', data, offset + 2)[0], offset + 4) if first & 0x8000 else (first, offset + 2)


def _encode8(length: int) -> bytes:
    if not 0 <= length <= 0x7fff:
        raise ValueError('UTF-8 pool string is too long')
    return bytes([length]) if length < 0x80 else bytes([(length >> 8) | 0x80, length & 0xff])


def _encode16(length: int) -> bytes:
    if not 0 <= length <= 0x7fffffff:
        raise ValueError('UTF-16 pool string is too long')
    return struct.pack('<H', length) if length < 0x8000 else struct.pack('<HH', (length >> 16) | 0x8000, length & 0xffff)


def rewrite_pool_string(xml: bytes, old: str, new: str) -> bytes:
    """Rebuild a string pool without changing indices. Require at least one match."""
    if len(xml) < 8:
        raise ValueError('Truncated binary XML')
    kind, root_header, root_size = struct.unpack_from('<HHI', xml, 0)
    if kind != 3 or root_header < 8 or root_size != len(xml):
        raise ValueError('Invalid binary XML header')
    cursor, matches, pools = root_header, 0, 0
    rebuilt = bytearray(xml[:root_header])
    while cursor < len(xml):
        if cursor + 8 > len(xml):
            raise ValueError('Truncated binary XML chunk')
        chunk_type, header_size, size = struct.unpack_from('<HHI', xml, cursor)
        if header_size < 8 or size < header_size or cursor + size > len(xml):
            raise ValueError('Invalid binary XML chunk')
        chunk = xml[cursor:cursor + size]
        if chunk_type != 1:
            rebuilt.extend(chunk)
            cursor += size
            continue
        pools += 1
        if header_size < 28:
            raise ValueError('Invalid string-pool header')
        count, styles, flags, strings_start, styles_start = struct.unpack_from('<IIIII', chunk, 8)
        offsets_end = header_size + 4 * (count + styles)
        strings_end = styles_start or size
        if offsets_end > strings_start or strings_start > strings_end or strings_end > size:
            raise ValueError('Invalid string-pool offsets')
        utf8 = bool(flags & 0x100)
        offsets = []
        encoded_values = bytearray()
        for index in range(count):
            string_offset = struct.unpack_from('<I', chunk, header_size + 4 * index)[0]
            position = strings_start + string_offset
            if not strings_start <= position < strings_end:
                raise ValueError('Invalid string position')
            if utf8:
                _, pos = _len8(chunk, position)
                byte_length, pos = _len8(chunk, pos)
                end = pos + byte_length
                if end >= strings_end or chunk[end] != 0:
                    raise ValueError('Invalid UTF-8 string')
                value = chunk[pos:end].decode('utf-8')
                original = chunk[position:end + 1]
                if value == old:
                    payload = new.encode('utf-8')
                    units = len(new.encode('utf-16le')) // 2
                    original = _encode8(units) + _encode8(len(payload)) + payload + b'\0'
                    matches += 1
            else:
                units, pos = _len16(chunk, position)
                end = pos + units * 2
                if end + 2 > strings_end or chunk[end:end + 2] != b'\0\0':
                    raise ValueError('Invalid UTF-16 string')
                value = chunk[pos:end].decode('utf-16le')
                original = chunk[position:end + 2]
                if value == old:
                    payload = new.encode('utf-16le')
                    original = _encode16(len(payload) // 2) + payload + b'\0\0'
                    matches += 1
            offsets.append(len(encoded_values))
            encoded_values.extend(original)
        while len(encoded_values) % 4:
            encoded_values.append(0)
        prefix = bytearray(chunk[:strings_start])
        for index, offset in enumerate(offsets):
            struct.pack_into('<I', prefix, header_size + 4 * index, offset)
        style_data = chunk[styles_start:] if styles_start else b''
        if styles_start:
            struct.pack_into('<I', prefix, 24, strings_start + len(encoded_values))
        new_chunk = prefix + encoded_values + style_data
        struct.pack_into('<I', new_chunk, 4, len(new_chunk))
        rebuilt.extend(new_chunk)
        cursor += size
    if cursor != len(xml) or pools != 1 or not matches:
        raise ValueError(f'Expected one string pool and at least one package match; got {pools}/{matches}')
    struct.pack_into('<I', rebuilt, 4, len(rebuilt))
    return bytes(rebuilt)
