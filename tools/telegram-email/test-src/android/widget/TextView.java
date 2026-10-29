package android.widget;
import android.content.Context; import android.view.View;
public class TextView extends View {
  private CharSequence text; public TextView(Context c){super(c);} public void setGravity(int g){}
  public void setTextSize(float f){} public void setTextColor(int c){} public void setMinimumHeight(int h){}
  public void setText(CharSequence s){text=s;} public CharSequence getText(){return text;}
}
