package android.widget;
import android.content.Context; import android.view.ViewGroup;
public class LinearLayout extends ViewGroup {
  public LinearLayout(Context c){super(c);}
  public static class LayoutParams extends ViewGroup.LayoutParams { public LayoutParams(int w,int h){super(w,h);} }
}
