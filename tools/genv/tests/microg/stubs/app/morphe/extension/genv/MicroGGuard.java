package app.morphe.extension.genv;

import android.content.Context;

// Compile-time only. The test APK contains the real classes2.dex from the MPP.
public final class MicroGGuard {
    public static boolean isAvailable(Context context) { throw new AssertionError("compile-time stub"); }
}
