import android.os.SystemClock;
import android.view.View;
import android.view.ViewGroup;
import android.widget.EditText;
import android.widget.ScrollView;
import android.widget.TextView;
import app.morphe.extension.simsimi.QuickReturn;

/** JVM contract test against minimal Android stand-ins; not an Android device test. */
public final class QuickReturnTest {
    private static int checks;
    private static void check(boolean result, String name) {
        if (!result) throw new AssertionError(name);
        checks++;
    }
    public static final class BottomBar extends View {
        int selected = 1;
        public int getCurrentItem() { return selected; }
    }
    private static final class Fixture {
        final ViewGroup root = new ViewGroup();
        final TextView header = new TextView("Conversation");
        final ScrollView list = new ScrollView();
        final ScrollView nested = new ScrollView();
        final BottomBar bar = new BottomBar();
        Fixture() {
            View.clearQueue();
            root.bounds(0, 0, 400, 900);
            header.bounds(0, 35, 400, 85);
            list.bounds(0, 100, 400, 800);
            list.scrollY = 1800;
            list.scrollX = 17;
            nested.bounds(100, 300, 300, 500);
            nested.scrollY = 300;
            bar.bounds(0, 800, 400, 900);
            list.addView(nested);
            root.addView(header);
            root.addView(list);
            root.addView(bar);
        }
        void click(long time, int index) {
            SystemClock.now = time;
            QuickReturn.onTabClicked(bar, index);
        }
    }
    public static void main(String[] args) {
        Fixture a = new Fixture();
        // No room-section labels are present: the user has scrolled far down.
        a.click(100, 1);
        check(a.list.scrollY == 1800 && View.queued() == 0, "single click never scrolls");
        a.click(350, 1);
        check(a.list.scrollY == 1800 && View.queued() == 1, "scroll is posted after original click");
        View.runAll();
        check(a.list.scrollY == 0 && a.list.calls == 1 && a.list.scrollX == 17, "double click scrolls main list to top");
        check(a.nested.scrollY == 300 && a.nested.calls == 0, "does not scroll a smaller nested pane");

        Fixture b = new Fixture();
        b.header.setText("A chat room");
        b.click(1000, 1); b.click(1200, 1); View.runAll();
        check(b.list.scrollY == 1800 && View.queued() == 0, "does not scroll an individual room");

        Fixture c = new Fixture();
        c.click(2000, 1); c.click(2200, 1);
        c.bar.selected = 2;
        View.runAll();
        check(c.list.scrollY == 1800, "changing tab before the posted action cancels it");

        Fixture d = new Fixture();
        d.click(3000, 1); d.click(3200, 1);
        d.header.setText("Other page");
        View.runAll();
        check(d.list.scrollY == 1800, "changing screen before the posted action cancels it");

        Fixture e = new Fixture();
        EditText focusedEditor = new EditText("private text is never read");
        focusedEditor.bounds(0, 700, 400, 780);
        e.root.addView(focusedEditor);
        e.root.focus = focusedEditor;
        e.click(4000, 1); e.click(4200, 1); View.runAll();
        check(e.list.scrollY == 1800, "visible focused editor blocks quick return");

        Fixture f = new Fixture();
        f.click(5000, 1); f.click(5200, 0); f.click(5300, 1); View.runAll();
        check(f.list.scrollY == 1800, "another tab resets the double-click sequence");
        f.click(6000, 1); f.click(6700, 1); View.runAll();
        check(f.list.scrollY == 1800, "slow clicks do not trigger");

        Fixture g = new Fixture();
        g.list.bounds(0, 100, 180, 190); // small/non-list scroll regions are rejected
        g.click(8000, 1); g.click(8100, 1); View.runAll();
        check(g.list.scrollY == 1800 && g.nested.scrollY == 300, "rejects small unrelated scroll views");

        Fixture h = new Fixture();
        h.click(9000, 1); h.click(9100, 1);
        h.bar.attached = false;
        View.runAll();
        check(h.list.scrollY == 1800, "detached navigation is not touched");

        Fixture i = new Fixture();
        i.bar.selected = 0;
        i.click(10000, 1);
        i.bar.selected = 1;
        i.click(10100, 1); View.runAll();
        check(i.list.scrollY == 1800, "switching into Chat is not counted as a selected-tab click");

        Fixture j = new Fixture();
        EditText roomEditor = new EditText("conversation text is never read");
        roomEditor.bounds(0, 700, 400, 780);
        j.root.addView(roomEditor); // not focused, as in a room with its keyboard hidden
        j.click(11000, 1); j.click(11100, 1); View.runAll();
        check(j.list.scrollY == 1800, "an unfocused visible room editor also blocks quick return");

        Fixture k = new Fixture();
        EditText hiddenEditor = new EditText("hidden text is never read");
        hiddenEditor.bounds(0, 700, 400, 780);
        hiddenEditor.shown = false;
        k.root.addView(hiddenEditor);
        k.click(12000, 1); k.click(12100, 1); View.runAll();
        check(k.list.scrollY == 0, "a hidden editor does not block the Conversation list");

        System.out.println(checks + " Quick Return view/click contract checks passed (JVM stubs)");
    }
}
