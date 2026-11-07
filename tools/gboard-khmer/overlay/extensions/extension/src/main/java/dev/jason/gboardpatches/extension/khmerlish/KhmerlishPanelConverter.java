package dev.jason.gboardpatches.extension.khmerlish;

import java.util.Locale;

/** Pure, bounded conversion for the explicitly opened Khmerlish panel. */
final class KhmerlishPanelConverter {
    static final int MAX_LENGTH = 8192;

    private KhmerlishPanelConverter() {}

    /**
     * Exact known words are converted as they are typed. Personal phrases take
     * precedence, using the longest complete match separated by single spaces.
     * Unknown words and URL/email/code-like tokens are preserved unchanged.
     */
    static String convert(CharSequence input, KhmerlishDictionary dictionary) {
        if (input == null) return "";
        String text = input.toString();
        if (dictionary == null || text.length() > MAX_LENGTH) return text;
        KhmerlishDictionary.PersonalSnapshot snapshot = dictionary.personalSnapshot();
        StringBuilder output = new StringBuilder(text.length());
        boolean previousConverted = false;
        String pendingWhitespace = "";
        for (int offset = 0; offset < text.length();) {
            char c = text.charAt(offset);
            if (Character.isWhitespace(c)) {
                int end = offset + 1;
                while (end < text.length() && Character.isWhitespace(text.charAt(end))) end++;
                pendingWhitespace = text.substring(offset, end);
                offset = end;
                continue;
            }
            int end = tokenEnd(text, offset);
            Match phrase = matchPhrase(text, offset, snapshot);
            Token converted;
            if (phrase != null) {
                converted = phrase.token;
                end = phrase.end;
            } else {
                converted = convertToken(text.substring(offset, end), dictionary, snapshot);
            }
            if (!(previousConverted && converted.pureConverted && " ".equals(pendingWhitespace))) {
                output.append(pendingWhitespace);
            }
            pendingWhitespace = "";
            output.append(converted.text);
            previousConverted = converted.pureConverted;
            offset = end;
        }
        return output.append(pendingWhitespace).toString();
    }

    private static Match matchPhrase(String text, int start, KhmerlishDictionary.PersonalSnapshot snapshot) {
        int end = tokenEnd(text, start);
        Part first = part(text.substring(start, end));
        if (first == null || !first.suffix.isEmpty()) return null;
        String roman = first.word.toLowerCase(Locale.ROOT);
        if (!snapshot.hasPhrasePrefix(roman)) return null;
        Match best = null;
        while (end + 1 < text.length() && text.charAt(end) == ' '
                && !Character.isWhitespace(text.charAt(end + 1))) {
            int nextEnd = tokenEnd(text, end + 1);
            Part next = part(text.substring(end + 1, nextEnd));
            if (next == null || !next.prefix.isEmpty()) break;
            roman += " " + next.word.toLowerCase(Locale.ROOT);
            if (roman.length() > KhmerlishPersonalData.MAX_ROMAN) break;
            String value = snapshot.phrase(roman);
            if (value != null) {
                best = new Match(nextEnd, new Token(first.prefix + value + next.suffix,
                        first.prefix.isEmpty() && next.suffix.isEmpty()));
            }
            if (!next.suffix.isEmpty() || !snapshot.hasPhrasePrefix(roman)) break;
            end = nextEnd;
        }
        return best;
    }

    private static int tokenEnd(String text, int start) {
        int end = start;
        while (end < text.length() && !Character.isWhitespace(text.charAt(end))) end++;
        return end;
    }

    private static Part part(String token) {
        if (looksLikeAddressOrCode(token)) return null;
        int start = 0;
        while (start < token.length() && !isAsciiLetter(token.charAt(start))) {
            if ("([{«“‘\"'".indexOf(token.charAt(start)) < 0) return null;
            start++;
        }
        int end = start;
        while (end < token.length() && isAsciiLetter(token.charAt(end))) end++;
        if (start == end) return null;
        for (int i = end; i < token.length(); i++) {
            if (".,!?;:)]}»”’\"'\u17d4".indexOf(token.charAt(i)) < 0) return null;
        }
        return new Part(token.substring(0, start), token.substring(start, end), token.substring(end));
    }

    private static Token convertToken(String token, KhmerlishDictionary dictionary,
            KhmerlishDictionary.PersonalSnapshot snapshot) {
        if (looksLikeAddressOrCode(token)) return new Token(token, false);
        StringBuilder result = new StringBuilder(token.length());
        boolean pureConverted = false;
        for (int i = 0; i < token.length();) {
            if (!isAsciiLetter(token.charAt(i))) {
                result.append(token.charAt(i++));
                continue;
            }
            int end = i + 1;
            while (end < token.length() && isAsciiLetter(token.charAt(end))) end++;
            String original = token.substring(i, end);
            String replacement = dictionary.lookup(original, snapshot);
            if (replacement != null) {
                result.append(replacement);
                pureConverted = i == 0 && end == token.length();
            } else {
                result.append(original);
            }
            i = end;
        }
        return new Token(result.toString(), pureConverted);
    }

    private static boolean looksLikeAddressOrCode(String token) {
        for (int i = 0; i < token.length(); i++) {
            char c = token.charAt(i);
            if (c == '@' || c == '/' || c == '\\' || c == '_' || c == '#'
                    || Character.isDigit(c)) return true;
            // A period between alphabetic characters is probably a domain/file.
            if (c == '.' && i > 0 && i + 1 < token.length()
                    && isAsciiLetter(token.charAt(i - 1)) && isAsciiLetter(token.charAt(i + 1))) {
                return true;
            }
        }
        return false;
    }

    private static boolean isAsciiLetter(char c) {
        return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z');
    }

    private static final class Part {
        final String prefix, word, suffix;
        Part(String prefix, String word, String suffix) {
            this.prefix = prefix;
            this.word = word;
            this.suffix = suffix;
        }
    }

    private static final class Match {
        final int end;
        final Token token;
        Match(int end, Token token) {
            this.end = end;
            this.token = token;
        }
    }

    private static final class Token {
        final String text;
        final boolean pureConverted;
        Token(String text, boolean pureConverted) {
            this.text = text;
            this.pureConverted = pureConverted;
        }
    }
}
