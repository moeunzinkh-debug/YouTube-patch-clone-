// CI-ONLY synthetic host. Never included in the Morphe bundle or distributed APK.
package app.morphe.extension.instanttranslate;

import android.app.Activity;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;

public final class HarnessActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        SettingsUi.initialize(this);
        SettingsUi.attach(this);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        TextView title = new TextView(this); title.setText("Settings test harness (synthetic only)"); layout.addView(title);
        TextView result = new TextView(this); result.setText("NOT TESTED"); layout.addView(result);
        Button open = new Button(this); open.setText("Settings Patch >");
        open.setOnClickListener(v -> new SettingsClick().invoke()); layout.addView(open);
        Button verify = new Button(this); verify.setText("Verify saved fixture");
        verify.setOnClickListener(v -> {
            try {
                SeaLionClient.Config config = ProviderSettings.seaLionConfig();
                if (!SeaLionClient.DEFAULT_BASE.equals(config.baseUrl) || !SeaLionClient.DEFAULT_MODEL.equals(config.model) ||
                        !"fixture-key-2026".equals(config.key)) throw new IllegalStateException();
                final int[] calls = {0};
                ProviderRouter router = new ProviderRouter(ProviderSettings::selected,
                        (text, from, to) -> { calls[0]++; return "mock-sealion"; });
                if (!"mock-sealion".equals(router.translate("hola", "es", "en")) || calls[0] != 1) {
                    throw new IllegalStateException();
                }
                result.setText("SEA-LION CONFIG AND ROUTING OK");
            } catch (Exception ignored) { result.setText("CONFIG NOT VERIFIED"); }
        });
        layout.addView(verify);
        setContentView(layout);
    }
}
