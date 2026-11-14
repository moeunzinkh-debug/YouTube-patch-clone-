package dev.jason.gboardpatches.extension.khmerlish;

import android.content.Context;
import android.content.res.Configuration;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.inputmethodservice.InputMethodService;
import android.os.Handler;
import android.os.Looper;
import android.text.Editable;
import android.text.InputFilter;
import android.text.InputType;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewParent;
import android.view.Window;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.ExtractedText;
import android.view.inputmethod.ExtractedTextRequest;
import android.view.inputmethod.InputConnection;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * A self-contained, offline keyboard panel in the IME's own window. It does not
 * launch Google Translate, use the network, or persist or log editor contents.
 */
public final class KhmerlishPanelRuntime {
    private static WeakReference<InputMethodService> serviceRef = new WeakReference<>(null);
    private static Panel panel;
    private static long generation;

    private KhmerlishPanelRuntime() {}

    static void inputStarted(InputMethodService service) {
        dismiss();
        serviceRef = new WeakReference<>(service);
    }

    static void inputFinished(InputMethodService service) {
        dismiss();
        if (service == null || serviceRef.get() == service) {
            serviceRef = new WeakReference<>(null);
        }
    }

    static boolean isActive(InputMethodService service) {
        return panel != null && panel.service == service;
    }

    /** Invoked only from the synthetic Khmerlish access point. */
    public static void open(Context context) {
        try {
            InputMethodService service = serviceRef.get();
            if (service == null || !KhmerlishRuntime.isSafeField(service.getCurrentInputEditorInfo())
                    || service.getCurrentInputConnection() == null) {
                notifyUser(context, "Khmerlish is unavailable for this field");
                return;
            }
            if (panel != null) {
                dismiss();
                return;
            }
            KhmerlishRuntime.preload(service);
            long ticket = ++generation;
            InputConnection connection = service.getCurrentInputConnection();
            EditorInfo editor = service.getCurrentInputEditorInfo();
            awaitDictionary(new WeakReference<>(service), connection, editor, ticket, 0);
        } catch (Throwable ignored) {
            notifyUser(context, "Khmerlish panel is unavailable");
        }
    }

    private static void awaitDictionary(WeakReference<InputMethodService> reference,
            InputConnection connection, EditorInfo editor, long ticket, int attempt) {
        InputMethodService service = reference.get();
        if (service == null || ticket != generation || panel != null
                || service.getCurrentInputConnection() != connection
                || service.getCurrentInputEditorInfo() != editor
                || !KhmerlishRuntime.isSafeField(editor)) return;
        KhmerlishDictionary dictionary = KhmerlishRuntime.dictionaryIfReady();
        if (dictionary == null) {
            if (attempt >= 40) {
                notifyUser(service, "Khmerlish dictionary could not be loaded");
                return;
            }
            new Handler(Looper.getMainLooper()).postDelayed(
                    () -> awaitDictionary(reference, connection, editor, ticket, attempt + 1), 100);
            return;
        }
        try {
            Window window = service.getWindow() == null ? null : service.getWindow().getWindow();
            if (window == null) throw new IllegalStateException("IME window unavailable");
            // Gboard's decor can occupy the whole screen while only the bottom
            // keyboard area receives touches. Overlay the real keyboard holder,
            // never the full decor (which could cover the host app's editor).
            int holderId = service.getResources().getIdentifier(
                    "keyboard_holder", "id", service.getPackageName());
            View holder = holderId == 0 ? null : window.findViewById(holderId);
            if (holder == null || !holder.isShown()
                    || holder.getWidth() < dp(service, 180) || holder.getHeight() < dp(service, 160)) {
                throw new IllegalStateException("Gboard keyboard area unavailable");
            }
            FrameLayout parent = findOverlayParent(holder);
            if (parent == null) throw new IllegalStateException("Keyboard overlay area unavailable");
            Panel next = new Panel(service, connection, editor, dictionary, parent, holder);
            panel = next;
            // Commit any previous Gboard composition before starting our own.
            connection.finishComposingText();
            next.attach();
        } catch (Throwable ignored) {
            dismiss();
            notifyUser(service, "Khmerlish panel is unavailable");
        }
    }

    private static int dp(Context context, int value) {
        return Math.round(value * context.getResources().getDisplayMetrics().density);
    }

    private static FrameLayout findOverlayParent(View holder) {
        for (ViewParent candidate = holder.getParent(); candidate instanceof View;
                candidate = candidate.getParent()) {
            if (candidate instanceof FrameLayout
                    && overlayLayout((FrameLayout) candidate, holder) != null) {
                return (FrameLayout) candidate;
            }
        }
        return null;
    }

    /** The holder and its ancestor are already laid out in the same window. */
    private static FrameLayout.LayoutParams overlayLayout(FrameLayout parent, View holder) {
        int[] parentLocation = new int[2];
        int[] holderLocation = new int[2];
        parent.getLocationOnScreen(parentLocation);
        holder.getLocationOnScreen(holderLocation);
        int width = holder.getWidth(), height = holder.getHeight();
        int left = holderLocation[0] - parentLocation[0] - parent.getPaddingLeft();
        int top = holderLocation[1] - parentLocation[1] - parent.getPaddingTop();
        int availableWidth = parent.getWidth() - parent.getPaddingLeft() - parent.getPaddingRight();
        int availableHeight = parent.getHeight() - parent.getPaddingTop() - parent.getPaddingBottom();
        if (!KhmerlishPanelBounds.fits(availableWidth, availableHeight, left, top, width, height)) {
            return null;
        }
        FrameLayout.LayoutParams layout = new FrameLayout.LayoutParams(width, height, Gravity.TOP | Gravity.LEFT);
        layout.leftMargin = left;
        layout.topMargin = top;
        return layout;
    }

    static void onSelection(InputMethodService service, int start, int end,
            int composingStart, int composingEnd) {
        Panel current = panel;
        if (current == null || current.service != service || !current.written) return;
        // A selection in the host field must not be overwritten. A collapsed
        // cursor move is checked authoritatively before the next panel edit.
        if (start != end) dismiss();
    }

    public static void dismiss() {
        generation++;
        Panel old = panel;
        if (old != null) {
            old.written = false;
            old.close();
            if (panel == old) panel = null;
        }
    }

    private static void notifyUser(Context context, String message) {
        try {
            if (context != null) Toast.makeText(context, message, Toast.LENGTH_SHORT).show();
        } catch (Throwable ignored) {}
    }

    private static final class Panel {
        final InputMethodService service;
        final InputConnection connection;
        final EditorInfo editor;
        final FrameLayout parent;
        final View holder;
        final KhmerlishDictionary dictionary;
        final LinearLayout root;
        final EditText input;
        final HorizontalScrollView suggestionScroll;
        final LinearLayout suggestionRow;
        final KhmerlishPanelSession session;
        final TextWatcher watcher;
        final View.OnLayoutChangeListener layoutListener;
        final List<TextView> letterKeys = new ArrayList<>();
        final boolean dark;
        TextView shiftKey;
        TextView modeKey;
        int previousAccessibility;
        boolean accessibilityHidden;
        boolean written;
        boolean shift;
        boolean symbols;
        boolean moreSymbols;

        Panel(InputMethodService service, InputConnection connection, EditorInfo editor,
                KhmerlishDictionary dictionary, FrameLayout parent, View holder) {
            this.service = service;
            this.connection = connection;
            this.editor = editor;
            this.parent = parent;
            this.holder = holder;
            this.dictionary = dictionary;
            layoutListener = (view, left, top, right, bottom, oldLeft, oldTop, oldRight, oldBottom)
                    -> updatePosition();
            dark = (service.getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK)
                    == Configuration.UI_MODE_NIGHT_YES;
            root = new LinearLayout(service);
            root.setOrientation(LinearLayout.VERTICAL);
            root.setPadding(dp(5), dp(3), dp(5), dp(4));
            root.setBackgroundColor(dark ? 0xff202124 : 0xffe8edf5);
            root.setContentDescription("Khmerlish offline panel");
            root.setClickable(true);

            LinearLayout header = new LinearLayout(service);
            header.setGravity(Gravity.CENTER_VERTICAL);
            TextView title = new TextView(service);
            title.setText("Khmerlish → ខ្មែរ  ·  Offline");
            title.setTextSize(15);
            title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
            title.setTextColor(dark ? Color.WHITE : 0xff263247);
            header.addView(title, new LinearLayout.LayoutParams(0, dp(32), 1));
            TextView close = plainButton("✕", "Close Khmerlish panel");
            close.setOnClickListener(v -> dismiss());
            header.addView(close, new LinearLayout.LayoutParams(dp(48), dp(32)));
            root.addView(header);

            input = new EditText(service);
            input.setSingleLine(true);
            input.setTextSize(17);
            input.setHint("Type Khmerlish here");
            input.setContentDescription("Khmerlish input");
            input.setTextColor(dark ? Color.WHITE : 0xff1c2533);
            input.setHintTextColor(dark ? 0xffb9c1cb : 0xff6d7889);
            input.setPadding(dp(12), 0, dp(12), 0);
            input.setBackground(background(dark ? 0xff393b40 : Color.WHITE, 12));
            input.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
            input.setShowSoftInputOnFocus(false);
            input.setSaveEnabled(false);
            input.setFilters(new InputFilter[]{new InputFilter.LengthFilter(KhmerlishPanelConverter.MAX_LENGTH)});
            root.addView(input, new LinearLayout.LayoutParams(-1, dp(40)));

            suggestionScroll = new HorizontalScrollView(service);
            suggestionScroll.setHorizontalScrollBarEnabled(false);
            suggestionScroll.setFillViewport(false);
            suggestionScroll.setContentDescription("Khmerlish predictions");
            suggestionScroll.setVisibility(View.GONE);
            suggestionRow = new LinearLayout(service);
            suggestionRow.setOrientation(LinearLayout.HORIZONTAL);
            suggestionRow.setGravity(Gravity.CENTER_VERTICAL);
            suggestionScroll.addView(suggestionRow, new HorizontalScrollView.LayoutParams(
                    -2, HorizontalScrollView.LayoutParams.MATCH_PARENT));
            root.addView(suggestionScroll, new LinearLayout.LayoutParams(-1, dp(38)));

            KhmerlishPanelCommitter.Host host = new KhmerlishPanelCommitter.Host() {
                @Override public boolean isCurrent() {
                    return panel == Panel.this && service.getCurrentInputConnection() == connection
                            && service.getCurrentInputEditorInfo() == editor
                            && KhmerlishRuntime.isSafeField(editor);
                }
                @Override public int cursor() {
                    ExtractedTextRequest request = new ExtractedTextRequest();
                    request.hintMaxChars = 1;
                    request.hintMaxLines = 1;
                    ExtractedText current = connection.getExtractedText(request, 0);
                    if (current == null || current.startOffset < 0 || current.selectionStart < 0
                            || current.selectionStart != current.selectionEnd) return -1;
                    long position = (long) current.startOffset + current.selectionStart;
                    return position > Integer.MAX_VALUE ? -1 : (int) position;
                }
                @Override public CharSequence before(int length) {
                    return connection.getTextBeforeCursor(length, 0);
                }
                @Override public boolean begin() { return connection.beginBatchEdit(); }
                @Override public boolean deleteBefore(int length) {
                    return connection.deleteSurroundingText(length, 0);
                }
                @Override public boolean commit(String value) { return connection.commitText(value, 1); }
                @Override public void end() { connection.endBatchEdit(); }
            };
            session = new KhmerlishPanelSession(dictionary, new KhmerlishPanelCommitter(host));
            watcher = new TextWatcher() {
                @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) {}
                @Override public void onTextChanged(CharSequence s, int start, int before, int count) {}
                @Override public void afterTextChanged(Editable editable) {
                    if (!session.update(editable)) {
                        notifyUser(service, "This field cannot safely update Khmerlish text");
                        root.post(KhmerlishPanelRuntime::dismiss);
                    } else {
                        written = true;
                        updateSuggestions(editable, input.getSelectionStart());
                    }
                }
            };
            input.addTextChangedListener(watcher);
            addKeyboard();
        }

        void attach() {
            FrameLayout.LayoutParams layout = overlayLayout(parent, holder);
            if (layout == null) throw new IllegalStateException("Keyboard area changed");
            root.setElevation(dp(8));
            parent.addView(root, layout);
            previousAccessibility = holder.getImportantForAccessibility();
            holder.setImportantForAccessibility(View.IMPORTANT_FOR_ACCESSIBILITY_NO_HIDE_DESCENDANTS);
            accessibilityHidden = true;
            holder.addOnLayoutChangeListener(layoutListener);
            parent.addOnLayoutChangeListener(layoutListener);
            input.requestFocus();
        }

        void updatePosition() {
            if (panel != this || root.getParent() != parent) return;
            FrameLayout.LayoutParams next = overlayLayout(parent, holder);
            if (next == null || holder.getWidth() < dp(180) || holder.getHeight() < dp(160)) {
                root.post(() -> { if (panel == this) KhmerlishPanelRuntime.dismiss(); });
                return;
            }
            FrameLayout.LayoutParams old = (FrameLayout.LayoutParams) root.getLayoutParams();
            if (old.width != next.width || old.height != next.height
                    || old.leftMargin != next.leftMargin || old.topMargin != next.topMargin) {
                root.setLayoutParams(next);
            }
        }

        void close() {
            holder.removeOnLayoutChangeListener(layoutListener);
            parent.removeOnLayoutChangeListener(layoutListener);
            input.removeTextChangedListener(watcher);
            session.close();
            try { input.setText(""); } catch (Throwable ignored) {}
            if (root.getParent() instanceof ViewGroup) {
                ((ViewGroup) root.getParent()).removeView(root);
            }
            if (accessibilityHidden
                    && holder.getImportantForAccessibility() == View.IMPORTANT_FOR_ACCESSIBILITY_NO_HIDE_DESCENDANTS) {
                holder.setImportantForAccessibility(previousAccessibility);
            }
            accessibilityHidden = false;
        }

        void addKeyboard() {
            LinearLayout keyboard = new LinearLayout(service);
            keyboard.setOrientation(LinearLayout.VERTICAL);
            LinearLayout.LayoutParams keyboardParams = new LinearLayout.LayoutParams(-1, 0, 1);
            keyboardParams.topMargin = dp(3);
            root.addView(keyboard, keyboardParams);
            addLetterRow(keyboard, "qwertyuiop", false);
            addLetterRow(keyboard, "asdfghjkl", false);
            addLetterRow(keyboard, "zxcvbnm", true);
            LinearLayout bottom = row(keyboard);
            modeKey = key("?123", "Khmerlish symbols", 1.4f);
            modeKey.setOnClickListener(v -> { symbols = !symbols; moreSymbols = false; updateKeyLabels(); });
            bottom.addView(modeKey, keyParams(1.4f));
            addCharacterKey(bottom, ",", 1);
            TextView space = key("space", "Khmerlish key space", 5);
            space.setOnClickListener(v -> insert(" "));
            bottom.addView(space, keyParams(5));
            addCharacterKey(bottom, ".", 1);
            TextView done = key("✓", "Done Khmerlish", 1.4f);
            done.setOnClickListener(v -> dismiss());
            bottom.addView(done, keyParams(1.4f));
        }

        void addLetterRow(LinearLayout keyboard, String letters, boolean modifiers) {
            LinearLayout row = row(keyboard);
            if (modifiers) {
                shiftKey = key("⇧", "Khmerlish shift", 1.3f);
                shiftKey.setOnClickListener(v -> {
                    if (symbols) moreSymbols = !moreSymbols;
                    else shift = !shift;
                    updateKeyLabels();
                });
                row.addView(shiftKey, keyParams(1.3f));
            }
            for (int i = 0; i < letters.length(); i++) {
                String letter = String.valueOf(letters.charAt(i));
                TextView key = key(letter, "Khmerlish key " + letter, 1);
                key.setTag(letter);
                key.setOnClickListener(v -> {
                    String value = ((TextView) v).getText().toString();
                    insert(value);
                    if (shift && !symbols) { shift = false; updateKeyLabels(); }
                });
                letterKeys.add(key);
                row.addView(key, keyParams(1));
            }
            if (modifiers) {
                TextView back = key("⌫", "Khmerlish backspace", 1.3f);
                back.setOnClickListener(v -> backspace());
                row.addView(back, keyParams(1.3f));
            }
        }

        void updateKeyLabels() {
            // Both symbol pages together, plus the comma and period keys,
            // provide every printable ASCII punctuation character.
            String symbolKeys = moreSymbols ? KhmerlishPanelKeys.MORE : KhmerlishPanelKeys.PRIMARY;
            if (modeKey != null) modeKey.setText(symbols ? "ABC" : "?123");
            if (shiftKey != null) {
                shiftKey.setText(symbols ? (moreSymbols ? "1/2" : "2/2") : "⇧");
                shiftKey.setContentDescription(symbols ? "More Khmerlish symbols" : "Khmerlish shift");
            }
            for (int i = 0; i < letterKeys.size(); i++) {
                TextView key = letterKeys.get(i);
                String value = symbols ? String.valueOf(symbolKeys.charAt(i)) : (String) key.getTag();
                if (shift && !symbols) value = value.toUpperCase(Locale.ROOT);
                key.setText(value);
                key.setContentDescription("Khmerlish key " + value.toLowerCase(Locale.ROOT));
            }
        }

        LinearLayout row(LinearLayout parent) {
            LinearLayout row = new LinearLayout(service);
            row.setGravity(Gravity.CENTER);
            parent.addView(row, new LinearLayout.LayoutParams(-1, 0, 1));
            return row;
        }

        void addCharacterKey(LinearLayout row, String character, float weight) {
            TextView key = key(character, "Khmerlish key " + character, weight);
            key.setOnClickListener(v -> insert(character));
            row.addView(key, keyParams(weight));
        }

        TextView key(String label, String description, float weight) {
            TextView result = plainButton(label, description);
            result.setBackground(background(dark ? 0xff484b51 : Color.WHITE, 6));
            result.setTextSize(label.length() > 3 ? 13 : 20);
            return result;
        }

        TextView plainButton(String label, String description) {
            TextView result = new TextView(service);
            result.setGravity(Gravity.CENTER);
            result.setText(label);
            result.setContentDescription(description);
            result.setTextColor(dark ? Color.WHITE : 0xff273141);
            result.setClickable(true);
            result.setFocusable(false);
            return result;
        }

        LinearLayout.LayoutParams keyParams(float weight) {
            LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, -1, weight);
            params.setMargins(dp(2), dp(2), dp(2), dp(2));
            return params;
        }

        void updateSuggestions(CharSequence text, int cursor) {
            suggestionRow.removeAllViews();
            int start = predictionStart(text, cursor);
            if (start < 0) {
                suggestionScroll.setVisibility(View.GONE);
                return;
            }
            List<String> values = dictionary.suggest(text.subSequence(start, cursor).toString(), 5);
            for (String value : values) {
                TextView candidate = plainButton(value, "Khmerlish suggestion " + value);
                candidate.setTextSize(18);
                candidate.setPadding(dp(14), 0, dp(14), 0);
                candidate.setBackground(background(dark ? 0xff484b51 : Color.WHITE, 12));
                candidate.setOnClickListener(view -> chooseSuggestion(value));
                LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-2, -1);
                params.setMargins(dp(2), dp(2), dp(2), dp(2));
                suggestionRow.addView(candidate, params);
            }
            suggestionScroll.setVisibility(values.isEmpty() ? View.GONE : View.VISIBLE);
            suggestionScroll.scrollTo(0, 0);
        }

        void chooseSuggestion(String value) {
            Editable text = input.getText();
            int cursor = input.getSelectionStart();
            int start = predictionStart(text, cursor);
            if (start < 0 || !dictionary.suggest(text.subSequence(start, cursor).toString(), 5)
                    .contains(value)) return;
            text.replace(start, cursor, value);
            input.setSelection(Math.min(start + value.length(), text.length()));
        }

        static int predictionStart(CharSequence text, int cursor) {
            if (text == null || cursor <= 0 || cursor > text.length()) return -1;
            int start = cursor;
            while (start > 0) {
                char value = text.charAt(start - 1);
                if (Character.isWhitespace(value) || value < 0x21 || value > 0x7e) break;
                start--;
            }
            return start == cursor ? -1 : start;
        }

        void insert(String value) {
            Editable text = input.getText();
            int start = Math.max(0, input.getSelectionStart());
            int end = Math.max(start, input.getSelectionEnd());
            text.replace(start, end, value);
            input.setSelection(Math.min(start + value.length(), text.length()));
        }

        void backspace() {
            Editable text = input.getText();
            int start = Math.max(0, input.getSelectionStart());
            int end = Math.max(start, input.getSelectionEnd());
            if (end > start) text.delete(start, end);
            else if (start > 0) {
                int previous = start - 1;
                if (previous > 0 && Character.isLowSurrogate(text.charAt(previous))
                        && Character.isHighSurrogate(text.charAt(previous - 1))) previous--;
                text.delete(previous, start);
            }
        }

        int dp(int value) {
            return Math.round(value * service.getResources().getDisplayMetrics().density);
        }

        GradientDrawable background(int color, int radius) {
            GradientDrawable drawable = new GradientDrawable();
            drawable.setColor(color);
            drawable.setCornerRadius(dp(radius));
            return drawable;
        }
    }
}
