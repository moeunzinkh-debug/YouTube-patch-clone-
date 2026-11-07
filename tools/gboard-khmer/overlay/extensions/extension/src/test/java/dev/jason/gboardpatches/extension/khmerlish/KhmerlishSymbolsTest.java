package dev.jason.gboardpatches.extension.khmerlish;

import static org.junit.Assert.*;

import org.junit.Test;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;

/** Explicit personal symbols must work in both conversion modes without rewriting unrelated text. */
public final class KhmerlishSymbolsTest {
    private KhmerlishDictionary dictionary(Map<String, String> personal) throws Exception {
        KhmerlishDictionary dictionary = KhmerlishDictionary.read(new ByteArrayInputStream(
                "nv\tនៅ\nna\tណា\no\tអូន\nmin\tមិន\n".getBytes(StandardCharsets.UTF_8)));
        dictionary.setPersonal(personal);
        return dictionary;
    }

    @Test public void everyPrintableAsciiSymbolCanBePartOfAPersonalKey() throws Exception {
        String symbols = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~";
        Map<String, String> entries = new LinkedHashMap<>();
        for (char symbol : symbols.toCharArray()) entries.put("a" + symbol + "b", "ពិសេស");
        KhmerlishDictionary d = dictionary(entries);
        for (char symbol : symbols.toCharArray()) {
            String key = "a" + symbol + "b";
            assertEquals("Panel: " + key, "ពិសេស", KhmerlishPanelConverter.convert(key, d));
            assertEquals("Automatic: " + key, "ពិសេស ", type(key + " ", d));
        }
    }

    @Test public void panelSymbolPagesExposePrintableAsciiPunctuation() {
        String available = KhmerlishPanelKeys.PRIMARY + KhmerlishPanelKeys.MORE + ",.";
        assertEquals(26, KhmerlishPanelKeys.PRIMARY.length());
        assertEquals(26, KhmerlishPanelKeys.MORE.length());
        for (char symbol : "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~".toCharArray()) {
            assertTrue("Missing panel key: " + symbol, available.indexOf(symbol) >= 0);
        }
        for (char symbol : "_-+'".toCharArray()) {
            assertTrue("Requested symbol should be on first page: " + symbol,
                    KhmerlishPanelKeys.PRIMARY.indexOf(symbol) >= 0);
        }
    }

    @Test public void symbolOnlyAndLeadingOrTrailingSymbolsAreSupported() throws Exception {
        String symbols = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~";
        Map<String, String> entries = new LinkedHashMap<>();
        for (char symbol : symbols.toCharArray()) {
            entries.put(String.valueOf(symbol), "សញ្ញា");
            entries.put(symbol + "a", "មុខ");
            entries.put("a" + symbol, "ក្រោយ");
        }
        KhmerlishDictionary d = dictionary(entries);
        for (char symbol : symbols.toCharArray()) {
            for (String[] example : new String[][]{
                    {String.valueOf(symbol), "សញ្ញា"}, {symbol + "a", "មុខ"}, {"a" + symbol, "ក្រោយ"}}) {
                assertEquals("Panel: " + example[0], example[1], KhmerlishPanelConverter.convert(example[0], d));
                assertEquals("Automatic: " + example[0], example[1] + " ", type(example[0] + " ", d));
            }
        }
    }

    @Test public void apostropheAndOtherSymbolsWorkWithCaseSpacingAndPunctuation() throws Exception {
        KhmerlishDictionary d = dictionary(Map.of(
                "p'o", "ប្អូន", "p_o", "មិត្ត", "p-o", "ស្រី", "p+o", "ប្រុស"));
        assertEquals("ប្អូន", KhmerlishPanelConverter.convert("P'O", d));
        assertEquals("ប្អូន ", type("P'o ", d));
        assertEquals("ប្អូន!", type("p'o!", d));
        assertEquals("(ប្អូន)!", KhmerlishPanelConverter.convert("(p'o)!", d));
        assertEquals("មិត្តស្រីប្រុស ", type("p_o p-o p+o ", d));
        assertEquals("មិត្តស្រីប្រុស", KhmerlishPanelConverter.convert("p_o p-o p+o", d));
    }

    @Test public void symbolKeysAndLongerPhrasesTakePrecedence() throws Exception {
        KhmerlishDictionary d = dictionary(Map.of(
                "p'o", "ប្អូន", "p'o!", "ប្អូនពិសេស", "p'o min-dg", "ឃ្លាវែង",
                "nv!na", "នៅណាពិសេស"));
        assertEquals("ប្អូនពិសេស", KhmerlishPanelConverter.convert("p'o!", d));
        assertEquals("ប្អូនពិសេស ", type("p'o! ", d));
        assertEquals("ឃ្លាវែង ", type("p'o min-dg ", d));
        assertEquals("(ឃ្លាវែង)!", KhmerlishPanelConverter.convert("(p'o min-dg)!", d));
        assertEquals("នៅណាពិសេស ", type("nv!na ", d));
        assertEquals("នៅណាពិសេស", KhmerlishPanelConverter.convert("nv!na", d));
    }

    @Test public void unfinishedSymbolKeyPreservesOrdinaryPunctuationBehavior() throws Exception {
        KhmerlishDictionary d = dictionary(Map.of("nv!na", "ពិសេស", "nv! na", "ឃ្លា"));
        assertEquals("នៅ! ", type("nv! ", d));
        assertEquals("នៅ! អូន ", type("nv! o ", d));
        assertEquals("ឃ្លា ", type("nv! na ", d));
        assertEquals("នៅ? ", type("nv? ", d));
    }

    @Test public void unicodeAndSymbolOnlyKeysWorkWhenExplicitlySaved() throws Exception {
        KhmerlishDictionary d = dictionary(Map.of("🙂", "ញញឹម", "p€o", "តម្លៃ", "p🙂o", "មិត្ត"));
        for (String[] example : new String[][]{
                {"🙂", "ញញឹម"}, {"p€o", "តម្លៃ"}, {"p🙂o", "មិត្ត"}}) {
            assertEquals(example[1], KhmerlishPanelConverter.convert(example[0], d));
            assertEquals(example[1] + " ", type(example[0] + " ", d));
        }
    }

    @Test public void unrecognizedAddressesAndLongerTokensStayUnchanged() throws Exception {
        KhmerlishDictionary d = dictionary(Map.of("p'o", "ប្អូន", "nv!na", "ពិសេស"));
        assertEquals("p'o@site p'oXYZ foo_kampu ", type("p'o@site p'oXYZ foo_kampu ", d));
        assertEquals("p'o@site p'oXYZ foo_kampu", KhmerlishPanelConverter.convert(
                "p'o@site p'oXYZ foo_kampu", d));
        assertEquals("foo@nv.com ", type("foo@nv.com ", d));
        assertEquals("foo@nv.com", KhmerlishPanelConverter.convert("foo@nv.com", d));
    }

    @Test public void pastedOrModifiedSymbolTokensAreNotRewritten() throws Exception {
        KhmerlishDictionary d = dictionary(Map.of("p'o", "ប្អូន"));
        KhmerlishController c = new KhmerlishController();
        assertNull(c.observe("p'o ", 4, -1, -1, d)); // Pasted with delimiter.
        c.observe("p'o", 3, -1, -1, d);
        assertNull(c.observe("p'x ", 4, -1, -1, d)); // Same-length mutation.
        c.reset();
        c.observe("p'o", 3, 0, 3, d);
        assertNull(c.observe("p'o ", 4, 0, 3, d));
        assertNotNull(c.observe("p'o ", 4, -1, -1, d));
    }

    private String type(String input, KhmerlishDictionary dictionary) {
        KhmerlishController controller = new KhmerlishController();
        StringBuilder editor = new StringBuilder();
        for (int i = 0; i < input.length(); i++) {
            editor.append(input.charAt(i));
            apply(controller, dictionary, editor);
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
