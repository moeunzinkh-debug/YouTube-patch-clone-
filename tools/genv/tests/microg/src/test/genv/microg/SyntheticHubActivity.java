package test.genv.microg;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.os.Parcelable;
import com.google.android.gms.auth.api.signin.internal.SignInConfiguration;

/**
 * Models the reviewed intent handoff using synthetic code and a null-options
 * test parcel. It does not contain GenV code and cannot produce a login.
 */
public final class SyntheticHubActivity extends Activity {
    private static final String ACTION = "app.revanced.android.gms.auth.GOOGLE_SIGN_IN";
    private static final String MICROG_PACKAGE = "app.revanced.android.gms";
    private static final int REQUEST = 43;

    private void finishWith(int status) {
        setResult(RESULT_OK, new Intent().putExtra("test_status", status));
        finish();
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        if (state != null) return;
        if (!ACTION.equals(getIntent().getAction())) { finishWith(-1); return; }
        Bundle bundle = getIntent().getBundleExtra("config");
        if (bundle == null) { finishWith(-1); return; }
        bundle.setClassLoader(SignInConfiguration.class.getClassLoader());
        Parcelable config = bundle.getParcelable("config");
        if (!(config instanceof SignInConfiguration)) { finishWith(-1); return; }
        Intent route = new Intent(ACTION).setPackage(MICROG_PACKAGE).putExtra("config", config);
        try {
            startActivityForResult(route, REQUEST);
        } catch (Exception ignored) {
            finishWith(-1);
        }
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        int status = -1;
        if (requestCode == REQUEST && data != null) {
            try {
                status = data.getIntExtra("errorCode", -1);
            } catch (RuntimeException ignored) {
                // Report a fixed failure rather than logging intent contents.
            }
        }
        finishWith(status);
    }
}
