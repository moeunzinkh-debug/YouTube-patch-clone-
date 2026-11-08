package test.genv;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import com.pairip.licensecheck.LicenseClient;

/** Counters only: entirely synthetic, with no network, account or GenV code. */
public final class MainActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        new LicenseClient().initializeLicenseCheck();
        TextView result = new TextView(this);
        result.setText("SYNTHETIC-PAIRIP-" + LicenseClient.checkRuns + "-" + LicenseClient.initRuns);
        setContentView(result);
    }
}
