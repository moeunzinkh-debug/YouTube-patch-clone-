package app.morphe.extension.king;

import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.nio.CharBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Narrow, fail-closed binary Android XML editor used for an opt-in UI experiment.
 * It marks explicitly selected compiled XML elements GONE; it does not remove
 * IDs or code and it cannot change Compose, WebView or server-rendered UI.
 */
public final class AxmlEditor {
    private static final int XML = 0x0003, STRING_POOL = 0x0001, RESOURCE_MAP = 0x0180;
    private static final int START_ELEMENT = 0x0102, END_ELEMENT = 0x0103;
    private static final int UTF8 = 0x00000100;
    private static final int NO_INDEX = -1;
    private static final int ANDROID_ID = 0x010100d0;
    private static final int ANDROID_VISIBILITY = 0x010100dc;
    private static final int ANDROID_TEXT = 0x0101014f;
    private static final int TYPE_STRING = 0x03, TYPE_INT_DEC = 0x10;
    private static final String ANDROID_NS = "http://schemas.android.com/apk/res/android";
    private static final int MAX_BYTES = 16 * 1024 * 1024;

    private AxmlEditor() {}

    public static final class Node {
        public final int ordinal;
        public final int depth;
        public final String tag;
        public final int resourceId;
        public final String text;

        Node(int ordinal, int depth, String tag, int resourceId, String text) {
            this.ordinal = ordinal;
            this.depth = depth;
            this.tag = tag;
            this.resourceId = resourceId;
            this.text = text;
        }
    }

    private static final class Chunk {
        final int type;
        byte[] bytes;
        Chunk(int type, byte[] bytes) { this.type = type; this.bytes = bytes; }
    }

    private static final class Doc {
        final byte[] header;
        final List<Chunk> chunks;
        final int poolIndex;
        final int mapIndex;
        final Pool pool;
        final int[] ids;

        Doc(byte[] header, List<Chunk> chunks, int poolIndex, int mapIndex, Pool pool, int[] ids) {
            this.header = header;
            this.chunks = chunks;
            this.poolIndex = poolIndex;
            this.mapIndex = mapIndex;
            this.pool = pool;
            this.ids = ids;
        }
    }

    private static final class Pool {
        final byte[] original;
        final int headerSize, count, styles, flags, stringsStart, stylesStart;
        final List<String> strings;
        final int[] offsets;
        Pool(byte[] original, int headerSize, int count, int styles, int flags,
             int stringsStart, int stylesStart, List<String> strings, int[] offsets) {
            this.original = original; this.headerSize = headerSize; this.count = count;
            this.styles = styles; this.flags = flags; this.stringsStart = stringsStart;
            this.stylesStart = stylesStart; this.strings = strings; this.offsets = offsets;
        }
    }

    private static int u16(byte[] b, int p) {
        need(b, p, 2);
        return (b[p] & 255) | ((b[p + 1] & 255) << 8);
    }
    private static int i32(byte[] b, int p) {
        need(b, p, 4);
        return (b[p] & 255) | ((b[p + 1] & 255) << 8) | ((b[p + 2] & 255) << 16) | (b[p + 3] << 24);
    }
    private static void p16(byte[] b, int p, int v) {
        need(b, p, 2); b[p] = (byte) v; b[p + 1] = (byte) (v >>> 8);
    }
    private static void p32(byte[] b, int p, int v) {
        need(b, p, 4); b[p] = (byte) v; b[p + 1] = (byte) (v >>> 8);
        b[p + 2] = (byte) (v >>> 16); b[p + 3] = (byte) (v >>> 24);
    }
    private static void need(byte[] b, int start, int length) {
        if (start < 0 || length < 0 || start > b.length || length > b.length - start)
            throw new IllegalArgumentException("Truncated or invalid binary XML");
    }
    private static int[] len8(byte[] b, int p, int end) {
        if (p >= end) throw new IllegalArgumentException("Invalid UTF-8 length");
        int n = b[p++] & 255;
        if ((n & 128) != 0) {
            if (p >= end) throw new IllegalArgumentException("Invalid UTF-8 length");
            n = ((n & 127) << 8) | (b[p++] & 255);
        }
        return new int[] { n, p };
    }
    private static int[] len16(byte[] b, int p, int end) {
        if (p + 2 > end) throw new IllegalArgumentException("Invalid UTF-16 length");
        int n = u16(b, p); p += 2;
        if ((n & 0x8000) != 0) {
            if (p + 2 > end) throw new IllegalArgumentException("Invalid UTF-16 length");
            long value = ((long)(n & 0x7fff) << 16) | u16(b, p); p += 2;
            if (value > Integer.MAX_VALUE) throw new IllegalArgumentException("String too long");
            n = (int) value;
        }
        return new int[] { n, p };
    }
    private static String decode(byte[] bytes, int offset, int length, boolean utf8) {
        try {
            CharBuffer out = (utf8 ? StandardCharsets.UTF_8 : StandardCharsets.UTF_16LE)
                    .newDecoder().onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT)
                    .decode(ByteBuffer.wrap(bytes, offset, length));
            return out.toString();
        } catch (CharacterCodingException e) {
            throw new IllegalArgumentException("Malformed XML string", e);
        }
    }
    private static Pool parsePool(byte[] bytes) {
        int header = u16(bytes, 2);
        if (header < 28 || i32(bytes, 4) != bytes.length) throw new IllegalArgumentException("Invalid string pool");
        int count = i32(bytes, 8), styles = i32(bytes, 12), flags = i32(bytes, 16);
        int start = i32(bytes, 20), styleStart = i32(bytes, 24);
        if (count < 0 || count > 100000 || styles < 0 || styles > count) throw new IllegalArgumentException("Invalid string counts");
        long offsetsEnd = (long)header + 4L * (count + styles);
        int stringsEnd = styleStart == 0 ? bytes.length : styleStart;
        if (offsetsEnd > start || start < header || stringsEnd < start || stringsEnd > bytes.length
                || (styles > 0 && styleStart == 0)) throw new IllegalArgumentException("Invalid string pool offsets");
        int[] offsets = new int[count];
        List<String> values = new ArrayList<>(count);
        boolean utf8 = (flags & UTF8) != 0;
        for (int i = 0; i < count; i++) {
            int relative = i32(bytes, header + i * 4);
            long address = (long)start + relative;
            if (relative < 0 || address < start || address >= stringsEnd) throw new IllegalArgumentException("Invalid string offset");
            offsets[i] = relative;
            int pos = (int) address;
            if (utf8) {
                int[] units = len8(bytes, pos, stringsEnd);
                int[] length = len8(bytes, units[1], stringsEnd);
                pos = length[1];
                if (length[0] > stringsEnd - pos - 1 || bytes[pos + length[0]] != 0)
                    throw new IllegalArgumentException("Invalid UTF-8 terminator");
                String value = decode(bytes, pos, length[0], true);
                if (value.length() != units[0]) throw new IllegalArgumentException("Invalid UTF-8 unit length");
                values.add(value);
            } else {
                int[] length = len16(bytes, pos, stringsEnd); pos = length[1];
                long byteLength = 2L * length[0];
                if (byteLength > stringsEnd - pos - 2 || u16(bytes, pos + (int)byteLength) != 0)
                    throw new IllegalArgumentException("Invalid UTF-16 terminator");
                values.add(decode(bytes, pos, (int)byteLength, false));
            }
        }
        return new Pool(bytes, header, count, styles, flags, start, styleStart, values, offsets);
    }
    private static Doc parse(byte[] xml) {
        if (xml == null || xml.length < 8 || xml.length > MAX_BYTES || u16(xml, 0) != XML
                || u16(xml, 2) < 8 || i32(xml, 4) != xml.length)
            throw new IllegalArgumentException("Not a supported binary Android XML document");
        int rootHeader = u16(xml, 2), cursor = rootHeader, poolIndex = -1, mapIndex = -1;
        need(xml, 0, rootHeader);
        List<Chunk> chunks = new ArrayList<>();
        while (cursor < xml.length) {
            need(xml, cursor, 8);
            int type = u16(xml, cursor), header = u16(xml, cursor + 2), size = i32(xml, cursor + 4);
            if (header < 8 || size < header || size > xml.length - cursor || (size & 3) != 0)
                throw new IllegalArgumentException("Invalid binary XML chunk size");
            if (type == STRING_POOL) {
                if (poolIndex != -1 || !chunks.isEmpty()) throw new IllegalArgumentException("Unexpected string pool");
                poolIndex = chunks.size();
            }
            if (type == RESOURCE_MAP) {
                if (mapIndex != -1 || poolIndex == -1 || chunks.size() != poolIndex + 1 || header != 8 || ((size - 8) & 3) != 0)
                    throw new IllegalArgumentException("Unexpected resource map");
                mapIndex = chunks.size();
            }
            chunks.add(new Chunk(type, Arrays.copyOfRange(xml, cursor, cursor + size)));
            cursor += size;
        }
        if (cursor != xml.length || poolIndex != 0) throw new IllegalArgumentException("String pool missing");
        Pool pool = parsePool(chunks.get(poolIndex).bytes);
        int[] ids = new int[0];
        if (mapIndex >= 0) {
            byte[] map = chunks.get(mapIndex).bytes;
            ids = new int[(map.length - 8) / 4];
            if (ids.length > pool.count) throw new IllegalArgumentException("Resource map exceeds string pool");
            for (int i = 0; i < ids.length; i++) ids[i] = i32(map, 8 + 4 * i);
        }
        return new Doc(Arrays.copyOf(xml, rootHeader), chunks, poolIndex, mapIndex, pool, ids);
    }
    private static String string(Pool pool, int index) {
        if (index < 0 || index >= pool.count) throw new IllegalArgumentException("Invalid XML string index");
        return pool.strings.get(index);
    }
    private static int resourceId(int[] ids, int index) { return index >= 0 && index < ids.length ? ids[index] : 0; }
    private static int attrOffset(byte[] chunk) {
        if (u16(chunk, 2) != 16 || chunk.length < 36) throw new IllegalArgumentException("Unsupported element header");
        int offset = 16 + u16(chunk, 24);
        int size = u16(chunk, 26), count = u16(chunk, 28);
        if (offset < 36 || size != 20 || (long)offset + (long)size * count > chunk.length)
            throw new IllegalArgumentException("Unsupported XML attributes");
        for (int off : new int[] {30, 32, 34}) if (u16(chunk, off) > count)
            throw new IllegalArgumentException("Invalid special attribute index");
        return offset;
    }
    public static List<Node> list(byte[] xml) {
        Doc doc = parse(xml);
        List<Node> nodes = new ArrayList<>();
        List<Integer> names = new ArrayList<>(), namespaces = new ArrayList<>();
        int depth = 0, roots = 0;
        for (Chunk chunk : doc.chunks) {
            byte[] b = chunk.bytes;
            if (chunk.type == START_ELEMENT) {
                if (depth == 0 && ++roots != 1) throw new IllegalArgumentException("Multiple XML roots");
                int offset = attrOffset(b), count = u16(b, 28), id = 0;
                int nameIndex = i32(b, 20), namespaceIndex = i32(b, 16);
                String tag = string(doc.pool, nameIndex), text = "";
                if (namespaceIndex != NO_INDEX) string(doc.pool, namespaceIndex);
                names.add(nameIndex); namespaces.add(namespaceIndex);
                for (int i = 0; i < count; i++) {
                    int p = offset + i * 20, name = i32(b, p + 4), attrId = resourceId(doc.ids, name);
                    string(doc.pool, name);
                    int ns = i32(b, p); if (ns != NO_INDEX) string(doc.pool, ns);
                    if (u16(b, p + 12) != 8 || b[p + 14] != 0) throw new IllegalArgumentException("Invalid typed attribute");
                    if (attrId == ANDROID_ID) id = i32(b, p + 16);
                    if (attrId == ANDROID_TEXT) {
                        int raw = i32(b, p + 8), type = b[p + 15] & 255, data = i32(b, p + 16);
                        if (raw != NO_INDEX) text = string(doc.pool, raw);
                        else if (type == TYPE_STRING) text = string(doc.pool, data);
                        else if (data != 0) text = String.format("@0x%08x", data);
                    }
                }
                nodes.add(new Node(nodes.size(), depth++, tag, id, text));
            } else if (chunk.type == END_ELEMENT) {
                if (u16(b, 2) != 16 || b.length != 24 || --depth < 0)
                    throw new IllegalArgumentException("Unbalanced XML elements");
                int last = names.size() - 1;
                if (last < 0 || names.remove(last) != i32(b, 20) || namespaces.remove(last) != i32(b, 16))
                    throw new IllegalArgumentException("Mismatched XML element close");
            }
        }
        if (depth != 0 || nodes.isEmpty()) throw new IllegalArgumentException("Unbalanced or empty XML");
        return Collections.unmodifiableList(nodes);
    }
    private static void writeLen8(ByteArrayOutputStream out, int value) {
        if (value < 0 || value > 0x7fff) throw new IllegalArgumentException("String too long");
        if (value >= 0x80) out.write((value >>> 8) | 0x80);
        out.write(value & 255);
    }
    private static void writeLen16(ByteArrayOutputStream out, int value) {
        if (value < 0) throw new IllegalArgumentException("String too long");
        if (value >= 0x8000) { int high = (value >>> 16) | 0x8000; out.write(high & 255); out.write(high >>> 8); }
        out.write(value & 255); out.write((value >>> 8) & 255);
    }
    private static byte[] appendString(Pool pool, String value) {
        boolean utf8 = (pool.flags & UTF8) != 0;
        byte[] encoded = value.getBytes(utf8 ? StandardCharsets.UTF_8 : StandardCharsets.UTF_16LE);
        int oldEnd = pool.stylesStart == 0 ? pool.original.length : pool.stylesStart;
        int oldLen = oldEnd - pool.stringsStart;
        ByteArrayOutputStream payload = new ByteArrayOutputStream();
        payload.write(pool.original, pool.stringsStart, oldLen);
        if (utf8) { writeLen8(payload, value.length()); writeLen8(payload, encoded.length); }
        else writeLen16(payload, value.length());
        payload.write(encoded, 0, encoded.length);
        payload.write(0); if (!utf8) payload.write(0);
        while ((payload.size() & 3) != 0) payload.write(0);
        int extra = pool.stringsStart - (pool.headerSize + 4 * (pool.count + pool.styles));
        int newStart = pool.headerSize + 4 * (pool.count + 1 + pool.styles) + extra;
        int stylesLen = pool.stylesStart == 0 ? 0 : pool.original.length - pool.stylesStart;
        byte[] result = new byte[newStart + payload.size() + stylesLen];
        System.arraycopy(pool.original, 0, result, 0, pool.headerSize);
        p32(result, 4, result.length); p32(result, 8, pool.count + 1); p32(result, 20, newStart);
        // Appending can invalidate the optional sorted-string-pool flag.
        p32(result, 16, pool.flags & ~1);
        p32(result, 24, pool.stylesStart == 0 ? 0 : newStart + payload.size());
        for (int i = 0; i < pool.count; i++) p32(result, pool.headerSize + 4 * i, pool.offsets[i]);
        p32(result, pool.headerSize + 4 * pool.count, oldLen);
        int oldStyleOffsets = pool.headerSize + 4 * pool.count;
        int newStyleOffsets = pool.headerSize + 4 * (pool.count + 1);
        int tail = 4 * pool.styles + extra;
        System.arraycopy(pool.original, oldStyleOffsets, result, newStyleOffsets, tail);
        byte[] data = payload.toByteArray(); System.arraycopy(data, 0, result, newStart, data.length);
        if (stylesLen != 0) System.arraycopy(pool.original, pool.stylesStart, result, newStart + data.length, stylesLen);
        return result;
    }
    private static byte[] resourceMap(int[] old, int index) {
        int[] ids = Arrays.copyOf(old, Math.max(old.length, index + 1)); ids[index] = ANDROID_VISIBILITY;
        byte[] b = new byte[8 + 4 * ids.length]; p16(b, 0, RESOURCE_MAP); p16(b, 2, 8); p32(b, 4, b.length);
        for (int i = 0; i < ids.length; i++) p32(b, 8 + 4 * i, ids[i]);
        return b;
    }
    private static byte[] hideElement(byte[] original, int[] ids, Pool pool, int namespaceIndex, int visibilityIndex) {
        int offset = attrOffset(original), count = u16(original, 28), found = -1;
        for (int i = 0; i < count; i++) {
            int p = offset + i * 20, name = i32(original, p + 4), id = resourceId(ids, name);
            if (i32(original, p) == namespaceIndex && "visibility".equals(string(pool, name)) && id != ANDROID_VISIBILITY)
                throw new IllegalArgumentException("Unmapped visibility attribute");
            if (id == ANDROID_VISIBILITY) {
                if (found >= 0 || i32(original, p) != namespaceIndex) throw new IllegalArgumentException("Ambiguous visibility attribute");
                found = i;
            }
        }
        if (found >= 0) {
            byte[] b = original.clone(); int p = offset + found * 20;
            p32(b, p + 8, NO_INDEX); p16(b, p + 12, 8); b[p + 14] = 0; b[p + 15] = TYPE_INT_DEC; p32(b, p + 16, 8);
            return b;
        }
        if (count == 0xffff) throw new IllegalArgumentException("Too many XML attributes");
        int insert = count;
        for (int i = 0; i < count; i++) {
            int existing = resourceId(ids, i32(original, offset + i * 20 + 4));
            if (existing == 0 || (existing & 0xffffffffL) > (ANDROID_VISIBILITY & 0xffffffffL)) { insert = i; break; }
        }
        int pos = offset + 20 * insert;
        byte[] b = new byte[original.length + 20];
        System.arraycopy(original, 0, b, 0, pos);
        System.arraycopy(original, pos, b, pos + 20, original.length - pos);
        p32(b, 4, b.length); p16(b, 28, count + 1);
        for (int field : new int[] {30, 32, 34}) {
            int v = u16(original, field); if (v != 0 && v > insert) p16(b, field, v + 1);
        }
        p32(b, pos, namespaceIndex); p32(b, pos + 4, visibilityIndex); p32(b, pos + 8, NO_INDEX);
        p16(b, pos + 12, 8); b[pos + 14] = 0; b[pos + 15] = TYPE_INT_DEC; p32(b, pos + 16, 8);
        return b;
    }
    public static byte[] hide(byte[] xml, Set<Integer> selected) {
        if (selected == null || selected.isEmpty()) throw new IllegalArgumentException("Select at least one XML element");
        Doc doc = parse(xml);
        int total = list(xml).size();
        Set<Integer> unique = new HashSet<>(selected);
        for (Integer value : unique) if (value == null || value < 0 || value >= total)
            throw new IllegalArgumentException("Selected XML element no longer exists");
        int ns = doc.pool.strings.indexOf(ANDROID_NS);
        if (ns < 0) throw new IllegalArgumentException("XML has no Android namespace");
        int visibility = -1;
        for (int i = 0; i < doc.ids.length; i++) if (doc.ids[i] == ANDROID_VISIBILITY) {
            if (!"visibility".equals(doc.pool.strings.get(i)) || visibility != -1)
                throw new IllegalArgumentException("Ambiguous visibility resource name");
            visibility = i;
        }
        if (visibility < 0) {
            visibility = doc.pool.count;
            doc.chunks.get(doc.poolIndex).bytes = appendString(doc.pool, "visibility");
            byte[] map = resourceMap(doc.ids, visibility);
            if (doc.mapIndex >= 0) doc.chunks.get(doc.mapIndex).bytes = map;
            else doc.chunks.add(doc.poolIndex + 1, new Chunk(RESOURCE_MAP, map));
        }
        int ordinal = 0;
        for (Chunk chunk : doc.chunks) if (chunk.type == START_ELEMENT) {
            if (unique.contains(ordinal)) chunk.bytes = hideElement(chunk.bytes, doc.ids, doc.pool, ns, visibility);
            ordinal++;
        }
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        out.write(doc.header, 0, doc.header.length);
        for (Chunk chunk : doc.chunks) out.write(chunk.bytes, 0, chunk.bytes.length);
        byte[] result = out.toByteArray();
        if (result.length > MAX_BYTES) throw new IllegalArgumentException("Modified XML exceeds limit");
        p32(result, 4, result.length);
        list(result); // Re-parse all structural bounds before returning any bytes.
        return result;
    }
}
