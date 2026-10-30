/* Copyright (C) 2026. This fork is distributed under GPL-3.0-or-later. */
package app.morphe.extension.instanttranslate;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.graphics.Typeface;
import android.text.InputType;
import android.text.method.PasswordTransformationMethod;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;
import android.view.inputmethod.EditorInfo;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import java.lang.ref.WeakReference;

/** Native dialog opened by the Settings Patch row in the app's Settings page. */
public final class SettingsUi {
    private static volatile WeakReference<Activity> currentActivity = new WeakReference<>(null);
    private SettingsUi() {}

    /** Called by the exact-build app's MainActivity after its existing integrity check. */
    public static void attach(Activity activity) {
        if (activity == null) return;
        try {
            ProviderSettings.initialize(activity);
            currentActivity = new WeakReference<>(activity);
        } catch (RuntimeException ignored) {
            // A settings integration error must not prevent the original app from opening.
        }
    }

    /** Called from the application's onCreate, including background-only process starts. */
    public static void initialize(Context context) {
        try { ProviderSettings.initialize(context); } catch (RuntimeException ignored) { /* preserve app startup */ }
    }

    static void open() {
        Activity activity = currentActivity.get();
        if (activity == null || activity.isFinishing() || activity.isDestroyed()) return;
        activity.runOnUiThread(() -> {
            if (activity.isFinishing() || activity.isDestroyed()) return;
            try { show(activity); }
            catch (RuntimeException error) {
                Toast.makeText(activity, "Unable to open Settings Patch", Toast.LENGTH_LONG).show();
            }
        });
    }

    private static int dp(Context c, int value) { return (int) (value * c.getResources().getDisplayMetrics().density + 0.5f); }

    private static TextView label(Context context, String text) {
        TextView view = new TextView(context);
        view.setText(text); view.setTextSize(14); view.setTypeface(null, Typeface.BOLD);
        view.setPadding(0, dp(context, 14), 0, dp(context, 4));
        return view;
    }

    private static EditText field(Context context, String hint, String value) {
        EditText view = new EditText(context);
        view.setSingleLine(true); view.setTextSize(14); view.setHint(hint); view.setText(value);
        return view;
    }

    private static void secure(AlertDialog dialog) {
        Window window = dialog.getWindow();
        if (window != null) window.addFlags(WindowManager.LayoutParams.FLAG_SECURE);
    }

    private static void show(Activity activity) {
        Context context = activity.getApplicationContext();
        LinearLayout content = new LinearLayout(activity);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(activity, 22), dp(activity, 8), dp(activity, 22), dp(activity, 12));
        ScrollView scroll = new ScrollView(activity);
        scroll.setFillViewport(false); scroll.addView(content);

        content.addView(label(activity, "Translation provider"));
        Spinner provider = new Spinner(activity);
        String savedName = ProviderSettings.name(context);
        String[] choices = {"Original only", "Google fallback", savedName};
        provider.setAdapter(new ArrayAdapter<>(activity, android.R.layout.simple_spinner_dropdown_item, choices));
        content.addView(provider);
        String selected = ProviderSettings.selected();
        provider.setSelection(ProviderRouter.SEA_LION.equals(selected) ? 2 : ProviderRouter.ORIGINAL.equals(selected) ? 0 : 1);

        LinearLayout fields = new LinearLayout(activity);
        fields.setOrientation(LinearLayout.VERTICAL);
        content.addView(fields);
        fields.addView(label(activity, "Name"));
        EditText name = field(activity, "Provider name", savedName); fields.addView(name);
        fields.addView(label(activity, "URL"));
        EditText base = field(activity, "HTTPS base URL", ProviderSettings.base(context));
        base.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        fields.addView(base);
        fields.addView(label(activity, "Model"));
        EditText model = field(activity, "Model ID", ProviderSettings.model(context)); fields.addView(model);
        fields.addView(label(activity, "Key"));
        EditText key = field(activity, ProviderSettings.hasKey(context) ? "Saved — leave blank to keep" : "API key", "");
        key.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        key.setTransformationMethod(PasswordTransformationMethod.getInstance());
        key.setSaveEnabled(false);
        key.setImportantForAutofill(View.IMPORTANT_FOR_AUTOFILL_NO);
        key.setImeOptions(EditorInfo.IME_FLAG_NO_PERSONALIZED_LEARNING);
        fields.addView(key);
        TextView help = new TextView(activity);
        help.setText("After an original translation fails, the selected provider may receive its text. SEA-LION also receives your API key; usage limits or charges may apply. The key is encrypted locally and excluded from Android backup.");
        help.setTextSize(12); help.setPadding(0, dp(activity, 16), 0, dp(activity, 8)); content.addView(help);
        provider.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                fields.setVisibility(position == 2 ? View.VISIBLE : View.GONE);
            }
            @Override public void onNothingSelected(AdapterView<?> parent) { fields.setVisibility(View.GONE); }
        });

        AlertDialog dialog = new AlertDialog.Builder(activity).setTitle("Settings Patch")
                .setView(scroll).setNegativeButton("Cancel", (d, w) -> key.setText(""))
                .setNeutralButton("Clear key", null).setPositiveButton("Save", null).create();
        dialog.setOnShowListener(ignored -> {
            secure(dialog);
            dialog.getButton(AlertDialog.BUTTON_NEUTRAL).setOnClickListener(v -> {
                AlertDialog confirm = new AlertDialog.Builder(activity).setTitle("Clear SEA-LION key?")
                        .setMessage("The locally stored key will be removed. If SEA-LION is selected, the provider will switch to Original only.")
                        .setNegativeButton("Cancel", null).setPositiveButton("Clear", (d, w) -> {
                            try {
                                ProviderSettings.clearKey(context);
                                if (provider.getSelectedItemPosition() == 2) provider.setSelection(0);
                                key.setText(""); key.setHint("API key");
                                Toast.makeText(activity, "Key cleared", Toast.LENGTH_SHORT).show();
                            } catch (Exception error) {
                                Toast.makeText(activity, "Unable to clear key securely", Toast.LENGTH_LONG).show();
                            }
                        }).create();
                confirm.show(); secure(confirm);
            });
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(v -> {
                String choice = provider.getSelectedItemPosition() == 2 ? ProviderRouter.SEA_LION :
                        provider.getSelectedItemPosition() == 0 ? ProviderRouter.ORIGINAL : ProviderRouter.GOOGLE;
                String enteredName = name.getText().toString().trim();
                String enteredBase = base.getText().toString().trim();
                String enteredModel = model.getText().toString().trim();
                String enteredKey = key.getText().toString();
                Runnable save = () -> {
                    try {
                        ProviderSettings.save(context, choice, enteredName, enteredBase, enteredModel, enteredKey);
                        key.setText("");
                        dialog.dismiss();
                        Toast.makeText(activity, "Settings saved", Toast.LENGTH_SHORT).show();
                    } catch (Exception error) {
                        // All detailed validation happens without logging user inputs.
                        Toast.makeText(activity, "Unable to save. Check the HTTPS URL, model, name and API key.", Toast.LENGTH_LONG).show();
                    }
                };
                if (ProviderRouter.SEA_LION.equals(choice)) {
                    String host;
                    try { host = SeaLionClient.endpoint(enteredBase).getHost(); }
                    catch (Exception invalid) {
                        Toast.makeText(activity, "Enter a valid HTTPS base URL", Toast.LENGTH_LONG).show();
                        return;
                    }
                    AlertDialog confirm = new AlertDialog.Builder(activity).setTitle("Use SEA-LION fallback?")
                            .setMessage("When the original translation fails, text and your API key will be sent to " + host +
                                    ". This uses internet and may consume your provider quota or incur charges.")
                            .setNegativeButton("Cancel", null).setPositiveButton("I understand", (d, w) -> save.run()).create();
                    confirm.show(); secure(confirm);
                } else {
                    save.run();
                }
            });
        });
        dialog.show();
        secure(dialog);
    }
}
