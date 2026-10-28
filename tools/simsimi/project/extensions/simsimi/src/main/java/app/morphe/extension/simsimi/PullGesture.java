package app.morphe.extension.simsimi;

/** Input-only state machine; consumes no Android touch events. */
public final class PullGesture {
    private boolean tracking;
    private float startX, startY;
    private long startTime, lastReload = Long.MIN_VALUE;
    public void down(float x, float y, long time, float density, boolean allowed) {
        tracking = allowed && y >= 0 && y <= 96 * density;
        startX = x; startY = y; startTime = time;
    }
    public void cancel() { tracking = false; }
    public boolean up(float x, float y, long time, float density) {
        boolean active = tracking;
        tracking = false;
        if (!active || density <= 0 || time < startTime) return false;
        long elapsed = time - startTime;
        if (elapsed < 100 || elapsed > 1500 || y-startY < 160*density
                || Math.abs(x-startX) > 64*density) return false;
        if (lastReload != Long.MIN_VALUE && time-lastReload < 5000) return false;
        lastReload = time;
        return true;
    }
}
