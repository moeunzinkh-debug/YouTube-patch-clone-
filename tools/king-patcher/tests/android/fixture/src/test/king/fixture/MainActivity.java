package test.king.fixture;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import com.android.vending.licensing.LicenseChecker;
import com.android.vending.licensing.LicenseCheckerCallback;

/** Disposable test app: no live license check, purchases, or network calls. */
public final class MainActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        int layout = getResources().getIdentifier("activity_main", "layout", getPackageName());
        setContentView(layout);
        int id = getResources().getIdentifier("licence", "id", getPackageName());
        TextView status = findViewById(id);
        new LicenseChecker().checkAccess(new LicenseCheckerCallback() {
            @Override public void allow(int reason) { status.setText("LICENSED-" + reason); }
            @Override public void dontAllow(int reason) { status.setText("DENIED-" + reason); }
            @Override public void applicationError(int reason) { status.setText("ERROR-" + reason); }
        });
    }
}
