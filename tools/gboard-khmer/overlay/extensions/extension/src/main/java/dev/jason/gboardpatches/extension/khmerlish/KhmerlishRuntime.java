package dev.jason.gboardpatches.extension.khmerlish;

import android.content.Context;
import android.inputmethodservice.InputMethodService;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.ExtractedText;
import android.view.inputmethod.ExtractedTextRequest;
import android.view.inputmethod.InputConnection;
import android.view.inputmethod.SurroundingText;

import java.lang.ref.WeakReference;

/** Gboard lifecycle bridge. No user text is logged, persisted or transmitted. */
public final class KhmerlishRuntime {
    private static final int WINDOW = 96;
    private static final KhmerlishController CONTROLLER = new KhmerlishController();
    private static volatile KhmerlishDictionary dictionary;
    private static boolean loading;
    private static boolean loadFailed;
    private static long generation;
    private static WeakReference<InputConnection> sessionConnection = new WeakReference<>(null);
    private static boolean editing;

    private KhmerlishRuntime() {}

    public static void onInputViewStarted(InputMethodService service) {
        try {
            reset(service);
            if (service != null && KhmerlishSettings.isEnabled(service)) preload(service);
        } catch (Throwable ignored) {
            // The stock keyboard must remain usable if an extension fails.
        }
    }

    public static void reset(InputMethodService ignored) {
        generation++;
        sessionConnection = new WeakReference<>(null);
        CONTROLLER.reset();
    }

    public static void onSelection(InputMethodService service, int oldStart, int oldEnd,
            int newStart, int newEnd, int composingStart, int composingEnd) {
        try {
            if (service == null || editing || !KhmerlishSettings.isEnabled(service)
                    || !isSafeField(service.getCurrentInputEditorInfo())) {
                reset(service);
                return;
            }
            if (dictionary == null) {
                preload(service);
                return;
            }
            final InputConnection connection = service.getCurrentInputConnection();
            final EditorInfo editor = service.getCurrentInputEditorInfo();
            if (connection == null || newStart != newEnd || newStart < 0) {
                reset(service);
                return;
            }
            if (sessionConnection.get() != connection) {
                generation++;
                sessionConnection = new WeakReference<>(connection);
                CONTROLLER.reset();
            }
            final long capturedGeneration = generation;
            // Let Gboard finish its native callback before touching the editor.
            new Handler(Looper.getMainLooper()).post(() -> {
                try {
                    if (capturedGeneration != generation || editing
                            || service.getCurrentInputConnection() != connection
                            || service.getCurrentInputEditorInfo() != editor
                            || !KhmerlishSettings.isEnabled(service) || !isSafeField(editor)) return;
                    CharSequence before = readBeforeAtCursor(connection, newStart, newEnd);
                    if (before == null) return; // stale callback or an unsupported editor
                    KhmerlishController.Edit edit = CONTROLLER.observe(
                            before, newEnd, composingStart, composingEnd, dictionary);
                    if (edit != null) {
                        editing = true;
                        try {
                            if (applyEdit(connection, before, edit)) CONTROLLER.applied(edit);
                            else CONTROLLER.reset();
                        } finally {
                            editing = false;
                        }
                    }
                } catch (Throwable ignored) {
                    CONTROLLER.reset();
                }
            });
        } catch (Throwable ignored) {
            reset(service);
        }
    }

    static boolean isSafeField(EditorInfo editor) {
        if (editor == null) return false;
        int type = editor.inputType;
        if ((type & InputType.TYPE_MASK_CLASS) != InputType.TYPE_CLASS_TEXT) return false;
        int variation = type & InputType.TYPE_MASK_VARIATION;
        if (variation == InputType.TYPE_TEXT_VARIATION_PASSWORD
                || variation == InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD
                || variation == InputType.TYPE_TEXT_VARIATION_WEB_PASSWORD
                || variation == InputType.TYPE_TEXT_VARIATION_EMAIL_ADDRESS
                || variation == InputType.TYPE_TEXT_VARIATION_WEB_EMAIL_ADDRESS
                || variation == InputType.TYPE_TEXT_VARIATION_URI) return false;
        return (type & InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS) == 0
                && (editor.imeOptions & EditorInfo.IME_FLAG_NO_PERSONALIZED_LEARNING) == 0;
    }

    /** Reject delayed selection notifications, selections, and editors that cannot report a cursor. */
    static CharSequence readBeforeAtCursor(InputConnection connection, int start, int end) {
        if (start != end) return null;
        if (Build.VERSION.SDK_INT >= 31) {
            CursorView view = Api31.read(connection, end);
            // An authoritative mismatch means a stale callback; never fall back
            // to another API to bypass that result. Unavailable offsets may fall back.
            if (view.authoritative) return view.before;
        }
        ExtractedTextRequest request = new ExtractedTextRequest();
        request.hintMaxChars = WINDOW;
        request.hintMaxLines = 1;
        ExtractedText text = connection.getExtractedText(request, 0);
        if (text == null || text.selectionStart != text.selectionEnd || text.startOffset < 0
                || text.startOffset + text.selectionStart != end) return null;
        return connection.getTextBeforeCursor(WINDOW, 0);
    }

    private static final class CursorView {
        final boolean authoritative;
        final CharSequence before;
        CursorView(boolean authoritative, CharSequence before) {
            this.authoritative = authoritative;
            this.before = before;
        }
    }

    // Isolate the Android 12 API reference so the bridge can load on older Android.
    private static final class Api31 {
        static CursorView read(InputConnection connection, int expectedEnd) {
            try {
                SurroundingText text = connection.getSurroundingText(WINDOW, 0, 0);
                if (text == null || text.getText() == null || text.getOffset() < 0) {
                    return new CursorView(false, null);
                }
                int selected = text.getSelectionStart();
                if (selected != text.getSelectionEnd() || selected < 0
                        || selected > text.getText().length()
                        || text.getOffset() + selected != expectedEnd) {
                    return new CursorView(true, null);
                }
                return new CursorView(true, text.getText().subSequence(0, selected));
            } catch (Throwable unavailable) {
                return new CursorView(false, null);
            }
        }
    }

    /** Recheck the exact suffix, batch the edit, and attempt rollback if insertion fails. */
    static boolean applyEdit(InputConnection connection, CharSequence observed,
            KhmerlishController.Edit edit) {
        if (connection == null || observed == null || edit == null || edit.deleteBefore <= 0
                || edit.deleteBefore > observed.length()) return false;
        String original = observed.subSequence(observed.length() - edit.deleteBefore,
                observed.length()).toString();
        boolean started = false;
        boolean deleted = false;
        try {
            CharSequence selected = connection.getSelectedText(0);
            if (selected != null && selected.length() != 0) return false;
            CharSequence current = connection.getTextBeforeCursor(edit.deleteBefore, 0);
            if (current == null || !original.contentEquals(current)) return false;
            started = connection.beginBatchEdit();
            if (!started) return false;
            if (!connection.deleteSurroundingText(edit.deleteBefore, 0)) return false;
            deleted = true;
            if (!connection.commitText(edit.insert, 1)) return false;
            deleted = false;
            return true;
        } catch (Throwable ignored) {
            return false;
        } finally {
            // Some editors implement InputConnection incompletely; recovery is best effort.
            if (deleted) {
                try { connection.commitText(original, 1); } catch (Throwable ignored) {}
            }
            if (started) {
                try { connection.endBatchEdit(); } catch (Throwable ignored) {}
            }
        }
    }

    static void preload(Context context) {
        if (context == null || dictionary != null) return;
        final Context application = context.getApplicationContext() != null
                ? context.getApplicationContext() : context;
        synchronized (KhmerlishRuntime.class) {
            if (dictionary != null || loading || loadFailed) return;
            loading = true;
        }
        Thread worker = new Thread(() -> {
            KhmerlishDictionary loaded = null;
            try {
                loaded = KhmerlishDictionary.read(
                        application.getAssets().open("gboard-khmer/dictionary.tsv"));
            } catch (Throwable ignored) {
                // Missing/corrupt assets fail closed; no typed content is logged.
            }
            synchronized (KhmerlishRuntime.class) {
                dictionary = loaded;
                loadFailed = loaded == null;
                loading = false;
            }
        }, "GboardKhmerlishDictionary");
        worker.setDaemon(true);
        worker.start();
    }
}
