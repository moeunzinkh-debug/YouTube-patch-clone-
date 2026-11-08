package com.android.vending.licensing;

/** Synthetic denial to verify that the test patch actually changes the callback path. */
public class LicenseChecker {
    public void checkAccess(LicenseCheckerCallback callback) { callback.dontAllow(561); }
}
