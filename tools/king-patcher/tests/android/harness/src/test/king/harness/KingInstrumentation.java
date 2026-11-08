package test.king.harness;

import android.app.Activity;
import android.app.DialogFragment;
import android.app.Instrumentation;
import android.content.Intent;
import android.content.IntentFilter;
import android.net.Uri;
import android.os.Bundle;
import android.os.SystemClock;
import android.view.accessibility.AccessibilityNodeInfo;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

/** Runs inside the disposable patched King's process with its actual embedded libraries. */
public final class KingInstrumentation extends Instrumentation {
    private static final String TOOL = "app.morphe.extension.king.ToolFragment";
    private static final String TAG = "app.morphe.king.tool";
    private File input;
    private Activity host;

    @Override public void onCreate(Bundle arguments) { super.onCreate(arguments); start(); }
    private void phase(String message) { Bundle status = new Bundle(); status.putString("phase", message); sendStatus(0, status); }
    private static void copy(InputStream source, File target) throws Exception {
        try (InputStream in = source; OutputStream out = new FileOutputStream(target)) {
            byte[] buffer = new byte[32768]; int n; while ((n = in.read(buffer)) != -1) if (n > 0) out.write(buffer, 0, n);
        }
    }
    private static byte[] sha(File file) throws Exception {
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (InputStream in = new FileInputStream(file)) { byte[] b = new byte[32768]; int n; while ((n = in.read(b)) != -1) if (n > 0) digest.update(b, 0, n); }
        return digest.digest();
    }
    private static Object field(Object target, String name) throws Exception {
        Field f = target.getClass().getDeclaredField(name); f.setAccessible(true); return f.get(target);
    }
    private boolean isBusy(Object activity) throws Exception {
        AtomicBoolean result = new AtomicBoolean();
        runOnMainSync(() -> { try { result.set((Boolean) field(activity, "busy")); } catch (Exception e) { throw new RuntimeException(e); } });
        return result.get();
    }
    private void waitIdle(Object activity, long timeout) throws Exception {
        long end = SystemClock.uptimeMillis() + timeout;
        while (SystemClock.uptimeMillis() < end) {
            if (!isBusy(activity)) return;
            SystemClock.sleep(200);
        }
        throw new AssertionError("Timed out waiting for tool operation");
    }
    private void click(String text, long timeout) throws Exception {
        long end = SystemClock.uptimeMillis() + timeout;
        while (SystemClock.uptimeMillis() < end) {
            AccessibilityNodeInfo root = getUiAutomation().getRootInActiveWindow();
            if (root != null) {
                List<AccessibilityNodeInfo> matches = root.findAccessibilityNodeInfosByText(text);
                for (AccessibilityNodeInfo match : matches) {
                    AccessibilityNodeInfo candidate = match;
                    while (candidate != null) {
                        if (candidate.isClickable() && candidate.isEnabled()
                                && candidate.performAction(AccessibilityNodeInfo.ACTION_CLICK)) {
                            SystemClock.sleep(400); return;
                        }
                        candidate = candidate.getParent();
                    }
                }
            }
            SystemClock.sleep(250);
        }
        throw new AssertionError("Could not click UI text: " + text);
    }
    private Object openTool(int mode) throws Exception {
        Intent intent = new Intent().setClassName(getTargetContext(), "ru.jgaiecip.osuojvyxe.MainActivity")
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        phase("launching King host Activity for mode " + mode);
        ActivityMonitor monitor = addMonitor("ru.jgaiecip.osuojvyxe.MainActivity", null, false);
        getTargetContext().startActivity(intent);
        host = waitForMonitorWithTimeout(monitor, 30000);
        removeMonitor(monitor);
        phase("King host Activity started for mode " + mode);
        if (host == null) throw new AssertionError("King host Activity did not open");
        Class<?> menuClass = getTargetContext().getClassLoader().loadClass("ʽٴ.ᐧᐧ");
        java.lang.reflect.Constructor<?> constructor = menuClass.getDeclaredConstructor(); constructor.setAccessible(true);
        Object menu = constructor.newInstance();
        Method dispatch = menuClass.getMethod("ˊᵎ", int.class);
        int id = mode == 1 ? 0x7e4d0001 : 0x7e4d0002;
        runOnMainSync(() -> {
            try {
                dispatch.invoke(menu, id); // Exercise the injected host dispatcher, not just the bridge.
                host.getFragmentManager().executePendingTransactions();
            } catch (Exception e) { throw new RuntimeException(e); }
        });
        phase("dispatcher returned for mode " + mode);
        Object fragment = host.getFragmentManager().findFragmentByTag(TAG);
        if (fragment == null || !fragment.getClass().getName().equals(TOOL)) throw new AssertionError("Tool dialog did not open");
        Method load = fragment.getClass().getDeclaredMethod("load", Uri.class); load.setAccessible(true);
        runOnMainSync(() -> { try { load.invoke(fragment, Uri.fromFile(input)); } catch (Exception e) { throw new RuntimeException(e); } });
        waitIdle(fragment, 45000);
        if (field(fragment, "source") == null) throw new AssertionError("Target APK failed to load");
        phase("synthetic target loaded for mode " + mode);
        return fragment;
    }
    private void createOutput(Object activity, String createLabel, String filename) throws Exception {
        phase("requesting signed output " + filename);
        click(createLabel, 15000);
        click("Continue", 15000);
        phase("build confirmed " + filename);
        waitIdle(activity, 120000);
        phase("build finished " + filename);
        File result = (File) field(activity, "signed");
        if (result == null || !result.isFile() || result.length() == 0) {
            Object message = field(activity, "status");
            throw new AssertionError("Tool did not produce a verified signed output: " + ((android.widget.TextView) message).getText());
        }
        File external = getTargetContext().getExternalFilesDir(null);
        if (external == null) throw new AssertionError("No target app external test directory");
        File output = new File(external, filename); copy(new FileInputStream(result), output);
        if (!Arrays.equals(sha(result), sha(output))) throw new AssertionError("Test output copy mismatch");
        runOnMainSync(() -> { ((DialogFragment) activity).dismissAllowingStateLoss(); host.getFragmentManager().executePendingTransactions(); host.finish(); });
        SystemClock.sleep(300);
    }
    @Override public void onStart() {
        Bundle result = new Bundle();
        try {
            phase("instrumentation started");
            addMonitor(new IntentFilter(Intent.ACTION_CREATE_DOCUMENT), new ActivityResult(Activity.RESULT_CANCELED, null), true);
            input = new File(getTargetContext().getCacheDir(), "king-synthetic-input.apk");
            copy(getContext().getAssets().open("fixture.apk"), input);
            byte[] before = sha(input);
            Object ui = openTool(2);
            phase("opening layout chooser");
            click("2. Select layout elements", 15000);
            click("res/layout/activity_main.xml", 15000);
            click("HIDE-ME", 15000);
            click("Save selection", 15000);
            phase("manual node selected");
            createOutput(ui, "3. Create modified APK", "king-ui-fixture.apk");
            Object lvl = openTool(1);
            createOutput(lvl, "2. Create modified APK", "king-lvl-fixture.apk");
            if (!Arrays.equals(before, sha(input))) throw new AssertionError("Input fixture was modified");
            result.putString("status", "PASS");
            result.putString("coverage", "Manual layout selection, classic LVL rewrite, host libraries, Android Keystore signing and verification on synthetic APKs");
            finish(Activity.RESULT_OK, result);
        } catch (Throwable failure) {
            java.io.StringWriter text = new java.io.StringWriter(); failure.printStackTrace(new java.io.PrintWriter(text));
            result.putString("status", "FAIL"); result.putString("error", text.toString());
            finish(Activity.RESULT_CANCELED, result);
        }
    }
}
