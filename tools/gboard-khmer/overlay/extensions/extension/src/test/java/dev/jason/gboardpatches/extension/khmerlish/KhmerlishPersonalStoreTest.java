package dev.jason.gboardpatches.extension.khmerlish;

import static org.junit.Assert.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;

import android.content.Context;

import java.io.File;
import java.util.ConcurrentModificationException;
import java.util.LinkedHashMap;
import java.util.Map;

@RunWith(RobolectricTestRunner.class)
@Config(sdk = 33)
public final class KhmerlishPersonalStoreTest {
    @Test public void crudAndImportsArePrivateAndAtomic() throws Exception {
        Context app = RuntimeEnvironment.getApplication();
        assertTrue(KhmerlishPersonalStore.read(app).isEmpty());
        KhmerlishPersonalStore.save(app, null, null, "NV", " នាវា ");
        assertEquals(Map.of("nv", "នាវា"), KhmerlishPersonalStore.read(app));
        KhmerlishPersonalStore.save(app, null, null, "MIN  dg del", "មិនដឹងដែល");
        assertEquals("មិនដឹងដែល", KhmerlishPersonalStore.read(app).get("min dg del"));
        try {
            KhmerlishPersonalStore.save(app, null, null, "min dg del", "ខ្មែរ");
            fail("Normalized phrase duplicates must not overwrite a saved entry");
        } catch (IllegalArgumentException expected) {
            assertEquals("duplicate_key", expected.getMessage());
        }
        KhmerlishPersonalStore.delete(app, "min dg del", "មិនដឹងដែល");
        File database = new File(app.getNoBackupFilesDir(),
                "khmerlish_personal_dictionary_v1.db");
        assertTrue(database.isFile());
        try {
            KhmerlishPersonalStore.save(app, null, null, "nv", "នៅ");
            fail("Duplicate add must not replace a personal entry");
        } catch (IllegalArgumentException expected) {
            assertEquals("duplicate_key", expected.getMessage());
        }
        try {
            KhmerlishPersonalStore.save(app, "nv", "outdated", "nv", "នៅ");
            fail("A stale edit must not overwrite another change");
        } catch (ConcurrentModificationException expected) { }
        assertEquals("នាវា", KhmerlishPersonalStore.read(app).get("nv"));

        Map<String, String> incoming = KhmerlishPersonalData.parse("nv,នឹក\nzztest,សួស្តី\n");
        KhmerlishPersonalStore.Preview first = KhmerlishPersonalStore.preview(app, incoming);
        assertEquals(1, first.added);
        assertEquals(1, first.conflicts);
        KhmerlishPersonalStore.importEntries(app, first, incoming, false);
        assertEquals(Map.of("nv", "នាវា", "zztest", "សួស្តី"), KhmerlishPersonalStore.read(app));
        KhmerlishPersonalStore.Preview second = KhmerlishPersonalStore.preview(app, incoming);
        assertEquals(1, second.conflicts);
        assertEquals(1, second.unchanged);
        KhmerlishPersonalStore.importEntries(app, second, incoming, true);
        assertEquals("នឹក", KhmerlishPersonalStore.read(app).get("nv"));

        KhmerlishPersonalStore.Preview stale = KhmerlishPersonalStore.preview(app, incoming);
        KhmerlishPersonalStore.save(app, "zztest", "សួស្តី", "zztest", "សុខសប្បាយ");
        try {
            KhmerlishPersonalStore.importEntries(app, stale, incoming, true);
            fail("Stale import preview must not replace newer edits");
        } catch (ConcurrentModificationException expected) { }
        assertEquals("សុខសប្បាយ", KhmerlishPersonalStore.read(app).get("zztest"));
        Map<String, String> tampered = new LinkedHashMap<>(incoming);
        KhmerlishPersonalStore.Preview prior = KhmerlishPersonalStore.preview(app, tampered);
        tampered.put("other", "ផ្សេង");
        try {
            KhmerlishPersonalStore.importEntries(app, prior, tampered, true);
            fail("Import must match the previewed file");
        } catch (ConcurrentModificationException expected) { }
        Map<String, String> bad = new LinkedHashMap<>();
        bad.put("valid", "ខ្មែរ");
        bad.put("bad", "English");
        KhmerlishPersonalStore.Preview badPreview = KhmerlishPersonalStore.preview(app, bad);
        try {
            KhmerlishPersonalStore.importEntries(app, badPreview, bad, false);
            fail("Invalid rows must reject the entire transaction");
        } catch (IllegalArgumentException expected) { }
        assertFalse(KhmerlishPersonalStore.read(app).containsKey("valid"));

        KhmerlishPersonalStore.save(app, "zztest", "សុខសប្បាយ", "newword", "សុខសប្បាយ");
        assertFalse(KhmerlishPersonalStore.read(app).containsKey("zztest"));
        try {
            KhmerlishPersonalStore.delete(app, "nv", "outdated");
            fail("Stale delete must not remove a newer entry");
        } catch (ConcurrentModificationException expected) { }
        KhmerlishPersonalStore.delete(app, "nv", "នឹក");
        KhmerlishPersonalStore.delete(app, "newword", "សុខសប្បាយ");
        assertTrue(KhmerlishPersonalStore.read(app).isEmpty());
    }
}
