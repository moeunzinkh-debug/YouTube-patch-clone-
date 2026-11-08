package test.king.harness;

import android.app.Activity;
import android.app.DialogFragment;
import android.app.Instrumentation;
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
        StringBuilder visible = new StringBuilder(); collectTexts(getUiAutomation().getRootInActiveWindow(), visible);
        throw new AssertionError("Could not click UI text: " + text + " Visible: " + visible);
    }
    private void clickExactFile(String filename, long timeout) throws Exception {
        long end = SystemClock.uptimeMillis() + timeout;
        while (SystemClock.uptimeMillis() < end) {
            AccessibilityNodeInfo root = getUiAutomation().getRootInActiveWindow();
            if (root != null) for (AccessibilityNodeInfo match : root.findAccessibilityNodeInfosByText(filename)) {
                CharSequence text = match.getText(), desc = match.getContentDescription();
                if (!(filename.contentEquals(text == null ? "" : text) || filename.contentEquals(desc == null ? "" : desc))) continue;
                AccessibilityNodeInfo candidate = match;
                while (candidate != null) {
                    if (candidate.isClickable() && candidate.isEnabled()
                            && candidate.performAction(AccessibilityNodeInfo.ACTION_CLICK)) {
                        SystemClock.sleep(400); return;
                    }
                    candidate = candidate.getParent();
                }
            }
            SystemClock.sleep(250);
        }
        StringBuilder visible = new StringBuilder(); collectTexts(getUiAutomation().getRootInActiveWindow(), visible);
        throw new AssertionError("Could not select exact file: " + filename + " Visible: " + visible);
    }
    private boolean visible(String label) {
        AccessibilityNodeInfo root = getUiAutomation().getRootInActiveWindow();
        return root != null && !root.findAccessibilityNodeInfosByText(label).isEmpty();
    }
    private void openDownloadsInPicker() throws Exception {
        long deadline = SystemClock.uptimeMillis() + 20000;
        while (SystemClock.uptimeMillis() < deadline) {
            AccessibilityNodeInfo root = getUiAutomation().getRootInActiveWindow();
            CharSequence pkg = root == null ? null : root.getPackageName();
            if (pkg != null && pkg.toString().contains("documentsui")) break;
            SystemClock.sleep(200);
        }
        SystemClock.sleep(600);
        pickerPhase("picker opened");
        if (visible("Show roots")) {
            click("Show roots", 5000); pickerPhase("picker roots");
            click("Downloads", 10000); pickerPhase("picker Downloads");
        }
    }
    private void pickerPhase(String label) {
        AccessibilityNodeInfo root = getUiAutomation().getRootInActiveWindow();
        StringBuilder texts = new StringBuilder(); collectTexts(root, texts);
        phase(label + " package=" + (root == null ? "unknown" : root.getPackageName()) + " "
                + texts.substring(0, Math.min(texts.length(), 650)));
    }
    private void waitForSource(Object fragment) throws Exception {
        long deadline = SystemClock.uptimeMillis() + 45000;
        while (SystemClock.uptimeMillis() < deadline) {
            if (field(fragment, "source") != null && !isBusy(fragment)) return;
            SystemClock.sleep(200);
        }
        StringBuilder visible = new StringBuilder(); collectTexts(getUiAutomation().getRootInActiveWindow(), visible);
        throw new AssertionError("Target APK was not loaded after selection: " + visible);
    }
    private void waitForSaved(Object fragment) throws Exception {
        long deadline = SystemClock.uptimeMillis() + 45000;
        while (SystemClock.uptimeMillis() < deadline) {
            String[] message = new String[1];
            runOnMainSync(() -> { try { message[0] = ((android.widget.TextView) field(fragment, "status")).getText().toString(); }
                                  catch (Exception e) { message[0] = "status unavailable"; } });
            if (message[0].startsWith("Saved and SHA-256 verified")) return;
            if (message[0].startsWith("Operation failed")) break;
            SystemClock.sleep(200);
        }
        StringBuilder visible = new StringBuilder(); collectTexts(getUiAutomation().getRootInActiveWindow(), visible);
        throw new AssertionError("Saving did not complete: " + visible);
    }
    private void collectTexts(AccessibilityNodeInfo node, StringBuilder out) {
        if (node == null || out.length() > 2000) return;
        CharSequence text = node.getText();
        if (text != null && text.length() > 0) out.append(text).append(" | ");
        CharSequence description = node.getContentDescription();
        if (description != null && description.length() > 0) out.append(description).append(" | ");
        for (int i = 0; i < node.getChildCount(); i++) collectTexts(node.getChild(i), out);
    }
    private boolean hasText(android.view.View view, String text) {
        if (view instanceof android.widget.TextView && text.contentEquals(((android.widget.TextView) view).getText())) return true;
        if (view instanceof android.view.ViewGroup) {
            android.view.ViewGroup group = (android.view.ViewGroup) view;
            for (int i = 0; i < group.getChildCount(); i++) if (hasText(group.getChildAt(i), text)) return true;
        }
        return false;
    }
    private void checkKingRenderer() throws Exception {
        phase("testing King menu renderer");
        Throwable[] error = new Throwable[1];
        runOnMainSync(() -> {
            try {
                ClassLoader loader = getTargetContext().getClassLoader();
                Class<?> model = loader.loadClass("ʽᐧ.ˉ");
                java.lang.reflect.Constructor<?> modelConstructor = model.getDeclaredConstructor(
                    int.class, String.class, int.class, String.class, String.class, int.class);
                modelConstructor.setAccessible(true);
                java.util.ArrayList<Object> items = new java.util.ArrayList<>();
                String[] labels = {"Remove license (Google Play LVL)", "Remove insignificant things"};
                items.add(modelConstructor.newInstance(0x7e4d0001, labels[0], 0, "LVL", "#FFFFFF", 0x7f080083));
                items.add(modelConstructor.newInstance(0x7e4d0002, labels[1], 0, "UI", "#FFFFFF", 0x7f080083));
                Class<?> adapterType = loader.loadClass("ʽᐧ.ʽ$ˑˑ");
                java.lang.reflect.Constructor<?> adapterConstructor = adapterType.getDeclaredConstructor(
                    android.content.Context.class, int.class, java.util.List.class, boolean.class);
                adapterConstructor.setAccessible(true);
                android.widget.ArrayAdapter<?> adapter = (android.widget.ArrayAdapter<?>)
                    adapterConstructor.newInstance(host, 0x7f0c005a, items, false);
                for (int i = 0; i < labels.length; i++) {
                    android.view.View row = adapter.getView(i, null, new android.widget.LinearLayout(host));
                    if (!hasText(row, labels[i])) throw new AssertionError("Expected menu row label was not rendered: " + labels[i]);
                }
            } catch (Throwable failure) { error[0] = failure; }
        });
        if (error[0] != null) throw new AssertionError("King menu renderer failed", error[0]);
        phase("King menu renderer accepted both labels and colors");
    }
    private void checkKingLvlLibrary() throws Exception {
        phase("testing King embedded LVL editor ABI");
        File dex = new File(getTargetContext().getCacheDir(), "king-test-input.dex");
        File patched = new File(getTargetContext().getCacheDir(), "king-test-output.dex");
        dex.delete(); patched.delete();
        try (java.util.zip.ZipFile zip = new java.util.zip.ZipFile(input)) {
            copy(zip.getInputStream(zip.getEntry("classes.dex")), dex);
        }
        try {
            Class<?> editor = getTargetContext().getClassLoader().loadClass("app.morphe.extension.king.LvlEditor");
            Method patch = editor.getMethod("patch", java.util.List.class, File.class);
            patch.invoke(null, java.util.Collections.singletonList(dex), patched);
            if (!patched.isFile() || patched.length() == 0) throw new AssertionError("LVL editor returned no DEX");
        } finally { dex.delete(); patched.delete(); }
        phase("King embedded LVL editor ABI succeeded");
    }
    private Object openTool(int mode) throws Exception {
        if (host == null) {
            phase("launching King host Activity for mode " + mode);
            ActivityMonitor monitor = addMonitor("ru.jgaiecip.osuojvyxe.MainActivity", null, false);
            // The runner starts in the background on Android 10+; ask UiAutomation's shell
            // to bring the real Activity forward rather than relying on a blocked launch.
            try (InputStream stream = new android.os.ParcelFileDescriptor.AutoCloseInputStream(
                    getUiAutomation().executeShellCommand("am start -n ru.jgaiecip.osuojvyxe/.MainActivity -f 0x10000000"))) {
                byte[] bytes = new byte[1024];
                while (stream.read(bytes) != -1) { /* drain the command output */ }
            }
            host = waitForMonitorWithTimeout(monitor, 30000);
            removeMonitor(monitor);
            if (host == null) throw new AssertionError("King host Activity did not open");
            phase("King host Activity started for mode " + mode);
            checkKingRenderer();
            checkKingLvlLibrary();
        }
        ClassLoader loader = getTargetContext().getClassLoader();
        Class<?> menuClass = loader.loadClass("ʽٴ.ᐧᐧ");
        java.lang.reflect.Constructor<?> constructor = menuClass.getDeclaredConstructor(); constructor.setAccessible(true);
        Object menu = constructor.newInstance();
        java.lang.reflect.Field currentMenu = menuClass.getDeclaredField("ʼˋ"); currentMenu.setAccessible(true);
        Object previousMenu = currentMenu.get(null);
        Class<?> modelClass = loader.loadClass("ʽᐧ.ˉ");
        java.lang.reflect.Constructor<?> modelCtor = modelClass.getDeclaredConstructor(
                int.class, String.class, int.class, String.class, String.class, int.class);
        modelCtor.setAccessible(true);
        int id = mode == 1 ? 0x7e4d0001 : 0x7e4d0002;
        String label = mode == 1 ? "Remove license (Google Play LVL)" : "Remove insignificant things";
        java.util.ArrayList<Object> items = new java.util.ArrayList<>();
        items.add(modelCtor.newInstance(id, label, 0, "test", "#FFFFFF", 0x7f080083));
        // Invoke each inspected King click listener with its actual item model; it calls the patched dispatcher.
        String parentName = mode == 2 ? "ʽᐧ.ʽ$ˊˊ" : "ʽᐧ.ʽ$ˏˏ";
        Class<?> parent = loader.loadClass(parentName);
        java.lang.reflect.Constructor<?> parentCtor = mode == 2
                ? parent.getDeclaredConstructor(java.util.ArrayList.class, boolean.class)
                : parent.getDeclaredConstructor(java.util.ArrayList.class, boolean.class, String.class);
        parentCtor.setAccessible(true);
        Object outer = mode == 2 ? parentCtor.newInstance(items, false) : parentCtor.newInstance(items, false, "test");
        Class<?> listenerClass = loader.loadClass(parentName + "$ʻ");
        java.lang.reflect.Constructor<?> listenerCtor = listenerClass.getDeclaredConstructor(parent); listenerCtor.setAccessible(true);
        Object listener = listenerCtor.newInstance(outer);
        Method onClick = listenerClass.getDeclaredMethod("onItemClick", android.widget.AdapterView.class,
                android.view.View.class, int.class, long.class); onClick.setAccessible(true);
        Throwable[] dispatchError = new Throwable[1];
        runOnMainSync(() -> {
            try {
                currentMenu.set(null, menu);
                onClick.invoke(listener, null, null, 0, 0L);
                host.getFragmentManager().executePendingTransactions();
            } catch (Throwable failure) { dispatchError[0] = failure; }
            finally { try { currentMenu.set(null, previousMenu); } catch (Throwable failure) { dispatchError[0] = failure; } }
        });
        if (dispatchError[0] != null) throw new AssertionError("King click listener or patched dispatcher failed", dispatchError[0]);
        phase("King click listener and dispatcher returned for mode " + mode);
        Object fragment = host.getFragmentManager().findFragmentByTag(TAG);
        if (fragment == null || !fragment.getClass().getName().equals(TOOL)) throw new AssertionError("Tool dialog did not open");
        if (mode == 2) {
            phase("selecting synthetic APK through system document picker");
            click("1. Choose target APK", 15000);
            openDownloadsInPicker();
            clickExactFile("king-fixture.apk", 15000);
            pickerPhase("after selecting fixture");
            waitForSource(fragment);
        } else {
            Method load = fragment.getClass().getDeclaredMethod("load", Uri.class); load.setAccessible(true);
            runOnMainSync(() -> { try { load.invoke(fragment, Uri.fromFile(input)); } catch (Exception e) { throw new RuntimeException(e); } });
            waitForSource(fragment);
        }
        phase("synthetic target loaded for mode " + mode);
        return fragment;
    }
    private void verifyFailedSelectionClearsPreviousTarget(Object fragment) throws Exception {
        phase("checking failed selection clears previous target");
        Method load = fragment.getClass().getDeclaredMethod("load", Uri.class); load.setAccessible(true);
        File missing = new File(getTargetContext().getCacheDir(), "king-nonexistent-fixture.apk"); missing.delete();
        runOnMainSync(() -> { try { load.invoke(fragment, Uri.fromFile(missing)); } catch (Exception e) { throw new RuntimeException(e); } });
        waitIdle(fragment, 45000);
        if (field(fragment, "source") != null || field(fragment, "signed") != null || field(fragment, "inputPackage") != null)
            throw new AssertionError("Failed selection left the previous APK or signed output active");
        click("OK", 10000);
        phase("failed selection safely cleared previous target");
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
            StringBuilder visible = new StringBuilder(); collectTexts(getUiAutomation().getRootInActiveWindow(), visible);
            throw new AssertionError("Tool did not produce a verified signed output: " + ((android.widget.TextView) message).getText() + " " + visible);
        }
        phase("saving verified output through system document picker");
        openDownloadsInPicker();
        click("SAVE", 15000);
        waitForSaved(activity);
        phase("system document picker saved and verified " + filename);
        File external = getTargetContext().getExternalFilesDir(null);
        if (external == null) throw new AssertionError("No target app external test directory");
        File output = new File(external, filename); copy(new FileInputStream(result), output);
        if (!Arrays.equals(sha(result), sha(output))) throw new AssertionError("Test output copy mismatch");
        phase("copied signed output " + filename);
        if (filename.equals("king-ui-fixture.apk")) verifyFailedSelectionClearsPreviousTarget(activity);
        // King terminates its process when its MainActivity is finished; keep the
        // same real host alive for both experiments and only dismiss our dialog.
        runOnMainSync(() -> { ((DialogFragment) activity).dismissAllowingStateLoss(); host.getFragmentManager().executePendingTransactions(); });
        SystemClock.sleep(300);
    }
    @Override public void onStart() {
        Bundle result = new Bundle();
        try {
            phase("instrumentation started");
            input = new File(getTargetContext().getCacheDir(), "king-synthetic-input.apk");
            copy(getContext().getAssets().open("fixture.apk"), input);
            byte[] before = sha(input);
            Object ui = openTool(2);
            phase("opening layout chooser");
            click("2. Select layout elements", 15000);
            click("res/layout/activity_main.xml", 15000);
            click("HIDE-ME", 15000);
            click("HIDE-EXISTING", 15000);
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
