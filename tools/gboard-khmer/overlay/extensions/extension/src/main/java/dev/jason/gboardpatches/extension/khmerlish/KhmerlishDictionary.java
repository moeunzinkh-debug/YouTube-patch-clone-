package dev.jason.gboardpatches.extension.khmerlish;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

/** Immutable exact-match dictionary. No text is logged, stored or sent over the network. */
final class KhmerlishDictionary {
    private static final int MAX_ENTRIES = 30000;
    private final Map<String, String> words;

    private KhmerlishDictionary(Map<String, String> words) {
        this.words = Collections.unmodifiableMap(words);
    }

    static KhmerlishDictionary read(InputStream input) throws IOException {
        Map<String, String> words = new HashMap<>();
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(input, StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                int tab = line.indexOf('\t');
                if (tab <= 0 || tab != line.lastIndexOf('\t') || tab > 32
                        || tab == line.length() - 1 || words.size() >= MAX_ENTRIES) {
                    throw new IOException("Invalid Khmerlish dictionary");
                }
                String key = line.substring(0, tab);
                for (int i = 0; i < key.length(); i++) {
                    if (key.charAt(i) < 'a' || key.charAt(i) > 'z') {
                        throw new IOException("Invalid Khmerlish dictionary key");
                    }
                }
                if (words.put(key, line.substring(tab + 1)) != null) {
                    throw new IOException("Duplicate Khmerlish dictionary key");
                }
            }
        }
        if (words.isEmpty()) throw new IOException("Empty Khmerlish dictionary");
        return new KhmerlishDictionary(words);
    }

    String lookup(String roman) {
        return words.get(roman.toLowerCase(Locale.ROOT));
    }

    int size() { return words.size(); }
}
