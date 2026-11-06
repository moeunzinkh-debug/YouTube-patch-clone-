package dev.jason.gboardpatches.extension.khmerlish;

/** Pure, bounded conversion for the explicitly opened Khmerlish panel. */
final class KhmerlishPanelConverter {
    static final int MAX_LENGTH = 8192;

    private KhmerlishPanelConverter() {}

    /**
     * Exact known words are converted as they are typed. Adjacent converted
     * words separated by one space are joined, as in the Khmer examples.
     * Unknown words and URL/email/code-like tokens are preserved unchanged.
     */
    static String convert(CharSequence input, KhmerlishDictionary dictionary) {
        if (input == null) return "";
        String text = input.toString();
        if (dictionary == null || text.length() > MAX_LENGTH) return text;
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
            int end = offset + 1;
            while (end < text.length() && !Character.isWhitespace(text.charAt(end))) end++;
            String token = text.substring(offset, end);
            Token converted = convertToken(token, dictionary);
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

    private static Token convertToken(String token, KhmerlishDictionary dictionary) {
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
            String replacement = dictionary.lookup(original);
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

    private static final class Token {
        final String text;
        final boolean pureConverted;
        Token(String text, boolean pureConverted) {
            this.text = text;
            this.pureConverted = pureConverted;
        }
    }
}
