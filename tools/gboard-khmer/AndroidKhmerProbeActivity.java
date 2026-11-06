package dev.arena.khmerprobe;

import android.app.Activity;
import android.os.Bundle;
import android.text.InputType;
import android.view.inputmethod.InputMethodManager;
import android.view.WindowManager;
import android.widget.EditText;

/** Synthetic editor on a disposable emulator; contains no account or user data. */
public final class AndroidKhmerProbeActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        EditText editor = new EditText(this);
        editor.setId(android.R.id.edit);
        editor.setHint("Synthetic Khmerlish test");
        editor.setInputType(InputType.TYPE_CLASS_TEXT);
        editor.setSingleLine(true);
        setContentView(editor);
        getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_STATE_ALWAYS_VISIBLE);
        editor.requestFocus();
        editor.postDelayed(() -> {
            InputMethodManager manager = (InputMethodManager) getSystemService(INPUT_METHOD_SERVICE);
            if (manager != null) manager.showSoftInput(editor, InputMethodManager.SHOW_IMPLICIT);
        }, 500);
    }
}
