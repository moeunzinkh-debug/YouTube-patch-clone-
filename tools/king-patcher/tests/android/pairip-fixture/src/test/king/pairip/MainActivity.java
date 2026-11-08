package test.king.pairip;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import com.pairip.licensecheck.LicenseClient;

/** Synthetic counters only: no network, real license, purchase or user data. */
public final class MainActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        new LicenseClient().initializeLicenseCheck();
        TextView result = new TextView(this);
        result.setText("PAIRIP-" + LicenseClient.checkRuns + "-" + LicenseClient.initRuns);
        setContentView(result);
    }
}
