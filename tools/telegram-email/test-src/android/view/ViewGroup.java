package android.view;
import android.content.Context; import java.util.ArrayList;
public class ViewGroup extends View {
  private final ArrayList<View> children=new ArrayList<>(); public ViewGroup(Context c){super(c);}
  public int getChildCount(){return children.size();} public View getChildAt(int i){return children.get(i);}
  public void addView(View v,int i,LayoutParams p){children.add(i,v);}
  public static class LayoutParams { public static final int MATCH_PARENT=-1,WRAP_CONTENT=-2; public LayoutParams(int w,int h){} }
}
