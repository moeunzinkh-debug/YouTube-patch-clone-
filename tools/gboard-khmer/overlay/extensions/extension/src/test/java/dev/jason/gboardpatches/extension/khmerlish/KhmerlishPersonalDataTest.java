package dev.jason.gboardpatches.extension.khmerlish;

import static org.junit.Assert.*;
import org.junit.Test;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;

public class KhmerlishPersonalDataTest {
    @Test public void validatesKeysAndKhmerWithoutAcceptingUnsafeSeparators() {
        assertEquals("soksabay", KhmerlishPersonalData.roman(" SokSabAy "));
        assertEquals("a", KhmerlishPersonalData.roman("A"));
        assertNull(KhmerlishPersonalData.roman("nv na"));
        assertNull(KhmerlishPersonalData.roman("word42"));
        assertNull(KhmerlishPersonalData.roman("x".repeat(33)));
        assertEquals("សួស្តី", KhmerlishPersonalData.khmer(" សួស្តី "));
        assertEquals("សួស្តី, មិត្ត", KhmerlishPersonalData.khmer("សួស្តី, មិត្ត"));
        assertNull(KhmerlishPersonalData.khmer("hello"));
        assertNull(KhmerlishPersonalData.khmer("សួស្តី\nលាក់"));
        assertNull(KhmerlishPersonalData.khmer("ខ្មែរ\tផ្សេង"));
        assertNull(KhmerlishPersonalData.khmer("ខ្មែរ" + '\ud800'));
    }

    @Test public void importsUtf8TsvCsvQuotedFieldsAndRoundTrips() throws Exception {
        String input = "\ufeff# Personal pairs\nkhmerlish,khmer\n"
                + "Soksabay,សុខសប្បាយ\n"
                + "\"srey\",\"ស្រី, ស្អាត\"\n"
                + "\"friend\",\"មិត្ត \"\"ស្អាត\"\"\"\n"
                + "nv\tនៅ\n";
        Map<String, String> entries = KhmerlishPersonalData.parse(input);
        assertEquals(4, entries.size());
        assertEquals("សុខសប្បាយ", entries.get("soksabay"));
        assertEquals("ស្រី, ស្អាត", entries.get("srey"));
        assertEquals("មិត្ត \"ស្អាត\"", entries.get("friend"));
        assertEquals(entries, KhmerlishPersonalData.parse(KhmerlishPersonalData.exportTsv(entries)));
    }

    @Test public void invalidImportRejectsAllRowsAndDoesNotRevealContent() throws Exception {
        for (String invalid : new String[]{"", "roman,khmer\n", "nv,នៅ\nNA,english\n",
                "nv,នៅ\nNV,ណា\n", "two words,ខ្មែរ\n", "nv,នៅ,ណា\n",
                "nv,\"នៅ\n", "nv,នៅ\u0000\n", "a,ខ្មែរ\rផ្សេង"}) {
            try {
                KhmerlishPersonalData.parse(invalid);
                fail("Expected invalid dictionary file");
            } catch (KhmerlishPersonalData.ImportException expected) {
                assertFalse(expected.getMessage().contains("នៅ"));
            }
        }
        try {
            KhmerlishPersonalData.parse("x".repeat(KhmerlishPersonalData.MAX_IMPORT_CHARS + 1));
            fail("Expected size rejection");
        } catch (KhmerlishPersonalData.ImportException expected) {
            assertEquals(0, expected.line);
        }
    }

    @Test public void personalOverrideFeedsBothPanelAndAutomaticController() throws Exception {
        KhmerlishDictionary dictionary = KhmerlishDictionary.read(new ByteArrayInputStream(
                "nv\tនៅ\nna\tណា\n".getBytes(StandardCharsets.UTF_8)));
        Map<String, String> custom = new LinkedHashMap<>();
        custom.put("nv", "នាវា");
        custom.put("hello", "សួស្តី");
        dictionary.setPersonal(custom);
        custom.put("nv", "ប្ដូរ"); // Published snapshots cannot be mutated by the caller.
        assertEquals("នាវា", dictionary.lookup("NV"));
        assertEquals("សួស្តីណា", KhmerlishPanelConverter.convert("hello na", dictionary));
        KhmerlishController controller = new KhmerlishController();
        controller.observe("nv", 2, -1, -1, dictionary);
        KhmerlishController.Edit edit = controller.observe("nv ", 3, -1, -1, dictionary);
        assertNotNull(edit);
        assertEquals("នាវា ", edit.insert);
        dictionary.setPersonal(Map.of());
        assertEquals("នៅ", dictionary.lookup("nv"));
        assertNull(dictionary.lookup("hello"));
    }
}
