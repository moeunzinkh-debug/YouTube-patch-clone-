package app.morphe.extension.instanttranslate;

import org.junit.Test;
import java.io.IOException;
import java.util.concurrent.atomic.AtomicInteger;
import static org.junit.Assert.*;

public class ProviderRouterTest {
    @Test public void selectsOneProviderAndNeverSilentlyFallsBackToAnother() throws Exception {
        String[] selection = {ProviderRouter.GOOGLE};
        AtomicInteger googleCalls = new AtomicInteger();
        AtomicInteger seaCalls = new AtomicInteger();
        ProviderRouter router = new ProviderRouter(() -> selection[0], (text, from, to) -> {
            googleCalls.incrementAndGet(); return "google";
        }, (text, from, to) -> {
            seaCalls.incrementAndGet(); throw new IOException("unavailable");
        });
        assertEquals("google", router.translate("hola", "es", "en"));
        selection[0] = ProviderRouter.SEA_LION;
        assertThrows(IOException.class, () -> router.translate("hola", "es", "en"));
        assertEquals(1, googleCalls.get());
        assertEquals(1, seaCalls.get());
        selection[0] = ProviderRouter.ORIGINAL;
        assertThrows(IOException.class, () -> router.translate("hola", "es", "en"));
        selection[0] = "unknown";
        assertThrows(IOException.class, () -> router.translate("hola", "es", "en"));
        assertEquals(1, googleCalls.get());
        assertEquals(1, seaCalls.get());
    }
}
