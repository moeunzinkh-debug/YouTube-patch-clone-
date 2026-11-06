package dev.jason.gboardpatches.extension.khmerlish;

import static org.junit.Assert.assertEquals;

import org.junit.Test;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;

public class KhmerlishPanelConverterTest {
    private KhmerlishDictionary dictionary() throws Exception {
        String entries = "nv\tនៅ\nna\tណា\nkampuchea\tកម្ពុជា\nkampu\tកម្ពុជា\n"
                + "nak\tអ្នក\nsrey\tស្រី\nsart\tស្អាត\nnik\tនឹក\no\tអូន\n";
        return KhmerlishDictionary.read(new ByteArrayInputStream(entries.getBytes(StandardCharsets.UTF_8)));
    }

    @Test public void convertsRequiredExamplesLiveAndIgnoringCase() throws Exception {
        KhmerlishDictionary d = dictionary();
        assertEquals("នៅណា", KhmerlishPanelConverter.convert("nv na", d));
        assertEquals("កម្ពុជា", KhmerlishPanelConverter.convert("Kampuchea", d));
        assertEquals("កម្ពុជា", KhmerlishPanelConverter.convert("kampu", d));
        assertEquals("អ្នកណា", KhmerlishPanelConverter.convert("nak na", d));
        assertEquals("ស្រីស្អាត", KhmerlishPanelConverter.convert("srey sart", d));
        assertEquals("នឹកអូន", KhmerlishPanelConverter.convert("Nik o", d));
        assertEquals("នៅ n", KhmerlishPanelConverter.convert("nv n", d));
    }

    @Test public void keepsPunctuationSpacingAndUnknownWords() throws Exception {
        KhmerlishDictionary d = dictionary();
        assertEquals("នៅ, ណា!", KhmerlishPanelConverter.convert("nv, na!", d));
        assertEquals("  នៅ  ណា\nunknown", KhmerlishPanelConverter.convert("  nv  na\nunknown", d));
        assertEquals("នៅ unknown ណា", KhmerlishPanelConverter.convert("nv unknown na", d));
        assertEquals("នៅ ", KhmerlishPanelConverter.convert("nv ", d));
        assertEquals("", KhmerlishPanelConverter.convert("", d));
    }

    @Test public void leavesAddressesNumbersAndCodeUntouched() throws Exception {
        KhmerlishDictionary d = dictionary();
        assertEquals("nv@na.com nv.na kampu_test nv42 https://na", KhmerlishPanelConverter.convert(
                "nv@na.com nv.na kampu_test nv42 https://na", d));
    }

    @Test public void missingDictionaryAndOversizeFailClosed() throws Exception {
        assertEquals("nv na", KhmerlishPanelConverter.convert("nv na", null));
        String text = "n".repeat(KhmerlishPanelConverter.MAX_LENGTH + 1);
        assertEquals(text, KhmerlishPanelConverter.convert(text, dictionary()));
    }
}
