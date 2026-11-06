package dev.jason.gboardpatches.extension.khmerlish;

import static org.junit.Assert.*;
import org.junit.Test;

public class KhmerlishPanelBoundsTest {
    @Test public void acceptsOnlyAContainedNonEmptyKeyboardArea() {
        assertTrue(KhmerlishPanelBounds.fits(320, 592, 0, 357, 320, 235));
        assertTrue(KhmerlishPanelBounds.fits(320, 235, 0, 0, 320, 235));
        assertTrue(KhmerlishPanelBounds.fits(500, 300, 40, 30, 300, 200));
        assertFalse(KhmerlishPanelBounds.fits(320, 235, -1, 0, 320, 235));
        assertFalse(KhmerlishPanelBounds.fits(320, 235, 0, 1, 320, 235));
        assertFalse(KhmerlishPanelBounds.fits(320, 235, 1, 0, 320, 235));
    }

    @Test public void rejectsUnmeasuredAndOverflowingAreas() {
        assertFalse(KhmerlishPanelBounds.fits(0, 235, 0, 0, 1, 1));
        assertFalse(KhmerlishPanelBounds.fits(320, 0, 0, 0, 1, 1));
        assertFalse(KhmerlishPanelBounds.fits(320, 235, 0, 0, 0, 1));
        assertFalse(KhmerlishPanelBounds.fits(320, 235, 0, 0, 1, -1));
        assertFalse(KhmerlishPanelBounds.fits(Integer.MAX_VALUE, 235,
                Integer.MAX_VALUE - 10, 0, 100, 100));
    }
}
