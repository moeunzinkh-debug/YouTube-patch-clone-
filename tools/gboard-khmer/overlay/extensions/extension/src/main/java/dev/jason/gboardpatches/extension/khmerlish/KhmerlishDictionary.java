package dev.jason.gboardpatches.extension.khmerlish;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

/** Offline built-in lookup plus an explicitly managed, in-memory personal overlay. */
final class KhmerlishDictionary {
    private static final int MAX_ENTRIES = 30000;
    private final Map<String, String> words;
    private volatile PersonalSnapshot personal = new PersonalSnapshot(Collections.emptyMap());

    /** Immutable personal entries and prefixes for bounded, longest-phrase matching. */
    static final class PersonalSnapshot {
        final Map<String, String> entries;
        private final Set<String> phrasePrefixes;

        PersonalSnapshot(Map<String, String> values) {
            entries = Collections.unmodifiableMap(new HashMap<>(values));
            Set<String> prefixes = new HashSet<>();
            for (String key : entries.keySet()) {
                for (int space = key.indexOf(' '); space >= 0; space = key.indexOf(' ', space + 1)) {
                    prefixes.add(key.substring(0, space));
                }
            }
            phrasePrefixes = Collections.unmodifiableSet(prefixes);
        }

        boolean hasPhrasePrefix(String key) { return phrasePrefixes.contains(key); }
        String phrase(String key) { return key.indexOf(' ') < 0 ? null : entries.get(key); }
    }

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

    String lookup(String roman) { return lookup(roman, personal); }

    String lookup(String roman, PersonalSnapshot snapshot) {
        if (roman == null) return null;
        String key = roman.toLowerCase(Locale.ROOT);
        String custom = snapshot.entries.get(key);
        return custom != null ? custom : words.get(key);
    }

    PersonalSnapshot personalSnapshot() { return personal; }

    /** Atomic snapshot swap; readers never touch the database while typing. */
    void setPersonal(Map<String, String> values) {
        personal = new PersonalSnapshot(values == null ? Collections.emptyMap() : values);
    }

    Map<String, String> builtInEntries() { return words; }
    int size() { return words.size(); }
}
