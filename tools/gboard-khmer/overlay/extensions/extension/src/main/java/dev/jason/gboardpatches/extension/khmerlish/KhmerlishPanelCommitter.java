package dev.jason.gboardpatches.extension.khmerlish;

/**
 * Replace only this panel's own last output in a host editor. Some Gboard
 * versions finish composing spans during selection callbacks, so a composing
 * span alone is not a reliable anchor. The cursor and exact previous suffix
 * must still match before any deletion; a mismatch stops the session.
 */
final class KhmerlishPanelCommitter implements KhmerlishPanelSession.Output {
    interface Host {
        boolean isCurrent();
        /** Collapsed absolute cursor position, or -1 for a selection/unknown cursor. */
        int cursor();
        CharSequence before(int length);
        boolean begin();
        boolean deleteBefore(int length);
        boolean commit(String text);
        void end();
    }

    private final Host host;
    private String previous = "";
    private int origin = -1;
    private int expectedCursor = -1;

    KhmerlishPanelCommitter(Host host) {
        if (host == null) throw new IllegalArgumentException();
        this.host = host;
    }

    @Override public boolean isCurrent() { return host.isCurrent(); }

    @Override public boolean replace(String next) {
        if (next == null || next.length() > 32768 || !host.isCurrent()) return false;
        int cursor = host.cursor();
        if (cursor < 0) return false;
        if (origin < 0) {
            origin = cursor;
            expectedCursor = cursor;
        }
        if (cursor != expectedCursor) return false;
        if (!previous.isEmpty()) {
            CharSequence actual = host.before(previous.length());
            if (actual == null || !previous.contentEquals(actual)) return false;
        }
        if (previous.equals(next)) return true;
        if ((long) origin + next.length() > Integer.MAX_VALUE || !host.begin()) return false;
        boolean deleted = false;
        try {
            if (!previous.isEmpty()) {
                if (!host.deleteBefore(previous.length())) return false;
                deleted = true;
            }
            if (!next.isEmpty() && !host.commit(next)) return false;
            deleted = false;
            previous = next;
            expectedCursor = origin + next.length();
            return true;
        } finally {
            // Some editors implement InputConnection incompletely. Restore the
            // exact text we removed if insertion fails, on a best-effort basis.
            if (deleted) {
                try { host.commit(previous); } catch (Throwable ignored) {}
            }
            try { host.end(); } catch (Throwable ignored) {}
        }
    }

    /** Output is already committed as it is displayed. */
    @Override public void finish() {}
}
