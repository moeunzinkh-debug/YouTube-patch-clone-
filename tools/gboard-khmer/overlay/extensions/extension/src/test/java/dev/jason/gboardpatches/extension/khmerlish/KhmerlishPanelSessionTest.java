package dev.jason.gboardpatches.extension.khmerlish;

import static org.junit.Assert.*;
import org.junit.Test;
import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

public class KhmerlishPanelSessionTest {
    private KhmerlishDictionary dictionary() throws Exception {
        return KhmerlishDictionary.read(new ByteArrayInputStream(
                "nv\tនៅ\nna\tណា\n".getBytes(StandardCharsets.UTF_8)));
    }

    static final class Output implements KhmerlishPanelSession.Output {
        boolean current = true;
        boolean available = true;
        int finishes;
        List<String> writes = new ArrayList<>();
        public boolean isCurrent() { return current; }
        public boolean replace(String text) { writes.add(text); return available; }
        public void finish() { finishes++; }
    }

    @Test public void updatesAndDeletesInPlaceThenCommitsOnce() throws Exception {
        Output out = new Output();
        KhmerlishPanelSession session = new KhmerlishPanelSession(dictionary(), out);
        assertTrue(session.update("nv"));
        assertTrue(session.update("nv na"));
        assertTrue(session.update("nv n"));
        assertTrue(session.update(""));
        assertEquals(List.of("នៅ", "នៅណា", "នៅ n", ""), out.writes);
        session.close();
        session.close();
        assertEquals(1, out.finishes);
        assertFalse(session.update("nv"));
    }

    @Test public void neverWritesIntoANewEditor() throws Exception {
        Output out = new Output();
        KhmerlishPanelSession session = new KhmerlishPanelSession(dictionary(), out);
        assertTrue(session.update("nv"));
        out.current = false;
        assertFalse(session.update("nv na"));
        assertEquals(List.of("នៅ"), out.writes);
        assertEquals(0, out.finishes);
    }

    @Test public void closesIfHostRejectsComposition() throws Exception {
        Output out = new Output();
        KhmerlishPanelSession session = new KhmerlishPanelSession(dictionary(), out);
        assertTrue(session.update("nv"));
        out.available = false;
        assertFalse(session.update("nv na"));
        assertEquals(1, out.finishes);
        assertFalse(session.update("nv"));
    }
}
