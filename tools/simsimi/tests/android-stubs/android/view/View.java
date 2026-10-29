package android.view;
import android.content.res.Resources;
import android.graphics.Rect;
import java.util.ArrayList;
import java.util.List;
public class View {
    private static final List<Runnable> QUEUE = new ArrayList<>();
    private final Resources resources = new Resources();
    private int l,t,r,b;
    public boolean shown = true, attached = true;
    public int scrollX;
    View parent;
    public View focus;
    public View bounds(int left,int top,int right,int bottom) { l=left; t=top; r=right; b=bottom; return this; }
    public boolean isShown() { return shown; }
    public boolean isAttachedToWindow() { return attached; }
    public View getRootView() { return parent == null ? this : parent.getRootView(); }
    public View findFocus() { return focus; }
    public boolean getGlobalVisibleRect(Rect rect) { if (!shown || r<=l || b<=t) return false; rect.set(l,t,r,b); return true; }
    public Resources getResources() { return resources; }
    public boolean canScrollVertically(int direction) { return false; }
    public int getScrollX() { return scrollX; }
    public void scrollTo(int x, int y) { scrollX = x; }
    public boolean postDelayed(Runnable task, long delay) { QUEUE.add(task); return true; }
    public static int queued() { return QUEUE.size(); }
    public static void runAll() { while (!QUEUE.isEmpty()) QUEUE.remove(0).run(); }
    public static void clearQueue() { QUEUE.clear(); }
}
