package dev.arena.khmerprobe;

import android.app.Activity;
import android.app.Instrumentation;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ApplicationInfo;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.util.Base64;

import org.json.JSONObject;

import java.io.InputStream;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.util.List;

/** Disposable, same-signature test inspector. Never included in the MPP. */
public final class AndroidGboardInspector extends Instrumentation {
    private Bundle arguments;

    @Override public void onCreate(Bundle args) {
        super.onCreate(args);
        arguments = args;
        start();
    }

    @Override public void onStart() {
        JSONObject diagnostic = new JSONObject();
        Bundle result = new Bundle();
        try {
            Context context = getTargetContext();
            ClassLoader loader = context.getClassLoader();
            ApplicationInfo info = context.getPackageManager().getApplicationInfo(
                    context.getPackageName(), PackageManager.GET_META_DATA);
            diagnostic.put("marker", info.metaData != null
                    && info.metaData.getBoolean("dev.jason.gboardpatches.feature.khmerlish", false));
            try (InputStream input = context.getAssets().open("gboard-khmer/dictionary.tsv")) {
                diagnostic.put("dictionary_asset_present", input.read() >= 0);
            }
            Class<?> settings = Class.forName(
                    "dev.jason.gboardpatches.extension.khmerlish.KhmerlishSettings", true, loader);
            if (arguments != null && "true".equals(arguments.getString("enable"))) {
                Object saved = settings.getMethod("setEnabled", Context.class, boolean.class)
                        .invoke(null, context, true);
                diagnostic.put("programmatic_set", saved);
            }
            diagnostic.put("preference", context.getSharedPreferences("gboard_patches_settings", 0)
                    .getBoolean("pref_khmerlish_to_khmer_enabled", false));
            diagnostic.put("runtime_enabled", settings.getMethod("isEnabled", Context.class)
                    .invoke(null, context));
            Class<?> registry = Class.forName(
                    "dev.jason.gboardpatches.extension.settings.GboardPatchesSettingsFeatureRegistry", true, loader);
            Method features = registry.getMethod("features", Context.class);
            List<?> list = (List<?>) features.invoke(null, context);
            boolean present = false;
            for (Object feature : list) {
                if (feature.getClass().getName().equals(
                        "dev.jason.gboardpatches.extension.khmerlish.KhmerlishSettingsFeature")) {
                    present = true;
                }
            }
            diagnostic.put("registry_entry", present);
            if (arguments != null && "true".equals(arguments.getString("open_settings"))) {
                Intent intent = new Intent();
                intent.setClassName(context, "dev.jason.gboardpatches.extension.settings.GboardPatchesSettingsActivity");
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                startActivitySync(intent);
                diagnostic.put("settings_activity_started", true);
                int holdMillis = Math.min(60000, Math.max(0,
                        Integer.parseInt(arguments.getString("hold_ms", "0"))));
                if (holdMillis > 0) Thread.sleep(holdMillis);
            }
        } catch (Throwable error) {
            try {
                Throwable cause = error.getCause() == null ? error : error.getCause();
                diagnostic.put("error_type", cause.getClass().getName());
            } catch (Exception ignored) { }
        }
        String payload = Base64.encodeToString(diagnostic.toString().getBytes(StandardCharsets.UTF_8), Base64.NO_WRAP);
        result.putString("diagnostic", payload);
        finish(Activity.RESULT_OK, result);
    }
}
