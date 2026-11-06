package dev.jason.gboardpatches.extension.khmerlish;

import static org.junit.Assert.*;
import org.junit.Test;

import java.util.Map;
import java.util.TreeMap;

public class KhmerlishWordGuideTest {
    @Test public void searchesRomanOrKhmerAndMarksPersonalOverrides() {
        Map<String, String> builtIn = Map.of("nv", "នៅ", "na", "ណា", "srey", "ស្រី");
        Map<String, String> personal = Map.of("nv", "នាវា", "hello", "សួស្តី");
        KhmerlishWordGuide.Page all = KhmerlishWordGuide.search(builtIn, personal, "", false, 0);
        assertEquals(4, all.total);
        assertEquals("hello", all.entries.get(0).roman);
        assertTrue(all.entries.get(0).personal);
        KhmerlishWordGuide.Page override = KhmerlishWordGuide.search(builtIn, personal, "NV", false, 0);
        assertEquals(1, override.total);
        assertEquals("នាវា", override.entries.get(0).khmer);
        assertTrue(override.entries.get(0).personal);
        KhmerlishWordGuide.Page byKhmer = KhmerlishWordGuide.search(builtIn, personal, "ណា", false, 0);
        assertEquals("na", byKhmer.entries.get(0).roman);
        assertFalse(byKhmer.entries.get(0).personal);
        assertEquals(2, KhmerlishWordGuide.search(builtIn, personal, "", true, 0).total);
    }

    @Test public void paginatesAndClampsWithoutDroppingEntries() {
        Map<String, String> builtIn = new TreeMap<>();
        for (int i = 0; i < 85; i++) builtIn.put(String.format("key%03d", i), "ខ្មែរ");
        KhmerlishWordGuide.Page first = KhmerlishWordGuide.search(builtIn, Map.of(), "", false, -1);
        KhmerlishWordGuide.Page last = KhmerlishWordGuide.search(builtIn, Map.of(), "", false, 999);
        assertEquals(85, first.total);
        assertEquals(3, first.pages);
        assertEquals(40, first.entries.size());
        assertEquals(2, last.index);
        assertEquals(5, last.entries.size());
        assertEquals("key084", last.entries.get(4).roman);
        KhmerlishWordGuide.Page empty = KhmerlishWordGuide.search(builtIn, Map.of(), "no-match", false, 5);
        assertEquals(0, empty.total);
        assertEquals(0, empty.index);
        assertEquals(1, empty.pages);
        assertTrue(empty.entries.isEmpty());
    }
}
