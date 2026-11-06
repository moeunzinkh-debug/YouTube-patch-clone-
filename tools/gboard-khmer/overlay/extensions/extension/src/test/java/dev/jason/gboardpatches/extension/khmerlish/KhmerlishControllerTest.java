package dev.jason.gboardpatches.extension.khmerlish;

import org.junit.Assert;
import org.junit.Before;
import org.junit.Test;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public final class KhmerlishControllerTest {
    private KhmerlishDictionary dictionary;

    @Before public void loadDictionary() throws IOException {
        Path path = Path.of("..", "..", "patches", "src", "main", "resources",
                "gboard-khmer", "dictionary.tsv");
        if (!Files.exists(path)) {
            path = Path.of("patches", "src", "main", "resources", "gboard-khmer", "dictionary.tsv");
        }
        dictionary = KhmerlishDictionary.read(Files.newInputStream(path));
        Assert.assertTrue(dictionary.size() > 24000);
    }

    @Test public void requestedExamplesConvertOnWordBoundary() {
        Assert.assertEquals("នៅណា ", type("nv na "));
        Assert.assertEquals("កម្ពុជា ", type("Kampuchea "));
        Assert.assertEquals("កម្ពុជា ", type("kampu "));
        Assert.assertEquals("អ្នកណា ", type("nak na "));
        Assert.assertEquals("ស្រីស្អាត ", type("srey sart "));
        Assert.assertEquals("នឹកអូន ", type("Nik o "));
    }

    @Test public void casingAndPunctuationAreHandled() {
        Assert.assertEquals("កម្ពុជា!", type("KAMPU!"));
        Assert.assertEquals("នៅណា, ខ្មែរ!", type("nv na, khmer!"));
        Assert.assertEquals("ស្រឡាញ់ ", type("srolanh "));
    }

    @Test public void gboardCapitalizationAtCommitStillMatchesObservedSpelling() {
        KhmerlishController controller = new KhmerlishController();
        controller.observe("nv", 2, 0, 2, dictionary);
        KhmerlishController.Edit edit = controller.observe("NV ", 3, -1, -1, dictionary);
        Assert.assertNotNull(edit);
        Assert.assertEquals("នៅ ", edit.insert);

        controller.reset();
        controller.observe("nik", 3, 0, 3, dictionary);
        edit = controller.observe("Nik ", 4, -1, -1, dictionary);
        Assert.assertNotNull(edit);
        Assert.assertEquals("នឹក ", edit.insert);

        controller.reset();
        controller.observe("srey", 4, 0, 4, dictionary);
        Assert.assertNull(controller.observe("sorry ", 6, -1, -1, dictionary));
    }

    @Test public void unknownAndAmbiguousWordsRemainLatin() {
        Assert.assertEquals("zzzzzz ", type("zzzzzz "));
        Assert.assertEquals("som ", type("som "));
        Assert.assertEquals("a i ", type("a i "));
        Assert.assertEquals("នៅ zzzzzz ណា ", type("nv zzzzzz na "));
    }

    @Test public void urlAndIdentifiersAreNotPartiallyConverted() {
        Assert.assertEquals("foo@kampu.com ", type("foo@kampu.com "));
        Assert.assertEquals("https://kampu ", type("https://kampu "));
        Assert.assertEquals("123kampu ", type("123kampu "));
        Assert.assertEquals("foo_kampu ", type("foo_kampu "));
    }

    @Test public void pastedCompletedWordAndStaleCallbackAreNotRewritten() {
        KhmerlishController c = new KhmerlishController();
        Assert.assertNull(c.observe("nv ", 3, -1, -1, dictionary));
        c.observe("nv", 2, 0, 2, dictionary);
        Assert.assertNull(c.observe("na ", 3, -1, -1, dictionary));
    }

    @Test public void activeComposingRegionIsNeverModified() {
        KhmerlishController c = new KhmerlishController();
        c.observe("nv", 2, 0, 2, dictionary);
        Assert.assertNull(c.observe("nv ", 3, 0, 2, dictionary));
        Assert.assertNotNull(c.observe("nv ", 3, -1, -1, dictionary));
    }

    @Test public void doesNotJoinAcrossManualSpacingOrUnrelatedText() {
        Assert.assertEquals("នៅ  ណា ", type("nv  na "));
        Assert.assertEquals("នៅ. ណា ", type("nv. na "));
    }

    private String type(String input) {
        KhmerlishController controller = new KhmerlishController();
        StringBuilder editor = new StringBuilder();
        for (int i = 0; i < input.length(); i++) {
            char c = input.charAt(i);
            editor.append(c);
            KhmerlishController.Edit edit = controller.observe(
                    editor, editor.length(), -1, -1, dictionary);
            if (edit != null) {
                editor.delete(editor.length() - edit.deleteBefore, editor.length());
                editor.append(edit.insert);
                controller.applied(edit);
                // A real editor reports the new cursor after our batched change.
                controller.observe(editor, editor.length(), -1, -1, dictionary);
            }
        }
        return editor.toString();
    }
}
