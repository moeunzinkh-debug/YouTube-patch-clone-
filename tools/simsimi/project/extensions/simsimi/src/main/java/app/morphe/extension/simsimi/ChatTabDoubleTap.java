package app.morphe.extension.simsimi;

/** A non-consuming double-tap detector for SimSimi's already-selected Chat tab. */
public final class ChatTabDoubleTap {
    static final int CHAT_INDEX = 1;
    static final long MIN_INTERVAL_MS = 40;
    static final long MAX_INTERVAL_MS = 550;
    private long firstTap = -1;

    public boolean tap(int index, boolean alreadySelected, boolean conversation, long now) {
        if (index != CHAT_INDEX || !alreadySelected || !conversation || now < 0) {
            reset();
            return false;
        }
        if (firstTap >= 0 && now >= firstTap) {
            long elapsed = now - firstTap;
            if (elapsed >= MIN_INTERVAL_MS && elapsed <= MAX_INTERVAL_MS) {
                reset();
                return true;
            }
        }
        firstTap = now;
        return false;
    }

    public void reset() { firstTap = -1; }
}
