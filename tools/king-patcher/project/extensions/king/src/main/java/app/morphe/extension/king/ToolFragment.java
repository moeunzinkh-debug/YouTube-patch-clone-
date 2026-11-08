package app.morphe.extension.king;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.Dialog;
import android.app.DialogFragment;
import android.app.FragmentManager;
import android.content.Context;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.DocumentsContract;
import android.view.View;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.security.MessageDigest;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Local-only APK picker, manual layout selector, and verified output flow. */
public final class ToolFragment extends DialogFragment {
    public static final String EXTRA_MODE = "app.morphe.king.MODE";
    public static final String TAG = "app.morphe.king.tool";
    public static final int MODE_LVL = 1, MODE_UI = 2;
    private static final int PICK_INPUT = 6211, PICK_OUTPUT = 6212;
    private static final long MAX_APK = 512L * 1024 * 1024;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final ExecutorService worker = Executors.newSingleThreadExecutor();
    private final Map<String, Set<Integer>> selected = new HashMap<>();
    private int mode;
    private File session, source, signed;
    private Uri inputUri;
    private PackageInfo inputPackage;
    private ApkArchive.Layouts layouts;
    private TextView status;
    private Button choose, elements, build, save;
    private boolean busy, destroyed;
    private Context application;

    /** Uses the existing host Activity and a platform dialog fragment; no manifest edit. */
    public static void open(Activity activity, int selectedMode) {
        FragmentManager manager = activity.getFragmentManager();
        manager.executePendingTransactions();
        if (manager.findFragmentByTag(TAG) != null) return;
        ToolFragment fragment = new ToolFragment();
        Bundle arguments = new Bundle(); arguments.putInt(EXTRA_MODE, selectedMode); fragment.setArguments(arguments);
        fragment.show(manager, TAG);
    }
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        application = getActivity().getApplicationContext();
        mode = getArguments() == null ? 0 : getArguments().getInt(EXTRA_MODE, 0);
    }
    @Override public Dialog onCreateDialog(Bundle state) {
        final Activity activity = getActivity();
        if ((mode != MODE_LVL && mode != MODE_UI) || Build.VERSION.SDK_INT < 23) {
            return new AlertDialog.Builder(activity).setTitle("Unsupported")
                    .setMessage("This experimental tool requires Android 6 or newer.")
                    .setPositiveButton("Close", (d, w) -> dismissAllowingStateLoss()).create();
        }
        String title = mode == MODE_LVL ? "Remove license (Google Play LVL)" : "Remove insignificant UI elements";
        LinearLayout root = new LinearLayout(activity); root.setOrientation(LinearLayout.VERTICAL);
        int margin = (int) (16 * getResources().getDisplayMetrics().density + 0.5f); root.setPadding(margin, margin, margin, margin);
        TextView intro = new TextView(activity);
        intro.setText(mode == MODE_LVL
                ? "Select a single APK file. Only the classic, unobfuscated Google Play LVL checker is supported; other checks are rejected."
                : "Select a single APK file, then choose compiled layout elements to hide. Runtime-generated, Compose and WebView content is not supported.");
        root.addView(intro);
        choose = new Button(activity); choose.setText("1. Choose target APK"); choose.setOnClickListener(v -> pickInput()); root.addView(choose);
        elements = new Button(activity); elements.setText("2. Select layout elements"); elements.setOnClickListener(v -> chooseLayout()); root.addView(elements);
        build = new Button(activity); build.setText(mode == MODE_LVL ? "2. Create modified APK" : "3. Create modified APK");
        build.setOnClickListener(v -> confirmBuild()); root.addView(build);
        save = new Button(activity); save.setText("Save verified APK"); save.setOnClickListener(v -> pickOutput()); root.addView(save);
        status = new TextView(activity); status.setTextIsSelectable(true); root.addView(status);
        ScrollView scroll = new ScrollView(activity); scroll.addView(root);
        status.setText("No APK selected. The original file will not be modified."); refreshButtons();
        return new AlertDialog.Builder(activity).setTitle(title).setView(scroll).setNegativeButton("Close", null).create();
    }
    private void refreshButtons() {
        if (choose == null) return;
        choose.setEnabled(!busy);
        elements.setVisibility(mode == MODE_UI ? View.VISIBLE : View.GONE);
        elements.setEnabled(!busy && source != null && layouts != null && !layouts.layouts.isEmpty());
        build.setEnabled(!busy && source != null && inputPackage != null && (mode != MODE_UI || !selected.isEmpty()));
        save.setVisibility(signed != null && signed.isFile() ? View.VISIBLE : View.GONE);
        save.setEnabled(!busy && signed != null && signed.isFile());
    }
    private void pickInput() {
        if (busy) return;
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE)
                .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        try { startActivityForResult(intent, PICK_INPUT); }
        catch (ActivityNotFoundException unavailable) { showError("No file picker is available on this device."); }
    }
    private static void copyLimited(InputStream source, OutputStream target, long limit) throws IOException {
        byte[] buffer = new byte[32768]; long total = 0; int n;
        try (InputStream in = new BufferedInputStream(source); OutputStream out = new BufferedOutputStream(target)) {
            while ((n = in.read(buffer)) != -1) {
                if (n == 0) continue;
                total += n; if (total > limit) throw new IOException("APK exceeds the 512 MiB limit");
                out.write(buffer, 0, n);
            }
        }
        if (total == 0) throw new IOException("APK is empty");
    }
    private File newSession() throws IOException {
        File candidate = File.createTempFile("morphe-king-", ".dir", application.getCacheDir());
        if (!candidate.delete() || !candidate.mkdir()) throw new IOException("Cannot create private working directory");
        return candidate;
    }
    private static void deleteTree(File file) {
        if (file == null) return;
        File[] children = file.listFiles();
        if (children != null) for (File child : children) deleteTree(child);
        file.delete();
    }
    private void load(Uri uri) {
        busy = true; refreshButtons(); status.setText("Reading and checking the selected APK…");
        worker.execute(() -> {
            File newDir = null;
            try {
                newDir = newSession(); File newSource = new File(newDir, "input.apk");
                InputStream in = application.getContentResolver().openInputStream(uri);
                if (in == null) throw new IOException("Cannot read selected APK");
                copyLimited(in, new FileOutputStream(newSource), MAX_APK);
                PackageInfo info = application.getPackageManager().getPackageArchiveInfo(newSource.getAbsolutePath(), 0);
                if (info == null || info.packageName == null) throw new IOException("Android could not parse this APK");
                if (Build.VERSION.SDK_INT >= 26 && info.splitNames != null && info.splitNames.length != 0)
                    throw new IOException("Split APKs are not supported; choose a complete single APK");
                ApkArchive.Layouts found = mode == MODE_UI ? ApkArchive.listLayouts(newSource) : null;
                final File resultDir = newDir;
                main.post(() -> {
                    if (destroyed) { deleteTree(resultDir); return; }
                    deleteTree(session); session = resultDir; source = newSource; inputPackage = info;
                    inputUri = uri; signed = null; layouts = found; selected.clear(); busy = false;
                    String extra = found == null ? "" : "\n" + found.layouts.size() + " compiled layouts available"
                            + (found.truncated ? " (scan limit reached; some layouts omitted)" : "");
                    status.setText("Target: " + info.packageName + "\nVersion: " + (info.versionName == null ? "unknown" : info.versionName) + extra);
                    refreshButtons();
                });
            } catch (Exception error) {
                deleteTree(newDir);
                failAsync(error);
            }
        });
    }
    private static String shortText(String value, int length) {
        if (value == null) return "";
        value = value.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ');
        return value.length() > length ? value.substring(0, length) + "…" : value;
    }
    private void chooseLayout() {
        if (busy || layouts == null || layouts.layouts.isEmpty()) return;
        String[] names = new String[layouts.layouts.size()];
        for (int i = 0; i < names.length; i++) {
            ApkArchive.Layout item = layouts.layouts.get(i);
            Set<Integer> current = selected.get(item.path);
            names[i] = item.path + (current == null ? "" : "  (" + current.size() + " selected)");
        }
        new AlertDialog.Builder(getActivity()).setTitle("Choose a compiled layout")
                .setItems(names, (dialog, index) -> chooseNodes(layouts.layouts.get(index)))
                .setNegativeButton("Close", null).show();
    }
    private void chooseNodes(ApkArchive.Layout layout) {
        Set<Integer> prior = selected.get(layout.path);
        Set<Integer> draft = prior == null ? new HashSet<>() : new HashSet<>(prior);
        String[] names = new String[layout.nodes.size()]; boolean[] checked = new boolean[names.length];
        for (int i = 0; i < names.length; i++) {
            AxmlEditor.Node node = layout.nodes.get(i); checked[i] = draft.contains(node.ordinal);
            StringBuilder label = new StringBuilder();
            for (int n = 0; n < Math.min(node.depth, 8); n++) label.append("  ");
            label.append(shortText(node.tag, 90));
            if (node.resourceId != 0) label.append("  #").append(String.format(java.util.Locale.ROOT, "%08x", node.resourceId));
            if (node.text != null && !node.text.isEmpty()) label.append(" — ").append(shortText(node.text, 80));
            names[i] = label.toString();
        }
        new AlertDialog.Builder(getActivity()).setTitle(shortText(layout.path, 100))
                .setMultiChoiceItems(names, checked, (dialog, index, isChecked) -> {
                    int ordinal = layout.nodes.get(index).ordinal;
                    if (isChecked) draft.add(ordinal); else draft.remove(ordinal);
                })
                .setPositiveButton("Save selection", (dialog, which) -> {
                    if (draft.isEmpty()) selected.remove(layout.path); else selected.put(layout.path, draft);
                    int count = 0; for (Set<Integer> set : selected.values()) count += set.size();
                    status.setText("Target: " + inputPackage.packageName + "\nSelected " + count + " elements across " + selected.size() + " layouts.\n"
                            + "Only these compiled XML entries will be changed.");
                    refreshButtons();
                }).setNegativeButton("Cancel", null).show();
    }
    private void confirmBuild() {
        if (busy || source == null || (mode == MODE_UI && selected.isEmpty())) return;
        new AlertDialog.Builder(getActivity()).setTitle("Create a separately signed APK?")
                .setMessage("The original APK stays unchanged. The new APK uses a non-exportable key stored in this King-Patcher installation. "
                        + "It usually cannot update an app signed by a different key. Uninstalling an app may erase its data; back up first. "
                        + "If King-Patcher is removed or its app data is cleared, the signing key may be lost. "
                        + "Split APKs and signature-sensitive apps may not work.")
                .setNegativeButton("Cancel", null).setPositiveButton("Continue", (d, w) -> buildOutput()).show();
    }
    private void buildOutput() {
        signed = null;
        busy = true; refreshButtons(); status.setText("Creating and verifying a new APK. Please wait…");
        final File dir = session, original = source;
        final Map<String, Set<Integer>> selection = new HashMap<>();
        for (Map.Entry<String, Set<Integer>> item : selected.entrySet()) selection.put(item.getKey(), new HashSet<>(item.getValue()));
        worker.execute(() -> {
            File unsigned = new File(dir, "unsigned.apk"), result = new File(dir, "signed.apk"), work = new File(dir, "dex-work");
            try {
                if (unsigned.exists() && !unsigned.delete()) throw new IOException("Cannot clear previous temporary output");
                if (result.exists() && !result.delete()) throw new IOException("Cannot clear previous signed output");
                if (mode == MODE_LVL) {
                    if (!work.mkdir()) throw new IOException("Cannot create private DEX working directory");
                    try { ApkArchive.buildLvl(original, work, unsigned); } finally { deleteTree(work); }
                } else ApkArchive.buildUi(original, unsigned, selection);
                ApkSignerBridge.signAndVerify(unsigned, result);
                PackageInfo parsed = application.getPackageManager().getPackageArchiveInfo(result.getAbsolutePath(), 0);
                if (parsed == null || !inputPackage.packageName.equals(parsed.packageName)) throw new IOException("Signed output failed package validation");
                unsigned.delete();
                main.post(() -> {
                    if (destroyed) return;
                    signed = result; busy = false; refreshButtons();
                    status.setText("Signature verified. Choose a NEW destination for the modified APK; do not select the original.");
                    pickOutput();
                });
            } catch (Exception error) {
                unsigned.delete(); result.delete(); deleteTree(work); failAsync(error);
            } catch (LinkageError incompatible) {
                unsigned.delete(); result.delete(); deleteTree(work);
                failAsync(new IOException("The installed King library ABI is incompatible; no APK was exported", incompatible));
            }
        });
    }
    private void pickOutput() {
        Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT).setType("application/vnd.android.package-archive")
                .addCategory(Intent.CATEGORY_OPENABLE)
                .putExtra(Intent.EXTRA_TITLE, mode == MODE_LVL ? "king-lvl-modified.apk" : "king-ui-modified.apk")
                .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
        try { startActivityForResult(intent, PICK_OUTPUT); }
        catch (ActivityNotFoundException unavailable) { showError("No document save picker is available."); }
    }
    private boolean sameDocument(Uri first, Uri second) {
        if (first == null || second == null) return false;
        if (first.equals(second)) return true;
        if (!java.util.Objects.equals(first.getAuthority(), second.getAuthority())) return false;
        try {
            return DocumentsContract.isDocumentUri(application, first) && DocumentsContract.isDocumentUri(application, second)
                    && DocumentsContract.getDocumentId(first).equals(DocumentsContract.getDocumentId(second));
        } catch (RuntimeException invalid) { return false; }
    }
    private static byte[] digest(InputStream source) throws Exception {
        MessageDigest sha = MessageDigest.getInstance("SHA-256"); byte[] buffer = new byte[32768]; long total = 0; int n;
        try (InputStream in = new BufferedInputStream(source)) {
            while ((n = in.read(buffer)) != -1) { if (n == 0) continue; total += n; if (total > MAX_APK * 2) throw new IOException("Saved output too large"); sha.update(buffer, 0, n); }
        }
        return sha.digest();
    }
    private void save(Uri destination) {
        if (sameDocument(inputUri, destination)) { showError("Choose a different destination; the original APK must not be overwritten."); return; }
        if (signed == null || !signed.isFile()) { showError("No verified output is available."); return; }
        busy = true; refreshButtons(); status.setText("Saving and checking the new APK…");
        worker.execute(() -> {
            try {
                byte[] before = digest(new FileInputStream(signed));
                OutputStream target = application.getContentResolver().openOutputStream(destination, "w");
                if (target == null) throw new IOException("Cannot write to the selected destination");
                copyLimited(new FileInputStream(signed), target, MAX_APK * 2);
                InputStream check = application.getContentResolver().openInputStream(destination);
                if (check == null || !Arrays.equals(before, digest(check))) throw new IOException("Saved file could not be verified");
                main.post(() -> { if (!destroyed) { busy = false; status.setText("Saved and SHA-256 verified:\n" + destination + "\nOriginal APK was not changed."); refreshButtons(); } });
            } catch (Exception error) { failAsync(error); }
        });
    }
    private void showError(String text) { new AlertDialog.Builder(getActivity()).setTitle("Cannot continue").setMessage(text).setPositiveButton("OK", null).show(); }
    private void failAsync(Exception error) {
        String message = error.getMessage() == null ? error.getClass().getSimpleName() : error.getMessage();
        main.post(() -> { if (!destroyed) { busy = false; status.setText("Operation failed. If saving had started, the destination may contain an incomplete file."); refreshButtons(); showError(shortText(message, 300)); } });
    }
    @Override public void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (resultCode != Activity.RESULT_OK || data == null || data.getData() == null) return;
        if (requestCode == PICK_INPUT) load(data.getData());
        else if (requestCode == PICK_OUTPUT) save(data.getData());
    }
    @Override public void onDestroy() {
        destroyed = true;
        File cleanup = session;
        worker.execute(() -> deleteTree(cleanup)); worker.shutdown();
        super.onDestroy();
    }
}
