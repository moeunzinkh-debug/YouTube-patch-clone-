package dev.jason.gboardpatches.extension.khmerlish;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import dev.jason.gboardpatches.extension.settings.GboardPatchesFeatureAvailability;
import dev.jason.gboardpatches.extension.settings.GboardPatchesSettingsContract;

/** The entry is visible only if its Morphe patch was selected. */
public final class KhmerlishSettingsFeature implements GboardPatchesSettingsContract.Feature {
    private static final String MARKER = "dev.jason.gboardpatches.feature.khmerlish";
    private static final String TITLE = "Khmerlish → ខ្មែរ (experimental)";
    private static final String SUMMARY = "បម្លែងអក្សរឡាតាំងទៅខ្មែរដោយប្រើវចនានុក្រម offline។";

    public KhmerlishSettingsFeature(Context context) {}

    /** Called by the injected settings registry hook before its list is frozen. */
    public static void append(Context context, List<GboardPatchesSettingsContract.Feature> features) {
        try {
            if (features != null && GboardPatchesFeatureAvailability.hasFeature(context, MARKER)) {
                features.add(new KhmerlishSettingsFeature(context));
            }
        } catch (Throwable ignored) {
            // A broken or unavailable feature must not prevent other Patches settings from opening.
        }
    }

    @Override public String getEntryTitle() { return TITLE; }
    @Override public String getEntrySummary() { return SUMMARY; }
    @Override public boolean isAvailable(Context context) {
        return GboardPatchesFeatureAvailability.hasFeature(context, MARKER);
    }

    @Override public GboardPatchesSettingsContract.Screen buildScreen(
            GboardPatchesSettingsContract.FeatureHost host) {
        Context context = host == null ? null : host.getContext();
        boolean enabled = context != null && KhmerlishSettings.isEnabled(context);
        return new GboardPatchesSettingsContract.Screen(
                TITLE, "Patches", TITLE, SUMMARY,
                Collections.emptyList(),
                Arrays.asList(
                        new GboardPatchesSettingsContract.Section("មុខងារ / Feature",
                                Collections.singletonList(
                                        new GboardPatchesSettingsContract.ToggleRow(
                                                "បើក Khmerlish → ខ្មែរ",
                                                "Automatic conversion in normal typing; default off. The toolbar panel works separately.",
                                                context != null, enabled,
                                                value -> KhmerlishSettings.setEnabled(context, value)))),
                        new GboardPatchesSettingsContract.Section("វចនានុក្រម / Dictionary",
                                Collections.singletonList(
                                        new GboardPatchesSettingsContract.NavigationRow(
                                                "Personal Dictionary & Documents",
                                                "បន្ថែមពាក្យផ្ទាល់ខ្លួន · មើល ស្វែងរក និងនាំចូលបញ្ជីពាក្យ offline",
                                                context != null, () -> openDictionary(context)))),
                        new GboardPatchesSettingsContract.Section("ការប្រើប្រាស់ / Usage",
                                Arrays.asList(
                                        new GboardPatchesSettingsContract.InfoRow(
                                                "សរសេរជាអក្សរឡាតាំង",
                                                "nv na → នៅណា · kampu → កម្ពុជា · nik o → នឹកអូន", true),
                                        new GboardPatchesSettingsContract.InfoRow(
                                                "ដែនកំណត់ និងឯកជនភាព",
                                                "Offline only. Unknown or ambiguous spellings stay unchanged. " +
                                                "English words may also match. Password, email, URL and " +
                                                "no-suggestions fields are excluded. Turn off Gboard " +
                                                "autocorrect if it replaces Khmerlish before this feature can act.",
                                                true)))));
    }

    private static void openDictionary(Context context) {
        if (context == null) return;
        try {
            Intent intent = new Intent(context, KhmerlishDictionaryActivity.class);
            if (!(context instanceof Activity)) intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            context.startActivity(intent);
        } catch (Throwable unavailable) {
            // Leave the existing Gboard settings screen usable on incompatible targets.
            android.widget.Toast.makeText(context, "Khmerlish dictionary is unavailable", android.widget.Toast.LENGTH_SHORT).show();
        }
    }
}
