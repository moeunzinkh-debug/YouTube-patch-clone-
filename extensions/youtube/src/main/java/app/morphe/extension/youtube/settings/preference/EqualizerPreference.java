package app.morphe.extension.youtube.settings.preference;

import android.app.AlertDialog;
import android.content.Context;
import android.preference.Preference;
import android.util.AttributeSet;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.SeekBar;
import android.widget.Switch;
import android.widget.TextView;
import java.util.Locale;
import app.morphe.extension.youtube.patches.EqualizerPatch;

/** Dynamic controls reflect the actual device's Equalizer engine. */
@SuppressWarnings("deprecation")
public class EqualizerPreference extends Preference {
    public EqualizerPreference(Context context, AttributeSet attrs) {
        super(context, attrs);
        setPersistent(false);
    }

    @Override protected void onClick() {
        Context context = getContext();
        LinearLayout content = new LinearLayout(context);
        content.setOrientation(LinearLayout.VERTICAL);
        int padding = (int) (20 * context.getResources().getDisplayMetrics().density);
        content.setPadding(padding, padding, padding, padding);
        ScrollView scroll = new ScrollView(context);
        scroll.addView(content);
        render(content);
        new AlertDialog.Builder(context).setTitle(getTitle()).setView(scroll)
                .setPositiveButton(android.R.string.ok, null).show();
    }

    private void render(LinearLayout content) {
        content.removeAllViews();
        Context context = getContext();
        Switch enabled = new Switch(context);
        enabled.setText("Enable equalizer");
        enabled.setChecked(EqualizerPatch.isEnabled());
        content.addView(enabled);
        enabled.setOnCheckedChangeListener((button, checked) -> {
            EqualizerPatch.setEnabled(checked);
            render(content);
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
        presets.setText("Presets");
        final String[] names = EqualizerPatch.presets();
        presets.setEnabled(names.length > 0);
        presets.setOnClickListener(v -> new AlertDialog.Builder(context).setTitle("EQ presets")
                .setItems(names, (dialog, index) -> { EqualizerPatch.usePreset(index); render(content); }).show());
        content.addView(presets);
        Button reset = new Button(context);
        reset.setText("Reset to flat");
        reset.setOnClickListener(v -> { EqualizerPatch.reset(); render(content); });
        content.addView(reset);
        Button refresh = new Button(context);
        refresh.setText("Refresh audio session");
        refresh.setOnClickListener(v -> { EqualizerPatch.setEnabled(EqualizerPatch.isEnabled()); render(content); });
        content.addView(refresh);
    }
}
