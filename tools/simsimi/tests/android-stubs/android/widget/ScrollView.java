package android.widget;
import android.view.ViewGroup;
public class ScrollView extends ViewGroup {
    public int scrollY, calls;
    @Override public boolean canScrollVertically(int direction) { return direction < 0 && scrollY > 0; }
    @Override public void scrollTo(int x,int y) { super.scrollTo(x,y); scrollY=y; calls++; }
}
