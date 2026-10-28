package dev.jason.gboardpatches.extension.directtranslate;

import org.junit.Assume;
import org.junit.Test;

import static org.junit.Assert.assertFalse;

/** Opt-in integration probe: fixed synthetic text only, never keyboard input. */
public class GtxLiveProbeTest {
    @Test public void syntheticPostBothDirectionsAndAuto() throws Exception {
        Assume.assumeTrue("1".equals(System.getenv("GBOARD_DIRECT_LIVE_PROBE")));
        GtxClient client = new GtxClient();
        assertFalse(client.translate("Hello world", "en", "km").text.isEmpty());
        assertFalse(client.translate("សួស្តី", "km", "en").text.isEmpty());
        assertFalse(client.translate("How are you?", "auto", "km").text.isEmpty());
    }
}
