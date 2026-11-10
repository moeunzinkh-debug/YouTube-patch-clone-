package test.genv.microg;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.os.Bundle;
import android.widget.TextView;
import app.morphe.extension.genv.MicroGGuard;
import com.google.android.gms.auth.api.signin.internal.SignInConfiguration;

/**
 * A synthetic, credential-free caller for MicroG's interactive sign-in route.
 * This is not GenV and never contacts Google, a user account or a server.
 */
public final class HandoffProbeActivity extends Activity {
    private static final String ACTION = "app.revanced.android.gms.auth.GOOGLE_SIGN_IN";
    private static final int REQUEST = 42;
    private TextView result;

    private boolean offline() {
        ConnectivityManager cm = (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
        @SuppressWarnings("deprecation") NetworkInfo active = cm == null ? null : cm.getActiveNetworkInfo();
        return active == null || !active.isConnected();
    }

    private void show(String status) {
        result.setText("HANDOFF:" + status + ";NETWORK:" + (offline() ? "OFF" : "ON"));
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        result = new TextView(this);
        result.setTextSize(20);
        setContentView(result);
        if (!offline()) { show("NETWORK_REQUIRED_OFF"); return; }
        if (!MicroGGuard.isAvailable(this)) { show("GUARD_REJECTED"); return; }
        if (state != null) { show("WAITING"); return; }

        String caller = getIntent().getBooleanExtra("mismatch", false)
                ? "test.genv.not.the.caller" : getPackageName();
        Bundle configuration = new Bundle();
        configuration.putParcelable("config", new SignInConfiguration(caller));
        Intent hub = new Intent(ACTION).setClass(this, SyntheticHubActivity.class);
        hub.putExtra("config", configuration);
        try {
            show("WAITING");
            startActivityForResult(hub, REQUEST);
        } catch (Exception ignored) {
            show("START_FAILED");
        }
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQUEST) return;
        int status = data == null ? -1 : data.getIntExtra("test_status", -1);
        show(status == 10 ? "MISMATCH_REJECTED" : "RETURNED_WITHOUT_SIGNIN");
    }
}
