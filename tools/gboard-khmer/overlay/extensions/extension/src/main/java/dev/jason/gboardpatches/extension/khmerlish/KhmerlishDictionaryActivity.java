package dev.jason.gboardpatches.extension.khmerlish;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.res.Configuration;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.InputFilter;
import android.text.InputType;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.WindowManager;
import android.view.inputmethod.EditorInfo;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Private, offline word guide and explicit personal-dictionary manager. */
public final class KhmerlishDictionaryActivity extends Activity {
    private static final int REQUEST_IMPORT = 0x4b31;
    private static final int REQUEST_EXPORT = 0x4b32;
    private final Handler main = new Handler(Looper.getMainLooper());
    private final ExecutorService worker = Executors.newSingleThreadExecutor(runnable -> {
        Thread thread = new Thread(runnable, "KhmerlishWordGuide");
        thread.setDaemon(true);
        return thread;
    });
    private KhmerlishDictionary builtIn;
    private LinearLayout results;
    private LinearLayout personalActions;
    private EditText search;
    private TextView status;
    private TextView pageLabel;
    private Button previous;
    private Button next;
    private Button guideTab;
    private Button personalTab;
    private ScrollView scroll;
    private boolean personalOnly;
    private boolean destroyed;
    private int page;
    private int generation;
    private Runnable pendingSearch;
    private int foreground;
    private int muted;
    private int surface;
    private int accent;

    @Override protected void onCreate(Bundle state) {
        boolean dark = (getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK)
                == Configuration.UI_MODE_NIGHT_YES;
        setTheme(dark ? android.R.style.Theme_DeviceDefault_NoActionBar
                : android.R.style.Theme_DeviceDefault_Light_NoActionBar);
        super.onCreate(state);
        getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
        foreground = dark ? 0xffeef0f8 : 0xff1c2533;
        muted = dark ? 0xffc2c8d7 : 0xff596579;
        surface = dark ? 0xff1d2027 : 0xffedf1f9;
        accent = dark ? 0xffb8caff : 0xff405e9b;
        buildView(dark);
        if (state != null) personalOnly = state.getBoolean("personal_tab", false);
        updateTabs();
        scheduleSearch(false);
    }

    @Override protected void onSaveInstanceState(Bundle state) {
        state.putBoolean("personal_tab", personalOnly);
        super.onSaveInstanceState(state);
    }

    @Override protected void onDestroy() {
        destroyed = true;
        generation++;
        if (pendingSearch != null) main.removeCallbacks(pendingSearch);
        worker.shutdownNow();
        super.onDestroy();
    }

    private void buildView(boolean dark) {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(12), dp(4), dp(12), dp(4));
        root.setBackgroundColor(dark ? 0xff101216 : 0xfff8f9fd);
        setContentView(root);

        LinearLayout bar = horizontal();
        Button back = button("‹", "Back to Khmerlish settings");
        back.setTextSize(28);
        back.setOnClickListener(v -> finish());
        bar.addView(back, new LinearLayout.LayoutParams(dp(52), dp(52)));
        TextView title = text("Khmerlish Dictionary", 20, foreground);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        title.setPadding(dp(8), 0, 0, 0);
        bar.addView(title, new LinearLayout.LayoutParams(0, dp(52), 1));
        root.addView(bar);

        LinearLayout tabs = horizontal();
        guideTab = button("ឯកសារពាក្យ", "Word guide");
        personalTab = button("ផ្ទាល់ខ្លួន", "Personal dictionary");
        guideTab.setOnClickListener(v -> selectTab(false));
        personalTab.setOnClickListener(v -> selectTab(true));
        tabs.addView(guideTab, new LinearLayout.LayoutParams(0, dp(48), 1));
        tabs.addView(personalTab, new LinearLayout.LayoutParams(0, dp(48), 1));
        root.addView(tabs);

        search = new EditText(this);
        search.setSingleLine(true);
        search.setHint("ស្វែងរក Khmerlish ឬ ខ្មែរ");
        search.setContentDescription("Search Khmerlish or Khmer");
        search.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        search.setImeOptions(EditorInfo.IME_FLAG_NO_PERSONALIZED_LEARNING | EditorInfo.IME_ACTION_SEARCH);
        search.setSaveEnabled(false);
        search.setFilters(new InputFilter[]{new InputFilter.LengthFilter(128)});
        search.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) {
                page = 0;
                scheduleSearch(true);
            }
            @Override public void afterTextChanged(Editable s) {}
        });
        root.addView(search, new LinearLayout.LayoutParams(-1, dp(52)));

        personalActions = horizontal();
        Button add = button("＋ បន្ថែម", "Add personal word");
        Button importFile = button("នាំចូល", "Import dictionary file");
        Button exportFile = button("នាំចេញ", "Export personal dictionary");
        add.setOnClickListener(v -> showEditor(null));
        importFile.setOnClickListener(v -> showImportInstructions());
        exportFile.setOnClickListener(v -> chooseDocument(true));
        personalActions.addView(add, new LinearLayout.LayoutParams(0, dp(48), 1));
        personalActions.addView(importFile, new LinearLayout.LayoutParams(0, dp(48), 1));
        personalActions.addView(exportFile, new LinearLayout.LayoutParams(0, dp(48), 1));
        root.addView(personalActions);

        status = text("", 13, muted);
        status.setPadding(dp(4), dp(2), dp(4), dp(2));
        root.addView(status, new LinearLayout.LayoutParams(-1, dp(36)));
        LinearLayout pager = horizontal();
        previous = button("‹", "Previous word page");
        next = button("›", "Next word page");
        pageLabel = text("", 13, muted);
        pageLabel.setGravity(Gravity.CENTER);
        previous.setOnClickListener(v -> { if (page > 0) { page--; scheduleSearch(false); } });
        next.setOnClickListener(v -> { page++; scheduleSearch(false); });
        pager.addView(previous, new LinearLayout.LayoutParams(dp(56), dp(42)));
        pager.addView(pageLabel, new LinearLayout.LayoutParams(0, dp(42), 1));
        pager.addView(next, new LinearLayout.LayoutParams(dp(56), dp(42)));
        root.addView(pager);

        scroll = new ScrollView(this);
        scroll.setFillViewport(false);
        results = new LinearLayout(this);
        results.setOrientation(LinearLayout.VERTICAL);
        results.setPadding(0, dp(4), 0, dp(16));
        scroll.addView(results, new ScrollView.LayoutParams(-1, -2));
        root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1));
    }

    private void selectTab(boolean personal) {
        if (personalOnly == personal) return;
        personalOnly = personal;
        page = 0;
        updateTabs();
        scheduleSearch(false);
    }

    private void updateTabs() {
        guideTab.setTextColor(personalOnly ? muted : accent);
        personalTab.setTextColor(personalOnly ? accent : muted);
        guideTab.setTypeface(Typeface.DEFAULT, personalOnly ? Typeface.NORMAL : Typeface.BOLD);
        personalTab.setTypeface(Typeface.DEFAULT, personalOnly ? Typeface.BOLD : Typeface.NORMAL);
        personalActions.setVisibility(personalOnly ? View.VISIBLE : View.GONE);
    }

    private void scheduleSearch(boolean debounce) {
        if (destroyed || search == null) return;
        int ticket = ++generation;
        if (pendingSearch != null) main.removeCallbacks(pendingSearch);
        String query = search.getText().toString();
        boolean onlyPersonal = personalOnly;
        int requestedPage = page;
        status.setText("កំពុងស្វែងរក… / Loading…");
        pendingSearch = () -> worker.execute(() -> {
            try {
                if (builtIn == null) {
                    builtIn = KhmerlishDictionary.read(getAssets().open("gboard-khmer/dictionary.tsv"));
                }
                Map<String, String> custom = KhmerlishPersonalStore.read(this);
                KhmerlishWordGuide.Page found = KhmerlishWordGuide.search(
                        builtIn.builtInEntries(), custom, query, onlyPersonal, requestedPage);
                main.post(() -> {
                    if (!destroyed && ticket == generation) render(found, onlyPersonal);
                });
            } catch (Throwable failure) {
                main.post(() -> {
                    if (!destroyed && ticket == generation) {
                        results.removeAllViews();
                        status.setText("មិនអាចបើកវចនានុក្រមបាន / Dictionary unavailable");
                        pageLabel.setText("");
                        previous.setEnabled(false);
                        next.setEnabled(false);
                    }
                });
            }
        });
        main.postDelayed(pendingSearch, debounce ? 180 : 0);
    }

    private void render(KhmerlishWordGuide.Page found, boolean onlyPersonal) {
        page = found.index;
        status.setText(onlyPersonal
                ? "ពាក្យផ្ទាល់ខ្លួន " + found.total + " · កែ ឬលុប"
                : "ពាក្យ " + found.total + " · ចុចរូបកែដើម្បីកែ");
        pageLabel.setText((found.index + 1) + " / " + found.pages);
        previous.setEnabled(found.index > 0);
        next.setEnabled(found.index + 1 < found.pages);
        results.removeAllViews();
        if (found.entries.isEmpty()) {
            TextView empty = text(onlyPersonal ? "មិនទាន់មានពាក្យផ្ទាល់ខ្លួន ឬគ្មានលទ្ធផល។"
                    : "រកមិនឃើញពាក្យ។", 15, muted);
            empty.setPadding(dp(12), dp(18), dp(12), dp(18));
            results.addView(empty);
        }
        for (KhmerlishWordGuide.Entry entry : found.entries) {
            LinearLayout row = horizontal();
            row.setPadding(dp(14), dp(2), dp(4), dp(2));
            row.setMinimumHeight(dp(50));
            row.setBackground(rounded(surface, 10));
            TextView label = text(entry.roman + "  →  " + entry.khmer
                    + (entry.personal ? "  · ផ្ទាល់ខ្លួន" : ""), 16, foreground);
            label.setPadding(0, dp(10), dp(4), dp(10));
            String description = (entry.personal ? "Edit personal word " : "Edit word ") + entry.roman;
            label.setContentDescription(description + " " + entry.khmer);
            label.setClickable(true);
            label.setFocusable(true);
            label.setOnClickListener(v -> showEditor(entry));
            row.addView(label, new LinearLayout.LayoutParams(0, -2, 1));
            ImageButton edit = new ImageButton(this);
            edit.setImageResource(android.R.drawable.ic_menu_edit);
            edit.setColorFilter(accent);
            edit.setBackgroundColor(android.graphics.Color.TRANSPARENT);
            edit.setContentDescription(description);
            edit.setOnClickListener(v -> showEditor(entry));
            row.addView(edit, new LinearLayout.LayoutParams(dp(48), dp(48)));
            LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
            params.bottomMargin = dp(3);
            results.addView(row, params);
        }
        scroll.scrollTo(0, 0);
    }

    private void showEditor(KhmerlishWordGuide.Entry original) {
        LinearLayout fields = new LinearLayout(this);
        fields.setOrientation(LinearLayout.VERTICAL);
        fields.setPadding(dp(20), dp(4), dp(20), 0);
        EditText roman = editor("Khmerlish (អក្សរ សញ្ញា និងដកឃ្លា)", "Personal Khmerlish spelling",
                KhmerlishPersonalData.MAX_ROMAN);
        EditText khmer = editor("ពាក្យខ្មែរ / Khmer", "Personal Khmer word", KhmerlishPersonalData.MAX_KHMER);
        boolean builtInEntry = original != null && !original.personal;
        if (original != null) {
            roman.setText(original.roman);
            khmer.setText(original.khmer);
        }
        fields.addView(roman);
        fields.addView(khmer);
        AlertDialog.Builder builder = new AlertDialog.Builder(this)
                .setTitle(original == null ? "បន្ថែមពាក្យ / Add word" : "កែពាក្យ / Edit word")
                .setMessage(builtInEntry
                        ? "ការកែត្រូវរក្សាទុកផ្ទាល់ខ្លួន។ បើប្តូរ Khmerlish នឹងបង្កើតពាក្យថ្មី ហើយពាក្យដើមនៅដដែល។"
                        : "Khmerlish អាចប្រើសញ្ញា និងដកឃ្លា ដូចជា p'o → អត្ថបទខ្មែរ។ ពាក្យផ្ទាល់ខ្លួនមានអាទិភាព។")
                .setView(fields)
                .setPositiveButton("រក្សាទុក / Save", null)
                .setNegativeButton("បោះបង់ / Cancel", null);
        if (original != null && original.personal) builder.setNeutralButton("លុប / Delete", null);
        AlertDialog dialog = builder.create();
        dialog.setOnShowListener(ignored -> {
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
                String key = KhmerlishPersonalData.roman(roman.getText().toString());
                String value = KhmerlishPersonalData.khmer(khmer.getText().toString());
                if (key == null) {
                    roman.setError("បញ្ចូលអក្សរ ឬសញ្ញា (អតិបរមា 64 តួ មិនមានបន្ទាត់ថ្មី ឬ tab)");
                    return;
                }
                if (value == null) {
                    khmer.setError("បញ្ចូលអក្សរខ្មែរ (អតិបរមា 128)");
                    return;
                }
                dialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(false);
                worker.execute(() -> {
                    try {
                        KhmerlishPersonalStore.save(this,
                                original != null && original.personal ? original.roman : null,
                                original != null && original.personal ? original.khmer : null, key, value);
                        main.post(() -> {
                            if (destroyed) return;
                            dialog.dismiss();
                            boolean renamed = original != null && !original.roman.equals(key);
                            if (renamed && search.length() > 0) {
                                search.setText(key);
                                search.setSelection(search.length());
                            }
                            toast(builtInEntry && renamed
                                    ? "បានបន្ថែមពាក្យថ្មី; ពាក្យដើមនៅដដែល។"
                                    : "បានរក្សាទុក / Saved");
                            page = 0;
                            scheduleSearch(false);
                        });
                    } catch (Throwable failure) {
                        main.post(() -> {
                            if (destroyed) return;
                            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setEnabled(true);
                            String reason = failure instanceof IllegalArgumentException
                                    && "duplicate_key".equals(failure.getMessage())
                                    ? "ពាក្យ Khmerlish នេះមានរួចហើយ។ សូមកែពីបញ្ជី។"
                                    : "មិនអាចរក្សាទុកបាន។ សូមពិនិត្យពាក្យ ឬព្យាយាមម្ដងទៀត។";
                            toast(reason);
                        });
                    }
                });
            });
            if (original != null && original.personal) dialog.getButton(AlertDialog.BUTTON_NEUTRAL).setOnClickListener(v ->
                    new AlertDialog.Builder(this).setTitle("លុបពាក្យផ្ទាល់ខ្លួន?")
                            .setMessage("ពាក្យក្នុងវចនានុក្រមដើមនឹងត្រឡប់មកវិញ ប្រសិនបើមាន។")
                            .setNegativeButton("បោះបង់ / Cancel", null)
                            .setPositiveButton("លុប / Delete", (d, which) -> worker.execute(() -> {
                                try {
                                    KhmerlishPersonalStore.delete(this, original.roman, original.khmer);
                                    main.post(() -> {
                                        if (destroyed) return;
                                        dialog.dismiss();
                                        toast("បានលុប / Deleted");
                                        page = 0;
                                        scheduleSearch(false);
                                    });
                                } catch (Throwable failure) {
                                    main.post(() -> { if (!destroyed) toast("មិនអាចលុបបាន / Delete failed"); });
                                }
                            })).show());
        });
        dialog.show();
    }

    private void showImportInstructions() {
        new AlertDialog.Builder(this)
                .setTitle("នាំចូលបញ្ជីពាក្យ / Import word list")
                .setMessage("UTF-8 .txt / .tsv / .csv ប៉ុណ្ណោះ។ មួយជួរមួយគូ៖\n"
                        + "khmerlish,ខ្មែរ\nKhmerlish អាចប្រើសញ្ញា និងដកឃ្លា (អតិបរមា 64 តួ)។\n"
                        + "បើ key មាន comma, សញ្ញា quote ឬចាប់ផ្ដើមដោយ # សូមដាក់ក្នុង quote។\n"
                        + "អតិបរមា 5,000 ពាក្យ និង 2.5 MB។ PDF/DOCX មិនគាំទ្រ។\n"
                        + "ពាក្យទំនាស់នឹងរក្សាទុក លុះត្រាតែអ្នកជ្រើសជំនួស។")
                .setNegativeButton("បោះបង់ / Cancel", null)
                .setPositiveButton("ជ្រើសឯកសារ / Choose file", (dialog, which) -> chooseDocument(false))
                .show();
    }

    @SuppressWarnings("deprecation")
    private void chooseDocument(boolean export) {
        try {
            Intent intent = new Intent(export ? Intent.ACTION_CREATE_DOCUMENT : Intent.ACTION_OPEN_DOCUMENT);
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            intent.setType(export ? "text/plain" : "*/*");
            if (export) {
                intent.putExtra(Intent.EXTRA_TITLE, "khmerlish-personal.tsv");
                intent.addFlags(Intent.FLAG_GRANT_WRITE_URI_PERMISSION);
            } else {
                intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            }
            startActivityForResult(intent, export ? REQUEST_EXPORT : REQUEST_IMPORT);
        } catch (Throwable unavailable) {
            toast("មិនអាចបើកឧបករណ៍ជ្រើសឯកសារ / File picker unavailable");
        }
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (resultCode != RESULT_OK || data == null || data.getData() == null) return;
        Uri selected = data.getData();
        if (requestCode == REQUEST_IMPORT) readImport(selected);
        else if (requestCode == REQUEST_EXPORT) writeExport(selected);
    }

    private void readImport(Uri uri) {
        toast("កំពុងអានឯកសារ… / Reading…");
        worker.execute(() -> {
            try {
                String text = readUtf8(uri);
                Map<String, String> incoming = KhmerlishPersonalData.parse(text);
                KhmerlishPersonalStore.Preview preview = KhmerlishPersonalStore.preview(this, incoming);
                main.post(() -> { if (!destroyed) confirmImport(incoming, preview); });
            } catch (KhmerlishPersonalData.ImportException invalid) {
                main.post(() -> { if (!destroyed) toast(invalid.line > 0
                        ? "ទម្រង់មិនត្រឹមត្រូវនៅជួរទី " + invalid.line
                        : "ឯកសារពាក្យមិនត្រឹមត្រូវ ឬធំពេក"); });
            } catch (Throwable failure) {
                main.post(() -> { if (!destroyed) toast("មិនអាចអានឯកសារ UTF-8 នេះបាន"); });
            }
        });
    }

    private void confirmImport(Map<String, String> incoming, KhmerlishPersonalStore.Preview preview) {
        String message = "ថ្មី: " + preview.added + " · ទំនាស់: " + preview.conflicts
                + " · ដដែល: " + preview.unchanged
                + "\nទម្រង់: Khmerlish,ខ្មែរ ឬ Khmerlish [tab] ខ្មែរ។"
                + "\nពាក្យដែលមានទំនាស់នឹងត្រូវរក្សាទុក លុះត្រាតែអ្នកជ្រើសជំនួស។";
        AlertDialog.Builder builder = new AlertDialog.Builder(this)
                .setTitle("នាំចូលវចនានុក្រម / Import")
                .setMessage(message)
                .setNegativeButton("បោះបង់ / Cancel", null)
                .setPositiveButton("នាំចូល / Keep existing", (d, which) -> applyImport(incoming, preview, false));
        if (preview.conflicts > 0) builder.setNeutralButton("ជំនួសទំនាស់ / Replace",
                (d, which) -> applyImport(incoming, preview, true));
        builder.show();
    }

    private void applyImport(Map<String, String> incoming, KhmerlishPersonalStore.Preview preview,
            boolean replace) {
        worker.execute(() -> {
            try {
                KhmerlishPersonalStore.importEntries(this, preview, incoming, replace);
                main.post(() -> {
                    if (destroyed) return;
                    personalOnly = true;
                    updateTabs();
                    page = 0;
                    toast("បាននាំចូល / Imported");
                    scheduleSearch(false);
                });
            } catch (Throwable failure) {
                main.post(() -> { if (!destroyed) toast("នាំចូលមិនបាន; ទិន្នន័យចាស់មិនត្រូវបានផ្លាស់ប្ដូរ។"); });
            }
        });
    }

    private String readUtf8(Uri uri) throws IOException {
        try (InputStream input = getContentResolver().openInputStream(uri)) {
            if (input == null) throw new IOException("Input unavailable");
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            byte[] buffer = new byte[8192];
            int count;
            while ((count = input.read(buffer)) != -1) {
                if (count == 0) continue;
                if ((long) bytes.size() + count > KhmerlishPersonalData.MAX_IMPORT_BYTES) {
                    throw new IOException("Import too large");
                }
                bytes.write(buffer, 0, count);
            }
            try {
                return StandardCharsets.UTF_8.newDecoder()
                        .onMalformedInput(CodingErrorAction.REPORT)
                        .onUnmappableCharacter(CodingErrorAction.REPORT)
                        .decode(ByteBuffer.wrap(bytes.toByteArray())).toString();
            } catch (CharacterCodingException invalid) {
                throw new IOException("Expected UTF-8 text", invalid);
            }
        }
    }

    private void writeExport(Uri uri) {
        worker.execute(() -> {
            try {
                Map<String, String> words = KhmerlishPersonalStore.read(this);
                byte[] data = KhmerlishPersonalData.exportTsv(words).getBytes(StandardCharsets.UTF_8);
                try (OutputStream output = getContentResolver().openOutputStream(uri, "wt")) {
                    if (output == null) throw new IOException("Output unavailable");
                    output.write(data);
                    output.flush();
                }
                main.post(() -> { if (!destroyed) toast("បាននាំចេញ / Exported"); });
            } catch (Throwable failure) {
                main.post(() -> { if (!destroyed) toast("នាំចេញមិនបាន / Export failed"); });
            }
        });
    }

    private EditText editor(String hint, String description, int length) {
        EditText input = new EditText(this);
        input.setSingleLine(true);
        input.setHint(hint);
        input.setContentDescription(description);
        input.setSaveEnabled(false);
        input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        input.setImeOptions(EditorInfo.IME_FLAG_NO_PERSONALIZED_LEARNING);
        input.setFilters(new InputFilter[]{new InputFilter.LengthFilter(length)});
        return input;
    }

    private LinearLayout horizontal() {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        return row;
    }

    private Button button(String label, String description) {
        Button result = new Button(this);
        result.setText(label);
        result.setTextSize(13);
        result.setAllCaps(false);
        result.setContentDescription(description);
        return result;
    }

    private TextView text(String value, int size, int color) {
        TextView result = new TextView(this);
        result.setText(value);
        result.setTextSize(size);
        result.setTextColor(color);
        result.setGravity(Gravity.CENTER_VERTICAL);
        return result;
    }

    private GradientDrawable rounded(int color, int radius) {
        GradientDrawable result = new GradientDrawable();
        result.setColor(color);
        result.setCornerRadius(dp(radius));
        return result;
    }

    private void toast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_LONG).show();
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }
}
