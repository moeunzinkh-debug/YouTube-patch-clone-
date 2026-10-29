package android.widget;
import android.view.View;
public class TextView extends View {
    private CharSequence text;
    public TextView(CharSequence text) { this.text=text; }
    public CharSequence getText() { return text; }
    public void setText(CharSequence text) { this.text=text; }
}
