package dev.jason.gboardpatches.extension.khmerlish;

/** Pure, session-scoped edit planner; does not retain the user's text. */
final class KhmerlishController {
    private static final int MAX_WORD = 32;
    private int trackedStart = -1;
    private int trackedEnd = -1;
    private long trackedHash;
    // Only a space emitted by this feature can be removed when joining Khmer words.
    private int joinAfter = -1;

    static final class Edit {
        final int deleteBefore;
        final String insert;
        final int joinAfter;
        Edit(int deleteBefore, String insert, int joinAfter) {
            this.deleteBefore = deleteBefore;
            this.insert = insert;
            this.joinAfter = joinAfter;
        }
    }

    void reset() {
        clearTracked();
        joinAfter = -1;
    }

    private void clearTracked() {
        trackedStart = -1;
        trackedEnd = -1;
        trackedHash = 0;
    }

    /** Called with a verified collapsed cursor and at most the text immediately before it. */
    Edit observe(CharSequence before, int cursor, int composingStart, int composingEnd,
            KhmerlishDictionary dictionary) {
        if (before == null || cursor < 0 || before.length() == 0 || dictionary == null) {
            reset();
            return null;
        }
        int length = before.length();
        char last = before.charAt(length - 1);
        if (asciiLetter(last)) {
            int start = wordStart(before, length);
            int wordLength = length - start;
            int absoluteStart = cursor - wordLength;
            if (absoluteStart < 0 || wordLength > MAX_WORD || forbiddenPrefix(before, start)) {
                reset();
                return null;
            }
            if (joinAfter >= 0 && absoluteStart != joinAfter) joinAfter = -1;
            trackedStart = absoluteStart;
            trackedEnd = cursor;
            trackedHash = hash(before, start, length);
            return null;
        }
        if (!delimiter(last)) {
            clearTracked();
            if (cursor != joinAfter) joinAfter = -1;
            return null;
        }
        int end = length - 1;
        int start = wordStart(before, end);
        int wordLength = end - start;
        int absoluteStart = cursor - 1 - wordLength;
        if (wordLength == 0) {
            clearTracked();
            if (cursor != joinAfter) joinAfter = -1;
            return null;
        }
        if (wordLength > MAX_WORD || absoluteStart < 0 || forbiddenPrefix(before, start)
                || trackedStart != absoluteStart || trackedEnd != cursor - 1
                || trackedHash != hash(before, start, end)) {
            reset();
            return null;
        }
        // Do not touch a word while the editor still marks it as composing.
        if (composingStart >= 0 && composingEnd > composingStart) return null;
        String replacement = dictionary.lookup(before.subSequence(start, end).toString());
        clearTracked();
        if (replacement == null) {
            joinAfter = -1;
            return null;
        }
        boolean join = joinAfter == absoluteStart && start >= 2
                && before.charAt(start - 1) == ' ' && isKhmer(before.charAt(start - 2));
        int delete = wordLength + 1 + (join ? 1 : 0);
        String insert = replacement + last;
        int next = cursor - delete + insert.length();
        return new Edit(delete, insert, last == ' ' ? next : -1);
    }

    void applied(Edit edit) { joinAfter = edit == null ? -1 : edit.joinAfter; }

    private static int wordStart(CharSequence text, int end) {
        int start = end;
        while (start > 0 && asciiLetter(text.charAt(start - 1))) start--;
        return start;
    }

    private static boolean forbiddenPrefix(CharSequence text, int start) {
        if (start <= 0) return false;
        char c = text.charAt(start - 1);
        // Avoid rewriting pieces of URLs, email addresses, identifiers and numbers.
        return asciiLetter(c) || (c >= '0' && c <= '9') || c == '_' || c == '@'
                || c == '/' || c == '\\' || c == '.' || c == ':' || c == '#'
                || c == '+' || c == '-' || c == '\'';
    }

    private static boolean asciiLetter(char c) {
        return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z');
    }

    private static boolean isKhmer(char c) { return c >= '\u1780' && c <= '\u17ff'; }

    private static boolean delimiter(char c) {
        return c == ' ' || c == '\n' || c == '\t' || c == '.' || c == ','
                || c == '!' || c == '?' || c == ';' || c == ':' || c == '\u17d4';
    }

    // FNV-1a: track whether the same word was seen during typing, without retaining it.
    private static long hash(CharSequence value, int start, int end) {
        long result = 0xcbf29ce484222325L;
        for (int i = start; i < end; i++) {
            char c = value.charAt(i);
            // Gboard can change only the capitalization when it commits a word.
            // Dictionary lookup is case-insensitive, so treat that as the same
            // observed spelling while still rejecting a different correction.
            if (c >= 'A' && c <= 'Z') c = (char) (c + ('a' - 'A'));
            result = (result ^ c) * 0x100000001b3L;
        }
        return result;
    }
}
