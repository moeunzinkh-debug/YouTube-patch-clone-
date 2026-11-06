package dev.jason.gboardpatches.extension.khmerlish;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.TreeMap;

/** Deterministic offline guide with bounded pages and personal precedence. */
final class KhmerlishWordGuide {
    static final int PAGE_SIZE = 40;

    private KhmerlishWordGuide() {}

    static final class Entry {
        final String roman;
        final String khmer;
        final boolean personal;
        Entry(String roman, String khmer, boolean personal) {
            this.roman = roman;
            this.khmer = khmer;
            this.personal = personal;
        }
    }

    static final class Page {
        final List<Entry> entries;
        final int total;
        final int index;
        final int pages;
        Page(List<Entry> entries, int total, int index, int pages) {
            this.entries = Collections.unmodifiableList(entries);
            this.total = total;
            this.index = index;
            this.pages = pages;
        }
    }

    static Page search(Map<String, String> builtIn, Map<String, String> personal,
            String query, boolean personalOnly, int requestedPage) {
        if (personal == null) personal = Collections.emptyMap();
        TreeMap<String, String> combined = new TreeMap<>();
        if (!personalOnly && builtIn != null) combined.putAll(builtIn);
        combined.putAll(personal);
        String filter = query == null ? "" : query.trim().toLowerCase(Locale.ROOT);
        if (filter.length() > 128) filter = filter.substring(0, 128);
        List<Entry> matches = new ArrayList<>();
        for (Map.Entry<String, String> entry : combined.entrySet()) {
            if (filter.isEmpty() || entry.getKey().contains(filter)
                    || entry.getValue().toLowerCase(Locale.ROOT).contains(filter)) {
                matches.add(new Entry(entry.getKey(), entry.getValue(), personal.containsKey(entry.getKey())));
            }
        }
        int total = matches.size();
        int pages = Math.max(1, (total + PAGE_SIZE - 1) / PAGE_SIZE);
        int index = Math.max(0, Math.min(requestedPage, pages - 1));
        int start = index * PAGE_SIZE;
        return new Page(new ArrayList<>(matches.subList(start, Math.min(start + PAGE_SIZE, total))),
                total, index, pages);
    }
}
