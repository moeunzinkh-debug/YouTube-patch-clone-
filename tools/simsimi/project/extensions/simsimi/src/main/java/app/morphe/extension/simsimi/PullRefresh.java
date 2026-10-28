package app.morphe.extension.simsimi;

import android.app.Activity;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.Toast;
import android.util.Log;
import java.lang.reflect.Method;
import java.util.WeakHashMap;

/** Reloads the existing React runtime; does not kill the process or add an overlay. */
public final class PullRefresh {
    private static final WeakHashMap<Activity, PullGesture> gestures = new WeakHashMap<>();
    private PullRefresh() { }
    public static void onTouch(Activity activity, MotionEvent event) {
        try {
            if (activity == null || event == null || activity.isFinishing() || activity.isDestroyed()) return;
            PullGesture state = gestures.get(activity);
            if (state == null) { state = new PullGesture(); gestures.put(activity, state); }
            float density = activity.getResources().getDisplayMetrics().density;
            if (event.getPointerCount() != 1) { state.cancel(); return; }
            switch (event.getActionMasked()) {
                case MotionEvent.ACTION_DOWN:
                    View root = activity.getWindow().getDecorView();
                    View focused = activity.getCurrentFocus();
                    boolean allowed = !(focused instanceof EditText)
                            && !scrollableAt(root, event.getRawX(), event.getRawY());
                    state.down(event.getX(), event.getY(), event.getEventTime(), density, allowed);
                    break;
                case MotionEvent.ACTION_UP:
                    if (state.up(event.getX(), event.getY(), event.getEventTime(), density)) {
                        activity.getWindow().getDecorView().post(() -> reload(activity));
                    }
                    break;
                case MotionEvent.ACTION_CANCEL:
                    state.cancel();
                    break;
                default:
                    break;
            }
        } catch (Exception error) {
            Log.w("SimSimiPatch", "Pull-to-reload gesture failed", error);
        }
    }
    private static boolean scrollableAt(View view, float x, float y) {
        if (view.getVisibility() != View.VISIBLE) return false;
        int[] position = new int[2];
        view.getLocationOnScreen(position);
        if (x < position[0] || y < position[1] || x >= position[0]+view.getWidth() || y >= position[1]+view.getHeight()) return false;
        if (view.canScrollVertically(-1)) return true;
        if (view instanceof ViewGroup group) {
            for (int index = group.getChildCount()-1; index >= 0; index--)
                if (scrollableAt(group.getChildAt(index), x, y)) return true;
        }
        return false;
    }
    private static void reload(Activity activity) {
        if (activity.isFinishing() || activity.isDestroyed()) return;
        try {
            Object application = activity.getApplication();
            Object nativeHost = application.getClass().getMethod("getReactNativeHost").invoke(application);
            // Do not instantiate an unused legacy manager on a new-architecture app.
            boolean legacyActive = Boolean.TRUE.equals(nativeHost.getClass().getMethod("hasInstance").invoke(nativeHost));
            if (legacyActive) {
                Object manager = nativeHost.getClass().getMethod("getReactInstanceManager").invoke(nativeHost);
                manager.getClass().getMethod("recreateReactContextInBackground").invoke(manager);
            } else {
                Object host = application.getClass().getMethod("getReactHost").invoke(application);
                if (host == null) throw new IllegalStateException("No active React host");
                Method reload = host.getClass().getMethod("reload", String.class);
                reload.invoke(host, "SimSimi pull-to-reload patch");
            }
            Toast.makeText(activity, "Reloading SimSimi…", Toast.LENGTH_SHORT).show();
        } catch (Exception error) {
            Log.w("SimSimiPatch", "React reload unavailable", error);
            Toast.makeText(activity, "Cannot reload this SimSimi build", Toast.LENGTH_SHORT).show();
        }
    }
}
