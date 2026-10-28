/* Disposable emulator-only inspector. Never included in the Gboard MPP. */
package dev.jason.gboardpatches.extension.directtranslate;

import android.accessibilityservice.AccessibilityServiceInfo;
import android.app.Activity;
import android.app.Instrumentation;
import android.app.UiAutomation;
import android.graphics.Rect;
import android.os.Bundle;
import android.os.SystemClock;
import android.util.Base64;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.accessibility.AccessibilityWindowInfo;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.ByteArrayOutputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.zip.GZIPOutputStream;

/** Inspects only IME accessibility windows in a fresh, synthetic emulator. */
public final class AndroidWindowInspector extends Instrumentation {
    private static final int MAX_NODES = 800;
    private int count;

    @Override public void onCreate(Bundle arguments) {
        super.onCreate(arguments);
        start();
    }

    @Override public void onStart() {
        Bundle result = new Bundle();
        try {
            UiAutomation automation = getUiAutomation();
            AccessibilityServiceInfo info = automation.getServiceInfo();
            info.flags |= AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS
                    | AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS;
            automation.setServiceInfo(info);
            SystemClock.sleep(500);
            JSONArray windows = new JSONArray();
            List<AccessibilityWindowInfo> all = automation.getWindows();
            for (AccessibilityWindowInfo window : all) {
                if (window.getType() != AccessibilityWindowInfo.TYPE_INPUT_METHOD) continue;
                AccessibilityNodeInfo root = window.getRoot();
                if (root != null) windows.put(node(root));
            }
            byte[] json = windows.toString().getBytes(StandardCharsets.UTF_8);
            ByteArrayOutputStream buffer = new ByteArrayOutputStream();
            try (GZIPOutputStream gzip = new GZIPOutputStream(buffer)) { gzip.write(json); }
            result.putString("ime_windows", Base64.encodeToString(buffer.toByteArray(), Base64.NO_WRAP));
        } catch (Exception error) {
            // Do not put messages or stack traces into instrumentation output.
            result.putString("error", error.getClass().getSimpleName());
        }
        finish(Activity.RESULT_OK, result);
    }

    private JSONObject node(AccessibilityNodeInfo current) throws Exception {
        JSONObject item = new JSONObject();
        count++;
        Rect bounds = new Rect();
        current.getBoundsInScreen(bounds);
        item.put("bounds", "[" + bounds.left + "," + bounds.top + "][" + bounds.right + "," + bounds.bottom + "]");
        item.put("text", safe(current.getText()));
        item.put("description", safe(current.getContentDescription()));
        item.put("id", safe(current.getViewIdResourceName()));
        item.put("class", safe(current.getClassName()));
        item.put("clickable", current.isClickable());
        JSONArray children = new JSONArray();
        for (int index = 0; index < current.getChildCount() && count < MAX_NODES; index++) {
            AccessibilityNodeInfo child = current.getChild(index);
            if (child != null) children.put(node(child));
        }
        item.put("children", children);
        return item;
    }

    private static String safe(CharSequence value) {
        if (value == null) return "";
        String text = value.toString();
        return text.substring(0, Math.min(text.length(), 200));
    }
}
