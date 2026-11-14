package dev.jason.gboardpatches.extension.geminirouter;

import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.inputmethodservice.InputMethodService;
import android.net.Uri;
import android.text.InputType;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.InputConnection;
import android.widget.Toast;

import java.util.Locale;

/** Explicit user-initiated bridge from selected editor text to Gemini web chat. */
public final class GeminiChatRouter {
    static final String GEMINI_URL = "https://gemini.google.com/app";
    private static final int MAX_SELECTION = 8000;

    private GeminiChatRouter() {}

    public static void open(Context context) {
        if (context == null) return;
        boolean copied = false;
        try {
            if (context instanceof InputMethodService service
                    && !isSensitive(service.getCurrentInputEditorInfo())) {
                InputConnection connection = service.getCurrentInputConnection();
                CharSequence selected = connection == null ? null : connection.getSelectedText(0);
                String text = selected == null ? "" : selected.toString().trim();
                if (!text.isEmpty()) {
                    String prompt = buildPrompt(text, Locale.getDefault().getDisplayLanguage(Locale.ENGLISH));
                    ClipboardManager clipboard = (ClipboardManager) context.getSystemService(Context.CLIPBOARD_SERVICE);
                    if (clipboard != null) {
                        clipboard.setPrimaryClip(ClipData.newPlainText("Gemini translation prompt", prompt));
                        copied = true;
                    }
                }
            }
        } catch (Throwable ignored) {
            // Opening Gemini must not destabilize the IME if an editor rejects selection reads.
        }
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(GEMINI_URL));
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            context.startActivity(intent);
            Toast.makeText(context, copied
                    ? "Translation prompt copied. Paste it in Gemini and send."
                    : "Gemini opened. Select text before tapping Gmn to copy a translation prompt.",
                    Toast.LENGTH_LONG).show();
        } catch (Throwable ignored) {
            try { Toast.makeText(context, "Unable to open Gemini.", Toast.LENGTH_SHORT).show(); }
            catch (Throwable ignoredAgain) {}
        }
    }

    static String buildPrompt(String selected, String targetLanguage) {
        String text = selected == null ? "" : selected.trim();
        if (text.length() > MAX_SELECTION) text = text.substring(0, MAX_SELECTION);
        String target = targetLanguage == null || targetLanguage.trim().isEmpty()
                ? "the language I request" : targetLanguage.trim();
        return "Translate the text below into " + target +
                ". Detect the source language and return only the translation, without notes or quotation marks.\n\n" + text;
    }

    static boolean isSensitive(EditorInfo info) {
        if (info == null) return true;
        int type = info.inputType;
        int variation = type & InputType.TYPE_MASK_VARIATION;
        if ((type & InputType.TYPE_MASK_CLASS) == InputType.TYPE_CLASS_TEXT) {
            if (variation == InputType.TYPE_TEXT_VARIATION_PASSWORD
                    || variation == InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD
                    || variation == InputType.TYPE_TEXT_VARIATION_WEB_PASSWORD) return true;
        }
        if ((type & InputType.TYPE_MASK_CLASS) == InputType.TYPE_CLASS_NUMBER
                && variation == InputType.TYPE_NUMBER_VARIATION_PASSWORD) return true;
        return (info.imeOptions & EditorInfo.IME_FLAG_NO_PERSONALIZED_LEARNING) != 0;
    }
}
