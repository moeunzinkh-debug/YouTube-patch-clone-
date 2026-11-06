package dev.jason.gboardpatches.extension.khmerlish;

import android.content.Context;
import android.content.SharedPreferences;

import dev.jason.gboardpatches.extension.settings.GboardPatchesSettings;

/** This feature is always off until the user turns it on in Patches settings. */
public final class KhmerlishSettings {
    static final String KEY_ENABLED = "pref_khmerlish_to_khmer_enabled";

    private KhmerlishSettings() {}

    public static boolean isEnabled(Context context) {
        return GboardPatchesSettings.readRuntimeSetting(context,
                preferences -> preferences.getBoolean(KEY_ENABLED, false), false);
    }

    public static boolean setEnabled(Context context, boolean enabled) {
        try {
            SharedPreferences preferences = GboardPatchesSettings.preferences(context);
            return preferences.edit().putBoolean(KEY_ENABLED, enabled).commit();
        } catch (RuntimeException unavailable) {
            return false;
        }
    }
}
