package dev.jason.gboardpatches.extension.khmerlish;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;

/** Pure, session-scoped edit planner; no host-app text is persisted or logged. */
final class KhmerlishController {
    private static final int MAX_WORD = KhmerlishPersonalData.MAX_ROMAN;
    private static final long HASH_OFFSET = 0xcbf29ce484222325L;
    private static final long HASH_PRIME = 0x100000001b3L;
    private int trackedStart = -1;
    private int trackedEnd = -1;
    private long trackedHash;
    // Only a space emitted by this feature can be removed when joining Khmer words.
    private int joinAfter = -1;
    private KhmerlishDictionary.PersonalSnapshot snapshot;
    // Roman prefixes are limited to explicitly saved personal phrases. The
    // host suffix is represented only by positions and a hash, never retained.
    private List<PhraseCandidate> phrases = Collections.emptyList();

    private static final class PhraseCandidate {
        final String roman;
        final int start, end;
        final long outputHash;
        PhraseCandidate(String roman, int start, int end, long outputHash) {
            this.roman = roman;
            this.start = start;
            this.end = end;
            this.outputHash = outputHash;
        }
    }

    private static final class Seed {
        final String roman;
        final int start;
        final boolean newWord;
        Seed(String roman, int start, boolean newWord) {
            this.roman = roman;
            this.start = start;
            this.newWord = newWord;
        }
    }

    static final class Edit {
        final int deleteBefore;
        final String insert;
        final int joinAfter;
        private final List<PhraseCandidate> nextPhrases;
        Edit(int deleteBefore, String insert, int joinAfter) {
            this(deleteBefore, insert, joinAfter, Collections.emptyList());
        }
        private Edit(int deleteBefore, String insert, int joinAfter, List<PhraseCandidate> nextPhrases) {
            this.deleteBefore = deleteBefore;
            this.insert = insert;
            this.joinAfter = joinAfter;
            this.nextPhrases = nextPhrases;
        }
    }

    void reset() {
        clearTracked();
        joinAfter = -1;
        phrases = Collections.emptyList();
        snapshot = null;
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
        KhmerlishDictionary.PersonalSnapshot current = dictionary.personalSnapshot();
        if (snapshot != current) {
            reset();
            snapshot = current;
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
            retainBeforeWord(before, cursor, absoluteStart);
            if (joinAfter >= 0 && absoluteStart != joinAfter) joinAfter = -1;
            trackedStart = absoluteStart;
            trackedEnd = cursor;
            trackedHash = hashWord(before, start, length);
            return null;
        }
        if (!delimiter(last)) {
            clearTracked();
            phrases = Collections.emptyList();
            if (cursor != joinAfter) joinAfter = -1;
            return null;
        }
        int end = length - 1;
        int start = wordStart(before, end);
        int wordLength = end - start;
        int absoluteStart = cursor - 1 - wordLength;
        if (wordLength == 0) {
            clearTracked();
            if (last != ' ' || !hasCompletedPrefix(before, cursor)) phrases = Collections.emptyList();
            if (cursor != joinAfter) joinAfter = -1;
            return null;
        }
        if (wordLength > MAX_WORD || absoluteStart < 0 || forbiddenPrefix(before, start)
                || trackedStart != absoluteStart || trackedEnd != cursor - 1
                || trackedHash != hashWord(before, start, end)) {
            // An editor can send the same selection notification more than once.
            if (last == ' ' && trackedStart < 0 && hasCompletedPrefix(before, cursor)) return null;
            reset();
            return null;
        }
        // Do not touch a word while the editor still marks it as composing.
        if (composingStart >= 0 && composingEnd > composingStart) return null;
        String word = before.subSequence(start, end).toString().toLowerCase(Locale.ROOT);
        List<Seed> next = new ArrayList<>();
        PhraseCandidate match = null;
        String phraseReplacement = null;
        for (PhraseCandidate candidate : phrases) {
            if (candidate.end != absoluteStart || !matches(candidate, before, cursor)) continue;
            String extended = candidate.roman + " " + word;
            String value = current.phrase(extended);
            if (value != null && (match == null || candidate.start < match.start)) {
                match = candidate;
                phraseReplacement = value;
            }
            if (last == ' ' && current.hasPhrasePrefix(extended)) {
                next.add(new Seed(extended, candidate.start, false));
            }
        }
        if (last == ' ' && current.hasPhrasePrefix(word)) next.add(new Seed(word, absoluteStart, true));

        String replacement = phraseReplacement != null ? phraseReplacement : dictionary.lookup(word, current);
        clearTracked();
        if (replacement == null) {
            joinAfter = -1;
            phrases = buildCandidates(next, before, cursor, null, false);
            return null;
        }
        boolean joining = phraseReplacement == null && joinAfter == absoluteStart && start >= 2
                && before.charAt(start - 1) == ' ' && isKhmer(before.charAt(start - 2));
        int delete = phraseReplacement != null ? cursor - match.start
                : wordLength + 1 + (joining ? 1 : 0);
        if (delete <= 0 || delete > length) {
            reset();
            return null;
        }
        String insert = replacement + last;
        int newEnd = cursor - delete + insert.length();
        Edit planned = new Edit(delete, insert, last == ' ' ? newEnd : -1);
        return new Edit(delete, insert, planned.joinAfter,
                buildCandidates(next, before, cursor, planned, joining));
    }

    void applied(Edit edit) {
        joinAfter = edit == null ? -1 : edit.joinAfter;
        phrases = edit == null ? Collections.emptyList() : edit.nextPhrases;
    }

    private void retainBeforeWord(CharSequence before, int cursor, int wordStart) {
        if (phrases.isEmpty()) return;
        List<PhraseCandidate> retained = new ArrayList<>();
        for (PhraseCandidate candidate : phrases) {
            if (candidate.end == wordStart && matches(candidate, before, cursor)) retained.add(candidate);
        }
        phrases = retained;
    }

    private boolean hasCompletedPrefix(CharSequence before, int cursor) {
        for (PhraseCandidate candidate : phrases) {
            if (candidate.end == cursor && matches(candidate, before, cursor)) return true;
        }
        return false;
    }

    private static boolean matches(PhraseCandidate candidate, CharSequence before, int cursor) {
        int windowStart = cursor - before.length();
        int start = candidate.start - windowStart;
        int end = candidate.end - windowStart;
        return start >= 0 && end > start && end <= before.length()
                && hashExact(HASH_OFFSET, before, start, end) == candidate.outputHash;
    }

    private static List<PhraseCandidate> buildCandidates(List<Seed> seeds, CharSequence before,
            int cursor, Edit edit, boolean joining) {
        if (seeds.isEmpty()) return Collections.emptyList();
        int windowStart = cursor - before.length();
        int editStart = edit == null ? cursor : cursor - edit.deleteBefore;
        int newEnd = edit == null ? cursor : editStart + edit.insert.length();
        List<PhraseCandidate> result = new ArrayList<>();
        for (Seed seed : seeds) {
            int start = seed.start;
            // Joining a converted word consumes its preceding space. A phrase
            // starting at that word owns that space, not the prior Khmer text.
            if (edit != null && start > editStart) {
                if (seed.newWord && joining && start == editStart + 1) start = editStart;
                else continue; // A longer phrase replaced this seed's text.
            }
            int from = start - windowStart;
            int to = editStart - windowStart;
            if (from < 0 || from > to || to > before.length()) continue;
            long hash = hashExact(HASH_OFFSET, before, from, to);
            if (edit != null) hash = hashExact(hash, edit.insert, 0, edit.insert.length());
            result.add(new PhraseCandidate(seed.roman, start, newEnd, hash));
        }
        return result;
    }

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
    private static long hashWord(CharSequence value, int start, int end) {
        long result = HASH_OFFSET;
        for (int i = start; i < end; i++) {
            char c = value.charAt(i);
            // Gboard can change only the capitalization when it commits a word.
            if (c >= 'A' && c <= 'Z') c = (char) (c + ('a' - 'A'));
            result = (result ^ c) * HASH_PRIME;
        }
        return result;
    }

    private static long hashExact(long hash, CharSequence value, int start, int end) {
        for (int i = start; i < end; i++) hash = (hash ^ value.charAt(i)) * HASH_PRIME;
        return hash;
    }
}
