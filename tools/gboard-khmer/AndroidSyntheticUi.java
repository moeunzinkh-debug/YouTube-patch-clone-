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
            String value = new String(Base64.decode(arguments.getString("value", ""),
                    Base64.DEFAULT), StandardCharsets.UTF_8);
            UiAutomation automation = getUiAutomation();
            AccessibilityServiceInfo info = automation.getServiceInfo();
            info.flags |= AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS;
            automation.setServiceInfo(info);
            SystemClock.sleep(350);
            boolean set = false;
            for (AccessibilityWindowInfo window : automation.getWindows()) {
                if (window.getType() != AccessibilityWindowInfo.TYPE_APPLICATION) continue;
                AccessibilityNodeInfo root = window.getRoot();
                if (root != null && setText(root, description, value)) { set = true; break; }
            }
            result.putBoolean("set", set);
        } catch (Throwable failure) {
            result.putString("error_type", failure.getClass().getSimpleName());
        }
        finish(Activity.RESULT_OK, result);
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
