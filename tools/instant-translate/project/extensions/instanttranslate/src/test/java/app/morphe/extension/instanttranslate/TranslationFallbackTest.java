package app.morphe.extension.instanttranslate;

import org.junit.Test;
import static org.junit.Assert.*;

public class TranslationFallbackTest {
    @Test public void readsOnlyReviewedCurrentCoroutineFields() throws Exception {
        Object token = Class.forName("fra").getDeclaredConstructor().newInstance();
        token.getClass().getField("t").set(token, "sample");
        token.getClass().getField("u").set(token, "en");
        token.getClass().getField("v").set(token, "km");
        assertArrayEquals(new String[] {"sample", "en", "km"}, TranslationFallback.readSingleRequest(token));
        assertNull(TranslationFallback.readSingleRequest(null));
        assertNull(TranslationFallback.readSingleRequest(new Object()));
    }
}
