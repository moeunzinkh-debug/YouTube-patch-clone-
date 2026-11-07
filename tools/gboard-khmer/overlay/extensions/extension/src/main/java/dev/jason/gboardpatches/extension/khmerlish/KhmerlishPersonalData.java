package dev.jason.gboardpatches.extension.khmerlish;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;

/** Validated, bounded user-supplied entries. Never logs input or performs I/O. */
final class KhmerlishPersonalData {
    static final int MAX_ENTRIES = 5000;
    static final int MAX_ROMAN = 64;
    static final int MAX_KHMER = 128;
    // Large enough for a worst-case export of MAX_ENTRIES (including quoted
    // fields), while bounding allocations when a document is opened.
    static final int MAX_IMPORT_CHARS = 1_600_000;
    static final int MAX_IMPORT_BYTES = 2_500_000;

    private KhmerlishPersonalData() {}

    static String roman(String value) {
        if (value == null || containsControl(value)) return null;
        String raw = value.trim().toLowerCase(Locale.ROOT);
        StringBuilder result = new StringBuilder(raw.length());
        boolean pendingSpace = false;
        for (int i = 0; i < raw.length(); i++) {
            char c = raw.charAt(i);
            if (c == ' ') {
                pendingSpace = true;
            } else if (c >= 'a' && c <= 'z') {
                if (pendingSpace && result.length() > 0) result.append(' ');
                result.append(c);
                pendingSpace = false;
            } else {
                return null;
            }
            if (result.length() > MAX_ROMAN) return null;
        }
        return result.length() == 0 ? null : result.toString();
    }

    static String khmer(String value) {
        if (value == null || containsControl(value)) return null;
        String result = value.trim();
        if (result.isEmpty() || result.length() > MAX_KHMER) return null;
        boolean hasKhmer = false;
        for (int i = 0; i < result.length();) {
            char c = result.charAt(i);
            if (Character.isSurrogate(c)) {
                if (!Character.isHighSurrogate(c) || i + 1 >= result.length()
                        || !Character.isLowSurrogate(result.charAt(i + 1))) return null;
            }
            int point = result.codePointAt(i);
            if (Character.isISOControl(point) || point == 0x2028 || point == 0x2029) return null;
            if (point >= 0x1780 && point <= 0x17d3) hasKhmer = true;
            i += Character.charCount(point);
        }
        return hasKhmer ? result : null;
    }

    private static boolean containsControl(String value) {
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            if (Character.isISOControl(c) || c == '\u2028' || c == '\u2029') return true;
        }
        return false;
    }

    static final class ImportException extends Exception {
        private static final long serialVersionUID = 1L;
        final int line;
        ImportException(int line) {
            super(line > 0 ? "Invalid dictionary row " + line : "Invalid dictionary file");
            this.line = line;
        }
    }

    /**
     * UTF-8 text already decoded strictly by the document reader. Each nonempty
     * row is exactly two fields (Roman, Khmer), separated by a tab or comma.
     * CSV-style quotes are supported; comments and a single optional header are
     * ignored. An invalid row or duplicate key rejects the whole import.
     */
    static Map<String, String> parse(String text) throws ImportException {
        if (text == null || text.length() > MAX_IMPORT_CHARS) throw new ImportException(0);
        if (text.startsWith("\ufeff")) text = text.substring(1);
        Map<String, String> result = new LinkedHashMap<>();
        String[] lines = text.split("\\r?\\n", -1);
        boolean firstRecord = true;
        for (int index = 0; index < lines.length; index++) {
            String line = lines[index];
            if (line.trim().isEmpty() || line.trim().startsWith("#")) continue;
            if (line.length() > 512 || line.indexOf('\r') >= 0) throw new ImportException(index + 1);
            char separator = line.indexOf('\t') >= 0 ? '\t' : ',';
            String[] values = fields(line, separator, index + 1);
            if (firstRecord && isHeader(values[0], values[1])) {
                firstRecord = false;
                continue;
            }
            firstRecord = false;
            String key = roman(values[0]);
            String value = khmer(values[1]);
            if (key == null || value == null || result.containsKey(key)
                    || result.size() >= MAX_ENTRIES) throw new ImportException(index + 1);
            result.put(key, value);
        }
        if (result.isEmpty()) throw new ImportException(0);
        return Collections.unmodifiableMap(result);
    }

    private static boolean isHeader(String first, String second) {
        String a = first.trim().toLowerCase(Locale.ROOT);
        String b = second.trim().toLowerCase(Locale.ROOT);
        return (a.equals("khmerlish") || a.equals("roman") || a.equals("latin"))
                && (b.equals("khmer") || b.equals("khmer_text"));
    }

    private static String[] fields(String line, char separator, int number) throws ImportException {
        String[] values = new String[2];
        int offset = 0;
        for (int column = 0; column < 2; column++) {
            while (offset < line.length() && line.charAt(offset) == ' ') offset++;
            StringBuilder value = new StringBuilder();
            if (offset < line.length() && line.charAt(offset) == '"') {
                offset++;
                boolean closed = false;
                while (offset < line.length()) {
                    char ch = line.charAt(offset++);
                    if (ch == '"') {
                        if (offset < line.length() && line.charAt(offset) == '"') {
                            value.append('"');
                            offset++;
                        } else {
                            closed = true;
                            break;
                        }
                    } else {
                        value.append(ch);
                    }
                }
                if (!closed) throw new ImportException(number);
                while (offset < line.length() && line.charAt(offset) == ' ') offset++;
            } else {
                while (offset < line.length() && line.charAt(offset) != separator) {
                    char ch = line.charAt(offset++);
                    if (ch == '"') throw new ImportException(number);
                    value.append(ch);
                }
            }
            values[column] = value.toString();
            if (column == 0) {
                if (offset >= line.length() || line.charAt(offset) != separator) {
                    throw new ImportException(number);
                }
                offset++;
            } else if (offset != line.length()) {
                throw new ImportException(number);
            }
        }
        return values;
    }

    /** Safe TSV export: input validation guarantees no tabs or line breaks. */
    static String exportTsv(Map<String, String> entries) {
        StringBuilder output = new StringBuilder("khmerlish\tkhmer\n");
        for (Map.Entry<String, String> entry : entries.entrySet()) {
            String key = roman(entry.getKey()), value = khmer(entry.getValue());
            if (key == null || value == null) throw new IllegalArgumentException("Invalid entry");
            output.append(key).append('\t');
            if (value.indexOf('"') >= 0) {
                output.append('"').append(value.replace("\"", "\"\"")).append('"');
            } else {
                output.append(value);
            }
            output.append('\n');
        }
        return output.toString();
    }
}
