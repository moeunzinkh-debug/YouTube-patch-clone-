package app.morphe.extension.simsimi;

import android.graphics.Rect;
import android.os.Looper;
import android.os.SystemClock;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.ScrollView;
import android.widget.TextView;

import java.lang.ref.WeakReference;
import java.util.WeakHashMap;

/** Scrolls the visible Conversation list to its top; it never reloads the app. */
public final class QuickReturn {
    private static final WeakHashMap<View, ChatTabDoubleTap> TAPS = new WeakHashMap<>();
    private static final long SETTLE_DELAY_MS = 120;

    private QuickReturn() { }

    /** Called by the native bottom-tab click listener; the original click always continues. */
    public static void onTabClicked(View bottomBar, int index) {
        if (bottomBar == null || Looper.myLooper() != Looper.getMainLooper()) return;
        try {
            ChatTabDoubleTap taps = TAPS.get(bottomBar);
            if (taps == null) { taps = new ChatTabDoubleTap(); TAPS.put(bottomBar, taps); }
            if (index != ChatTabDoubleTap.CHAT_INDEX || selectedIndex(bottomBar) != index) {
                taps.reset();
                return;
            }
            View root = validRoot(bottomBar);
            boolean conversation = root != null && isConversationHeaderVisible(root)
                    && !hasVisibleEditor(root);
            if (!taps.tap(index, true, conversation, SystemClock.uptimeMillis())) return;
            WeakReference<View> barRef = new WeakReference<>(bottomBar);
            root.postDelayed(() -> returnToTop(barRef.get()), SETTLE_DELAY_MS);
        } catch (Exception ignored) {
            // Fail closed: never block the app's own tab handling or log chat text.
        }
    }

    private static void returnToTop(View bottomBar) {
        try {
            View root = validRoot(bottomBar);
            if (root == null || selectedIndex(bottomBar) != ChatTabDoubleTap.CHAT_INDEX
                    || hasVisibleEditor(root) || !isConversationHeaderVisible(root)) return;
            Rect rootBounds = new Rect();
            if (!root.getGlobalVisibleRect(rootBounds) || rootBounds.width() <= 0 || rootBounds.height() <= 0) return;
            ScrollCandidate best = new ScrollCandidate();
            findLargestScrollableList(root, rootBounds, best);
            if (best.view != null) best.view.scrollTo(best.view.getScrollX(), 0);
        } catch (Exception ignored) {
            // Unknown versions or transient view changes are a safe no-op.
        }
    }

    private static int selectedIndex(View bottomBar) throws ReflectiveOperationException {
        Object value = bottomBar.getClass().getMethod("getCurrentItem").invoke(bottomBar);
        return value instanceof Integer ? (Integer) value : -1;
    }

    private static View validRoot(View bottomBar) {
        if (bottomBar == null || !bottomBar.isAttachedToWindow() || !bottomBar.isShown()) return null;
        View root = bottomBar.getRootView();
        return root != null && root.isAttachedToWindow() && root.isShown() ? root : null;
    }

    /** Chat rooms normally have an editor even when the keyboard is hidden. Never inspect its text. */
    private static boolean hasVisibleEditor(View view) {
        if (!view.isShown()) return false;
        Rect visible = new Rect();
        if (!view.getGlobalVisibleRect(visible)) return false;
        if (view instanceof EditText) return true;
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int index = 0; index < group.getChildCount(); index++)
                if (hasVisibleEditor(group.getChildAt(index))) return true;
        }
        return false;
    }

    private static boolean isConversationHeaderVisible(View view) {
        if (!view.isShown()) return false;
        Rect visible = new Rect();
        if (!view.getGlobalVisibleRect(visible)) return false;
        if (view instanceof TextView) {
            float density = view.getResources().getDisplayMetrics().density;
            if (density > 0 && ConversationScreen.flags(((TextView) view).getText(), visible.top / density) == 1)
                return true;
        }
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int index = 0; index < group.getChildCount(); index++)
                if (isConversationHeaderVisible(group.getChildAt(index))) return true;
        }
        return false;
    }

    /** Prefer the largest visible vertical ScrollView over nested small panes. */
    private static void findLargestScrollableList(View view, Rect root, ScrollCandidate best) {
        if (!view.isShown()) return;
        Rect visible = new Rect();
        if (!view.getGlobalVisibleRect(visible)) return;
        if (view instanceof ScrollView && view.canScrollVertically(-1)
                && (long) visible.width() * 100 >= (long) root.width() * 55
                && (long) visible.height() * 100 >= (long) root.height() * 20) {
            long area = (long) visible.width() * visible.height();
            if (area > best.area) { best.area = area; best.view = (ScrollView) view; }
        }
        if (view instanceof ViewGroup) {
            ViewGroup group = (ViewGroup) view;
            for (int index = 0; index < group.getChildCount(); index++)
                findLargestScrollableList(group.getChildAt(index), root, best);
        }
    }

    private static final class ScrollCandidate {
        private long area;
        private ScrollView view;
    }
}
