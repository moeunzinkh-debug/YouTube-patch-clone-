package dev.jason.gboardpatches.extension.khmerlish;

import static org.junit.Assert.*;

import org.junit.Test;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;

public final class KhmerlishPhraseTest {
    private KhmerlishDictionary dictionary(Map<String, String> personal) throws Exception {
        String input = "min\tមិន\ndg\tដឹង\ndel\tដែល\nnv\tនៅ\nna\tណា\n";
        KhmerlishDictionary dictionary = KhmerlishDictionary.read(
                new ByteArrayInputStream(input.getBytes(StandardCharsets.UTF_8)));
        dictionary.setPersonal(personal);
        return dictionary;
    }

    @Test public void panelUsesLongestPersonalPhraseAndKeepsPunctuation() throws Exception {
        KhmerlishDictionary d = dictionary(Map.of("min dg", "ខ្លី", "min dg del", "ឃ្លាពិសេស"));
        assertEquals("ឃ្លាពិសេស", KhmerlishPanelConverter.convert("Min Dg Del", d));
        assertEquals("(ឃ្លាពិសេស)!", KhmerlishPanelConverter.convert("(min dg del)!", d));
        assertEquals("នៅឃ្លាពិសេសណា", KhmerlishPanelConverter.convert("nv min dg del na", d));
        assertEquals("ខ្លី", KhmerlishPanelConverter.convert("min dg", d));
        assertEquals("មិន  ដឹងដែល", KhmerlishPanelConverter.convert("min  dg del", d));
        assertEquals("min@site ដឹង del42", KhmerlishPanelConverter.convert("min@site dg del42", d));
    }

    @Test public void automaticUsesPhraseAfterPreviouslyConvertedWords() throws Exception {
        KhmerlishDictionary d = dictionary(Map.of("min dg del", "ឃ្លាពិសេស"));
        assertEquals("ឃ្លាពិសេស ", type("min dg del ", d));
        assertEquals("ឃ្លាពិសេស!", type("MIN dg Del!", d));
        assertEquals("នៅឃ្លាពិសេសណា ", type("nv min dg del na ", d));
        assertEquals("មិន  ដឹងដែល ", type("min  dg del ", d));
    }

    @Test public void automaticExtendsAnAlreadyConvertedShorterPhrase() throws Exception {
        KhmerlishDictionary d = dictionary(Map.of("min dg", "ខ្លី", "min dg del", "ឃ្លាពិសេស"));
        assertEquals("ខ្លី ", type("min dg ", d));
        assertEquals("ឃ្លាពិសេស ", type("min dg del ", d));
    }

    @Test public void unknownPrefixAndRepeatedCallbacksStillMatch() throws Exception {
        KhmerlishDictionary d = dictionary(Map.of("xyz dg del", "ឃ្លាពិសេស"));
        assertEquals("ឃ្លាពិសេស ", type("xyz dg del ", d));
        assertEquals("xyz@site ដឹងដែល ", type("xyz@site dg del ", d));
    }

    @Test public void overlappingPhrasesPreferTheLongestEligibleSuffix() throws Exception {
        KhmerlishDictionary d = dictionary(Map.of("min dg del na", "វែង", "dg del", "ខ្លី"));
        assertEquals("វែង ", type("min dg del na ", d));
        assertEquals("វែង", KhmerlishPanelConverter.convert("min dg del na", d));
    }

    @Test public void modifiedSameLengthPrefixIsNeverReplacedAsAPhrase() throws Exception {
        KhmerlishDictionary d = dictionary(Map.of("xyz dg", "ឃ្លាពិសេស"));
        KhmerlishController c = new KhmerlishController();
        c.observe("xyz", 3, -1, -1, d);
        assertNull(c.observe("xyz ", 4, -1, -1, d));
        // A host app changed the previously observed suffix without moving the cursor.
        c.observe("abc dg", 6, -1, -1, d);
        KhmerlishController.Edit edit = c.observe("abc dg ", 7, -1, -1, d);
        assertTrue(edit == null || !edit.insert.equals("ឃ្លាពិសេស "));
        if (edit != null) assertTrue(edit.deleteBefore <= 3);
    }

    @Test public void cursorChangesAndChangedPersonalSnapshotsFailClosed() throws Exception {
        Map<String, String> personal = new HashMap<>();
        personal.put("min dg", "ឃ្លាពិសេស");
        KhmerlishDictionary d = dictionary(personal);
        KhmerlishController c = new KhmerlishController();
        c.observe("min", 3, -1, -1, d);
        KhmerlishController.Edit first = c.observe("min ", 4, -1, -1, d);
        assertNotNull(first);
        c.applied(first);
        String next = "មិន dg";
        c.observe(next, next.length(), -1, -1, d);
        // Previously emitted output changed before the delimiter arrived.
        String modified = "ផ្សេង dg ";
        KhmerlishController.Edit changed = c.observe(modified, modified.length(), -1, -1, d);
        assertTrue(changed == null || !changed.insert.equals("ឃ្លាពិសេស "));

        c.reset();
        c.observe("min", 3, -1, -1, d);
        first = c.observe("min ", 4, -1, -1, d);
        c.applied(first);
        d.setPersonal(Map.of("min dg", "ថ្មី"));
        c.observe(next, next.length(), -1, -1, d);
        String committed = next + " ";
        KhmerlishController.Edit afterUpdate = c.observe(committed, committed.length(), -1, -1, d);
        assertTrue(afterUpdate == null || !afterUpdate.insert.equals("ថ្មី "));
    }

    private String type(String input, KhmerlishDictionary dictionary) {
        KhmerlishController controller = new KhmerlishController();
        StringBuilder editor = new StringBuilder();
        for (int i = 0; i < input.length(); i++) {
            editor.append(input.charAt(i));
            apply(controller, dictionary, editor);
            // Some editors report duplicate callbacks after a space or our edit.
            if (editor.length() > 0 && editor.charAt(editor.length() - 1) == ' ') {
                apply(controller, dictionary, editor);
            }
        }
        return editor.toString();
    }

    private void apply(KhmerlishController controller, KhmerlishDictionary dictionary, StringBuilder editor) {
        KhmerlishController.Edit edit = controller.observe(editor, editor.length(), -1, -1, dictionary);
        if (edit != null) {
            editor.delete(editor.length() - edit.deleteBefore, editor.length());
            editor.append(edit.insert);
            controller.applied(edit);
        }
    }
}
