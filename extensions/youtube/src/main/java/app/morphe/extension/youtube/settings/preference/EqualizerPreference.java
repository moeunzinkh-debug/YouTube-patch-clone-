package app.morphe.extension.youtube.settings.preference;

import android.content.Context;
import android.preference.Preference;
import android.util.AttributeSet;
import app.morphe.extension.youtube.patches.EqualizerDialog;

/** Settings entry uses the same dialog as the player shortcut. */
@SuppressWarnings("deprecation")
public class EqualizerPreference extends Preference {
    public EqualizerPreference(Context context, AttributeSet attrs) {
        super(context, attrs);
        setPersistent(false);
    }
    @Override protected void onClick() {
        EqualizerDialog.show(getContext());
    }
}
