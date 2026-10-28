import app.morphe.extension.simsimi.PullGesture;
public final class PullGestureTest {
    static int checks;
    static void check(boolean result, String name) {
        if (!result) throw new AssertionError(name);
        checks++;
    }
    public static void main(String[] args) {
        PullGesture g = new PullGesture();
        check(!g.up(0,200,300,1), "no down");
        g.down(20,20,0,1,true); check(g.up(20,220,300,1),"vertical top swipe");
        g.down(20,20,1000,1,true); check(!g.up(20,220,1300,1),"debounced");
        g.down(20,120,6000,1,true); check(!g.up(20,320,6300,1),"not top edge");
        g.down(20,20,7000,1,true); check(!g.up(100,220,7300,1),"horizontal movement");
        g.down(20,20,8000,1,false); check(!g.up(20,220,8300,1),"text input or scrolled content");
        g.down(20,20,9000,1,true); g.cancel(); check(!g.up(20,220,9300,1),"cancelled or multi-touch");
        g.down(20,20,10000,1,true); check(!g.up(20,100,10300,1),"too short");
        g.down(20,20,11000,1,true); check(!g.up(20,220,11010,1),"not a swipe");
        g.down(20,20,12000,1,true); check(!g.up(20,220,14000,1),"too slow");
        g.down(40,40,15000,2,true); check(g.up(40,400,15300,2),"density scaling");
        check(!g.up(40,400,16000,2),"no repeated up");
        System.out.println(checks+" pull-to-reload gesture checks passed");
    }
}
