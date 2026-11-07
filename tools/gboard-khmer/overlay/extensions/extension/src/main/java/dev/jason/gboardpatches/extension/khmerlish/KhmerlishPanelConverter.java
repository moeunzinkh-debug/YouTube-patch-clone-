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
            Match personal = matchPersonal(text, offset, snapshot);
            Token converted;
            if (personal != null) {
                converted = personal.token;
                end = personal.end;
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

    /** Match explicit personal keys first, including symbols and multiword keys. */
    private static Match matchPersonal(String text, int offset, KhmerlishDictionary.PersonalSnapshot snapshot) {
        int firstEnd = tokenEnd(text, offset);
        Match best = null;
        int bestLength = -1;
        for (int start = offset; start < firstEnd; start++) {
            // Permit ordinary opening punctuation around a saved key, but never
            // search arbitrary substrings inside an address or identifier.
            if (start > offset && "([{«“‘\"'".indexOf(text.charAt(start - 1)) < 0) break;
            for (int end = start + 1; end <= text.length()
                    && end - start <= KhmerlishPersonalData.MAX_ROMAN; end++) {
                char added = text.charAt(end - 1);
                if (Character.isWhitespace(added) && added != ' ') break;
                String key = text.substring(start, end).toLowerCase(Locale.ROOT);
                if (!snapshot.hasPrefix(key)) break;
                String value = snapshot.entries.get(key);
                if (value == null) continue;
                int tokenEnd = tokenEnd(text, end);
                if (!closingSuffix(text, end, tokenEnd)) continue;
                int length = end - start;
                if (length <= bestLength) continue;
                String prefix = text.substring(offset, start);
                String suffix = text.substring(end, tokenEnd);
                best = new Match(tokenEnd, new Token(prefix + value + suffix,
                        prefix.isEmpty() && suffix.isEmpty()));
                bestLength = length;
            }
        }
        return best;
    }

    private static boolean closingSuffix(String text, int start, int end) {
        for (int i = start; i < end; i++) {
            if (".,!?;:)]}»”’\"'\u17d4".indexOf(text.charAt(i)) < 0) return false;
        }
        return true;
    }

    private static int tokenEnd(String text, int start) {
        int end = start;
        while (end < text.length() && !Character.isWhitespace(text.charAt(end))) end++;
        return end;
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
