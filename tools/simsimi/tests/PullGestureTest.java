import app.morphe.extension.simsimi.PullGesture;
public final class PullGestureTest {
    static int checks;
    static void check(boolean result, String name) {
        if (!result) throw new AssertionError(name);
        checks++;
    }
    static boolean drag(PullGesture g, float sx, float sy, long start, float ex, float ey, long end, float density, boolean allowed) {
        g.down(sx,sy,start,density,allowed);
        g.move(sx,sy+100*density,start+100,density,allowed);
        return g.up(ex,ey,end,density);
    }
    public static void main(String[] args) {
        PullGesture g = new PullGesture();
        check(!g.up(0,200,300,1), "no down");
        check(drag(g,20,20,0,20,220,300,1,true),"vertical top swipe with real move");
        check(!drag(g,20,20,1000,20,220,1300,1,true),"debounced");
        check(!drag(g,20,120,6000,20,320,6300,1,true),"not top edge");
        g.down(20,20,7000,1,true); g.move(100,120,7100,1,true); check(!g.up(100,220,7300,1),"horizontal movement");
        check(!drag(g,20,20,8000,20,220,8300,1,false),"text input or scrolled content");
        g.down(20,20,9000,1,true); g.move(20,120,9100,1,true); g.cancel(); check(!g.up(20,220,9300,1),"cancelled or multi-touch");
        g.down(20,20,10000,1,true); g.move(20,120,10050,1,true); check(!g.up(20,100,10300,1),"too short");
        g.down(20,20,11000,1,true); g.move(20,120,11005,1,true); check(!g.up(20,220,11010,1),"not a swipe");
        g.down(20,20,12000,1,true); g.move(20,120,12100,1,true); check(!g.up(20,220,14000,1),"too slow");
        check(drag(g,40,40,15000,40,400,15300,2,true),"density scaling");
        check(!g.up(40,400,16000,2),"no repeated up");
        g.down(20,20,17000,1,true); check(!g.up(20,220,17300,1),"coordinate-changing up without move cannot reload");
        g.down(20,20,18000,1,true); g.move(20,120,18100,1,false); check(!g.up(20,220,18300,1),"navigation transition cancels active drag");
        g.down(20,20,19000,1,true); g.move(20,80,19100,1,true); check(!g.up(20,220,19300,1),"small move cannot arm reload");
        System.out.println(checks+" pull-to-reload gesture checks passed");
    }
}
