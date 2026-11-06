package dev.jason.gboardpatches.extension.khmerlish;

import static org.junit.Assert.*;
import org.junit.Test;

public class KhmerlishPanelCommitterTest {
    private static final class Editor implements KhmerlishPanelCommitter.Host {
        final StringBuilder text;
        int cursor;
        boolean current = true;
        boolean batch = true;
        boolean failCommit;
        boolean selected;
        int ends;
        Editor(String initial, int cursor) { text = new StringBuilder(initial); this.cursor = cursor; }
        public boolean isCurrent() { return current; }
        public int cursor() { return selected ? -1 : cursor; }
        public CharSequence before(int length) {
            if (length > cursor) return null;
            return text.substring(cursor - length, cursor);
        }
        public boolean begin() { return batch; }
        public boolean deleteBefore(int length) {
            text.delete(cursor - length, cursor); cursor -= length; return true;
        }
        public boolean commit(String value) {
            if (failCommit) { failCommit = false; return false; }
            text.insert(cursor, value); cursor += value.length(); return true;
        }
        public void end() { ends++; }
    }

    @Test public void replacesOnlyPanelOutputAndKeepsSurroundingText() {
        Editor host = new Editor("before after", 6);
        KhmerlishPanelCommitter writer = new KhmerlishPanelCommitter(host);
        assertTrue(writer.replace("n"));
        assertEquals("beforen after", host.text.toString());
        assertTrue(writer.replace("នៅ"));
        assertEquals("beforeនៅ after", host.text.toString());
        assertTrue(writer.replace("នៅណា"));
        assertEquals("beforeនៅណា after", host.text.toString());
        assertTrue(writer.replace(""));
        assertEquals("before after", host.text.toString());
        writer.finish();
    }

    @Test public void refusesChangedCursorSelectionAndText() {
        Editor host = new Editor("prefix", 6);
        KhmerlishPanelCommitter writer = new KhmerlishPanelCommitter(host);
        assertTrue(writer.replace("នៅ"));
        host.cursor = 0;
        assertFalse(writer.replace("នៅណា"));
        assertEquals("prefixនៅ", host.text.toString());
        host.cursor = host.text.length();
        host.selected = true;
        assertFalse(writer.replace("នៅណា"));
        host.selected = false;
        host.text.replace(host.text.length() - 1, host.text.length(), "x");
        assertFalse(writer.replace("នៅណា"));
        assertEquals("prefixនx", host.text.toString());
    }

    @Test public void restoresPreviousOutputAfterFailureAndNeverTouchesNewEditor() {
        Editor host = new Editor("", 0);
        KhmerlishPanelCommitter writer = new KhmerlishPanelCommitter(host);
        assertTrue(writer.replace("នៅ"));
        host.failCommit = true;
        assertFalse(writer.replace("នៅណា"));
        assertEquals("នៅ", host.text.toString());
        host.current = false;
        assertFalse(writer.replace("other"));
        assertEquals("នៅ", host.text.toString());
        assertEquals(2, host.ends);
    }

    @Test public void refusesUnsupportedBatchWithoutDeletingText() {
        Editor host = new Editor("before", 6);
        KhmerlishPanelCommitter writer = new KhmerlishPanelCommitter(host);
        assertTrue(writer.replace("n"));
        host.batch = false;
        assertFalse(writer.replace("នៅ"));
        assertEquals("beforen", host.text.toString());
    }
}
