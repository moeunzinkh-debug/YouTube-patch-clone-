package app.morphe.extension.simsimi;

/** Input-only state machine; consumes no Android touch events. */
public final class PullGesture {
    private boolean tracking, movedEnough;
    private float startX, startY;
    private long startTime, lastReload = Long.MIN_VALUE;
    public void down(float x, float y, long time, float density, boolean allowed) {
        tracking = allowed && density > 0 && y >= 0 && y <= 96 * density;
        movedEnough = false;
        startX = x; startY = y; startTime = time;
    }
    /**
     * Require a real drag event while the Conversation list is still visible.
     * An ACTION_UP delivered after navigation must never become a reload solely
     * because its coordinates differ from the original tap.
     */
    public void move(float x, float y, long time, float density, boolean allowed) {
        if (!tracking) return;
        if (!allowed || density <= 0 || time < startTime || time-startTime > 1500
                || x-startX > 64*density || startX-x > 64*density || y < startY) {
            cancel();
            return;
        }
        if (y-startY >= 96*density) movedEnough = true;
    }
    public void cancel() { tracking = false; movedEnough = false; }
    public boolean up(float x, float y, long time, float density) {
        boolean active = tracking && movedEnough;
        tracking = false;
        movedEnough = false;
        if (!active || density <= 0 || time < startTime) return false;
        long elapsed = time - startTime;
        if (elapsed < 100 || elapsed > 1500 || y-startY < 160*density
                || Math.abs(x-startX) > 64*density) return false;
        if (lastReload != Long.MIN_VALUE && time-lastReload < 5000) return false;
        lastReload = time;
        return true;
    }
}
