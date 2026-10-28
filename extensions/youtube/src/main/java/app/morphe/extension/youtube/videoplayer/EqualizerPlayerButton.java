package app.morphe.extension.youtube.videoplayer;

import android.view.View;
import app.morphe.extension.shared.Logger;
import app.morphe.extension.youtube.patches.EqualizerDialog;
import app.morphe.extension.youtube.settings.Settings;

/** Uses the normal top-control chain and follows native control visibility. */
@SuppressWarnings("unused")
public final class EqualizerPlayerButton {
    static {
        if (Settings.EQUALIZER_PLAYER_BUTTON.get()) {
            LegacyPlayerControlButton.incrementUpperButtonCount();
        }
    }

    public static void initializeLegacyButton(View controlsView) {
        try {
            new LegacyPlayerControlButton(controlsView,
                    "morphe_equalizer_button", null, "morphe_equalizer_button",
                    Settings.EQUALIZER_PLAYER_BUTTON,
                    view -> EqualizerDialog.show(view.getContext()), null);
        } catch (Exception ex) {
            Logger.printException(() -> "EQ player button initialization failed", ex);
        }
    }
    private EqualizerPlayerButton() { }
}
