package app.morphe.extension.instanttranslate;

import org.junit.Test;
import static org.junit.Assert.*;

public class CurrentSettingsClickTest {
    @Test public void callbackReturnsTheReviewedSyntheticUnitSingleton() {
        Object result = new CurrentSettingsClick().invoke();
        assertNotNull(result);
        assertEquals("d1b", result.getClass().getName());
    }
}
