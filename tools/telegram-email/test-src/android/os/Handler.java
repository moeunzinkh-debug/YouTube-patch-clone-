package android.os;
import java.util.ArrayList;
public class Handler {
  private static final class Job { final long time; final Runnable r; Job(long t,Runnable x){time=t;r=x;} }
  private static final ArrayList<Job> jobs=new ArrayList<>();
  public Handler(Looper l) {}
  public boolean post(Runnable r) { return postDelayed(r,0); }
  public boolean postDelayed(Runnable r,long delay){ jobs.add(new Job(SystemClock.now+Math.max(0,delay),r)); return true; }
  public static void reset(){ jobs.clear(); SystemClock.now=1000; }
  public static void advance(long ms){ SystemClock.now+=ms; runDue(); }
  public static void runDue(){
    for(int limit=0;limit<10000;limit++){
      Job best=null; for(Job j:jobs) if(j.time<=SystemClock.now && (best==null || j.time<best.time)) best=j;
      if(best==null) return; jobs.remove(best); best.r.run();
    } throw new AssertionError("runaway jobs");
  }
}
