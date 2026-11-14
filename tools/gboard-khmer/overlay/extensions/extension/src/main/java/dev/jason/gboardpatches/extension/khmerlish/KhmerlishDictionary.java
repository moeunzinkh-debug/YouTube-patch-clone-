package dev.jason.gboardpatches.extension.khmerlish;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;

/** Offline built-in lookup plus an explicitly managed, in-memory personal overlay. */
final class KhmerlishDictionary {
    private static final int MAX_ENTRIES = 30000;
    private static final int MAX_PREDICTIONS = 10000;
    private final Map<String, String> words;
    private final TreeMap<String, String> orderedWords;
    private final Map<String, List<String>> predictions;
    private volatile PersonalSnapshot personal = new PersonalSnapshot(Collections.emptyMap());

    /** Immutable personal entries and prefixes for bounded, longest-phrase matching. */
    static final class PersonalSnapshot {
        final Map<String, String> entries;
        private final Set<String> phrasePrefixes;
        // Sorted keys permit bounded prefix checks without retaining host text
        // or allocating every character-level prefix of up to 5,000 entries.
        private final TreeMap<String, String> ordered;

        PersonalSnapshot(Map<String, String> values) {
            entries = Collections.unmodifiableMap(new HashMap<>(values));
            ordered = new TreeMap<>(entries);
            Set<String> prefixes = new HashSet<>();
            for (String key : entries.keySet()) {
                for (int space = key.indexOf(' '); space >= 0; space = key.indexOf(' ', space + 1)) {
                    prefixes.add(key.substring(0, space));
                }
            }
            phrasePrefixes = Collections.unmodifiableSet(prefixes);
        }

        boolean hasPhrasePrefix(String key) { return phrasePrefixes.contains(key); }
        boolean hasPrefix(String key) {
            if (key == null || key.isEmpty() || key.length() > KhmerlishPersonalData.MAX_ROMAN) return false;
            String next = ordered.ceilingKey(key);
            return next != null && next.startsWith(key);
        }
        String phrase(String key) { return key.indexOf(' ') < 0 ? null : entries.get(key); }
    }

    private KhmerlishDictionary(Map<String, String> words, Map<String, List<String>> predictions) {
        this.words = Collections.unmodifiableMap(words);
        orderedWords = new TreeMap<>(words);
        Map<String, List<String>> immutable = new HashMap<>();
        for (Map.Entry<String, List<String>> entry : predictions.entrySet()) {
            immutable.put(entry.getKey(), Collections.unmodifiableList(new ArrayList<>(entry.getValue())));
        }
        this.predictions = Collections.unmodifiableMap(immutable);
    }

    static KhmerlishDictionary read(InputStream input) throws IOException {
        return read(input, null);
    }

    static KhmerlishDictionary read(InputStream input, InputStream predictionInput) throws IOException {
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
        Map<String, List<String>> predictions = new HashMap<>();
        if (predictionInput != null) readPredictions(predictionInput, predictions);
        return new KhmerlishDictionary(words, predictions);
    }

    private static void readPredictions(InputStream input,
            Map<String, List<String>> predictions) throws IOException {
        int count = 0;
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(input, StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                int tab = line.indexOf('\t');
                if (tab <= 0 || tab != line.lastIndexOf('\t') || tab > 32
                        || tab == line.length() - 1 || count++ >= MAX_PREDICTIONS) {
                    throw new IOException("Invalid Khmerlish predictions");
                }
                String key = line.substring(0, tab);
                for (int i = 0; i < key.length(); i++) {
                    if (key.charAt(i) < 'a' || key.charAt(i) > 'z') {
                        throw new IOException("Invalid Khmerlish prediction key");
                    }
                }
                String value = line.substring(tab + 1);
                List<String> values = predictions.computeIfAbsent(key, unused -> new ArrayList<>());
                if (values.contains(value)) throw new IOException("Duplicate Khmerlish prediction");
                values.add(value);
            }
        }
    }

    String lookup(String roman) { return lookup(roman, personal); }

    String lookup(String roman, PersonalSnapshot snapshot) {
        if (roman == null) return null;
        String key = roman.toLowerCase(Locale.ROOT);
        String custom = snapshot.entries.get(key);
        return custom != null ? custom : words.get(key);
    }

    /**
     * Returns distinct offline candidates for the current Roman prefix. Personal
     * entries are ranked first, followed by curated alternatives and bundled words.
     */
    List<String> suggest(String romanPrefix, int limit) {
        if (romanPrefix == null || limit <= 0) return Collections.emptyList();
        String prefix = romanPrefix.toLowerCase(Locale.ROOT);
        if (prefix.isEmpty() || prefix.length() > KhmerlishPersonalData.MAX_ROMAN) {
            return Collections.emptyList();
        }
        PersonalSnapshot snapshot = personal;
        LinkedHashSet<String> result = new LinkedHashSet<>();
        add(result, snapshot.entries.get(prefix), limit);
        List<String> curated = predictions.get(prefix);
        if (curated != null) {
            for (String value : curated) add(result, value, limit);
        }
        add(result, words.get(prefix), limit);
        addPrefixValues(result, snapshot.ordered, prefix, limit);
        addPrefixValues(result, orderedWords, prefix, limit);
        return Collections.unmodifiableList(new ArrayList<>(result));
    }

    private static void addPrefixValues(LinkedHashSet<String> result,
            TreeMap<String, String> source, String prefix, int limit) {
        for (Map.Entry<String, String> entry : source.tailMap(prefix, true).entrySet()) {
            if (!entry.getKey().startsWith(prefix) || result.size() >= limit) break;
            add(result, entry.getValue(), limit);
        }
    }

    private static void add(LinkedHashSet<String> result, String value, int limit) {
        if (value != null && !value.isEmpty() && result.size() < limit) result.add(value);
    }

    PersonalSnapshot personalSnapshot() { return personal; }

    /** Atomic snapshot swap; readers never touch the database while typing. */
    void setPersonal(Map<String, String> values) {
        personal = new PersonalSnapshot(values == null ? Collections.emptyMap() : values);
    }

    Map<String, String> builtInEntries() { return words; }
    int size() { return words.size(); }
}
