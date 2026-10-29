package android.widget;
import android.content.Context;
public class Toast { public static final int LENGTH_LONG=1; public static CharSequence last;
  private final CharSequence msg; private Toast(CharSequence x){msg=x;}
  public static Toast makeText(Context c,CharSequence s,int d){return new Toast(s);} public void show(){last=msg;}
}
