package test.genv.microg;

import android.app.Activity;
import android.content.Intent;
import android.content.pm.ResolveInfo;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.os.Bundle;
import android.widget.TextView;
import app.morphe.extension.genv.MicroGGuard;

/** Offline test of package visibility and the exact MPP extension's guard. */
public final class ProbeActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        String pkg = "app.revanced.android.gms";
        ResolveInfo service = getPackageManager().resolveService(
                new Intent(pkg + ".auth.api.signin.service.START").setPackage(pkg), 0);
        ResolveInfo activity = getPackageManager().resolveActivity(
                new Intent(pkg + ".auth.GOOGLE_SIGN_IN").setPackage(pkg), 0);
        String serviceName = service == null || service.serviceInfo == null ? "NONE"
                : "org.microg.gms.auth.signin.AuthSignInService".equals(service.serviceInfo.name) ? "AUTH" : "OTHER";
        String activityName = activity == null || activity.activityInfo == null ? "NONE"
                : "org.microg.gms.auth.signin.AuthSignInActivity".equals(activity.activityInfo.name) ? "AUTH" : "OTHER";
        ConnectivityManager connectivity = (ConnectivityManager) getSystemService(CONNECTIVITY_SERVICE);
        @SuppressWarnings("deprecation") NetworkInfo active = connectivity == null ? null : connectivity.getActiveNetworkInfo();
        String network = active != null && active.isConnected() ? "ON" : "OFF";
        boolean available = MicroGGuard.isAvailable(this);
        boolean prepared = MicroGGuard.prepareSignIn(this);
        // Simulate the injected cache-write decision with the exact MPP guard;
        // this is not the real GenV class or a successful authentication.
        int syntheticStaleMode = 2;
        if (prepared) syntheticStaleMode = 4;
        TextView result = new TextView(this);
        result.setText("GUARD:" + (available ? "YES" : "NO")
                + ";SERVICE:" + serviceName + ";ACTIVITY:" + activityName
                + ";PREPARE:" + (prepared ? "YES" : "NO") + ";MODE:" + syntheticStaleMode
                + ";NETWORK:" + network);
        result.setTextSize(20);
        setContentView(result);
    }
}
