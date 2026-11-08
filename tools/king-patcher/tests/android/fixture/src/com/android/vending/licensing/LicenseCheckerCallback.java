package com.android.vending.licensing;

/** Synthetic stand-in for the classic LVL callback ABI; no Play services involved. */
public interface LicenseCheckerCallback {
    void allow(int reason);
    void dontAllow(int reason);
    void applicationError(int reason);
}
