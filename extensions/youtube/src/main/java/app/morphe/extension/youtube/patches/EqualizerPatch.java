package app.morphe.extension.youtube.patches;

import static app.morphe.extension.shared.StringRef.str;

import android.content.Context;
import android.content.SharedPreferences;
import android.media.audiofx.Equalizer;
import app.morphe.extension.shared.Logger;
import app.morphe.extension.shared.Utils;

/** One effect attached to YouTube's current session, never the output mix. */
public final class EqualizerPatch {
    private static Equalizer effect;
    private static int session;
    private static String failure = "";

    private EqualizerPatch() { }

    private static SharedPreferences prefs() {
        return Utils.getContext().getSharedPreferences("morphe_equalizer", Context.MODE_PRIVATE);
    }

    public static synchronized boolean isEnabled() {
        return prefs().getBoolean("enabled", false);
    }

    public static synchronized void onAudioSessionId(int id) {
        try {
            if (id == session && effect != null) return;
            if (id != session) release();
            session = id;
            apply();
        } catch (RuntimeException ex) { failed(ex); }
    }

    public static synchronized void setEnabled(boolean enabled) {
        prefs().edit().putBoolean("enabled", enabled).apply();
        apply();
    }

    private static void apply() {
        failure = "";
        if (!isEnabled() || session <= 0) {
            release();
            return;
        }
        try {
            if (effect == null) effect = new Equalizer(0, session);
            if (!effect.hasControl()) {
                failure = str("morphe_equalizer_control_lost");
                release();
                return;
            }
            short[] range = effect.getBandLevelRange();
            for (short band = 0; band < effect.getNumberOfBands(); band++) {
                int level = prefs().getInt(key(band), 0);
                effect.setBandLevel(band, (short) Math.max(range[0], Math.min(range[1], level)));
            }
            if (effect.setEnabled(true) != android.media.audiofx.AudioEffect.SUCCESS) {
                throw new IllegalStateException("EQ engine did not enable");
            }
        } catch (RuntimeException ex) {
            failed(ex);
        }
    }

    private static String key(short band) {
        return "frequency_" + effect.getCenterFreq(band);
    }

    private static void release() {
        if (effect != null) {
            try { effect.release(); }
            catch (RuntimeException ex) { Logger.printException(() -> "EQ release failed", ex); }
            finally { effect = null; }
        }
    }

    private static void failed(RuntimeException ex) {
        failure = str("morphe_equalizer_unavailable");
        Logger.printException(() -> "YouTube equalizer unavailable", ex);
        release();
    }

    public static synchronized String status() {
        if (!failure.isEmpty()) return failure;
        if (!isEnabled()) return str("morphe_equalizer_off");
        if (effect == null) return str("morphe_equalizer_no_session");
        return str("morphe_equalizer_active");
    }

    /** A UI snapshot, rather than exposing an AudioEffect across threads. */
    public static synchronized int[][] bands() {
        if (effect == null) return new int[0][];
        try {
            short[] range = effect.getBandLevelRange();
            int count = effect.getNumberOfBands();
            int[][] result = new int[count][4];
            for (short band = 0; band < count; band++) {
                result[band] = new int[] {effect.getCenterFreq(band), range[0], range[1], effect.getBandLevel(band)};
            }
            return result;
        } catch (RuntimeException ex) {
            failed(ex);
            return new int[0][];
        }
    }

    public static synchronized boolean setBand(int band, int millibels) {
        if (effect == null) return false;
        try {
            if (!effect.hasControl()) {
                failure = str("morphe_equalizer_control_lost");
                release();
                return false;
            }
            if (band < 0 || band >= effect.getNumberOfBands()) return false;
            short[] range = effect.getBandLevelRange();
            short level = (short) Math.max(range[0], Math.min(range[1], millibels));
            effect.setBandLevel((short) band, level);
            prefs().edit().putInt(key((short) band), level).apply();
            return true;
        } catch (RuntimeException ex) {
            failed(ex);
            return false;
        }
    }

    public static synchronized String[] presets() {
        if (effect == null) return new String[0];
        try {
            String[] names = new String[effect.getNumberOfPresets()];
            for (short i = 0; i < names.length; i++) names[i] = effect.getPresetName(i);
            return names;
        } catch (RuntimeException ex) {
            failed(ex);
            return new String[0];
        }
    }

    public static synchronized void usePreset(int index) {
        if (effect == null) return;
        try {
            if (index < 0 || index >= effect.getNumberOfPresets()) return;
            effect.usePreset((short) index);
            SharedPreferences.Editor editor = prefs().edit();
            for (short b = 0; b < effect.getNumberOfBands(); b++) editor.putInt(key(b), effect.getBandLevel(b));
            editor.apply();
        } catch (RuntimeException ex) { failed(ex); }
    }

    public static synchronized void reset() {
        boolean enabled = isEnabled();
        prefs().edit().clear().putBoolean("enabled", enabled).apply();
        apply();
    }
}
