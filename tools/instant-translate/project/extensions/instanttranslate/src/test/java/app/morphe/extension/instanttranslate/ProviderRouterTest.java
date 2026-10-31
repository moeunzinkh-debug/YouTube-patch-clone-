package app.morphe.extension.instanttranslate;

import org.junit.Test;
import java.io.IOException;
import java.util.concurrent.atomic.AtomicInteger;
import static org.junit.Assert.*;

public class ProviderRouterTest {
    @Test public void routesOnlyExplicitSeaLionAndFailsClosedForLegacySelection() throws Exception {
        String[] selection = {ProviderRouter.ORIGINAL};
        AtomicInteger calls = new AtomicInteger();
        ProviderRouter router = new ProviderRouter(() -> selection[0], (text, from, to) -> {
            calls.incrementAndGet(); return "mock-sealion";
        });
        for (String disabled : new String[] {ProviderRouter.ORIGINAL, "google", "unknown", "", null}) {
            assertEquals(ProviderRouter.ORIGINAL, ProviderRouter.normalizeSelection(disabled));
            selection[0] = disabled;
            assertThrows(IOException.class, () -> router.translate("hola", "es", "en"));
        }
        assertEquals(ProviderRouter.ORIGINAL, ProviderSettings.selected());
        assertEquals(ProviderRouter.SEA_LION, ProviderRouter.normalizeSelection(ProviderRouter.SEA_LION));
        assertEquals(0, calls.get());
        selection[0] = ProviderRouter.SEA_LION;
        assertEquals("mock-sealion", router.translate("hola", "es", "en"));
        assertEquals(1, calls.get());
    }

    @Test public void providerFailuresDoNotSelectAnotherProvider() {
        AtomicInteger calls = new AtomicInteger();
        ProviderRouter router = new ProviderRouter(() -> ProviderRouter.SEA_LION, (text, from, to) -> {
            calls.incrementAndGet(); throw new IOException("unavailable");
        });
        assertThrows(IOException.class, () -> router.translate("hola", "es", "en"));
        assertEquals(1, calls.get());
    }
}
