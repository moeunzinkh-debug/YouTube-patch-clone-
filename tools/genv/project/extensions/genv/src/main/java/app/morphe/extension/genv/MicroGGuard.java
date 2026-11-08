package app.morphe.extension.genv;

import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageInfo;
import android.content.pm.PackageManager;
import android.content.pm.ResolveInfo;
import android.content.pm.Signature;

import java.security.MessageDigest;

/** Fail closed if Morphe's signed Google-sign-in service cannot be found. */
public final class MicroGGuard {
    private static final String PACKAGE = "app.revanced.android.gms";
    private static final String SIGN_IN_SERVICE =
            "app.revanced.android.gms.auth.api.signin.service.START";

    // APK signer certificate of the pinned MorpheApp/MicroG-RE 7.2.2 and 7.3.0
    // arm64 releases (SHA-256), NOT the source-stamp certificate.
    private static final byte[] SIGNER_SHA256 = {
            0x0b, 0x6c, (byte) 0x95, 0x15, (byte) 0xaf, (byte) 0xb1, (byte) 0x95, (byte) 0xfa,
            (byte) 0xc5, (byte) 0x96, 0x01, 0x69, 0x6b, (byte) 0xa0, (byte) 0xa7, (byte) 0x90,
            0x7a, 0x0b, 0x21, 0x7c, (byte) 0xcf, 0x72, 0x0b, 0x43,
            0x14, (byte) 0x84, 0x27, (byte) 0xcc, (byte) 0xf6, 0x43, 0x43, (byte) 0xe7
    };

    private MicroGGuard() { }

    @SuppressWarnings("deprecation") // GET_SIGNATURES is also available on Android 7-8.
    public static boolean isAvailable(Context context) {
        if (context == null) return false;
        try {
            PackageManager pm = context.getPackageManager();
            if (pm == null) return false;
            PackageInfo info = pm.getPackageInfo(PACKAGE, PackageManager.GET_SIGNATURES);
            if (info == null || info.applicationInfo == null || !info.applicationInfo.enabled) return false;
            Signature[] signatures = info.signatures;
            if (signatures == null || signatures.length != 1) return false;
            byte[] actual = MessageDigest.getInstance("SHA-256").digest(signatures[0].toByteArray());
            if (!MessageDigest.isEqual(SIGNER_SHA256, actual)) return false;

            Intent intent = new Intent(SIGN_IN_SERVICE).setPackage(PACKAGE);
            ResolveInfo result = pm.resolveService(intent, 0);
            return result != null && result.serviceInfo != null && result.serviceInfo.enabled
                    && result.serviceInfo.exported && PACKAGE.equals(result.serviceInfo.packageName);
        } catch (Exception | LinkageError ignored) {
            // No credentials, account data, or exception contents are logged.
            return false;
        }
    }
}
