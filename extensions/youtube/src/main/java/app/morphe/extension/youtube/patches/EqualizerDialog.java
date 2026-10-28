package app.morphe.extension.youtube.patches;

import static app.morphe.extension.shared.StringRef.str;

import android.app.AlertDialog;
import android.content.Context;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.Switch;
import android.widget.TextView;
import java.util.Locale;
import app.morphe.extension.youtube.patches.EqualizerPatch;

/** Shared EQ controls for the player shortcut and the settings entry. */
public final class EqualizerDialog {
    private static java.lang.ref.WeakReference<AlertDialog> activeDialog = new java.lang.ref.WeakReference<>(null);
    private EqualizerDialog() { }

    public static void show(Context context) {
        if (context == null) return;
        AlertDialog current = activeDialog.get();
        if (current != null && current.isShowing()) return;
        LinearLayout content = new LinearLayout(context);
        content.setOrientation(LinearLayout.VERTICAL);
        int padding = (int) (20 * context.getResources().getDisplayMetrics().density);
        content.setPadding(padding, padding, padding, padding);
        ScrollView scroll = new ScrollView(context);
        scroll.addView(content);
        render(context, content);
        AlertDialog dialog = new AlertDialog.Builder(context).setTitle(str("morphe_equalizer_title")).setView(scroll)
                .setPositiveButton(android.R.string.ok, null).create();
        activeDialog = new java.lang.ref.WeakReference<>(dialog);
        dialog.setOnDismissListener(ignored -> {
            if (activeDialog.get() == dialog) activeDialog.clear();
        });
        dialog.show();
    }

    private static void render(Context context, LinearLayout content) {
        content.removeAllViews();
        Switch enabled = new Switch(context);
        enabled.setText(str("morphe_equalizer_enable"));
        enabled.setChecked(EqualizerPatch.isEnabled());
        content.addView(enabled);
        enabled.setOnCheckedChangeListener((button, checked) -> {
            EqualizerPatch.setEnabled(checked);
            render(context, content);
        });
        TextView status = new TextView(context);
        status.setText(EqualizerPatch.status());
        content.addView(status);
        int[][] bands = EqualizerPatch.bands();
        for (int b = 0; b < bands.length; b++) {
            final int band = b;
            final int min = bands[b][1];
            TextView label = new TextView(context);
            float hz = bands[b][0] / 1000f;
            String frequency = hz >= 1000 ? String.format(Locale.getDefault(), "%.1f kHz", hz / 1000) : String.format(Locale.getDefault(), "%.0f Hz", hz);
            label.setText(frequency + String.format(Locale.getDefault(), "  %+.1f dB", bands[b][3] / 100f));
            content.addView(label);
            SeekBar slider = new SeekBar(context);
            slider.setMax(bands[b][2] - min);
            slider.setProgress(bands[b][3] - min);
            content.addView(slider);
            slider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
                public void onProgressChanged(SeekBar bar, int value, boolean fromUser) {
                    if (fromUser) {
                        if (!EqualizerPatch.setBand(band, value + min)) {
                            bar.setEnabled(false);
                            status.setText(EqualizerPatch.status());
                        }
                        label.setText(frequency + String.format(Locale.getDefault(), "  %+.1f dB", (value + min) / 100f));
                    }
                }
                public void onStartTrackingTouch(SeekBar bar) { }
                public void onStopTrackingTouch(SeekBar bar) { }
            });
        }
        Button presets = new Button(context);
        presets.setText(str("morphe_equalizer_presets"));
        final String[] names = EqualizerPatch.presets();
        presets.setEnabled(names.length > 0);
        presets.setOnClickListener(v -> new AlertDialog.Builder(context).setTitle(str("morphe_equalizer_presets"))
                .setItems(names, (dialog, index) -> { EqualizerPatch.usePreset(index); render(context, content); }).show());
        content.addView(presets);
        Button reset = new Button(context);
        reset.setText(str("morphe_equalizer_reset"));
        reset.setOnClickListener(v -> { EqualizerPatch.reset(); render(context, content); });
        content.addView(reset);
        Button refresh = new Button(context);
        refresh.setText(str("morphe_equalizer_refresh"));
        refresh.setOnClickListener(v -> { EqualizerPatch.setEnabled(EqualizerPatch.isEnabled()); render(context, content); });
        content.addView(refresh);
    }
}
