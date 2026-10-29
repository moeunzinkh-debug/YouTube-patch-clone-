package android.view;
import android.content.Context; import android.content.res.Resources;
public class View {
  public static final int VISIBLE=0, GONE=8; private Object tag; private int visibility=VISIBLE;
  private boolean enabled=true; private float alpha=1; private final Context context; private OnClickListener click;
  public View(Context c){context=c;} public Context getContext(){return context;} public Resources getResources(){return context.getResources();}
  public void setTag(Object x){tag=x;} public Object getTag(){return tag;}
  public void setVisibility(int v){visibility=v;} public int getVisibility(){return visibility;}
  public void setEnabled(boolean v){enabled=v;} public boolean isEnabled(){return enabled;}
  public void setAlpha(float v){alpha=v;} public float getAlpha(){return alpha;}
  public void setPadding(int l,int t,int r,int b){}
  public void setOnClickListener(OnClickListener l){click=l;}
  public boolean performClick(){if(!enabled || visibility!=VISIBLE || click==null)return false;click.onClick(this);return true;}
  public interface OnClickListener{void onClick(View v);}
}
