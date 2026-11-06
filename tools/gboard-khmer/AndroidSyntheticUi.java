/* Disposable emulator-only UI helper. Never included in the Gboard MPP. */
package dev.arena.khmerprobe;

import android.accessibilityservice.AccessibilityServiceInfo;
import android.app.Activity;
import android.app.Instrumentation;
import android.app.UiAutomation;
import android.os.Bundle;
import android.os.SystemClock;
import android.util.Base64;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.accessibility.AccessibilityWindowInfo;

import java.nio.charset.StandardCharsets;

/** Sets only explicitly named synthetic test fields; does not report their contents. */
public final class AndroidSyntheticUi extends Instrumentation {
    private Bundle arguments;

    @Override public void onCreate(Bundle args) {
        super.onCreate(args);
        arguments = args;
        start();
    }

    @Override public void onStart() {
        Bundle result = new Bundle();
        try {
            String description = new String(Base64.decode(arguments.getString("description", ""),
                    Base64.DEFAULT), StandardCharsets.UTF_8);
            String encoded = arguments.getString("value", "__empty__");
            String value = "__empty__".equals(encoded) ? ""
                    : new String(Base64.decode(encoded, Base64.DEFAULT), StandardCharsets.UTF_8);
            UiAutomation automation = getUiAutomation();
            AccessibilityServiceInfo info = automation.getServiceInfo();
            info.flags |= AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS;
            automation.setServiceInfo(info);
            SystemClock.sleep(350);
            boolean documentClick = "click_document".equals(arguments.getString("action"));
            boolean done = false;
            for (AccessibilityWindowInfo window : automation.getWindows()) {
                if (window.getType() != AccessibilityWindowInfo.TYPE_APPLICATION) continue;
                AccessibilityNodeInfo root = window.getRoot();
                if (root == null) continue;
                if (documentClick ? clickDocument(root, value) : setText(root, description, value)) {
                    done = true;
                    break;
                }
            }
            result.putBoolean(documentClick ? "clicked" : "set", done);
        } catch (Throwable failure) {
            result.putString("error_type", failure.getClass().getSimpleName());
        }
        finish(Activity.RESULT_OK, result);
    }

    private boolean clickDocument(AccessibilityNodeInfo node, String filename) {
        CharSequence packageName = node.getPackageName();
        String pkg = packageName == null ? "" : packageName.toString();
        if (filename.startsWith("khmerlish-smoke-")
                && ("com.google.android.documentsui".equals(pkg) || "com.android.documentsui".equals(pkg))
                && filename.equals(String.valueOf(node.getText()))) {
            for (AccessibilityNodeInfo target = node; target != null; target = target.getParent()) {
                if (target.isClickable() && target.isEnabled()
                        && target.performAction(AccessibilityNodeInfo.ACTION_CLICK)) return true;
            }
        }
        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            if (child != null && clickDocument(child, filename)) return true;
        }
        return false;
    }

    private boolean setText(AccessibilityNodeInfo node, String description, String value) {
        if (description.equals(String.valueOf(node.getContentDescription()))
                && node.getPackageName() != null
                && "dev.jason.com.google.android.inputmethod.latin".contentEquals(node.getPackageName())
                && node.isEditable()) {
            Bundle change = new Bundle();
            change.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE, value);
            return node.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, change);
        }
        for (int i = 0; i < node.getChildCount(); i++) {
            AccessibilityNodeInfo child = node.getChild(i);
            if (child != null && setText(child, description, value)) return true;
        }
        return false;
    }
}
