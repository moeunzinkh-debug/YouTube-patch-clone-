/* A disposable test app only; never bundled into the Gboard patch. */
package dev.jason.gboardpatches.extension.directtranslate;

import android.app.Activity;
import android.os.Bundle;
import android.os.Handler;
import android.util.Log;
import android.view.inputmethod.InputMethodManager;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

public final class AndroidSyntheticActivity extends Activity {
    private static final String TAG = "GboardDirectSmoke";

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        TextView label = new TextView(this);
        label.setText("Gboard synthetic test");
        layout.addView(label);
        EditText editor = new EditText(this);
        editor.setSingleLine(false);
        editor.setHint("Tap here for the test keyboard");
        editor.setMinLines(3);
        layout.addView(editor);
        setContentView(layout);
        editor.requestFocus();
        new Handler().postDelayed(() -> {
            InputMethodManager keyboard = (InputMethodManager) getSystemService(INPUT_METHOD_SERVICE);
            keyboard.showSoftInput(editor, InputMethodManager.SHOW_IMPLICIT);
        }, 800);
        new Thread(() -> {
            GtxClient client = new GtxClient();
            probe(client, "Hello world", "en", "km", "EN_KM");
            probe(client, "សួស្តី", "km", "en", "KM_EN");
            probe(client, "How are you?", "auto", "km", "AUTO_KM");
        }, "synthetic-translate-probe").start();
    }

    private static void probe(GtxClient client, String text, String source, String target, String label) {
        try {
            GtxClient.Translation result = client.translate(text, source, target);
            if (result.text.isEmpty()) throw new IllegalStateException();
            Log.i(TAG, "PASS_" + label);
        } catch (Exception failure) {
            // Fixed synthetic inputs only. Never put text, response bodies or
            // exception messages in logcat.
            Log.i(TAG, "FAIL_" + label + "_" + failure.getClass().getSimpleName());
        }
    }
}
