import app.morphe.extension.youtube.patches.EqualizerPatch;
import android.media.audiofx.Equalizer;
public class EqualizerControllerTest {
 static int checks;
 static void check(boolean b,String message){checks++;if(!b)throw new AssertionError(message);}
 public static void main(String[] args){
  check(!EqualizerPatch.isEnabled(),"off by default");
  EqualizerPatch.setEnabled(true);EqualizerPatch.onAudioSessionId(0);
  check(Equalizer.created==0,"never touch global output mix");
  EqualizerPatch.onAudioSessionId(10);
  check(EqualizerPatch.bands().length==2,"actual band count");
  check(EqualizerPatch.setBand(0,100000),"set band");
  check(Equalizer.last.getBandLevel((short)0)==1500,"clamp to hardware range");
  Equalizer old=Equalizer.last;EqualizerPatch.onAudioSessionId(11);
  check(old.released,"release on session replacement");
  check(Equalizer.last.getBandLevel((short)0)==1500,"restore saved gain");
  int created=Equalizer.created;EqualizerPatch.onAudioSessionId(11);
  check(created==Equalizer.created,"no duplicate effect on same session");
  EqualizerPatch.setEnabled(false);check(Equalizer.last.released,"release on disable");
  EqualizerPatch.setEnabled(true);check(Equalizer.last.getBandLevel((short)0)==1500,"restore on enable");
  EqualizerPatch.reset();check(Equalizer.last.getBandLevel((short)0)==0,"reset to flat");
  check(EqualizerPatch.presets().length==2,"enumerate hardware presets");
  EqualizerPatch.usePreset(1);EqualizerPatch.onAudioSessionId(12);
  check(Equalizer.last.getBandLevel((short)0)==500,"persist preset band gains");
  check(!EqualizerPatch.setBand(99,0),"reject invalid band");
  Equalizer.last.control=false;check(!EqualizerPatch.setBand(0,0),"handle lost control");
  check(EqualizerPatch.status().endsWith("control_lost"),"control loss status");
  Equalizer.failCreate=true;EqualizerPatch.onAudioSessionId(13);
  check(EqualizerPatch.bands().length==0,"unsupported engine does not crash");
  check(EqualizerPatch.status().endsWith("unavailable"),"hardware failure status");
  System.out.println("PASS: "+checks+" EQ controller checks (test doubles; not a real-device audio test)");
 }
}
