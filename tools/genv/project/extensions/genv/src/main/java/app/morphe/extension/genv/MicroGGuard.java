package app.morphe.extension.genv;

import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.content.pm.Signature;
import android.os.Build;
import android.os.Handler;
import android.os.Looper;
import android.widget.Toast;

import java.security.MessageDigest;

/** Fail closed if Morphe's signed Google-sign-in service cannot be found. */
public final class MicroGGuard {
    private static final String PACKAGE = "app.revanced.android.gms";
    private static final String SIGN_IN_SERVICE =
            "app.revanced.android.gms.auth.api.signin.service.START";
    private static final String SIGN_IN_ACTIVITY = "app.revanced.android.gms.auth.GOOGLE_SIGN_IN";
    private static final String EXPECTED_SERVICE = "org.microg.gms.auth.signin.AuthSignInService";
    private static final String EXPECTED_ACTIVITY = "org.microg.gms.auth.signin.AuthSignInActivity";

    // APK signer certificate of the pinned MorpheApp/MicroG-RE 7.2.2 and 7.3.0
    // arm64 releases (SHA-256), NOT the source-stamp certificate.
    private static final byte[] SIGNER_SHA256 = {
            0x0b, 0x6c, (byte) 0x95, 0x15, (byte) 0xaf, (byte) 0xb1, (byte) 0x95, (byte) 0xfa,
            (byte) 0xc5, (byte) 0x96, 0x01, 0x69, 0x6b, (byte) 0xa0, (byte) 0xa7, (byte) 0x90,
            0x7a, 0x0b, 0x21, 0x7c, (byte) 0xcf, 0x72, 0x0b, 0x43,
            0x14, (byte) 0x84, 0x27, (byte) 0xcc, (byte) 0xf6, 0x43, 0x43, (byte) 0xe7
    };

    private MicroGGuard() { }

    /**
     * Called only when GenV builds its interactive sign-in intent. The fixed
     * local status toast contains no account, credential, token or exception
     * information. A successful guard check does not mean login succeeded.
     */
    public static boolean prepareSignIn(Context context) {
        final boolean trusted = isAvailable(context);
        if (context != null) {
            try {
                Context app = context.getApplicationContext();
                final Context toastContext = app == null ? context : app;
                new Handler(Looper.getMainLooper()).post(() -> {
                    try {
                        Toast.makeText(toastContext,
                                trusted ? "GenV MicroG: MG00 (check passed)" : "GenV MicroG: MG01 (check failed)",
                                Toast.LENGTH_LONG).show();
                    } catch (Exception | LinkageError ignored) {
                        // Showing a diagnostic must not crash GenV.
                    }
                });
            } catch (Exception | LinkageError ignored) {
                // A diagnostic display must never change the guard's decision.
            }
        }
        return trusted;
    }

    @SuppressWarnings("deprecation") // GET_SIGNATURES is also available on Android 7-8.
    public static boolean isAvailable(Context context) {
        if (context == null) return false;
        try {
            PackageManager pm = context.getPackageManager();
            if (pm == null) return false;
            int flags = Build.VERSION.SDK_INT >= 28 ? 0 : PackageManager.GET_SIGNATURES;
            PackageInfo info = pm.getPackageInfo(PACKAGE, flags);
            if (info == null || info.applicationInfo == null || !info.applicationInfo.enabled) return false;
            if (Build.VERSION.SDK_INT >= 28) {
                // Ask the package manager about the installed signing lineage
                // rather than relying on the legacy, sometimes spoofed field.
                if (!pm.hasSigningCertificate(PACKAGE, SIGNER_SHA256, PackageManager.CERT_INPUT_SHA256)) return false;
            } else {
                Signature[] signatures = info.signatures;
                if (signatures == null || signatures.length != 1) return false;
                byte[] actual = MessageDigest.getInstance("SHA-256").digest(signatures[0].toByteArray());
                if (!MessageDigest.isEqual(SIGNER_SHA256, actual)) return false;
            }

            ResolveInfo service = pm.resolveService(new Intent(SIGN_IN_SERVICE).setPackage(PACKAGE), 0);
            if (service == null || service.serviceInfo == null || !service.serviceInfo.enabled
                    || !service.serviceInfo.exported || !PACKAGE.equals(service.serviceInfo.packageName)
                    || !EXPECTED_SERVICE.equals(service.serviceInfo.name)) return false;
            ResolveInfo activity = pm.resolveActivity(new Intent(SIGN_IN_ACTIVITY).setPackage(PACKAGE), 0);
            return activity != null && activity.activityInfo != null && activity.activityInfo.enabled
                    && activity.activityInfo.exported && PACKAGE.equals(activity.activityInfo.packageName)
                    && EXPECTED_ACTIVITY.equals(activity.activityInfo.name);
        } catch (Exception | LinkageError ignored) {
            // No credentials, account data, or exception contents are logged.
            return false;
        }
    }
}
