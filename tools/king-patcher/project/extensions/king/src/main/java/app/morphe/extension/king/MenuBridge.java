package app.morphe.extension.king;

import android.app.Activity;
import android.content.Intent;
import android.widget.Toast;

/** Called only from the inspected King-Patcher menu dispatcher. */
public final class MenuBridge {
    public static final int LVL_ID = 0x7e4d0001;
    public static final int UI_ID = 0x7e4d0002;
    private MenuBridge() {}
    public static boolean handle(Activity activity, int id) {
        int mode = id == LVL_ID ? ToolActivity.MODE_LVL : id == UI_ID ? ToolActivity.MODE_UI : 0;
        if (mode == 0) return false;
        if (activity == null || activity.isFinishing()) return true;
        try {
            Intent intent = new Intent(activity, ToolActivity.class).putExtra(ToolActivity.EXTRA_MODE, mode);
            activity.startActivity(intent);
        } catch (RuntimeException | LinkageError error) {
            Toast.makeText(activity, "Unable to open the experimental APK tool", Toast.LENGTH_LONG).show();
        }
        return true;
    }
}
